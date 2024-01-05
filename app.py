import base64
import json
import math
from pathlib import Path
import pandas as pd
import waitress

from flask import Flask, render_template, request, send_file
from SqlCursor import Cursor
import os

app = Flask(__name__)

# 獲取腳本所在目錄的絕對路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
# 構建到靜態資源的絕對路徑
audio_dir = os.path.join(script_dir, '..', 'static', 'audio', 'Tai_audio_test')
# 接下來，您可以使用這個路徑來訪問或操作檔案


# initial sql cursor
SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()
STUDENT_DATA = []
FILTERED_STUDENT_DATA = []
EXAM_QUESTIONS = {}
CORRECTION_DIR_ABSOLUTE_FILE_PATH = os.path.join(script_dir, "學生校正資料")


def duplicate_questions(questions) -> list:
    duplicated = []
    for index, q in enumerate(questions):
        duplicated.append({f"{index + 1}_p": q})
        duplicated.append({f"{index + 1}_c": f"{q} 造句"})

    return duplicated


def fetch_questions():
    global EXAM_QUESTIONS
    with open(os.path.join(script_dir, 'examQuestions2.js'), 'r', encoding="utf-8") as js_file:
        js_string = js_file.read()
    EXAM_QUESTIONS = json.loads(js_string)


def fetch_school_region():
    global SQL_CURSOR
    sql = "SELECT `學校代碼`, `鄉鎮市區`, `學校名稱`, `區域` FROM `region_of_elementary_school`;"
    SQL_CURSOR.execute(sql)
    SQL_CONNECTION.commit()
    result_elementary = SQL_CURSOR.fetchall()
    sql = "SELECT `學校代碼`, `鄉鎮市區`, `學校名稱`, `區域` FROM `region_of_junior_high_school`;"
    SQL_CURSOR.execute(sql)
    SQL_CONNECTION.commit()
    result_junior = SQL_CURSOR.fetchall()

    north_area, south_area, east_area, mid_area = set(), set(), set(), set()

    for school_code, _, school_name, region in result_elementary:
        cur_school = f"{school_name}{school_code}"
        if region == "北區":
            north_area.add(cur_school)
        elif region == "南區":
            south_area.add(cur_school)
        elif region == "東區":
            east_area.add(cur_school)
        elif region == "中區":
            mid_area.add(cur_school)

    for school_code, _, school_name, region in result_junior:
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


@app.route('/filter_by_selections', methods=["POST"])
def filter_by_selections():
    global STUDENT_DATA, FILTERED_STUDENT_DATA
    selections = request.get_json()["selections"]
    print(selections)
    FILTERED_STUDENT_DATA = STUDENT_DATA.copy()
    for selection in selections:

        filter_iterator = []
        category, value = next(iter(selection)), selection[next(iter(selection))]

        if value == "":
            continue

        for student in FILTERED_STUDENT_DATA:
            if student[category] == value:
                filter_iterator.append(student)

        FILTERED_STUDENT_DATA = filter_iterator.copy()
    print(pd.DataFrame(FILTERED_STUDENT_DATA)[70:90])
    return json.dumps(FILTERED_STUDENT_DATA, ensure_ascii=False, indent=10)


@app.route('/fetch_filter_selection', methods=["POST"])
def fetch_filter_selection():
    global STUDENT_DATA

    distinct_school_name = set()
    distinct_student_class = set()
    distinct_grade = set()
    for student in STUDENT_DATA:
        distinct_school_name.add(student["schoolName"])
        distinct_student_class.add(student["studentClass"])
        distinct_grade.add(student["grade"])

    return json.dumps({
        "distinctSchoolName": sorted(list(distinct_school_name)),
        "distinctStudentClass": sorted(list(distinct_student_class), key=int),
        "distinctGrade": sorted(list(distinct_grade))
    }, ensure_ascii=False)


@app.route('/fetch_all_student', methods=["POST"])
def fetch_all_student():
    global STUDENT_DATA, FILTERED_STUDENT_DATA
    STUDENT_DATA = []
    SQL_CURSOR.execute("SELECT RecordID from all_student_2023_new")
    SQL_CONNECTION.commit()
    result = SQL_CURSOR.fetchall()
    for student in result:
        split_by_underline = student[0].split("_")
        STUDENT_DATA.append({
            "schoolName": split_by_underline[0],
            "studentName": split_by_underline[1],
            "gender": "男" if split_by_underline[2] == "1" else "女",
            "grade": split_by_underline[3],
            "studentClass": split_by_underline[4],
            "seatNumber": split_by_underline[5],
            "birthdayYear": split_by_underline[6],
            "birthdayMonth": split_by_underline[7],
            "birthdayDay": split_by_underline[8]
        })
    FILTERED_STUDENT_DATA = STUDENT_DATA.copy()
    return json.dumps(STUDENT_DATA, ensure_ascii=False, indent=10)


