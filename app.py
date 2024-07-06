# -*- coding: utf-8 -*-
import base64
import json
import math
from pathlib import Path
import pandas as pd
from flask_cors import CORS
import threading
import waitress

from flask import Flask, request, send_file
from SqlCursor import Cursor
import os

LOCK = threading.Lock()

app = Flask(__name__)

CORS(app)

# fetch absolute file path for the script
script_dir = os.path.dirname(os.path.abspath(__file__))
# fetch absolute file path for audio directory
audio_dir = os.path.join(script_dir, '..', 'static', 'audio', 'Tai_audio_test')

# initial sql cursor
SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()
STUDENT_DATA = []
EXAM_QUESTIONS = {}
CORRECTION_DIR_ABSOLUTE_FILE_PATH = os.path.join(script_dir, "學生校正資料")


def calc_correction_progress(assessments: dict) -> int:
    count_list = [1 if x != "" else 0 for x in assessments.values()]

    return math.floor(sum(count_list) / len(count_list)) * 100


def fetch_school_region():
    global SQL_CURSOR

    with LOCK:
        sql = "SELECT `學校代碼`, `鄉鎮市區`, `學校名稱`, `區域` FROM `region_of_elementary_school`;"
        SQL_CURSOR.execute(sql)
        SQL_CONNECTION.commit()
        result_elementary = SQL_CURSOR.fetchall()
        sql = "SELECT `學校代碼`, `鄉鎮市區`, `學校名稱`, `區域` FROM `region_of_junior_high_school`;"
        SQL_CURSOR.execute(sql)
        SQL_CONNECTION.commit()
        result_junior = SQL_CURSOR.fetchall()

    north_area, south_area, east_area, mid_area = set(), set(), set(), set()

    for school_code, _, school_name, region in set(result_elementary).union(set(result_junior)):
        cur_school = f"{school_name}{school_code}"
        if region == "北區":
            north_area.add(cur_school)
        elif region == "南區":
            south_area.add(cur_school)
        elif region == "東區":
            east_area.add(cur_school)
        elif region == "中區":
            mid_area.add(cur_school)

    return north_area, south_area, east_area, mid_area


@app.route('/get_correction_details', methods=["POST"])
# renewed
def get_correction_details():
    student_key = request.get_json()["studentKey"]
    with LOCK:
        SQL_CURSOR.execute("SELECT assessments FROM student_correction WHERE student_id=%s", student_key)
        fetch_result = SQL_CURSOR.fetchone()

    if fetch_result:
        assessment_detail = eval(fetch_result[0])
    else:
        assessment_detail = {}

    return json.dumps(assessment_detail, ensure_ascii=False)


@app.route('/filter_by_options', methods=["POST"])
# renewed
def filter_by_options():
    options = request.get_json()["options"]
    school_name = options["schoolName"] if len(options["schoolName"]) > 0 else '%%'
    student_class = options["studentClass"] if len(options["studentClass"]) > 0 else '%%'
    student_grade = options["grade"] if len(options["grade"]) > 0 else '%%'

    sql = f"""
        SELECT RecordID FROM all_student_2023_new 
        WHERE `RecordID` LIKE '{school_name}\_%%\_%%_{student_grade}\_{student_class}\_%%\_%%\_%%\_%%';
        """

    SQL_CURSOR.execute(sql)
    SQL_CONNECTION.commit()

    result = SQL_CURSOR.fetchall()
    filter_storage = []

    for student in result:
        split_by_underline = student[0].split("_")
        filter_storage.append({
            "schoolName": split_by_underline[0],
            "studentName": split_by_underline[1],
            "gender": split_by_underline[2],
            "grade": split_by_underline[3],
            "studentClass": split_by_underline[4],
            "seatNumber": split_by_underline[5],
            "birthdayYear": split_by_underline[6],
            "birthdayMonth": split_by_underline[7],
            "birthdayDay": split_by_underline[8]
        })
    return json.dumps(filter_storage, ensure_ascii=False, indent=10)


@app.route('/update_correction_details', methods=["POST"])
def update_correction_details():
    obj = request.get_json()
    student_id, question_index, update_val = obj["studentId"], obj["questionIndex"], obj["value"]
    try:
        with LOCK:
            SQL_CURSOR.execute(f"""
                                update student_correction 
                                SET assessments=JSON_SET(assessments, '$."{question_index}"', '{update_val}') 
                                where student_id='{student_id}'
                                """)
            SQL_CONNECTION.commit()

        return "OK"
    except Exception as e:
        print(e)


