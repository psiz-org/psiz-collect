<?php
/**
 * Initialize assignment and return relevant assignment details.
 */

/**
 * Creates a random trial.
 *
 * @param integer $stimuliList  List of available stimuli.
 * @param integer $nReference  The number of reference stimuli to
 *  include in the trial.
 * @param integer $nSelect  The number of stimuli the must be selected.
 * @param boolean $isRanked  If the selections should be ranked.
 * @param boolean $isCatch  If the trial is a catch trial.
 * @return associative array
 */
function randomTrial($stimuliList, $nReference, $nSelect, $isRanked, $isCatch) {
    shuffle($stimuliList);
    $idxQuery = $stimuliList[0];
    $idxReference = array_slice($stimuliList, 1, $nReference);
    if ($isCatch) {
        $sameIdx = rand(0, $nReference - 1);
        $idxReference[$sameIdx] = $idxQuery;
    }
    $trial = array("query"=>$idxQuery, "references"=>$idxReference, "nSelect"=>$nSelect, "isRanked"=>$isRanked, "isCatch"=>$isCatch);
    return $trial;
}

/**
 * Determines which trials should be catch trials (if any).
 *
 * @param integer $nTrial  The total number of trials in the session.
 * @param integer $nCatch  The number of catch trials in the session.
 * @return array
 */
function allocateCatchTrial($nTrial, $nCatch) {
    $catchTrialList = array_fill(0, $nTrial, FALSE);
    if ($nCatch > 0) {
        $nCatch = min($nCatch, $nTrial);
        $step = round($nTrial / $nCatch);
        $idxStart = 0;
        for ($iCatch = 0; $iCatch < $nCatch; $iCatch++) {
            $idxEnd = min($idxStart + $step - 1, $nTrial -1);
            // Sample from interval.
            $catchIdx = rand($idxStart, $idxEnd);
            $catchTrialList[$catchIdx] = TRUE;
            $idxStart = $idxStart + $step;
        }
    }
    return $catchTrialList;
}

/**
 * Randomly shuffle the trial docket.
 *
 * @param object $docket  A trial docket.
 * @return object
 */
function shuffleDocket($docket) {
    $nTrial = sizeof($docket);
        $trialIdx = range(0, $nTrial - 1);
        shuffle($trialIdx);

        $docketShuffled = [];
        for ($iTrial = 0; $iTrial < $nTrial; $iTrial++) {
            $docketShuffled[] = $docket[$trialIdx[$iTrial]];
        }
    $docket = $docketShuffled;
    return $docket;
}

/**
 * Create a random docket.
 *
 * @param integer $nStimuli  The total number of stimuli
 * @param object $docketSpec  A docket specification.
 * @return array
 */
function randomDocket($nStimuli, $docketSpec) {
    $stimuliList = range(0, $nStimuli - 1);

    $nTrial = $docketSpec["nTrial"];
    $nCatch = $docketSpec["nCatch"];
    $nReference = $docketSpec["nReference"];
    $nSelect = $docketSpec["nSelect"];
    $isRanked = $docketSpec["isRanked"];
     
    $catchTrialList = allocateCatchTrial($nTrial, $nCatch);

    $docket = [];
    for ($iTrial = 0; $iTrial < $nTrial; $iTrial++) {
        $isCatch = $catchTrialList[$iTrial];
        $trial = randomTrial(
            $stimuliList, $nReference, $nSelect, $isRanked, $isCatch
        );
        $docket[] = $trial;
    }
    return $docket;
}

/**
 * Join paths in a manner similar to python os.path.join(*).
 *
 * See: https://stackoverflow.com/a/1557529
 * 
 * @param array $arg  An array of strings.
 * @return str
 */
function joinPaths() {
    $paths = array();

    foreach (func_get_args() as $arg) {
        if ($arg !== '') { $paths[] = $arg; }
    }

    return preg_replace('#/+#','/',join('/', $paths));
}

/**
 * Retreive list of available stimuli for the project.
 *
 * @param str $dirProject  The project filepath.
 * @return array
 */
function retrieveStimulusList($dirProject) {
    $fnStimulusList = joinPaths($dirProject, "stimuli.txt");
    $stimulusList = [];
    $handle = fopen($fnStimulusList, "r");
    if ($handle) {
        while (($line = fgets($handle)) !== false) {
            // Process the line.
            $line = str_replace(PHP_EOL, '', $line);
            $stimulusList[] = $line;	
        }
        fclose($handle);
    }
    return $stimulusList;
}

/**
 * Prepare docket from protocol.
 * @param str $json_obj  The protocol JSON object.
 * @param int $nStimuli  The number of stimuli available.
 * @return array
 */
function prepareDocket($json_obj, $nStimuli) {
    $gen_type = $json_obj["generator"];
    if ($gen_type == "deterministic") {
        // Use provided docket.
        $docket = $json_obj["docket"];
        if ($json_obj["shuffleTrials"]) {
            $docket = shuffleDocket($docket);
        }
    } else {
        // Generate a random docket.
        $docketSpec = $json_obj["docketSpec"];
        $docket = randomDocket($nStimuli, $docketSpec);
    }
    return $docket;
}

/**
 * Retrieve protocol history from database for specified project.
 * @param object The mysqli connection object.
 * @param str The project identifier.
 * @return array
 */
function retrieveProtocolHistory($link, $projectId){
    $protocolHistory = [];
    $query = "SELECT protocol_id FROM assignment WHERE project_id=?";
    if ($stmt = mysqli_prepare($link, $query)) {
        mysqli_stmt_bind_param($stmt, 's', $projectId);
        mysqli_stmt_execute($stmt);
        mysqli_stmt_bind_result($stmt, $rowResult);
        while (mysqli_stmt_fetch($stmt)) {
            $protocolHistory[] = $rowResult;	
        }
        mysqli_stmt_close($stmt);
    }
    return $protocolHistory;
}

