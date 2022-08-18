
<?php
/*
 * Return AMT query string parameters.
 *
 */

$projectId = $_GET["projectId"];
$workerId = $_GET["workerId"];
$assignmentId = $_GET["assignmentId"];
$hitId = $_GET["hitId"];
$isLive = $_GET["isLive"];

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