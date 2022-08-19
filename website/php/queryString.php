
<?php
/*
 * Return query string parameters.
 *
 */

$projectId = isset($_GET["projectId"]) ? : "";
$workerId = isset($_GET["workerId"]) ? $_GET["workerId"] : "";
$assignmentId = isset($_GET["assignmentId"]) ? $_GET["assignmentId"] : "";
$hitId = isset($_GET["hitId"]) ? $_GET["hitId"] : "";
$turkSubmitTo = isset($_GET["turkSubmitTo"]) ? : "";

$info = array(
    "projectId"=>$projectId, "workerId"=>$workerId,
    "assignmentId"=>$assignmentId, "hitId"=>$hitId,
    "turkSubmitTo"=>$turkSubmitTo
);
echo json_encode($info);
?>