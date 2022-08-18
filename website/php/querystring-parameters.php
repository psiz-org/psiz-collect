
<?php
/*
 * Return AMT query string parameters.
 *
 */

$projectId = isset($_GET["projectId"]) ? $_GET["projectId"] : "";
$workerId = isset($_GET["workerId"]) ? $_GET["workerId"]: "";
$assignmentId = isset($_GET["assignmentId"]) ? $_GET["assignmentId"] : "";
$hitId = isset($_GET["hitId"]) ? $_GET["hitId"] : "";
$isLive = isset($_GET["isLive"]) ? $_GET["isLive"] : "";

// If AMT query string parameters don't exist, set to empty strings.
if (is_null($assignmentId)) {
    $workerId = "";
    $assignmentId = "";
    $hitId = "";
    $isLive = -1;
}

$info = array(
    "projectId"=>$projectId,
    "workerId"=>$workerId,
    "assignmentId"=>$assignmentId,
    "hitId"=>$hitId,
    "isLive"=>$isLive
);
echo json_encode($info);
?>