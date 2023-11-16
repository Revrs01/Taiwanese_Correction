import base64
import json

from flask import Flask, render_template, request
from SqlCursor import Cursor
import os

app = Flask(__name__)

# initial sql cursor
SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()
STUDENT_DATA = []
EXAM_QUESTIONS = {}


def fetch_questions():
    global EXAM_QUESTIONS
    with open('./examQuestions2.js', 'r') as js_file:
        js_string = js_file.read()
    EXAM_QUESTIONS = json.loads(js_string)


@app.route('/filter_by_selections', methods=["POST"])
def filter_by_selections():
    global STUDENT_DATA
    selections = request.get_json()["selections"]

    filtered_student_data = STUDENT_DATA.copy()
    for selection in selections:
        filter_iterator = []
        category, value = next(iter(selection)), selection[next(iter(selection))]
        for student in filtered_student_data:
            if student[category] == value:
                filter_iterator.append(student)

        filtered_student_data = filter_iterator.copy()

    return json.dumps(filtered_student_data, ensure_ascii=False, indent=10)


@app.route('/fetch_all_student', methods=["POST"])
def fetch_all_student():
    global STUDENT_DATA
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
    base64_encoder = base64.b64encode(open(path_of_audio, "rb").read())

    base64_decoder = base64_encoder.decode("utf-8")
    return json.dumps({"base64String": base64_decoder}, ensure_ascii=False)


@app.route('/fetch_student_questions', methods=["POST"])
def fetch_student_questions():
    global EXAM_QUESTIONS

    grade = request.get_json()["grade"]

    questions_for_student = []
    questions_for_student.extend(EXAM_QUESTIONS["examQuestionRoman"])

    if int(grade) <= 2:
        questions_for_student.extend(EXAM_QUESTIONS["examQuestionLowGrade"])
    else:
        questions_for_student.extend(EXAM_QUESTIONS["examQuestionHighGrade"])

    return json.dumps(questions_for_student, ensure_ascii=False)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/correction_page', methods=["GET"])
def correction_page():
    return render_template("correctionPage.html")


if __name__ == '__main__':
    fetch_questions()
    app.run(host='localhost', port=31109, debug=True)
