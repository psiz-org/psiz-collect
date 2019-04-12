<?php
/**
 * Return experiment details.
 */

/**
 * Creates a random trial.
 *
 * @param integer $nStimuli  The total number of stimuli available.
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
    $trial = array("query"=>$idxQuery, "references"=>$idxReference, "n_select"=>$nSelect, "is_ranked"=>$isRanked, "is_catch"=>$isCatch);
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

    $nTrial = $docketSpec["n_trial"];
    $nCatch = $docketSpec["n_catch"];
    $nReference = $docketSpec["n_reference"];
    $nSelect = $docketSpec["n_select"];
    $isRanked = $docketSpec["is_ranked"];
     
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

$dirCollect = getenv('DIR_COLLECT');
$experimentId = $_POST[experimentId];
$dirExperiment = joinPaths($dirCollect, $experimentId);

// Retreive list of available stimuli.
$fnStimulusList = joinPaths($dirExperiment, "stimuli.txt");
$stimulusList = [];
$handle = fopen($fnStimulusList, "r");
if ($handle) {
    while (($line = fgets($handle)) !== false) {
        // process the line read.
        $line = str_replace(PHP_EOL, '', $line);
        $stimulusList[] = $line;	
    }
    fclose($handle);
}
$nStimuli = sizeof($stimulusList);

// Select a JSON-formatted protocol.
$protocolList = glob($dirExperiment.'/protocol*.json');
$nProtocol = sizeof($protocolList);
if ($nProtocol == 0) {
    // Issue error. TODO
} else {
    // Select from available protocol(s) based on usage history.
    for ($iProtocol = 0; $iProtocol < $nProtocol; $iProtocol++) {
        $protocolList[$iProtocol] = basename($protocolList[$iProtocol]);
    }
    // Retrieve usage history from database. TODO
    $fpProtocol = $dirExperiment."/protocol_0.json";
}

// Prepare docket from protocol.
$json_str = file_get_contents($fpProtocol);
$json_obj = json_decode($json_str, true);
$gen_type = $json_obj["generator"];
if ($gen_type == "deterministic") {
    // Use provided docket.
    $docket = $json_obj["docket"];
    if ($json_obj["shuffle_trials"]) {
        $docket = shuffleDocket($docket);
    }
} else {
    // Generate a random docket.
    $docketSpec = $json_obj["docket_spec"];
    $docket = randomDocket($nStimuli, $docketSpec);
}

// Prepare experiment configuration.

// Set consent.
$consent = NULL;
if (isset($json_obj["consent"])) {
    $fpConsent = joinPaths($dirExperiment, $json_obj["consent"]);
    if (file_exists($fpConsent)) {
        $consentFile = fopen($fpConsent, "r") or die("Unable to open specified consent file.");
        $consent = fread($consentFile, filesize($fpConsent));
        fclose($consentFile);
    }   
}

// Set instructions.
$instructions = NULL;
if (isset($json_obj["instructions"])) {
    $fpInstructions = joinPaths($dirExperiment, $json_obj["instructions"]);
    if (file_exists($fpInstructions)) {
        $instructionsFile = fopen($fpInstructions, "r") or die("Unable to open specified instructions file.");
        $instructions = fread($instructionsFile, filesize($fpInstructions));
        fclose($instructionsFile);
    }   
}

// Set survey.
$survey = NULL;
if (isset($json_obj["survey"])) {
    $fpSurvey = joinPaths($dirExperiment, $json_obj["survey"]);
    if (file_exists($fpSurvey)) {
        $surveyFile = fopen($fpSurvey, "r") or die("Unable to open specified survey file.");
        $survey = fread($surveyFile, filesize($fpSurvey));
        fclose($surveyFile);
    }   
}

$experimentConfig = array(
    "stimulusList"=>$stimulusList, "docket"=>$docket,
    "instructions"=>$instructions, "consent"=>$consent, "survey"=>$survey
);
echo json_encode($experimentConfig);
?>