let EXAM_QUESTIONS = [];
let urlParameters = new URLSearchParams(window.location.search);
let $studentName = urlParameters.get("studentName");
let $schoolName = urlParameters.get("schoolName");
let $grade = urlParameters.get("grade");
let $studentClass = urlParameters.get("studentClass");
let $seatNumber = urlParameters.get("seatNumber");
let base64String;


$(document).ready(() => {

    $('#cardTitle').append($studentName);
    let grade = urlParameters.get("grade");
    fetchStudentQuestion(grade);
});

function fetchStudentQuestion(grade) {
    $.ajax({
        type: "POST",
        url: "/fetch_student_questions",
        contentType: "application/json",
        data: JSON.stringify({"grade": grade})
    })
        .then((response) => {
            EXAM_QUESTIONS = JSON.parse(response);
            appendCorrectionTable();
        });
}

function appendCorrectionTable() {
    let $correctionTable = $("#correctionTable");
    for (let index = 0; index < EXAM_QUESTIONS.length; index++) {
        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 26px;">${EXAM_QUESTIONS[index]}</th>
                            <th scope="row" style="font-size: 16px;"><audio controls></audio></th>
                            <th>
                                <div class="d-flex align-items-center">
                                    <button class="btn" style="background-color: aquamarine" buttonIndex="${index}">糾正錯誤</button>
                                </div>
                            </th>
                        </tr>

                        </tbody>`
        $correctionTable.append(tableBody);
    }
}

function getRecordAudio(questionNumber){
    $.ajax({
        type: "POST",
        url: '/get_record_file',
        contentType: "application/json",
        data: JSON.stringify({
            grade_studentClass_seatNumber_studentName: `${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            questionNumber: questionNumber
        })
    })
        .then((response) => {
            base64String = JSON.parse(response)["base64String"];
        })
}