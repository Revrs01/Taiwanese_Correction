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

        let correctButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: #1c1c1c;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="correct">正確</button>`;
        let wrongButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: rgb(28,28,28);" questionIndex="${index}" onclick="writeCorrection(this)" correctness="wrong">錯誤</button>`;
        let iDontKnowButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: rgb(28,28,28);" questionIndex="${index}" onclick="writeCorrection(this)" correctness="iDontKnow">袂曉</button>`;
        let speakerSilenceButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: rgb(28,28,28);" questionIndex="${index}" onclick="writeCorrection(this)" correctness="speakerSilence">不出聲</button>`;
        let audioNoSoundButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: rgb(28,28,28);" questionIndex="${index}" onclick="writeCorrection(this)" correctness="audioNoSound">音檔無聲</button>`;


        let audioController = ``;
        if (audioString !== "") {
            audioController = `<audio controls><source src='data:audio/wav;base64,${audioString}' type="audio/wav"></audio>`;
        }

        // if isCorrected, then correct -> green button, incorrect -> red button
        // else button -> gray
        let currentStatus = correctionData[currentQuestionNumber];
        // status {correct: "1", wrong: "2", I don't know: "3", speaker silence: "4", audio no sound: "X"}
        if (currentStatus !== undefined && currentStatus !== "") {
            if (currentStatus === "1") {
                correctButton = `<button class="btn" style="background-color: #04AA6D; color: white;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="correct">正確</button>`;
            } else if (currentStatus === "2") {
                wrongButton = `<button class="btn" style="background-color: #f24213; color: white;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="wrong">錯誤</button>`;
            } else if (currentStatus === "3") {
                iDontKnowButton = `<button class="btn" style="background-color: #f24213; color: white;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="iDontKnow">袂曉</button>`;
            } else if (currentStatus === "4") {
                speakerSilenceButton = `<button class="btn" style="background-color: #f24213; color: white;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="speakerSilence">不出聲</button>`;
            } else if (currentStatus === "X") {
                audioNoSoundButton = `<button class="btn" style="background-color: #f24213; color: white;" questionIndex="${index}" onclick="writeCorrection(this)" correctness="audioNoSound">音檔無聲</button>`;
            }
        }

        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 26px;">${EXAM_QUESTIONS_LIST[index]}</th>
                            <th scope="row" style="font-size: 16px;">${audioController}</th>
                            <th>
                                <div class="d-flex align-items-center">
                                    ${correctButton}
                                    ${wrongButton}
                                    ${iDontKnowButton}
                                    ${speakerSilenceButton}
                                    ${audioNoSoundButton}
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
    let currentQuestionNumber = object.attributes.questionIndex.value;
    let currentQuestionCorrectness = object.attributes.correctness.value;
    let correctness;

    let currentButtonGroup = $(`button[questionIndex=${currentQuestionNumber}]`);
    let correctButton = currentButtonGroup.filter('[correctness="correct"]');
    let wrongButton = currentButtonGroup.filter('[correctness="wrong"]');
    let iDontKnowButton = currentButtonGroup.filter('[correctness="iDontKnow"]');
    let speakerSilenceButton = currentButtonGroup.filter('[correctness="speakerSilence"]');
    let audioNoSoundButton = currentButtonGroup.filter('[correctness="audioNoSound"]');

    correctButton.css({
        "background-color": "rgba(216,214,214,0.38)",
        "color": "#1c1c1c"
    });
    wrongButton.css({
        "background-color": "rgba(216,214,214,0.38)",
        "color": "#1c1c1c"
    });
    iDontKnowButton.css({
        "background-color": "rgba(216,214,214,0.38)",
        "color": "#1c1c1c"
    });
    speakerSilenceButton.css({
        "background-color": "rgba(216,214,214,0.38)",
        "color": "#1c1c1c"
    });
    audioNoSoundButton.css({
        "background-color": "rgba(216,214,214,0.38)",
        "color": "#1c1c1c"
    });


    if (currentQuestionCorrectness === "correct") {
        correctness = "1";
    } else if (currentQuestionCorrectness === "wrong") {
        correctness = "2";
    } else if (currentQuestionCorrectness === "iDontKnow") {
        correctness = "3";
    } else if (currentQuestionCorrectness === "speakerSilence") {
        correctness = "4";
    } else if (currentQuestionCorrectness === "audioNoSound") {
        correctness = "X";
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
            if (response !== "ERROR") {
                if (currentQuestionCorrectness === "correct") {
                    correctButton.css({
                        "background-color": "#04AA6D",
                        "color": "white"
                    });
                } else if (currentQuestionCorrectness === "wrong") {
                    wrongButton.css({
                        "background-color": "#f24213",
                        "color": "white"
                    })
                } else if (currentQuestionCorrectness === "iDontKnow") {
                    iDontKnowButton.css({
                        "background-color": "#f24213",
                        "color": "white"
                    });
                } else if (currentQuestionCorrectness === "speakerSilence") {
                    speakerSilenceButton.css({
                        "background-color": "#f24213",
                        "color": "white"
                    });
                } else if (currentQuestionCorrectness === "audioNoSound") {
                    audioNoSoundButton.css({
                        "background-color": "#f24213",
                        "color": "white"
                    });
                }
            }
            // if (currentQuestionCorrectness === "correct") {
            //     if (response !== "ERROR") {
            //         $(`button[questionIndex=${currentQuestionNumber}][correctness="${currentQuestionCorrectness}"]`).css({
            //             "background-color": "#04AA6D",
            //             "color": "white"
            //         });
            //
            //         $(`button[questionIndex=${currentQuestionNumber}][correctness="wrong"]`).css({
            //             "background-color": "rgba(216,214,214,0.38)",
            //             "color": "#1c1c1c"
            //         });
            //     }
            // } else {
            //     if (response !== "ERROR") {
            //         $(`button[questionIndex=${currentQuestionNumber}][correctness="${currentQuestionCorrectness}"]`).css({
            //             "background-color": "#f24213",
            //             "color": "white"
            //         });
            //         $(`button[questionIndex=${currentQuestionNumber}][correctness="correct"]`).css({
            //             "background-color": "rgba(216,214,214,0.38)",
            //             "color": "#1c1c1c"
            //         });
            //     }
            // }
        })
        .fail(() => {
            alert("發生問題導致暫時無法存檔，請連絡相關負責人");
        });
}
