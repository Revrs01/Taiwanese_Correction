let STUDENT_DATA = [];
let CORRECTION_PROGRESS = [];
$(document).ready(() => {
    fetchAllStudent();
});


function fetchAllStudent() {
    $.ajax({
        type: "POST",
        url: "/fetch_all_student",
        contentType: "application/json",
    })
        .then(async (response) => {
            STUDENT_DATA = JSON.parse(response);
            await getCorrectionProgress();
            appendMainTable();
            appendFilterSelection();
        });
}

async function getCorrectionProgress() {
    await $.ajax({
        type: "POST",
        url: "/get_correction_progress",
        contentType: "application/json",
    })
        .then((response) => {
            CORRECTION_PROGRESS = JSON.parse(response);
            console.log("Correction Progress fetched.");
        })
}

function appendMainTable() {
    let $mainTable = $("#mainTable")
    for (let index = 0; index < STUDENT_DATA.length; index++) {
        let state = ``
        if (CORRECTION_PROGRESS[index] > 0){
            state = `<span class="badge badge-dot mr-4"><i class="bg-info"></i> 校正中</span>`
        } else if (CORRECTION_PROGRESS[index] === 100) {
            state = `<span class="badge badge-dot mr-4"><i class="bg-success"></i> 校正完成</span>`
        } else {
            state = `<span class="badge badge-dot mr-4"><i class="bg-danger"></i> 尚未校正</span>`
        }
        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["studentName"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["grade"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["studentClass"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["seatNumber"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["gender"]}</th>
                            <th>
                                ${state}
                            </th>
                            <td>
                                <div class="d-flex align-items-center">
                                    <span class="mr-2">${CORRECTION_PROGRESS[index]}%</span>
                                    <div>
                                        <div class="progress">
                                            <div class="progress-bar bg-warning" role="progressbar" aria-valuenow="${CORRECTION_PROGRESS[index]}"
                                                 aria-valuemin="0" aria-valuemax="100" style="width: ${CORRECTION_PROGRESS[index]}%;"></div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                            <th>
                                <div class="d-flex align-items-center">
                                    <button class="btn" style="color: white; background-color: orange;" buttonIndex="${index}" onclick="goToCorrectionPage(this)">進入校正</button>
                                </div>
                            </th>
                        </tr>

                        </tbody>`
        $mainTable.append(tableBody);
    }
}

function goToCorrectionPage(object) {
    let selectedStudent = STUDENT_DATA[parseInt(object.attributes.buttonIndex.value)];
    console.log(selectedStudent);
    let url = "http://localhost:31109/correction_page?" + "schoolName=" + selectedStudent["schoolName"] +
        "&grade=" + selectedStudent["grade"] +
        "&studentClass=" + selectedStudent["studentClass"] +
        "&seatNumber=" + selectedStudent["seatNumber"] +
        "&studentName=" + selectedStudent["studentName"];
    // window.open(url);
    window.location = url;
}


function openOffcanvas() {
    document.getElementById("sideNavBar").style.width = "30%";
    document.getElementById("offcanvas").style.marginLeft = "30%";
}

function closeOffcanvas() {
    document.getElementById("sideNavBar").style.width = "0";
    document.getElementById("offcanvas").style.marginLeft = "0";
}

function appendFilterSelection() {
    let $schoolNameSelection = $("#filterSchoolName");
    let $gradeSelection = $("#filterGrade");
    let $studentClassSelection = $("#filterStudentClass");

    $.ajax({
        type: "POST",
        url: "/fetch_filter_selection",
        contentType: "application/json",
    })
        .then((response) => {
            let selections = JSON.parse(response);
            $schoolNameSelection.empty();
            $schoolNameSelection.append(`<option value=""></option>`);

            $studentClassSelection.empty();
            $studentClassSelection.append(`<option value=""></option>`)

            $gradeSelection.empty();
            $gradeSelection.append(`<option value=""></option>`);

            for (let schoolName of selections["distinctSchoolName"]) {
                let option = `<option value="${schoolName}">${schoolName}</option>`;
                $schoolNameSelection.append(option);
            }

            for (let studentClass of selections["distinctStudentClass"]) {
                let option = `<option value="${studentClass}">${studentClass}</option>`;
                $studentClassSelection.append(option);
            }

            for (let grade of selections["distinctGrade"]) {
                let option = `<option value="${grade}">${grade}</option>`;
                $gradeSelection.append(option);
            }
        })

}

function filterStudent() {
    let $schoolName = $("#filterSchoolName").val();
    let $studentClass = $("#filterStudentClass").val();
    let $grade = $("#filterGrade").val();
    let $mainTable = $("#mainTable");

    $.ajax({
        type: "POST",
        url: "/filter_by_selections",
        contentType: "application/json",
        data: JSON.stringify({
            selections: [{schoolName: $schoolName}, {studentClass: $studentClass}, {grade: $grade}]
        })
    })
        .then(async (response) => {
            STUDENT_DATA = JSON.parse(response);
            $mainTable.empty();
            $mainTable.append(`<thead class="thead-light">
                        <tr>
                            <th scope="col" style="font-size: 18px;">學生姓名</th>
                            <th scope="col" style="font-size: 18px;">年級</th>
                            <th scope="col" style="font-size: 18px;">班級</th>
                            <th scope="col" style="font-size: 18px;">座號</th>
                            <th scope="col" style="font-size: 18px;">性別</th>
                            <th scope="col" style="font-size: 18px;">狀態</th>
                            <th scope="col" style="font-size: 18px;">完成度</th>
                            <th scope="col" style="font-size: 18px;">校正按鈕</th>
                        </tr>
                        </thead>`)
            await getCorrectionProgress();
            appendMainTable();
            closeOffcanvas();
        })
}

function resetFilter() {
    $("#filterSchoolName").val("");
    $("#filterStudentClass").val("");
    $("#filterGrade").val("");
    let $mainTable = $("#mainTable");
    $mainTable.empty();
    $mainTable.append(`<thead class="thead-light">
                        <tr>
                            <th scope="col" style="font-size: 18px;">學生姓名</th>
                            <th scope="col" style="font-size: 18px;">年級</th>
                            <th scope="col" style="font-size: 18px;">班級</th>
                            <th scope="col" style="font-size: 18px;">座號</th>
                            <th scope="col" style="font-size: 18px;">性別</th>
                            <th scope="col" style="font-size: 18px;">狀態</th>
                            <th scope="col" style="font-size: 18px;">完成度</th>
                            <th scope="col" style="font-size: 18px;">校正按鈕</th>
                        </tr>
                        </thead>`)
    // await getCorrectionProgress();
    fetchAllStudent();
    closeOffcanvas();
}
