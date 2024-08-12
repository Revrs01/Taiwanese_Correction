import threading
import json

from shared_sql_connection import SQL_CONNECTION, SQL_CURSOR

LOCK = threading.Lock()


def fetch_basic(school_name, student_grade, student_class):
    sql = f"""
                SELECT RecordID FROM all_student_2023_new 
                WHERE `RecordID` LIKE '{school_name}\_%%\_%%\_{student_grade}\_{student_class}\_%%\_%%\_%%\_%%';
                """

    with LOCK:
        SQL_CURSOR.execute(sql)
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

    return filter_storage


def fetch_all(school_name, student_grade, student_class):
    all_students = fetch_basic(school_name, student_grade, student_class)

    return json.dumps(all_students, ensure_ascii=False, indent=10)


def fetch_student_require_second_check(school_name, student_grade, student_class):
    all_students = fetch_basic(school_name, student_grade, student_class)

    # In order to match the order in correction table
    re_arrange_student_info = tuple(
        f'{student_info["schoolName"]}_{student_info["grade"]}_{student_info["studentClass"]}_{student_info["seatNumber"]}_{student_info["studentName"]}_{student_info["birthdayYear"]}_{student_info["birthdayMonth"]}_{student_info["birthdayDay"]}_{student_info["gender"]}'
        for student_info in all_students)
    re_arrange_student_info = ', '.join('"{0}"'.format(w) for w in re_arrange_student_info)

    SQL_CURSOR.execute("select required_question from question_require_check where correction_ref='2023_02'")
    questions_require_second_check = eval(SQL_CURSOR.fetchone()[0])

    students_require_second_correction = []
    for question_num in questions_require_second_check:
        sql = f"""select student_id from student_correction 
                    where student_id in ({re_arrange_student_info}) and correction_ref='2023_02' 
                    and JSON_EXTRACT(assessments, '$."{question_num}"') = '2'"""
        SQL_CURSOR.execute(sql)

        students_require_second_correction.extend([x[0] for x in SQL_CURSOR.fetchall()])

    students_require_second_correction = set(students_require_second_correction)

    filter_storage = []
    for student in students_require_second_correction:
        split_by_underline = student.split("_")
        filter_storage.append({
            "schoolName": split_by_underline[0],
            "grade": split_by_underline[1],
            "studentClass": split_by_underline[2],
            "seatNumber": split_by_underline[3],
            "studentName": split_by_underline[4],
            "birthdayYear": split_by_underline[5],
            "birthdayMonth": split_by_underline[6],
            "birthdayDay": split_by_underline[7],
            "gender": split_by_underline[8],
        })

    return json.dumps(filter_storage, ensure_ascii=False, indent=10)


def create_correction_template_2023_02(student_id, correction_ref, student_level):
    SQL_CURSOR.execute(
        f"select questions from question_table where correction_ref='{correction_ref}' and student_level='{student_level}'")
    question_nums = eval(SQL_CURSOR.fetchone()[0])["_order"]
    assessment_template = {}

    for q in question_nums:
        assessment_template[q] = ""

    SQL_CURSOR.execute(
        f"insert into student_correction (student_id, assessments, correction_ref) VALUES ('{student_id}', '{json.dumps(assessment_template, ensure_ascii=False)}', '{correction_ref}')")
    SQL_CONNECTION.commit()

    SQL_CURSOR.execute(
        f"select assessments from student_correction where student_id='{student_id}' and correction_ref='{correction_ref}'")
    return eval(SQL_CURSOR.fetchone()[0])


def create_correction_template_2024_07(student_id, correction_ref, student_level):
    # fetch one from DB, check correction of the student exist 2023_02 assessments
    SQL_CURSOR.execute("select assessments from student_correction where student_id=%s and correction_ref='2023_02'",
                       student_id)
    query_result = SQL_CURSOR.fetchone()
    if query_result is None:
        return "DENIED"

    assessments_2023_02 = eval(query_result[0])

    SQL_CURSOR.execute(f"select required_question from question_require_check where correction_ref='2023_02'")

    questions_require_check = eval(SQL_CURSOR.fetchone()[0])
    questions_pass_to_second_correction = []
    for question_num in questions_require_check:
        if question_num in assessments_2023_02 and assessments_2023_02[question_num] == '2':
            questions_pass_to_second_correction.append(question_num)

    assessment_template = {}
    for qN in questions_pass_to_second_correction:
        assessment_template[qN] = {}

    SQL_CURSOR.execute(
        f"insert into student_correction (student_id, assessments, correction_ref) values ('{student_id}', '{json.dumps(assessment_template, ensure_ascii=False)}', '{correction_ref}')")
    SQL_CONNECTION.commit()

    SQL_CURSOR.execute(
        f"select assessments from student_correction where student_id='{student_id}' and correction_ref='{correction_ref}'")
    return eval(SQL_CURSOR.fetchone()[0])
