<?php
$referenceJson = json_decode(stripslashes($_POST['referenceJson']), true); // true gives an array (default is an object)

$dirCollect = getenv('DIR_COLLECT');
$projectId = $_POST[projectId];


?>