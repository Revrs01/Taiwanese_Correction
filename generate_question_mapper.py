import json


def construct_question_mapping():
    # this is the index of the question
    with open('./examQuestions2.js', 'r', encoding='utf-8') as q:
        question_data = json.loads(q.read())

    all_questions_correction = {}
    map_question = []
    question_index = []
    # roman test
    for i in range(1, len(question_data["examQuestionRoman"]) + 1):
        all_questions_correction[f"{i}_r"] = ""
        map_question.append(question_data["examQuestionRoman"][i - 1])
        question_index.append(f"{i}_r")
    # 1_p, 1_c ~ 65_p, 65_c
    for i in range(1, len(question_data["examQuestionHighGrade"]) + 1):
        all_questions_correction[f"{i}_p"] = ""
        all_questions_correction[f"{i}_c"] = ""
        map_question.append(question_data["examQuestionHighGrade"][i - 1])
        map_question.append(question_data["examQuestionHighGrade"][i - 1])
        question_index.append(f"{i}_p")
        question_index.append(f"{i}_c")

    with open("./question_mapper.js", 'w', encoding='utf-8') as qm:
        qm.write(json.dumps({
            "question_index": question_index,
            "correction_dict": all_questions_correction,
            "question_list": map_question
        }, ensure_ascii=False))