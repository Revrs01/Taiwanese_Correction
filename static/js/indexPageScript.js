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