/**
 * Select a JSON-formatted protocol based on usage statistics.
 * 
 * The protocol with the lowest use is selected. Ties are broken
 * stochastically. Only protocols in the project directory will be
 * used.
 * 
 * @param str The directory filepath.
 * @param array An array containing all previously used protocols.
 * @return str The filename of the selected protocol.
 */
function selectProtocol($dirProject, $protocolHistory) {
    $protocolList = glob($dirProject.'/protocol*.json');
    $nProtocol = sizeof($protocolList);
    if ($nProtocol == 0) {
        // Issue error. TODO
    } else {
        // Select from available protocol(s) based on usage history.
        for ($iProtocol = 0; $iProtocol < $nProtocol; $iProtocol++) {
            $protocolList[$iProtocol] = basename($protocolList[$iProtocol]);
        }
        
        // Tally all protocols in database.
        $allProtocolFrequency = array_count_values($protocolHistory);
        // But only select from protocols that are currently in the project
        // folder.
        $protocolFrequency = [];
        for ($iProtocol = 0; $iProtocol < $nProtocol; $iProtocol++) {
            $protocolId = $protocolList[$iProtocol];
            if (array_key_exists($protocolId, $allProtocolFrequency)) {
                $protocolFrequency[$protocolId] = $allProtocolFrequency[$protocolId];
            } else {
                $protocolFrequency[$protocolId] = 0;
            }
        }
        $minOptions = array_keys($protocolFrequency, min($protocolFrequency));
        $randIdx = random_int(0, sizeof($minOptions) - 1);
        $protocolId = $minOptions[$randIdx];
    }
    return $protocolId;
}

// NOTE: You must change the filepath to reflect your server setup.
$mysqlCredentialsPath = '/home/bdroads/.mysql/credentials';

$controllerState = json_decode($_POST[controllerState], true);

$dirCollect = getenv('DIR_COLLECT');
$dirProject = joinPaths($dirCollect, $controllerState["projectId"]);

$stimulusList = retrieveStimulusList($dirProject);
$nStimuli = sizeof($stimulusList);

// Parse MySQL configuration.
$config = parse_ini_file($mysqlCredentialsPath, true);

// Connect to database.
$link = mysqli_connect($config['psiz']['servername'], $config['psiz']['username'], $config['psiz']['password'], $config['psiz']['database']);
// Check the connection.
if (mysqli_connect_errno()) {
    printf("Connect failed: %s\n", mysqli_connect_error());
    exit();
}

if (! isset($controllerState["protocolId"])) {
    $protocolHistory = retrieveProtocolHistory($link, $controllerState["projectId"]);
    $controllerState["protocolId"] = selectProtocol($dirProject, $protocolHistory);

    // Create new assignment entry in database.
    $workerId = $_POST[workerId];
    $amtAssignmentId = $_POST[amtAssignmentId];
    $amtHitId = $_POST[amtHitId];
    $browser = $_POST[browser];
    $platform = $_POST[platform];
    $query = "INSERT INTO assignment (worker_id, project_id, protocol_id, amt_assignment_id, amt_hit_id, browser, platform) VALUES (?, ?, ?, ?, ?, ?, ?)";
    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param(
        $stmt, 'sssssss', $workerId, $controllerState["projectId"],
        $controllerState["protocolId"], $amtAssignmentId, $amtHitId, $browser,
        $platform
    );
    mysqli_stmt_execute($stmt);
    $controllerState["assignmentId"] = mysqli_insert_id($link);
    mysqli_stmt_close($stmt);
}

$fpProtocol = joinPaths($dirProject, $controllerState["protocolId"]);
$json_str = file_get_contents($fpProtocol);
$json_obj = json_decode($json_str, true);

if (! isset($controllerState["docket"])) {
    $controllerState["docket"] = prepareDocket($json_obj, $nStimuli);
    $controllerState["trialIdx"] = 0;
}

// Set consent.
$consent = NULL;
if (isset($json_obj["consent"])) {
    $fpConsent = joinPaths($dirProject, $json_obj["consent"]);
    if (file_exists($fpConsent)) {
        $consentFile = fopen($fpConsent, "r") or die("Unable to open specified consent file.");
        $consent = fread($consentFile, filesize($fpConsent));
        fclose($consentFile);
        $controllerState["isConsent"] = true;
    }   
}

// Set instructions.
$instructions = NULL;
if (isset($json_obj["instructions"])) {
    $fpInstructions = joinPaths($dirProject, $json_obj["instructions"]);
    if (file_exists($fpInstructions)) {
        $instructionsFile = fopen($fpInstructions, "r") or die("Unable to open specified instructions file.");
        $instructions = fread($instructionsFile, filesize($fpInstructions));
        fclose($instructionsFile);
    }   
}

// Set survey.
$survey = NULL;
if (isset($json_obj["survey"])) {
    $fpSurvey = joinPaths($dirProject, $json_obj["survey"]);
    if (file_exists($fpSurvey)) {
        $surveyFile = fopen($fpSurvey, "r") or die("Unable to open specified survey file.");
        $survey = fread($surveyFile, filesize($fpSurvey));
        fclose($surveyFile);
        $controllerState["isSurvey"] = true;
    }   
}

$projectConfig = array(
    "stimulusList"=>$stimulusList, "controllerState"=>$controllerState,
    "instructions"=>$instructions, "consent"=>$consent, "survey"=>$survey,
);
echo json_encode($projectConfig);
?>