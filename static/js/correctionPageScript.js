let EXAM_QUESTIONS_LIST = [];
let EXAM_QUESTIONS_NUMBER = [];
let urlParameters = new URLSearchParams(window.location.search);
let $studentName = urlParameters.get("studentName");
let $schoolName = urlParameters.get("schoolName");
let $grade = urlParameters.get("grade");
let $studentClass = urlParameters.get("studentClass");
let $seatNumber = urlParameters.get("seatNumber");
let CORRECTION_DATA = {};
let $CORRECTNESS = "";
let CURRENT_CORRECTING_NUMBER = "";


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

        let audioController = ``;
        if (audioString !== "") {
            audioController = `<audio controls><source src='data:audio/wav;base64,${audioString}' type="audio/wav"></audio>`;
        }

        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 26px;">${EXAM_QUESTIONS_LIST[index]}</th>
                            <th scope="row" style="font-size: 16px;">${audioController}</th>
                            <th>
                                <div class="d-flex align-items-center">
                                    <button class="btn-modal" buttonIndex="${index}" onclick="showCorrectStudentErrorPage(this)">糾正錯誤</button>
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

function showCorrectStudentErrorPage(object) {
    const modalHeader = `<div class="flex">
        <h1>校正列表</h1>
        <button class="btn-close" onclick="closeModalWithoutSave()">不保存離開</button>
    </div>
    <div>
        <label style="font-size: 24px;">正確性評分：
            <select id="correctness" required style="width: 100px; height: 25px;">
                <option value=""></option>
                <option value="正確">正確</option>
                <option value="錯誤">錯誤</option>
                <option value="沒念/毋知/袂曉">沒念/毋知/袂曉</option>
                <option value="音檔無聲">音檔無聲</option>
            </select>
        </label>

    </div>
    <hr style="height:3px;border-width:0;color:rgb(128,128,128);background-color:rgb(128,128,128)">`

    CURRENT_CORRECTING_NUMBER = object.attributes.buttonIndex.value;
    let $modalSection = $("#modalSection");
    let $modalOverlay = $("#modalOverlay");


    // fetch correction file first
    $.ajax({
        type: "POST",
        url: '/get_correction_data',
        contentType: "application/json",
        data: JSON.stringify({
            schoolName_grade_studentClass_seatNumber_studentName: `${$schoolName}_${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            questionNumber: EXAM_QUESTIONS_NUMBER[CURRENT_CORRECTING_NUMBER]
        })
    })
        .then((response) => {
            $modalSection.append(modalHeader);
            $CORRECTNESS = $("#correctness");
            CORRECTION_DATA = JSON.parse(response);
            console.log(CORRECTION_DATA);
            let modalBody = `<div style="font-size: 20px;">
        <label>
            入聲：
            <input type="text" class="input-block" maxlength="5" placeholder="例：1,2 (填入音節)" value="${CORRECTION_DATA["入聲"]}">
        </label>
    </div>
    <div style="font-size: 20px;">
        送氣音：
        <br>
        <div style="margin-left: 40px;">
            <label>
                脫落
                <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["脫落"]}">
            </label>
            &nbsp;
            <label>
                增加
                <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["增加"]}">
            </label>
        </div>

    </div>
    <div style="font-size: 20px;">
        <label>
            清濁錯誤：
            <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["清濁錯誤"]}">
        </label>
    </div>
    <div style="font-size: 20px;">
        聲調錯誤：
        <br>
        <div style="margin-left: 40px;">
            <label>
                讀成華語四聲
                <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["讀成華語四聲"]}">
            </label>
            <br>
            <label>
                錯讀
                <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["錯讀"]}">
            </label>
            <br>
            <label>
                變調錯誤
                <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["變調錯誤"]}">
            </label>
        </div>

    </div>
    <hr>
    <div style="width: 100%; justify-content: space-between">
        <label style="font-size: 20px;">
            讀異音：
            <input type="text" class="input-block" maxlength="5" placeholder="請填入音節用逗號隔開" value="${CORRECTION_DATA["讀異音"]}">
        </label>
        <label>
            <input placeholder="詳細說明" type="text" style="width: 70%;" value="${CORRECTION_DATA["讀異音詳細"]}">
        </label>
    </div>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            連結字偏旁：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["連結字偏旁"]}">
        </label>
    </div>
    <hr>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            從華語字義轉譯成台語：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["從華語字義轉譯成台語"]}">
        </label>
    </div>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            直接唸成華語讀法：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["直接唸成華語讀法"]}">
        </label>
    </div>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            字義理解錯誤：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["字義理解錯誤"]}">
        </label>
    </div>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            狀態：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["狀態"]}">
        </label>
    </div>
    <hr>
    <div style="width: 100%;">
        <label style="font-size: 20px;">
            備註欄：
            <input placeholder="詳細說明" type="text" style="width: 80%;" value="${CORRECTION_DATA["備註欄"]}">
        </label>
    </div>
    <button class="btn-modal" style="background-color: forestgreen; color: white" onclick="closeModalSaveData()">保存並離開</button>
<br>`

            $modalSection.append(modalBody);
            $CORRECTNESS.val(CORRECTION_DATA["正確性評分"]);
        })
        .done(() => {
            $modalOverlay.removeClass("hidden");
            $modalSection.removeClass("hidden");
        })
}

function closeModalWithoutSave() {
    let modalSection = document.getElementById("modalSection");
    let modalOverlay = document.getElementById("modalOverlay");
    modalSection.classList.add("hidden");
    modalOverlay.classList.add("hidden");
    modalSection.innerHTML = "";
}

function closeModalSaveData() {
    let modalSection = document.getElementById("modalSection");
    let modalOverlay = document.getElementById("modalOverlay");
    let correctnessEvaluate = document.getElementById("correctness")

    let correctionInput = [];
    modalSection.querySelectorAll("input").forEach((inputElement) => {
        correctionInput.push(inputElement.value);
    })
    modalSection.classList.add("hidden");
    modalOverlay.classList.add("hidden");
    modalSection.innerHTML = "";

    $.ajax({
        type: "POST",
        url: '/save_correction_data',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({
            schoolName_grade_studentClass_seatNumber_studentName: `${$schoolName}_${$grade}_${$studentClass}_${$seatNumber}_${$studentName}`,
            questionNumber: EXAM_QUESTIONS_NUMBER[CURRENT_CORRECTING_NUMBER],
            correctionData: {
                正確性評分: correctnessEvaluate.value,
                入聲: correctionInput[0],
                脫落: correctionInput[1],
                增加: correctionInput[2],
                清濁錯誤: correctionInput[3],
                讀成華語四聲: correctionInput[4],
                錯讀: correctionInput[5],
                變調錯誤: correctionInput[6],
                讀異音: correctionInput[7],
                讀異音詳細: correctionInput[8],
                連結字偏旁: correctionInput[9],
                從華語字義轉譯成台語: correctionInput[10],
                直接唸成華語讀法: correctionInput[11],
                字義理解錯誤: correctionInput[12],
                狀態: correctionInput[13],
                備註欄: correctionInput[14]
            }
        })
    })
        .then((response) => {
            console.log(response);
        });
}