@app.route('/get_record_file', methods=["POST"])
def get_record_file():
    req = request.get_json()
    student = req["grade_studentClass_seatNumber_studentName"]
    school_name = req["schoolName"]
    question_number = req["questionNumber"]

    path_of_audio = ""
    # for root, dirs, files in os.walk(f"C:/Program Files/Taiwanese_Correction/static/audio/Tai_audio_test/{school_name}/{student}"):

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


@app.route('/fetch_student_questions', methods=["POST"])
def fetch_student_questions():
    global EXAM_QUESTIONS

    grade = request.get_json()["grade"]

    questions_for_student = []
    for index, q in enumerate(EXAM_QUESTIONS["examQuestionRoman"]):
        questions_for_student.append({f"{index + 1}_r": q})

    if int(grade) <= 2:
        all_exam_question = duplicate_questions(EXAM_QUESTIONS["examQuestionLowGrade"])
        questions_for_student.extend(all_exam_question)
    else:
        all_exam_question = duplicate_questions(EXAM_QUESTIONS["examQuestionHighGrade"])
        questions_for_student.extend(all_exam_question)

    return json.dumps(questions_for_student, ensure_ascii=False)


@app.route('/get_correction_data', methods=["POST"])
def get_correction_data():
    """
    only for reading data purpose
    :return:
    """
    schoolName_grade_studentClass_seatNumber_studentName \
        = request.get_json()["schoolName_grade_studentClass_seatNumber_studentName"]

    question_number = request.get_json()["questionNumber"]
    print(question_number, schoolName_grade_studentClass_seatNumber_studentName)

    path_of_current_correction_data = ""
    for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
        for file in files:
            if file.endswith(f"{schoolName_grade_studentClass_seatNumber_studentName}.js"):
                path_of_current_correction_data = os.path.join(root, file)
                break

    # default_correction_pattern = {
    #     "正確性評分": "",
    #     "入聲": "",
    #     "脫落": "",
    #     "增加": "",
    #     "清濁錯誤": "",
    #     "讀成華語四聲": "",
    #     "錯讀": "",
    #     "變調錯誤": "",
    #     "讀異音": "",
    #     "讀異音詳細": "",
    #     "連結字偏旁": "",
    #     "從華語字義轉譯成台語": "",
    #     "直接唸成華語讀法": "",
    #     "字義理解錯誤": "",
    #     "狀態": "",
    #     "備註欄": "",
    # }
    with open(os.path.join(script_dir, 'question_mapper.json'), 'r', encoding='ytf-8') as qm:
        default_correction_pattern = json.loads(qm.read())["correction_dict"]

    # if file doesn't exist, then return NOT FOUND
    if path_of_current_correction_data == "":
        return json.dumps(default_correction_pattern, ensure_ascii=False)
    else:
        # founded, open the file then check if exist that questionNumber's data
        with open(path_of_current_correction_data, 'r', encoding='utf-8') as js_file:
            # JS structure -> {"1_r":"1", "2_r":"0" ...}
            student_correction_data = json.loads(js_file.read())

        # if question_number in student_correction_data:
        #     return json.dumps(student_correction_data[question_number], ensure_ascii=False)
        # else:
        #     return json.dumps(default_correction_pattern, ensure_ascii=False)

        return json.dumps(student_correction_data, ensure_ascii=False)


@app.route('/save_correction_data', methods=["POST"])
def save_correction_data():
    """
    save correction data for corresponding question number
    :return:
    """

    req = request.get_json()
    question_number = req["questionNumber"]
    correction_data = req["correctionData"]
    schoolName_grade_studentClass_seatNumber_studentName = req["schoolName_grade_studentClass_seatNumber_studentName"]

    student_correction_data = {}
    # check the file existence first, then write the file
    try:
        try:

            with open(f'{os.path.join(CORRECTION_DIR_ABSOLUTE_FILE_PATH, schoolName_grade_studentClass_seatNumber_studentName)}.js',
                      'r', encoding='utf-8') as js_file:
                student_correction_data = json.loads(js_file.read())
            return_message = "FILE FOUND"

        except FileNotFoundError as e:
            print(e)
            return_message = "NEW FILE CREATED"

        student_correction_data[question_number] = correction_data
        with open(f'{os.path.join(CORRECTION_DIR_ABSOLUTE_FILE_PATH, schoolName_grade_studentClass_seatNumber_studentName)}.js',
                  'w', encoding='utf-8') as write_file:
            write_file.write(json.dumps(student_correction_data, ensure_ascii=False))
    except Exception as big_error:
        print(big_error)
        return "ERROR"

    return return_message


