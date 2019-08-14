<?php

/**
 * 
 */
function insertTrial($stmt, $type, $assignmentId, $page) {
    // Create a new trial entry in database.
    $isCatch = $page["isCatch"];
    if ($isCatch == TRUE) {
        $isCatch = 1;
    } else {
        $isCatch = 0;
    }

    mysqli_stmt_bind_param(
        $stmt, $type, $assignmentId, $page["nSelect"], $page["isRanked"],
        $page["query"],
        $page["references"][0], $page["references"][1],
        $page["references"][2], $page["references"][3],
        $page["references"][4], $page["references"][5],
        $page["references"][6], $page["references"][7],
        $page["choices"][0], $page["choices"][1],
        $page["choices"][2], $page["choices"][3],
        $page["choices"][4], $page["choices"][5],
        $page["choices"][6], $page["choices"][7],
        $page["startTimestamp"], $page["choiceRtMs"][0],
        $page["choiceRtMs"][1], $page["choiceRtMs"][2], $page["choiceRtMs"][3],
        $page["choiceRtMs"][4], $page["choiceRtMs"][5], $page["choiceRtMs"][6], 
        $page["choiceRtMs"][7], $page["submitRtMs"], $isCatch
    );
    mysqli_stmt_execute($stmt);
    mysqli_stmt_free_result($stmt);
    return $page["startTimeMs"];
}

/**
 * 
 */
function updateAssignmentStatus($link, $assignmentId) {
    $query = "UPDATE assignment SET status_code = 1, end_hit = CURRENT_TIME() WHERE assignment_id=?";
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

// Save trial responses.
// Prepare statement.
$query = "INSERT INTO trial (assignment_id, n_select, is_ranked, q_idx, ".
    "r1_idx, r2_idx, r3_idx, r4_idx, r5_idx, r6_idx, r7_idx, r8_idx, ".
    "c1_idx, c2_idx, c3_idx, c4_idx, c5_idx, c6_idx, c7_idx, c8_idx, ".
    "start_ms, c1_rt_ms, c2_rt_ms, c3_rt_ms, c4_rt_ms, c5_rt_ms, c6_rt_ms, ".
    "c7_rt_ms, c8_rt_ms, submit_rt_ms, is_catch_trial".
    ") VALUES ".
    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ".
    "?, ?, ?, ?, ?, ?, ?, ?)";
$type = "iiiiiiiiiiiiiiiiiiiisiiiiiiiiii";
$stmt = mysqli_prepare($link, $query);
// Loop over docket, save trials.
$docket = $appState["docket"];
$nPage = count($docket);
foreach ($docket as &$page) {
    switch ($page["content"]) {
        case "trial":
            $str = insertTrial($stmt, $type, $assignmentId, $page);
            break;
    }
}
mysqli_stmt_close($stmt);

updateAssignmentStatus($link, $assignmentId);
mysqli_close($link);

$returnMessage = array(
    "status"=>1
);
echo json_encode($returnMessage);
?>