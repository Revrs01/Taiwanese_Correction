let STUDENT_DATA = [];

$(document).ready(() => {
    fetchAllStudent();
});


function fetchAllStudent() {
    $.ajax({
        type: "POST",
        url: "/fetch_all_student",
        contentType: "application/json",
    })
        .then((response) => {
            STUDENT_DATA = JSON.parse(response);
            appendMainTable();
            appendFilterSelection();
        });
}

function appendMainTable() {
    let $mainTable = $("#mainTable")


    for (let index = 0; index < STUDENT_DATA.length; index++) {
        // console.log(STUDENT_DATA[student]);
        let tableBody = `<tbody>
                        <tr>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["studentName"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["grade"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["studentClass"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["seatNumber"]}</th>
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["gender"]}</th>
                            <th>
                                <span class="badge badge-dot mr-4"><i class="bg-warning"></i> pending</span>
                            </th>
                            <td>
                                <div class="d-flex align-items-center">
                                    <span class="mr-2">60%</span>
                                    <div>
                                        <div class="progress">
                                            <div class="progress-bar bg-warning" role="progressbar" aria-valuenow="60"
                                                 aria-valuemin="0" aria-valuemax="100" style="width: 60%;"></div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                            <th>
                                <div class="d-flex align-items-center">
                                    <button class="btn" style="background-color: aquamarine" buttonIndex="${index}" onclick="goToCorrectionPage(this)">進入校正</button>
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
    console.log(STUDENT_DATA);
    $.ajax({
        type: "POST",
        url: "/filter_by_selections",
        contentType: "application/json",
        data: JSON.stringify({
            selections: [{schoolName: $schoolName}, {studentClass: $studentClass}, {grade: $grade}]
        })
    })
        .then((response) => {
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
            appendMainTable();
            closeOffcanvas();
        })
}

function resetFilter(){
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
    fetchAllStudent();
    closeOffcanvas();
}
