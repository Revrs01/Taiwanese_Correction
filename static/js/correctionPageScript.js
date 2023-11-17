let EXAM_QUESTIONS_LIST = [];
let EXAM_QUESTIONS_NUMBER = [];
let urlParameters = new URLSearchParams(window.location.search);
let $studentName = urlParameters.get("studentName");
let $schoolName = urlParameters.get("schoolName");
let $grade = urlParameters.get("grade");
let $studentClass = urlParameters.get("studentClass");
let $seatNumber = urlParameters.get("seatNumber");


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
            let receivedJs = JSON.parse(response);
            for (let question of receivedJs) {
                EXAM_QUESTIONS_NUMBER.push(Object.keys(question)[0])
                EXAM_QUESTIONS_LIST.push(Object.values(question)[0])
            }
            appendCorrectionTable().then(() => {
                console.log("學生個人校正網頁載入完畢");
            });
        });
}

async function appendCorrectionTable() {
    let $correctionTable = $("#correctionTable");

    for (let index = 0; index < EXAM_QUESTIONS_LIST.length; index++) {
        let currentQuestionNumber = EXAM_QUESTIONS_NUMBER[index];
        let audioString = await getRecordAudio(currentQuestionNumber);

        let audioSource = ``;
        if (audioString !== "") {
            audioSource = `<audio controls><source src='data:audio/wav;base64,${audioString}' type="audio/wav"></audio>`;
        }

        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 26px;">${EXAM_QUESTIONS_LIST[index]}</th>
                            <th scope="row" style="font-size: 16px;">${audioSource}</th>
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

async function getRecordAudio(questionNumber) {
    let base64String = "";
    await $.ajax({
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
            // Object.assign(BASE64STRINGS, {[questionNumber]:JSON.parse(response)["base64String"]})
        })

    return base64String
}