<?php
/**
 * Initialize assignment and return relevant information.
 * 
 * The current appState is passed in and based on it's values,
 * is appropriately completed. The major transfer overhead is the
 * docket, which is relatively marginal.
 */

/**
 * Prepare docket from protocol.
 * @param str $dirProject  The project directory filepath.
 * @param str $json_obj  The protocol JSON object.
 * @param int $nStimuli  The number of stimuli available.
 * @return array
 */
function prepareDocket($dirProject, $docketSpec, $nStimuli) {
    $stimuliList = range(0, $nStimuli - 1);

    $docket = [];
    $nPage = count($docketSpec);
    for ($iPage = 0; $iPage < $nPage; $iPage++) {
        $page = $docketSpec[$iPage];
        switch ($page["content"]) {
            case "trial":
                $docket[] = $page;
                break;
            case "trialSpec":
                $docket[] = randomTrial(
                    $stimuliList, $page["nReference"], $page["nSelect"],
                    $page["isRanked"], $page["isCatch"]
                );
                break;
            case "blockSpec":
                $trialBlock = randomBlock($nStimuli, $page);
                $docket = array_merge($docket, $trialBlock);
                break;
            case "message":
                $fp = joinPaths($dirProject, $page["fname"]);
                if (file_exists($fp)) {
                    $file = fopen($fp, "r") or die("Unable to open specified file.");
                    $html = fread($file, filesize($fp));
                    fclose($file);
                }
                $page["html"] = $html;
                $docket[] = $page;
                break;
        }
    }
    return $docket;
}

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
    $trial = array(
        "content"=>"trial", "query"=>$idxQuery, "references"=>$idxReference,
        "nSelect"=>$nSelect, "isRanked"=>$isRanked, "isCatch"=>$isCatch
    );
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
 * $docket = shuffleDocket($docket);
 * 
 * @param object $docket  A trial docket.
 * @return object
 */
function shuffleDocket($docket) {
    $nTrial = count($docket);
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
 * Create a random block of trials.
 *
 * @param integer $nStimuli  The total number of stimuli
 * @param object $blockSpec  A block specification.
 * @return array
 */
function randomBlock($nStimuli, $blockSpec) {
    $stimuliList = range(0, $nStimuli - 1);

    $nTrial = $blockSpec["nTrial"];
    $nCatch = $blockSpec["nCatch"];
    $nReference = $blockSpec["nReference"];
    $nSelect = $blockSpec["nSelect"];
    $isRanked = $blockSpec["isRanked"];
     
    $catchTrialList = allocateCatchTrial($nTrial, $nCatch);

    $trialBlock = [];
    for ($iTrial = 0; $iTrial < $nTrial; $iTrial++) {
        $isCatch = $catchTrialList[$iTrial];
        $trial = randomTrial(
            $stimuliList, $nReference, $nSelect, $isRanked, $isCatch
        );
        $trialBlock[] = $trial;
    }
    return $trialBlock;
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
 * Retrieve protocol history from database for specified project.
 * @param object The mysqli connection object.
 * @param str The project identifier.
 * @return array
 */
function retrieveProtocolHistory($link, $projectId){
    $protocolHistory = [];
    $query = "SELECT protocol_id FROM assignment WHERE project_id=? AND (status_code=0 OR status_code=1)";
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
    $nProtocol = count($protocolList);
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
        $randIdx = random_int(0, count($minOptions) - 1);
        $protocolId = $minOptions[$randIdx];
    }
    return $protocolId;
}

$dirCollect = getenv('DIR_COLLECT');
require $dirCollect."/php/utils.php";

$appState = json_decode($_POST[appState], true);

$dirProject = joinPaths($dirCollect, "projects", $appState["projectId"]);

$stimulusList = retrieveStimulusList($dirProject);
$nStimuli = count($stimulusList);

// Connect to database.
$link = mysqli_connect($config['psiz']['servername'], $config['psiz']['username'], $config['psiz']['password'], $config['psiz']['database']);
// Check the connection.
if (mysqli_connect_errno()) {
    printf("Connect failed: %s\n", mysqli_connect_error());
    exit();
}

if (! isset($appState["protocolId"])) {
    $protocolHistory = retrieveProtocolHistory($link, $appState["projectId"]);
    $appState["protocolId"] = selectProtocol($dirProject, $protocolHistory);

    // Create a new assignment entry in database.
    $query = "INSERT INTO assignment (worker_id, project_id, protocol_id, amt_assignment_id, amt_hit_id, browser, platform) VALUES (?, ?, ?, ?, ?, ?, ?)";
    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param(
        $stmt, 'sssssss', $appState["workerId"], $appState["projectId"],
        $appState["protocolId"], $appState["amtAssignmentId"],
        $appState["amtHitId"], $appState["browser"], $appState["platform"]
    );
    mysqli_stmt_execute($stmt);
    $appState["assignmentId"] = mysqli_insert_id($link);
    mysqli_stmt_close($stmt);
}

$fpProtocol = joinPaths($dirProject, $appState["protocolId"]);
$json_str = file_get_contents($fpProtocol);
$json_obj = json_decode($json_str, true);

if (! isset($appState["docket"])) {
    $appState["docket"] = prepareDocket($dirProject, $json_obj["docket"], $nStimuli);
    $appState["trialIdx"] = 0;  // TODO
    $appState["docketIdx"] = 0;
}

$projectConfig = array(
    "stimulusList"=>$stimulusList, "appState"=>$appState
);
echo json_encode($projectConfig);
?>