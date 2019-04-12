
<?php
/*
 * Return query string parameters.
 *
 */

$experimentId = $_GET[experimentId];
$workerId = $_GET[workerId];
$assignmentId = $_GET[assignmentId];
$hitId = $_GET[hitId];

$info = array(
    "experimentId"=>$experimentId, "workerId"=>$workerId,
    "assignmentId"=>$assignmentId, "hitId"=>$hitId
);
echo json_encode($info);
?>