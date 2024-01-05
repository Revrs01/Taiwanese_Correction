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
    $('#studentDetailInformation').append(`${$schoolName.substring(0, $schoolName.length - 6)} ${$grade} 年 ${$studentClass} 班 ${$seatNumber} 號`)
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

async function getCorrectionStatus() {
    let correction_data = "";
    await $.ajax({
        type: "POST",
        url: "/get_correction_status",
        contentType: "application/json",
        data: JSON.stringify({
            schoolName_grade_studentClass_seatNumber_studentName: `${$schoolName}_${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            birthday: `${urlParameters.get('birthdayYear')}_${urlParameters.get('birthdayMonth')}_${urlParameters.get('birthdayDay')}`,
            gender: `${urlParameters.get('gender')}`,
        })
    })
        .then((response) => {
            correction_data = JSON.parse(response);
        });

    return correction_data
}


async function appendCorrectionTable() {
    let $correctionTable = $("#correctionTable");
    let correctionData = await getCorrectionStatus();
    for (let index = 0; index < EXAM_QUESTIONS_LIST.length; index++) {
        let currentQuestionNumber = EXAM_QUESTIONS_NUMBER[index];
        let audioString = await getRecordAudio(currentQuestionNumber);
        let correctButton = "";
        let wrongButton = "";
        let audioController = ``;
        if (audioString !== "") {
            audioController = `<audio controls><source src='data:audio/wav;base64,${audioString}' type="audio/wav"></audio>`;
        }

        // if isCorrected, then correct -> green button, incorrect -> red button
        // else button -> gray
        if (correctionData[currentQuestionNumber] !== undefined && correctionData[currentQuestionNumber] !== "") {
            if (correctionData[currentQuestionNumber] === "1") {
                correctButton = `<button class="btn" style="background-color: #04AA6D; color: white;" buttonIndex="${index}" onclick="writeCorrection(this)" correctness="correct">正確</button>`;
                wrongButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: rgb(28,28,28);" buttonIndex="${index}" onclick="writeCorrection(this)" correctness="wrong">錯誤</button>`;
            } else {
                correctButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: #1c1c1c;" buttonIndex="${index}" onclick="writeCorrection(this)" correctness="correct">正確</button>`;
                wrongButton = `<button class="btn" style="background-color: #f24213; color: white;" buttonIndex="wrong${index}" onclick="writeCorrection(this)" correctness="wrong">錯誤</button>`;
            }

        } else {
            correctButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: #1c1c1c;" buttonIndex="${index}" onclick="writeCorrection(this)" correctness="correct">正確</button>`;
            wrongButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: #1c1c1c;" buttonIndex="${index}" onclick="writeCorrection(this)" correctness="wrong">錯誤</button>`;
        }

        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 26px;">${EXAM_QUESTIONS_LIST[index]}</th>
                            <th scope="row" style="font-size: 16px;">${audioController}</th>
                            <th>
                                <div class="d-flex align-items-center">
                                    ${correctButton}
                                    ${wrongButton}
                                </div>
                            </th>
                        </tr>

                        </tbody>`
        $correctionTable.append(tableBody);
    }

    $("#loader").addClass("hidden");
    $("#modalOverlay").addClass("hidden");

}

async function getRecordAudio(questionNumber) {
    let base64String = "";
    await $.ajax({
        type: "POST",
        url: '/get_record_file',
        contentType: "application/json",
        data: JSON.stringify({
            grade_studentClass_seatNumber_studentName: `${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            schoolName: $schoolName,
            questionNumber: questionNumber
        })
    })
        .then((response) => {
            base64String = JSON.parse(response)["base64String"];
            // Object.assign(BASE64STRINGS, {[questionNumber]:JSON.parse(response)["base64String"]})
        })
        .fail(() => {
            alert("出大事了！寄")
        });

    return base64String
}

function writeCorrection(object) {
    let currentQuestionNumber = object.attributes.buttonIndex.value;
    let currentQuestionCorrectness = object.attributes.correctness.value;
    let correctness;
    if (currentQuestionCorrectness === "correct") {
        correctness = "1";
    } else {
        correctness = "0";
    }
    $.ajax({
        type: "POST",
        url: '/save_correction_data',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            schoolName_grade_studentClass_seatNumber_studentName: `${$schoolName}_${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            birthday: `${urlParameters.get('birthdayYear')}_${urlParameters.get('birthdayMonth')}_${urlParameters.get('birthdayDay')}`,
            gender: `${urlParameters.get('gender')}`,
            questionNumber: EXAM_QUESTIONS_NUMBER[currentQuestionNumber],
            correctionData: correctness
        })
    })
        .then((response) => {
            if (currentQuestionCorrectness === "correct") {
                if (response !== "ERROR") {
                    $(`button[buttonIndex=${currentQuestionNumber}][correctness="${currentQuestionCorrectness}"]`).css({
                        "background-color": "#04AA6D",
                        "color": "white"
                    });

                    $(`button[buttonIndex=${currentQuestionNumber}][correctness="wrong"]`).css({
                        "background-color": "rgba(216,214,214,0.38)",
                        "color": "#1c1c1c"
                    });
                }
            } else {
                if (response !== "ERROR") {
                    $(`button[buttonIndex=${currentQuestionNumber}][correctness="${currentQuestionCorrectness}"]`).css({
                        "background-color": "#f24213",
                        "color": "white"
                    });
                    $(`button[buttonIndex=${currentQuestionNumber}][correctness="correct"]`).css({
                        "background-color": "rgba(216,214,214,0.38)",
                        "color": "#1c1c1c"
                    });
                }
            }
        })
        .fail(() => {
            alert("發生問題導致暫時無法存檔，請連絡相關負責人");
        });
}