@app.route('/fetch_test_question', methods=["POST"])
# renewed
def fetch_test_question():
    student_level = request.get_json()["studentLevel"]
    with LOCK:
        SQL_CURSOR.execute("select questions from question_table where questions_name=%s", student_level)
        fetch_result = SQL_CURSOR.fetchone()

    if fetch_result:
        questions = eval(fetch_result[0])

        order = questions['_order']
        question_list = questions['question_list']

        result = [question_list[x] for x in order]
        return json.dumps({"_order": order, "questionList": result}, ensure_ascii=False)
    else:
        return json.dumps({})


@app.route('/fetch_filter_selection', methods=["GET"])
# renewed
def fetch_filter_selection():
    global STUDENT_DATA
    SQL_CURSOR.execute("SELECT RecordID from all_student_2023_new;")
    SQL_CONNECTION.commit()
    result = SQL_CURSOR.fetchall()

    distinct_school_name = set()
    distinct_student_class = set()
    distinct_grade = set()

    for student in result:
        split_by_underline = student[0].split("_")

        distinct_school_name.add(split_by_underline[0])
        distinct_student_class.add(split_by_underline[4])
        distinct_grade.add(split_by_underline[3])

    # for student in STUDENT_DATA:
    #     distinct_school_name.add(student["schoolName"])
    #     distinct_student_class.add(student["studentClass"])
    #     distinct_grade.add(student["grade"])

    return json.dumps({
        "distinctSchoolName": list(distinct_school_name),
        "distinctStudentClass": sorted(list(distinct_student_class), key=int),
        "distinctGrade": sorted(list(distinct_grade))
    }, ensure_ascii=False)


@app.route('/get_correction_progress', methods=["POST"])
# renewed
def get_correction_progress():
    student_key = request.get_json()["studentKey"]
    with LOCK:
        SQL_CURSOR.execute("SELECT assessments from student_correction where student_id=%s", student_key)
        assessments = SQL_CURSOR.fetchone()

    progress = 0
    if assessments:
        progress = calc_correction_progress(eval(assessments[0]))

    return json.dumps({
        "progress": progress
    }, ensure_ascii=False)


@app.route('/get_record_file', methods=["POST"])
# renewed
def get_record_file():
    req = request.get_json()
    student = req["grade_studentClass_seatNumber_studentName"]
    school_name = req["schoolName"]
    question_number = req["questionNumber"]

    path_of_audio = ""

    full_path = os.path.join(audio_dir, school_name, student)
    print(full_path)
    for root, dirs, files in os.walk(full_path):
        for file in files:
            if file.endswith(f"2_{question_number}.wav"):
                path_of_audio = os.path.join(root, file)
                break

    try:
        base64_encoder = base64.b64encode(open(path_of_audio, "rb").read())
        base64_decoder = base64_encoder.decode("utf-8")
    except FileNotFoundError as error:
        print(error)
        base64_decoder = ""
    return json.dumps({"base64String": base64_decoder}, ensure_ascii=False)


@app.route('/save_correction_data', methods=["POST"])
# pending
def save_correction_data():
    """
    save correction data for corresponding question number
    :return:
    """

    req = request.get_json()
    question_number = req["questionNumber"]
    correction_data = req["correctionData"]
    schoolName_grade_studentClass_seatNumber_studentName = req["schoolName_grade_studentClass_seatNumber_studentName"]
    birthday = req["birthday"]
    gender = req["gender"]
    file_name = f"{schoolName_grade_studentClass_seatNumber_studentName}_{birthday}_{gender}"
    student_correction_data = {}
    # check the file existence first, then write the file
    try:
        try:

            with open(f'{os.path.join(CORRECTION_DIR_ABSOLUTE_FILE_PATH, file_name)}.js',
                      'r', encoding='utf-8') as js_file:
                student_correction_data = json.loads(js_file.read())
            return_message = "FILE FOUND"

        except FileNotFoundError as e:
            print(e)
            return_message = "NEW FILE CREATED"

        student_correction_data[question_number] = correction_data
        with open(f'{os.path.join(CORRECTION_DIR_ABSOLUTE_FILE_PATH, file_name)}.js',
                  'w', encoding='utf-8') as write_file:
            write_file.write(json.dumps(student_correction_data, ensure_ascii=False))
    except Exception as big_error:
        print(big_error)
        return "ERROR"

    return return_message


