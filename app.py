# -*- coding: utf-8 -*-
import base64
import json
import math
from pathlib import Path
import pandas as pd
from flask_cors import CORS
import threading
import waitress
from filter_students import *
from flask import Flask, request, send_file
from SqlCursor import Cursor
import os
from shared_sql_connection import SQL_CONNECTION, SQL_CURSOR

LOCK = threading.Lock()

app = Flask(__name__)

# Allow Cross Origin Connections
CORS(app)

# PATHs
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(SCRIPT_DIR, '..', 'static', 'audio', 'Tai_audio_test')
# CORRECTION_DIR_ABSOLUTE_FILE_PATH = os.path.join(SCRIPT_DIR, "學生校正資料")


# different correction table need different functions
FETCH_DEPENDENCY = {
    "2023_02": fetch_all,
    "2024_07": fetch_student_require_second_check
}

CREATE_CORRECTION_TEMPLATE = {
    "2023_02": create_correction_template_2023_02,
    "2024_07": create_correction_template_2024_07
}


def calc_correction_progress(assessments: dict) -> int:
    count_list = [1 if x != "" else 0 for x in assessments.values()]

    return math.floor((sum(count_list) / len(count_list)) * 100)


def region_sort(region):
    return {'中區': 0, '北區': 1, '南區': 2, '東區': 3}[region]


def is_correction_data_exist(student_id: str) -> bool:
    # Define the SQL query to check if the data exists
    query = f"SELECT 1 FROM student_correction WHERE student_id=%s;"

    # Execute the query
    SQL_CURSOR.execute(query, student_id)

    # Fetch one result
    result = SQL_CURSOR.fetchone()

    # Return True if a row was found, otherwise False
    return result is not None


def fetch_school_region():
    # global SQL_CURSOR

    with LOCK:
        # token amount will exceed mysql session default limit (1024), make it 60000 (minimum of required)
        SQL_CURSOR.execute("SET SESSION GROUP_CONCAT_MAX_LEN = 60000;")

        sql = """SELECT 區域, GROUP_CONCAT(學校名稱, 學校代碼) AS s
                    FROM (
                        SELECT 學校代碼, 學校名稱, 區域 FROM region_of_elementary_school
                        UNION ALL
                        SELECT 學校代碼, 學校名稱, 區域 FROM region_of_junior_high_school
                    ) AS concatenated_tables
                    GROUP BY 區域;"""
        SQL_CURSOR.execute(sql)
        query_result = SQL_CURSOR.fetchall()
        query_result = sorted(query_result, key=lambda x: region_sort(x[0]))

    mid_area, north_area, = set(query_result[0][1].split(",")), set(query_result[1][1].split(","))
    south_area, east_area = set(query_result[2][1].split(",")), set(query_result[3][1].split(","))

    return mid_area, north_area, south_area, east_area


@app.route('/get_correction_details', methods=["POST"])
def get_correction_details():
    try:
        obj = request.get_json()
        student_key = obj["studentKey"]
        student_level = obj["studentLevel"]
        correction_ref = obj["correctionRef"]
    except Exception as e:
        print(e)
        return

    try:
        with LOCK:
            SQL_CURSOR.execute("select assessments from student_correction where student_id=%s and correction_ref=%s",
                               (student_key, correction_ref))
            query_result = SQL_CURSOR.fetchone()
            if query_result is not None:
                # if found assessment, return assessment
                student_assessment = eval(query_result[0])
                print("FOUNDED !")
                return json.dumps(student_assessment, ensure_ascii=False)

            # else, create a new correction template (based on correction_ref), insert into table then read from table
            is_template_created = CREATE_CORRECTION_TEMPLATE[correction_ref](student_key, correction_ref, student_level)
            if is_template_created == "DENIED":
                return "Student Does not have 2023_02 correction data !", 701
            else:
                return json.dumps(is_template_created, ensure_ascii=False)

    except Exception as e:
        print(e)


@app.route('/filter_by_options', methods=["POST"])
def filter_by_options():
    options = request.get_json()["options"]
    school_name = options["schoolName"] if len(options["schoolName"]) > 0 else '%%'
    student_class = options["studentClass"] if len(options["studentClass"]) > 0 else '%%'
    student_grade = options["grade"] if len(options["grade"]) > 0 else '%%'
    correction_ref = options["correctionRef"]

    with LOCK:
        return FETCH_DEPENDENCY[correction_ref](school_name, student_grade, student_class)


