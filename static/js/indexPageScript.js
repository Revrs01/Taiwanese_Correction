let STUDENT_DATA = [];
let CORRECTION_PROGRESS = [];
let PAGE_NUMBER = sessionStorage.getItem('pageNumber') === null ? 0 : parseInt(sessionStorage.getItem('pageNumber'));
$(document).ready(async () => {
    await fetchStudents();

    if (sessionStorage.getItem('schoolName') || sessionStorage.getItem('studentClass') ||
        sessionStorage.getItem('grade')) {
        // console.log("YOU RUN INTO IF STATE");
        $('#filterGrade').val(sessionStorage.getItem('grade'));
        $('#filterSchoolName').val(sessionStorage.getItem('schoolName'));
        $('#filterStudentClass').val(sessionStorage.getItem('studentClass'));
        filterStudent();
    } else {
        console.log("First entry, initialize sessionStorage");
        sessionStorage.setItem('schoolName', '');
        sessionStorage.setItem('studentClass', '');
        sessionStorage.setItem('grade', '');
        sessionStorage.setItem('pageNumber', "0");
        sessionStorage.setItem('isFilterTriggered', "0");
    }
});

async function goToHomePage() {
    window.location = '/';
    console.log("Go to HomePage, clear sessionStorage");
    sessionStorage.clear();
    await fetchStudents();
}

async function fetchStudents() {
    await $.ajax({
        type: "POST",
        url: "/fetch_students",
        contentType: "application/json",
        data: JSON.stringify({
            startIndex: (PAGE_NUMBER * 40).toString(),
        }),
    })
        .then(async (response) => {
            STUDENT_DATA = JSON.parse(response);
            $('#currentPage').text((PAGE_NUMBER + 1).toString());
            await getCorrectionProgress();
            appendMainTable();
            await appendFilterSelection();
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
    let $mainTable = $("#mainTable");
    for (let index = 0; index < STUDENT_DATA.length; index++) {
        // if (index >= STUDENT_DATA.length) {
        //     break;
        // }
        let state = ``
        if (CORRECTION_PROGRESS[index] > 0 && CORRECTION_PROGRESS[index] < 100) {
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
                            <th scope="row" style="font-size: 16px;">${STUDENT_DATA[index]["gender"] === "1" ? "男" : "女"}</th>
                            <th>
                                ${state}
                            </th>
                            <td>
                                <div class="d-flex align-items-center">
                                    <span class="mr-2">${CORRECTION_PROGRESS[index]}%</span>
                                    <div>
                                        <div class="progress">
                                            <div class="progress-bar bg-success" role="progressbar" aria-valuenow="${CORRECTION_PROGRESS[index]}"
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

    let url = "correction_page?" + "schoolName=" + selectedStudent["schoolName"] +
        "&grade=" + selectedStudent["grade"] +
        "&studentClass=" + selectedStudent["studentClass"] +
        "&seatNumber=" + selectedStudent["seatNumber"] +
        "&studentName=" + selectedStudent["studentName"] +
        "&birthdayYear=" + selectedStudent["birthdayYear"] +
        "&birthdayMonth=" + selectedStudent["birthdayMonth"] +
        "&birthdayDay=" + selectedStudent["birthdayDay"] +
        "&gender=" + selectedStudent["gender"];

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

async function appendFilterSelection() {
    let $schoolNameSelection = $("#filterSchoolName");
    let $gradeSelection = $("#filterGrade");
    let $studentClassSelection = $("#filterStudentClass");

    await $.ajax({
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
    let $schoolName = document.getElementById('filterSchoolName').value;
    let $studentClass = document.getElementById('filterStudentClass').value;
    let $grade = document.getElementById('filterGrade').value;
    let $mainTable = $("#mainTable");
    let $currentPage = $("#currentPage");


    if (sessionStorage.getItem('isFilterTriggered') === "1") {
        // if the filter functionality is used, set PAGE_NUMBER to stored pageNumber
        PAGE_NUMBER = parseInt(sessionStorage.getItem('pageNumber'));
        $currentPage.text((PAGE_NUMBER + 1).toString());
    } else {
        // otherwise, this is a new incoming filter, then set PAGE_NUMBER to 0
        PAGE_NUMBER = 0;
        sessionStorage.setItem('pageNumber', "0");
        $currentPage.text((PAGE_NUMBER + 1).toString());
        sessionStorage.setItem('isFilterTriggered', "1");
    }

    // set session to new filter information
    sessionStorage.setItem('schoolName', $schoolName);
    sessionStorage.setItem('studentClass', $studentClass);
    sessionStorage.setItem('grade', $grade);

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

async function resetFilter() {
    sessionStorage.setItem('isFilterTriggered', "0");
    $("#filterSchoolName").val("");
    $("#filterStudentClass").val("");
    $("#filterGrade").val("");
    console.log("RESET button clicked ! Session Cleared.");
    sessionStorage.setItem('schoolName', "");
    sessionStorage.setItem('studentClass', "");
    sessionStorage.setItem('grade', "");
    sessionStorage.setItem('pageNumber', "0");

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
    await fetchStudents();
    closeOffcanvas();
}

async function switchPage(object) {
    if (sessionStorage.getItem("isFilterTriggered") === "1") {
        alert("已經到底囉");
        return;
    }

    if (object.innerText === '>') {
        PAGE_NUMBER++;
    } else if (object.innerText === '<' && PAGE_NUMBER !== 0) {
        PAGE_NUMBER--;
    } else {
        alert("已經到底囉");
        return;
    }
    sessionStorage.setItem('pageNumber', PAGE_NUMBER.toString());
    let $mainTable = $("#mainTable");
    let $currentPage = $("#currentPage");
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
    $currentPage.text((PAGE_NUMBER + 1).toString());
    await fetchStudents();
    await appendMainTable();
}

function exportExcelFile(exportTypeBool) {
    fetch('/output_xlsx', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // specify that the data is JSON
        },
        body: JSON.stringify({exportType: exportTypeBool}),
    })
        .then(response => {
            if (response.ok) {
                // If the response is successful, trigger a download
                return response.blob();
            } else {
                throw new Error('None of correction file exist, or consist authorization problem');
            }
        })
        .then(async (blob) => {
            // Create a link element to trigger the download
            const a = document.createElement('a');
            const url = window.URL.createObjectURL(await blob);
            a.href = url;
            if (exportTypeBool) {
                a.download = "學生總表(完整).xlsx"
            } else {
                a.download = '學生總表(刪減).xlsx';
            }
            a.style.display = 'none';

            // Append the link to the document and trigger a click event
            document.body.appendChild(a);
            a.click();

            // Remove the link from the document
            document.body.removeChild(a);

            // Clean up by revoking the object URL
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('必須有一筆校正資料才能下載，若仍然無法下載，請聯絡相關負責人。');
        });


}