@app.route('/output_xlsx', methods=["POST"])
# pending
def output_xlsx():
    """
    only output the current saved data
    :return:
    """
    exportType: bool = request.get_json()['exportType']
    north_area, south_area, east_area, mid_area = fetch_school_region()
    agg_north_area, agg_south_area, agg_east_area, agg_mid_area = [], [], [], []

    try:
        aggregated_data = []
        with open(os.path.join(script_dir, 'question_mapper.json'), 'r', encoding='utf-8') as qm:
            question_mapper = json.loads(qm.read())

        for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
            for file in files:
                if file.endswith('.js'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as correction_js:
                        current_student_correction_data = json.loads(correction_js.read())
                    current_student_personal_information = Path(file).stem.split('_')

                    extract_correctness = question_mapper["correction_dict"].copy()

                    if exportType:
                        for correctness in current_student_correction_data.keys():
                            if current_student_correction_data[correctness] == "1":
                                extract_correctness[correctness] = "1"
                            elif current_student_correction_data[correctness] == "2":
                                extract_correctness[correctness] = "0"
                            elif current_student_correction_data[correctness] == "4":
                                extract_correctness[correctness] = "2"
                            elif current_student_correction_data[correctness] == "3":
                                extract_correctness[correctness] = "3"
                            else:
                                extract_correctness[correctness] = "X"

                    else:
                        for correctness in current_student_correction_data.keys():
                            if current_student_correction_data[correctness] == "1":
                                extract_correctness[correctness] = "1"
                            elif current_student_correction_data[correctness] in {"2", "3", "4"}:
                                extract_correctness[correctness] = "0"
                            elif current_student_correction_data[correctness] == "X":
                                extract_correctness[correctness] = "X"

                    current_student_correction_data_list_form = [x for x in current_student_personal_information]
                    current_student_correction_data_list_form[-1] = \
                        "男" if current_student_correction_data_list_form[-1] == "1" else "女"

                    for index in question_mapper["question_index"]:
                        current_student_correction_data_list_form.append(extract_correctness[index])

                    aggregated_data.append(current_student_correction_data_list_form)

                    current_school = current_student_personal_information[0]

                    if current_school in north_area:
                        agg_north_area.append(current_student_correction_data_list_form)
                    elif current_school in south_area:
                        agg_south_area.append(current_student_correction_data_list_form)
                    elif current_school in east_area:
                        agg_east_area.append(current_student_correction_data_list_form)
                    elif current_school in mid_area:
                        agg_mid_area.append(current_student_correction_data_list_form)
        column_of_student_information = ["學校名稱", "年級", "班級", "座號", "學生姓名", "生日(年)", "生日(月)",
                                         "生日(日)", "性別"] + question_mapper["question_list"]

        # collects every student's data
        aggregate_dataframe = pd.DataFrame(aggregated_data, columns=column_of_student_information)

        # collect only if the student's school is in that area
        agg_north_area_dataframe = pd.DataFrame(agg_north_area, columns=column_of_student_information)
        agg_south_area_dataframe = pd.DataFrame(agg_south_area, columns=column_of_student_information)
        agg_east_area_dataframe = pd.DataFrame(agg_east_area, columns=column_of_student_information)
        agg_mid_area_dataframe = pd.DataFrame(agg_mid_area, columns=column_of_student_information)

        if aggregate_dataframe.size == 0:
            return "NO FILE EXIST", 400

        save_file_name = "output_fully.xlsx" if exportType else "output_pruned.xlsx"

        # save to local
        aggregate_dataframe.to_excel(os.path.join(script_dir, save_file_name), index=False)

        # write to each sheet if that area's DataFrame is not empty
        with pd.ExcelWriter(os.path.join(script_dir, save_file_name), engine='openpyxl') as writer:
            if not aggregate_dataframe.empty:
                print("Writing '總表'")
                aggregate_dataframe.to_excel(writer, sheet_name='總表', index=False)
            else:
                print("Skipped writing '總表' as the DataFrame is empty.")

            if not agg_north_area_dataframe.empty:
                print("Writing '北區'")
                agg_north_area_dataframe.to_excel(writer, sheet_name='北區', index=False)
            else:
                print("Skipped writing '北區' as the DataFrame is empty.")

            if not agg_south_area_dataframe.empty:
                print("Writing '南區'")
                agg_south_area_dataframe.to_excel(writer, sheet_name='南區', index=False)
            else:
                print("Skipped writing '南區' as the DataFrame is empty.")

            if not agg_east_area_dataframe.empty:
                print("Writing '東區'")
                agg_east_area_dataframe.to_excel(writer, sheet_name='東區', index=False)
            else:
                print("Skipped writing '東區' as the DataFrame is empty.")

            if not agg_mid_area_dataframe.empty:
                print("Writing '中區'")
                agg_mid_area_dataframe.to_excel(writer, sheet_name='中區', index=False)
            else:
                print("Skipped writing '中區' as the DataFrame is empty.")

        return send_file(os.path.join(script_dir, save_file_name), as_attachment=True)
    except Exception as E:
        print(E)
        return "ERROR"


if __name__ == '__main__':
    app.run(host='localhost', port=31109, debug=True)
    # waitress.serve(app, host="192.168.50.16", port=31109)
