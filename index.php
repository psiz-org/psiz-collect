<!DOCTYPE html>
<html>

<head>
	<title>Collect - PsiZ</title>
	<meta charset="UTF-8">
	<meta name="keywords" content="HTML, CSS, XML, XHTML, JavaScript">
	<meta name="description" content="PsiZ Collect">
    <meta name="author" content="B. D. Roads">

    <!-- jQuery library -->
    <script src="https://code.jquery.com/jquery-3.3.1.js" integrity="sha256-2Kok7MbOyxpgUVvAk/HJ2jigOSYS2auK4Pfzbm7uH60=" crossorigin="anonymous"></script>
    <!-- Bootstap - Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">

    <!-- Note: psiz-collection assets must be loaded by going up a directory
    since re-write rule places the active experiment in a subdirectory. -->
    <link rel='stylesheet' href='../psiz-collect/static/css/general.css'>
</head>

<body>
    <noscript>
        <h1>Warning: Javascript seems to be disabled</h1>
        <p>This website requires that Javascript be enabled on your browser.</p>
        <p>Instructions for enabling Javascript in your browser can be found <a href="http://support.google.com/bin/answer.py?hl=en&answer=23852">here</a></p>
    </noscript>
    
    <div class="consent">
        <div class="row">
            <div class="col-xs-1 col-md-2"></div>
            <div class="consent__content col-xs-10 col-md-8">
                <?php require "templates/default-consent.html"; ?>
            </div>
            <div class="col-xs-1 col-md-2"></div>
        </div>
        <div class="row">
            <div class="col-xs-3 col-md-5"></div>
            <div class="col-xs-3 col-md-2">
                <div id='consent-button' class='custom-button custom-button--enabled'>I Agree</div>
            </div>
            <div class="col-xs-3 col-md-5"></div>
        </div>
    </div>

    <div class="instructions">
        <div class="row">
            <div class="col-xs-1 col-md-3"></div>
            <div class="instructions__content col-xs-10 col-md-6">
                <?php require "templates/default-instructions.php"; ?>
            </div>
            <div class="col-xs-1 col-md-3"></div>
        </div>
        <div class="row">
            <div class="col-xs-3 col-md-5"></div>
            <div class="col-xs-3 col-md-2">
                <div id='instructions-button' class='custom-button custom-button--enabled'>OK</div>
            </div>
            <div class="col-xs-3 col-md-5"></div>
        </div>
    </div>

    <div class='container-fluid overlay overlay-instructions'>
        <div class="row">
            <div class="col-xs-1 col-md-3"></div>
            <div class="instructions__content col-xs-10 col-md-6">
                <?php require "templates/default-instructions.php"; ?>
            </div>
            <div class="col-xs-1 col-md-3"></div>
        </div>
        <div class="row">
            <button type="button" id='overlay-instructions-button' class='overlay__button'>OK</button>
        </div>
    </div>

    <div class="survey">
        <div class="row">
            <div class="col-xs-1 col-md-2"></div>
            <div class="survey__content col-xs-10 col-md-8"></div>
            <div class="col-xs-1 col-md-2"></div>
        </div>
        <div class="row">
            <div class="col-xs-3 col-md-5"></div>
            <div class="col-xs-3 col-md-2">
                <div id='survey-button' class='custom-button custom-button--enabled'>Submit</div>
            </div>
            <div class="col-xs-3 col-md-5"></div>
        </div>
    </div>

    <?php require "templates/grid.php"; ?>

    <script src="../psiz-collect/static/js/AppController.js"></script>
    <script src="../psiz-collect/static/js/utils.js"></script>
    <script type="text/javascript">
    var info = <?php require "./php/queryString.php"; ?>;
    var projectId = info["projectId"];
    var workerId = info['workerId']  // TODO
    var amtAssignmentId = info["assignmentId"]
    var amtHitId = info["hitId"]
    var userInfo = userSystemInfo();

    // Proposal
    // pass current controller state to initialize.php
    //     it will handle appropriate logic and return complete controller state
    //     overhead: docket

    var newAssignment = true;
    var controllerStateOld = {};
    var protocolId = "";
    if (sessionStorage.getObject(projectId)) {
        newAssignment = false;
        controllerStateOld = sessionStorage.getObject(projectId);
        protocolId = controllerStateOld.protocolId;
    }

    var stimulusList = [];
    var controllerState = {};
    // TODO inside initialize.php
    // handle new session logic
    // TODO have to store protocol ID, because need to know what instructions, etc. to use

    var dataToPost = {
        projectId: projectId, protocolId: protocolId, workerId: workerId,
        amtAssignmentId: amtAssignmentId, amtHitId: amtHitId,
        browser: userInfo["browserName"], platform: userInfo["userPlatform"]
    }
    $(document).ready(function () {
        var fetchProject = $.post( "../psiz-collect/php/initialize.php", dataToPost, function(result) {
            var projectConfig = JSON.parse(result);
            stimulusList = projectConfig["stimulusList"];
            protocolId = projectConfig["protocolId"];

            // Set any custom content.
            var htmlConsent = projectConfig["consent"];
            if (htmlConsent != null) {
                $( ".consent__content" ).html(htmlConsent);
            }
            var htmlInstructions = projectConfig["instructions"];
            if (htmlInstructions != null) {
                $( ".instructions__content" ).html(htmlInstructions);
            }
            var htmlSurvey = projectConfig["survey"];
            if (htmlSurvey != null) {
                $( ".survey__content" ).html(htmlSurvey);
            }

            var assignmentId = "";
            var docket = {};
            var trialIdx = 0;
            if (newAssignment) {
                assignmentId = projectConfig["assignmentId"];
                docket = projectConfig["docket"];
                trialIdx = 0
            } else {
                assignmentId = controllerStateOld.assignmentId;
                docket = controllerStateOld.docket;
                trialIdx = controllerStateOld.trialIdx;
            }
            controllerState = {
                assignmentId: assignmentId,
                projectId: projectId,
                protocolId: protocolId,
                docket: docket,
                trialIdx: trialIdx,
                isSurvey: (htmlSurvey != null)
            };
            // TODO save controller state to session variable.
        });
        $.when(fetchProject).done(function() {
            // Launch application.
            appController = new AppController(stimulusList, controllerState);
        });
    });
    </script>
</body>

</html>