@app.route('/update_correction_details', methods=["POST"])
def update_correction_details():
    try:
        syllable = None
        obj = request.get_json()

        student_id, question_number, update_val = obj["studentId"], obj["questionNumber"], obj["newValue"]
        correction_ref = obj["correctionRef"]

        if correction_ref == "2024_07":
            syllable = obj["syllable"]
    except Exception as e:
        print(e)
        return

    try:
        with LOCK:
            if not syllable:
                # correction_ref = 2023_02
                SQL_CURSOR.execute(f"""
                                    update student_correction 
                                    SET assessments=JSON_SET(assessments, '$."{question_number}"', '{update_val}') 
                                    where student_id='{student_id}' and correction_ref='{correction_ref}'
                                    """)
                SQL_CONNECTION.commit()
            else:
                # correction_ref = 2024_07
                SQL_CURSOR.execute(f"""
                                    update student_correction 
                                    SET assessments=JSON_SET(assessments, '$."{question_number}"."{question_number}_{syllable}"', '{update_val}')
                                    where student_id='{student_id}' and correction_ref='{correction_ref}'
                                    """)
                SQL_CONNECTION.commit()

        return "OK"
    except Exception as e:
        print(e)


@app.route('/fetch_test_question', methods=["POST"])
def fetch_test_question():
    req = request.get_json()
    student_level = req["studentLevel"]
    correction_ref = req["correctionRef"]

    with LOCK:
        SQL_CURSOR.execute(
            "select questions, button_mapper from question_table where student_level=%s and correction_ref=%s",
            (student_level, correction_ref))
        fetch_result = SQL_CURSOR.fetchone()

    if fetch_result:
        questions = eval(fetch_result[0])
        button_mapper = eval(fetch_result[1])

        order = questions['_order']
        question_list = questions['question_list']

        result = [question_list[x] for x in order]
        rearrange_button_mapper = [button_mapper[x] for x in order]
        return json.dumps({"_order": order, "questionList": result, "buttonKeys": rearrange_button_mapper},
                          ensure_ascii=False)
    else:
        return "Cannot find test question", 702


@app.route('/fetch_filter_selection', methods=["GET"])
def fetch_filter_selection():
    with LOCK:
        SQL_CURSOR.execute("SELECT RecordID from all_student_2023_new;")
        result = SQL_CURSOR.fetchall()

    distinct_school_name, distinct_student_class, distinct_grade = set(), set(), set()

    for student in result:
        split_by_underline = student[0].split("_")

        distinct_school_name.add(split_by_underline[0])
        distinct_student_class.add(split_by_underline[4])
        distinct_grade.add(split_by_underline[3])

    return json.dumps({
        "distinctSchoolName": list(distinct_school_name),
        "distinctStudentClass": sorted(list(distinct_student_class), key=int),
        "distinctGrade": sorted(list(distinct_grade))
    }, ensure_ascii=False)


@app.route('/get_correction_progress', methods=["POST"])
def get_correction_progress():
    req = request.get_json()
    student_key = req["studentKey"]
    correction_ref = req["correctionRef"]
    with LOCK:
        SQL_CURSOR.execute("SELECT assessments from student_correction where student_id=%s and correction_ref=%s",
                           (student_key, correction_ref))
        assessments = SQL_CURSOR.fetchone()

    progress = 0

    if assessments:
        progress = calc_correction_progress(eval(assessments[0]))

    return json.dumps({
        "progress": progress
    }, ensure_ascii=False)


@app.route('/get_record_file', methods=["POST"])
# pending
def get_record_file():
    req = request.get_json()
    student = req["grade_studentClass_seatNumber_studentName"]
    school_name = req["schoolName"]
    question_number = req["questionNumber"]

    path_of_audio = ""

    full_path = os.path.join(AUDIO_DIR, school_name, student)
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


