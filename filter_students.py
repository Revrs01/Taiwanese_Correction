import threading
import json

from SqlCursor import Cursor

SQL_CONNECTION = Cursor().get_connection()
SQL_CURSOR = SQL_CONNECTION.cursor()

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


def fetch_2023_02_is_2(school_name, student_grade, student_class):
    all_students = fetch_basic(school_name, student_grade, student_class)

    re_arrange_student_info = set([
        f'{student_info["schoolName"]}_{student_info["grade"]}_{student_info["studentClass"]}_{student_info["seatNumber"]}_{student_info["studentName"]}_{student_info["birthdayYear"]}_{student_info["birthdayMonth"]}_{student_info["birthdayDay"]}_{student_info["gender"]}'
        for student_info in all_students])
    SQL_CURSOR.execute("select required_question from question_require_check where correction_ref='2023_02'")
    second_check_question = eval(SQL_CURSOR.fetchone()[0])

    students_needs_second_correction = set()
    for question_num in second_check_question:
        sql = f"""select student_id from student_correction 
                    where correction_ref='2023_02' and JSON_EXTRACT(assessments, '$."{question_num}"') = '2'"""
        SQL_CURSOR.execute(sql)
        students_needs_second_correction = students_needs_second_correction.union(
            set([x[0] for x in SQL_CURSOR.fetchall()]))

    students_needs_second_correction = students_needs_second_correction.intersection(re_arrange_student_info)
    filter_storage = []
    for student in students_needs_second_correction:
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
        f"select questions from question_table where correction_ref={correction_ref} and student_level={student_level}")
    question_nums = eval(SQL_CURSOR.fetchone()[0])["_order"]
    assessment_template = {}

    for q in question_nums:
        assessment_template[q] = ""

    SQL_CURSOR.execute(
        f"insert into student_correction (student_id, assessments, correction_ref) VALUES ('{student_id}', '{json.dumps(assessment_template, ensure_ascii=False)}', '{correction_ref}')")
    SQL_CONNECTION.commit()

    SQL_CURSOR.execute(
        f"select assessments from student_correction where student_id={student_id} and correction_ref='{correction_ref}'")
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

    require_check = eval(SQL_CURSOR.fetchone()[0])
    need_to_check = []
    for question_num in require_check:
        if question_num in assessments_2023_02 and assessments_2023_02[question_num] == '2':
            need_to_check.append(question_num)

    SQL_CURSOR.execute(
        f"select questions from question_table where correction_ref='{correction_ref}' and student_level='{student_level}'")
    questions = eval(SQL_CURSOR.fetchone()[0])

    new_order = []
    for ques in need_to_check:
        for qn in questions["_order"]:
            qn: str
            if qn.startswith(ques):
                new_order.append(qn)

    questions["_order"] = new_order
    assessment_template = {}
    for q in questions["_order"]:
        assessment_template[q] = ""

    SQL_CURSOR.execute(
        f"insert into student_correction (student_id, assessments, correction_ref) values ('{student_id}', '{json.dumps(assessment_template, ensure_ascii=False)}', '{correction_ref}')")
    SQL_CONNECTION.commit()

    SQL_CURSOR.execute(
        f"select assessments from student_correction where student_id={student_id} and correction_ref='{correction_ref}'")
    return eval(SQL_CURSOR.fetchone()[0])

# print(fetch_2023_02_is_2("國立臺東大學附小140601", "1", "3"))
