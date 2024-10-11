# -*- coding: utf-8 -*-
import logging
import math
from flask_cors import CORS
from filter_students import *
from flask import Flask, request
from shared_sql_connection import *
from werkzeug.middleware.proxy_fix import ProxyFix

LOCK = threading.Lock()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Allow Cross Origin Connections
CORS(app)

# different correction table need different functions
FETCH_DEPENDENCY = {
    "2023_02": fetch_all,
    "2024_07": fetch_student_require_second_check
}

CREATE_CORRECTION_TEMPLATE = {
    "2023_02": create_correction_template_2023_02,
    "2024_07": create_correction_template_2024_07
}


def calc_correction_progress(assessments: dict, syllables=None) -> (int, int):
    if syllables is None:
        count_list = [1 if x != "" else 0 for x in assessments.values()]
        return math.floor((sum(count_list) / len(count_list)) * 100), len(count_list)
    else:
        cnt = 0
        total_cnt = 0
        for key in assessments.keys():
            cnt += len(assessments[key])
            total_cnt += syllables[key]
        return math.floor(cnt * 100 / total_cnt), len(assessments.keys())


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


@app.route('/reconnect_mysql', methods=["GET"])
def reconnect_mysql():
    try:
        with LOCK:
            reconnect()
        return "CONNECTION RECONNECTED"
    except Exception as e:
        logging.error(e)

@app.route('/get_correction_details', methods=["POST"])
def get_correction_details():
    try:
        obj = request.get_json()
        student_key = obj["studentKey"]
        student_level = obj["studentLevel"]
        correction_ref = obj["correctionRef"]
    except Exception as e:
        logging.error(e)
        return

    try:
        with LOCK:
            SQL_CURSOR.execute("select assessments from student_correction where student_id=%s and correction_ref=%s",
                               (student_key, correction_ref))
            query_result = SQL_CURSOR.fetchone()
            if query_result is not None:
                # if found assessment, return assessment
                student_assessment = eval(query_result[0])
                logging.info("Student correction data founded !")
                return json.dumps(student_assessment, ensure_ascii=False)

            # else, create a new correction template (based on correction_ref), insert into table then read from table
            is_template_created = CREATE_CORRECTION_TEMPLATE[correction_ref](student_key, correction_ref, student_level)
            if is_template_created == "DENIED":
                return "Student Does not have 2023_02 correction data !", 701
            else:
                return json.dumps(is_template_created, ensure_ascii=False)

    except Exception as e:
        logging.error(e)


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

        is_array = False

        if isinstance(update_val, list):
            update_val = "JSON_ARRAY({})".format(', '.join(f"'{v}'" for v in update_val))
            is_array = True

        if correction_ref == "2024_07":
            syllable = obj["syllable"]
    except Exception as e:
        logging.error(e)
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
                if is_array:
                    SQL_CURSOR.execute(f"""
                                        update student_correction 
                                        SET assessments=JSON_SET(assessments, '$."{question_number}"."{question_number}_{syllable}"', {update_val})
                                        where student_id='{student_id}' and correction_ref='{correction_ref}'
                                        """)
                else:
                    SQL_CURSOR.execute(f"""
                                        update student_correction 
                                        SET assessments=JSON_SET(assessments, '$."{question_number}"."{question_number}_{syllable}"', '{update_val}')
                                        where student_id='{student_id}' and correction_ref='{correction_ref}'
                                        """)

                SQL_CONNECTION.commit()

        return "OK"
    except Exception as e:
        logging.error(e)


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

        if correction_ref == "2024_07":
            SQL_CURSOR.execute("SELECT button_mapper from question_table where correction_ref='2024_07'")
            syllables_for_each_question = SQL_CURSOR.fetchone()

    progress = 0
    number_of_questions = 0

    if assessments:
        if correction_ref == "2023_02":
            progress, number_of_questions = calc_correction_progress(eval(assessments[0]))
        elif correction_ref == "2024_07":
            progress, number_of_questions = calc_correction_progress(eval(assessments[0]), eval(syllables_for_each_question[0]))

    return json.dumps({
        "progress": progress,
        "numberOfQuestions": number_of_questions
    }, ensure_ascii=False)

@app.route('/get_detail_correction_button', methods=["POST"])
def get_detail_correction_button():
    req = request.get_json()
    correction_ref = req["correctionRef"]
    question_number = req["questionNumber"]
    syllable = req["whichSyllable"]

    with LOCK:
        SQL_CURSOR.execute(f"select show_buttons from detail_correction_button where correction_ref='{correction_ref}'")
        show_buttons = SQL_CURSOR.fetchone()

    if show_buttons:
        show_buttons = eval(show_buttons[0])
        try:
            return json.dumps(show_buttons[question_number][f'{question_number}_{syllable}'], ensure_ascii=False)
        except KeyError as e:
            logging.error(e)
            return f"question number {question_number} or syllable {syllable} doesn't exist", 702

    return "No detail correction button found"
