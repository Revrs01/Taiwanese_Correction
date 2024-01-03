async function newLayout(){
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
            correctButton = `<button class="btn" style="background-color: #04AA6D; color: white;" buttonIndex="${index}" onclick="showCorrectStudentErrorPage(this)">正確</button>`;
            wrongButton = `<button class="btn" style="background-color: #f24213; color: white;" buttonIndex="${index}" onclick="showCorrectStudentErrorPage(this)">錯誤</button>`;
        } else {
            correctButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: white;" buttonIndex="${index}" onclick="showCorrectStudentErrorPage(this)">正確</button>`;
            wrongButton = `<button class="btn" style="background-color: rgba(216,214,214,0.38); color: white;" buttonIndex="${index}" onclick="showCorrectStudentErrorPage(this)">錯誤</button>`;
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
}