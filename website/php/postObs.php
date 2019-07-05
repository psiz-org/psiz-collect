<?php

/**
 * 
 */
function insertTrial($link, $assignmentId, $page) {
    // Create a new trial entry in database.
    $isCatch = $page["isCatch"];
    if ($isCatch == TRUE) {
        $isCatch = 1;
    } else {
        $isCatch = 0;
    }
    $isCorrect = 0; // TODO

    $query = "
        INSERT INTO trial (assignment_id, n_select, is_ranked, q_idx, r1_idx, 
        r2_idx, r3_idx, r4_idx, r5_idx, r6_idx, r7_idx, r8_idx, start_ms, 
        r1_rt_ms, r2_rt_ms, r3_rt_ms, r4_rt_ms, r5_rt_ms, r6_rt_ms, r7_rt_ms, 
        r8_rt_ms, is_catch_trial, is_catch_trial_correct) VALUES (?, ?, ?, ?, 
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    "; 
    $query = str_replace(array("\r","\n"), "", $query);
    $type = "iiiiiiiiiiiisiiiiiiiiii";
    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param(
        $stmt, $type, $assignmentId, $page["nSelect"], $page["isRanked"],
        $page["query"], $page["references"][0], $page["references"][1],
        $page["references"][2], $page["references"][3],
        $page["references"][4], $page["references"][5],
        $page["references"][6], $page["references"][7],
        $page["startTimestamp"], $page["choiceRtMs"][0],
        $page["choiceRtMs"][1], $page["choiceRtMs"][2], $page["choiceRtMs"][3],
        $page["choiceRtMs"][4], $page["choiceRtMs"][5], $page["choiceRtMs"][6], 
        $page["choiceRtMs"][7], $isCatch, $isCorrect
    );
    mysqli_stmt_execute($stmt);
    mysqli_stmt_close($stmt);
    return $page["startTimeMs"];
}

/**
 * 
 */
function updateAssignmentStatus($link, $assignmentId) {
    $query = "UPDATE assignment SET status_code = 1 WHERE assignment_id=?";
    $type = "i";
    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param(
        $stmt, $type, $assignmentId
    );
    mysqli_stmt_execute($stmt);
    mysqli_stmt_close($stmt);
}

$dirCollect = getenv('DIR_COLLECT');
require $dirCollect."/php/utils.php";

$dirProject = joinPaths($dirCollect, "projects", $appState["projectId"]);
$appState = json_decode($_POST[appState], true);
$assignmentId = $appState["assignmentId"];

// Connect to database.
$link = mysqli_connect($config['psiz']['servername'], $config['psiz']['username'], $config['psiz']['password'], $config['psiz']['database']);
// Check the connection.
if (mysqli_connect_errno()) {
    printf("Connect failed: %s\n", mysqli_connect_error());
    exit();
}

// Loop over docket, save trials.
$docket = $appState["docket"];
$nPage = count($docket);
foreach ($docket as &$page) {
    switch ($page["content"]) {
        case "trial":
            $str = insertTrial($link, $assignmentId, $page);
            break;
    }
}
updateAssignmentStatus($link, $assignmentId);

$returnMessage = array(
    "status"=>1
);
echo json_encode($returnMessage);
?>