# @app.route('/output_xlsx', methods=["POST"])
# # deprecated
# def output_xlsx():
#     """
#     only output the current saved data
#     :return:
#     """
#     exportType: bool = request.get_json()['exportType']
#     mid_area, north_area, south_area, east_area = fetch_school_region()
#     agg_north_area, agg_south_area, agg_east_area, agg_mid_area = [], [], [], []
#
#     try:
#         aggregated_data = []
#         with open(os.path.join(SCRIPT_DIR, 'question_mapper.json'), 'r', encoding='utf-8') as qm:
#             question_mapper = json.loads(qm.read())
#
#         for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
#             for file in files:
#                 if file.endswith('.js'):
#                     with open(os.path.join(root, file), 'r', encoding='utf-8') as correction_js:
#                         current_student_correction_data = json.loads(correction_js.read())
#                     current_student_personal_information = Path(file).stem.split('_')
#
#                     extract_correctness = question_mapper["correction_dict"].copy()
#
#                     if exportType:
#                         for correctness in current_student_correction_data.keys():
#                             if current_student_correction_data[correctness] == "1":
#                                 extract_correctness[correctness] = "1"
#                             elif current_student_correction_data[correctness] == "2":
#                                 extract_correctness[correctness] = "0"
#                             elif current_student_correction_data[correctness] == "4":
#                                 extract_correctness[correctness] = "2"
#                             elif current_student_correction_data[correctness] == "3":
#                                 extract_correctness[correctness] = "3"
#                             else:
#                                 extract_correctness[correctness] = "X"
#
#                     else:
#                         for correctness in current_student_correction_data.keys():
#                             if current_student_correction_data[correctness] == "1":
#                                 extract_correctness[correctness] = "1"
#                             elif current_student_correction_data[correctness] in {"2", "3", "4"}:
#                                 extract_correctness[correctness] = "0"
#                             elif current_student_correction_data[correctness] == "X":
#                                 extract_correctness[correctness] = "X"
#
#                     current_student_correction_data_list_form = [x for x in current_student_personal_information]
#                     current_student_correction_data_list_form[-1] = \
#                         "男" if current_student_correction_data_list_form[-1] == "1" else "女"
#
#                     for index in question_mapper["question_index"]:
#                         current_student_correction_data_list_form.append(extract_correctness[index])
#
#                     aggregated_data.append(current_student_correction_data_list_form)
#
#                     current_school = current_student_personal_information[0]
#
#                     if current_school in north_area:
#                         agg_north_area.append(current_student_correction_data_list_form)
#                     elif current_school in south_area:
#                         agg_south_area.append(current_student_correction_data_list_form)
#                     elif current_school in east_area:
#                         agg_east_area.append(current_student_correction_data_list_form)
#                     elif current_school in mid_area:
#                         agg_mid_area.append(current_student_correction_data_list_form)
#         column_of_student_information = ["學校名稱", "年級", "班級", "座號", "學生姓名", "生日(年)", "生日(月)",
#                                          "生日(日)", "性別"] + question_mapper["question_list"]
#
#         # collects every student's data
#         aggregate_dataframe = pd.DataFrame(aggregated_data, columns=column_of_student_information)
#
#         # collect only if the student's school is in that area
#         agg_north_area_dataframe = pd.DataFrame(agg_north_area, columns=column_of_student_information)
#         agg_south_area_dataframe = pd.DataFrame(agg_south_area, columns=column_of_student_information)
#         agg_east_area_dataframe = pd.DataFrame(agg_east_area, columns=column_of_student_information)
#         agg_mid_area_dataframe = pd.DataFrame(agg_mid_area, columns=column_of_student_information)
#
#         if aggregate_dataframe.size == 0:
#             return "NO FILE EXIST", 400
#
#         save_file_name = "output_fully.xlsx" if exportType else "output_pruned.xlsx"
#
#         # save to local
#         aggregate_dataframe.to_excel(os.path.join(SCRIPT_DIR, save_file_name), index=False)
#
#         # write to each sheet if that area's DataFrame is not empty
#         with pd.ExcelWriter(os.path.join(SCRIPT_DIR, save_file_name), engine='openpyxl') as writer:
#             if not aggregate_dataframe.empty:
#                 print("Writing '總表'")
#                 aggregate_dataframe.to_excel(writer, sheet_name='總表', index=False)
#             else:
#                 print("Skipped writing '總表' as the DataFrame is empty.")
#
#             if not agg_north_area_dataframe.empty:
#                 print("Writing '北區'")
#                 agg_north_area_dataframe.to_excel(writer, sheet_name='北區', index=False)
#             else:
#                 print("Skipped writing '北區' as the DataFrame is empty.")
#
#             if not agg_south_area_dataframe.empty:
#                 print("Writing '南區'")
#                 agg_south_area_dataframe.to_excel(writer, sheet_name='南區', index=False)
#             else:
#                 print("Skipped writing '南區' as the DataFrame is empty.")
#
#             if not agg_east_area_dataframe.empty:
#                 print("Writing '東區'")
#                 agg_east_area_dataframe.to_excel(writer, sheet_name='東區', index=False)
#             else:
#                 print("Skipped writing '東區' as the DataFrame is empty.")
#
#             if not agg_mid_area_dataframe.empty:
#                 print("Writing '中區'")
#                 agg_mid_area_dataframe.to_excel(writer, sheet_name='中區', index=False)
#             else:
#                 print("Skipped writing '中區' as the DataFrame is empty.")
#
#         return send_file(os.path.join(SCRIPT_DIR, save_file_name), as_attachment=True)
#     except Exception as E:
#         print(E)
#         return "ERROR"


if __name__ == '__main__':
    app.run(host='localhost', port=31109, debug=True)
    # waitress.serve(app, host="192.168.50.16", port=31109)
