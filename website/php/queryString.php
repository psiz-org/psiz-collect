
<?php
/*
 * Return query string parameters.
 *
 */

$projectId = $_GET["projectId"];
$workerId = $_GET["workerId"];
$assignmentId = $_GET["assignmentId"];
$hitId = $_GET["hitId"];
$turkSubmitTo = $_GET["turkSubmitTo"];

$info = array(
    "projectId"=>$projectId, "workerId"=>$workerId,
    "assignmentId"=>$assignmentId, "hitId"=>$hitId,
    "turkSubmitTo"=>$turkSubmitTo
);
echo json_encode($info);
?>