@app.route('/get_correction_status', methods=["POST"])
def get_correction_status():
    schoolName_grade_studentClass_seatNumber_studentName = request.get_json()[
        "schoolName_grade_studentClass_seatNumber_studentName"]
    path_of_current_correction_data = ""
    for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
        for file in files:
            if file.endswith(f"{schoolName_grade_studentClass_seatNumber_studentName}.js"):
                path_of_current_correction_data = os.path.join(root, file)
                break

    if path_of_current_correction_data == "":
        return "{}"
    else:
        with open(path_of_current_correction_data, 'r', encoding='utf-8') as js_file:
            correction_data = js_file.read()
        return correction_data


@app.route('/get_correction_progress', methods=["POST"])
def get_correction_progress():
    correction_progresses = []

    global STUDENT_DATA, FILTERED_STUDENT_DATA
    for student in FILTERED_STUDENT_DATA:
        path_of_current_correction_data = ""
        for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
            for file in files:
                if file.endswith(
                        f"{student['schoolName']}_{student['grade']}_{student['studentClass']}_{student['seatNumber']}_{student['studentName']}.js"):
                    path_of_current_correction_data = os.path.join(root, file)
                    break

        if int(student["grade"]) <= 2:
            examination_length = len(EXAM_QUESTIONS["examQuestionRoman"]) + 2 * len(
                EXAM_QUESTIONS["examQuestionLowGrade"])
        else:
            examination_length = len(EXAM_QUESTIONS["examQuestionRoman"]) + 2 * len(
                EXAM_QUESTIONS["examQuestionHighGrade"])

        if path_of_current_correction_data != "":
            with open(path_of_current_correction_data, 'r', encoding='utf-8') as js_file:
                correction_data = json.loads(js_file.read())

            correction_progresses.append(math.floor((len(correction_data) / examination_length) * 100))
        else:
            correction_progresses.append(0)

    return json.dumps(correction_progresses, ensure_ascii=False)


@app.route('/output_xlsx', methods=["POST"])
def output_xlsx():
    """
    only output the current saved data
    :return:
    """
    north_area, south_area, east_area, mid_area = fetch_school_region()
    agg_north_area, agg_south_area, agg_east_area, agg_mid_area = [], [], [], []
    try:
        aggregated_data = []
        with open(os.path.join(script_dir, 'question_mapper.js'), 'r', encoding='utf-8') as qm:
            question_mapper = json.loads(qm.read())

        for root, dirs, files in os.walk(CORRECTION_DIR_ABSOLUTE_FILE_PATH):
            for file in files:
                if file.endswith('.js'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as correction_js:
                        current_student_correction_data = json.loads(correction_js.read())
                    current_student_personal_information = Path(file).stem.split('_')
                    extract_correctness = question_mapper["correction_dict"].copy()

                    for correctness in current_student_correction_data.keys():
                        if current_student_correction_data[correctness] == "1":
                            extract_correctness[correctness] = 1
                        elif current_student_correction_data[correctness] == "0":
                            extract_correctness[correctness] = 0

                    current_student_correction_data_list_form = [current_student_personal_information[0],
                                                                 current_student_personal_information[1],
                                                                 current_student_personal_information[2],
                                                                 current_student_personal_information[3],
                                                                 current_student_personal_information[4]]

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

        aggregate_dataframe = pd.DataFrame(aggregated_data,
                                           columns=["學校名稱", "年級", "班級", "座號", "學生姓名"] +
                                                   question_mapper["question_list"])
        agg_north_area_dataframe = pd.DataFrame(agg_north_area,
                                                columns=["學校名稱", "年級", "班級", "座號", "學生姓名"] +
                                                        question_mapper["question_list"])

        agg_south_area_dataframe = pd.DataFrame(agg_south_area,
                                                columns=["學校名稱", "年級", "班級", "座號", "學生姓名"] +
                                                        question_mapper["question_list"])
        agg_east_area_dataframe = pd.DataFrame(agg_east_area,
                                               columns=["學校名稱", "年級", "班級", "座號", "學生姓名"] +
                                                       question_mapper["question_list"])

        agg_mid_area_dataframe = pd.DataFrame(agg_mid_area,
                                              columns=["學校名稱", "年級", "班級", "座號", "學生姓名"] +
                                                      question_mapper["question_list"])

        aggregate_dataframe.to_excel(os.path.join(script_dir, "output.xlsx"), index=False)
        with pd.ExcelWriter(os.path.join(script_dir, "output.xlsx"), engine='openpyxl') as writer:
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

        return send_file(os.path.join(script_dir, "output.xlsx"), as_attachment=True)
    except Exception as E:
        print(E)
        return "ERROR"


@app.route('/')
def home_page():
    SQL_CONNECTION.ping(reconnect=True)
    return render_template('index.html')


@app.route('/correction_page', methods=["GET"])
def correction_page():
    return render_template("correctionPage.html")


if __name__ == '__main__':
    fetch_questions()
    app.run(host='localhost', port=31109, debug=True)
    # waitress.serve(app, host="192.168.50.16", port=31109)
