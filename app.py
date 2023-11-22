import base64
import json
import math

from flask import Flask, render_template, request
from SqlCursor import Cursor
import os

app = Flask(__name__)

# initial sql cursor
SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()
STUDENT_DATA = []
FILTERED_STUDENT_DATA = []
EXAM_QUESTIONS = {}


def duplicate_questions(questions) -> list:
    duplicated = []
    for index, q in enumerate(questions):
        duplicated.append({f"{index + 1}_p": q})
        duplicated.append({f"{index + 1}_c": f"{q} 造句"})

    return duplicated


def fetch_questions():
    global EXAM_QUESTIONS
    with open('./examQuestions2.js', 'r') as js_file:
        js_string = js_file.read()
    EXAM_QUESTIONS = json.loads(js_string)


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
    SQL_CURSOR.execute("SELECT RecordID from All_student_2023")
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
    student = request.get_json()["grade_studentClass_seatNumber_studentName"]
    question_number = request.get_json()["questionNumber"]

    path_of_audio = ""
    for root, dirs, files in os.walk(f"./static/audio/{student}"):
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
    for root, dirs, files in os.walk(f"./學生校正資料/"):
        for file in files:
            if file.endswith(f"{schoolName_grade_studentClass_seatNumber_studentName}.js"):
                path_of_current_correction_data = os.path.join(root, file)
                break

    default_correction_pattern = {
        "正確性評分": "",
        "入聲": "",
        "脫落": "",
        "增加": "",
        "清濁錯誤": "",
        "讀成華語四聲": "",
        "錯讀": "",
        "變調錯誤": "",
        "讀異音": "",
        "讀異音詳細": "",
        "連結字偏旁": "",
        "從華語字義轉譯成台語": "",
        "直接唸成華語讀法": "",
        "字義理解錯誤": "",
        "狀態": "",
        "備註欄": "",
    }

    # if file doesn't exist, then return NOT FOUND
    if path_of_current_correction_data == "":
        return json.dumps(default_correction_pattern, ensure_ascii=False)
    else:
        # founded, open the file then check if exist that questionNumber's data
        with open(path_of_current_correction_data, 'r') as js_file:
            # JS structure -> {"1_r":{"正確性評分":"錯誤", ... }, "2_r":{"正確性評分":"正確", ...} ...}
            student_correction_data = json.loads(js_file.read())

        if question_number in student_correction_data:
            return json.dumps(student_correction_data[question_number], ensure_ascii=False)
        else:
            return json.dumps(default_correction_pattern, ensure_ascii=False)


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
        with open(f'./學生校正資料/{schoolName_grade_studentClass_seatNumber_studentName}.js', 'r') as js_file:
            student_correction_data = json.loads(js_file.read())
        return_message = "FILE FOUND"

    except FileNotFoundError as e:
        print(e)
        return_message = "NEW FILE CREATED"

    student_correction_data[question_number] = correction_data
    with open(f'./學生校正資料/{schoolName_grade_studentClass_seatNumber_studentName}.js', 'w') as write_file:
        write_file.write(json.dumps(student_correction_data, ensure_ascii=False))

    return return_message


@app.route('/get_correction_status', methods=["POST"])
def get_correction_status():
    schoolName_grade_studentClass_seatNumber_studentName = request.get_json()[
        "schoolName_grade_studentClass_seatNumber_studentName"]
    path_of_current_correction_data = ""
    for root, dirs, files in os.walk(f"./學生校正資料/"):
        for file in files:
            if file.endswith(f"{schoolName_grade_studentClass_seatNumber_studentName}.js"):
                path_of_current_correction_data = os.path.join(root, file)
                break

    if path_of_current_correction_data == "":
        return "{}"
    else:
        with open(path_of_current_correction_data, 'r') as js_file:
            correction_data = js_file.read()
        return correction_data


@app.route('/get_correction_progress', methods=["POST"])
def get_correction_progress():
    correction_progresses = []

    global STUDENT_DATA, FILTERED_STUDENT_DATA
    for student in FILTERED_STUDENT_DATA:
        path_of_current_correction_data = ""
        for root, dirs, files in os.walk(f"./學生校正資料/"):
            for file in files:
                if file.endswith(
                        f"{student['schoolName']}_{student['grade']}_{student['studentClass']}_{student['seatNumber']}_{student['studentName']}.js"):
                    path_of_current_correction_data = os.path.join(root, file)
                    break

        if int(student["grade"]) <= 2:
            examination_length = len(EXAM_QUESTIONS["examQuestionRoman"]) + 2 * len(EXAM_QUESTIONS["examQuestionLowGrade"])
        else:
            examination_length = len(EXAM_QUESTIONS["examQuestionRoman"]) + 2 * len(EXAM_QUESTIONS["examQuestionHighGrade"])

        if path_of_current_correction_data != "":
            with open(path_of_current_correction_data, 'r') as js_file:
                correction_data = json.loads(js_file.read())

            correction_progresses.append(math.floor((len(correction_data) / examination_length) * 100))
        else:
            correction_progresses.append(0)

    return json.dumps(correction_progresses, ensure_ascii=False)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/correction_page', methods=["GET"])
def correction_page():
    return render_template("correctionPage.html")


if __name__ == '__main__':
    fetch_questions()
    app.run(host='localhost', port=31109, debug=True)
