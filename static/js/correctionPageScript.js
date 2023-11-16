let EXAM_QUESTIONS = [];

$(document).ready(() => {
    let urlParameters = new URLSearchParams(window.location.search);
    $('#cardTitle').append(urlParameters.get("studentName"));
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
                            <th scope="row" style="font-size: 16px;"><audio controls style="width: 400px;"></audio></th>
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