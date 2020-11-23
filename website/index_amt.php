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
    <link rel='stylesheet' href='/collect/static/css/general.css'>
</head>

<body>
    <noscript>
        <h1>Warning: Javascript seems to be disabled</h1>
        <p>This website requires that Javascript be enabled on your browser.</p>
        <p>Instructions for enabling Javascript in your browser can be found <a href="http://support.google.com/bin/answer.py?hl=en&answer=23852">here</a></p>
    </noscript>
    
    <div class="container amtlogin">
        <div class="row">
            <div class="col"></div>
            <div class="col-6">
                <h1 class="amtlogin__heading">AMT Login</h1>
                <h3>Worker ID: <span id='amtlogin__workerid'></span></h3>
                <h3>HIT ID: <span id='amtlogin__hitid'></span></h3>
                <h3>Assignment ID: <span id='amtlogin__assignmentid'></span></h3>
            </div>
            <div class="col"></div>
        </div>
        <div class="row">
            <div class="col"></div>
            <div class="col-xs-3 col-md-2">
                <div id='amtlogin__button' class='custom-button unselectable custom-button--disabled'>OK</div>
            </div>
            <div class="col"></div>
        </div>
        <div class="row">
            <p class="amtlogin_error">Oops, something went wrong! Your AMT information did not transfer correctly. Please close this tab and retry the experiment link on the AMT page. If the problem persists, please return the HIT and let the requester know.</p>
        </div>
    </div>

    <div class="container app">
        <div class='docket-progress'>
            Progress: <span id='docket-progress__counter'>-</span> / <span class='docket-progress__total'>-</span>
            <div class='docket-progress__groove'>
                <div class='docket-progress__bar'>
                </div>
            </div>
        </div>
        
        <div class="message">
            <div class="message__content"></div>
        </div>

        <?php require "templates/grid.php"; ?>

        <?php require "templates/final.php"; ?>
        <!-- TODO remove extra close div? -->
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

    <script src="/collect/static/js/AppController.js"></script>
    <script src="/collect/static/js/utils.js"></script>
    <script type="text/javascript">
    var queryVariables = <?php require "./php/querystring-parameters.php"; ?>;
    var client = clientInfo();

    var stimulusList = [];
    var appState = {};
    if (sessionStorage.getObject(queryVariables["projectId"])) {
        appState = sessionStorage.getObject(queryVariables["projectId"]);
    } else {
        appState = {
            projectId: queryVariables["projectId"],
            workerId: queryVariables['workerId'],
            amtAssignmentId: queryVariables["assignmentId"],
            amtHitId: queryVariables["hitId"],
            amtIsLive: queryVariables["isLive"],
            browser: client["browser"],
            platform: client["platform"],
            postStatus: "",
            voucherCode: ""
        };
    }
    
    $(document).ready(function () {
        $("#amtlogin__workerid").html(appState['workerId'])
        $("#amtlogin__hitid").html(appState['hitId'])
        $("#amtlogin__assignmentid").html(appState['assignmentId'])

        $(".amtlogin").show(0);

        // If information is missing, do not advance. TODO
        var can_proceed = true
        if (appState['workerId'] == "") {
            can_proceed = false
        }
        if (appState['hitId'] == "") {
            can_proceed = false
        }
        if (appState['assignmentId'] == "") {
            can_proceed = false
        }
        if (can_proceed) {
            // Enable button.
            $('.amtlogin__button').removeClass('custom-button--disabled');
            $('.amtlogin__button').addClass('custom-button--enabled');
            $('.amtlogin__button').removeClass('unselectable');
        } else {
            // Do not enable button. Show error message.
        }
    });

    $("#amtlogin__button").click( function() {
        $(".amtlogin").hide(0);
        launchController();
    });

    function launchController() {
        var dataToPost = {
            appState: JSON.stringify(appState)
        }
        var fetchProject = $.post("/collect/php/initialize.php", dataToPost, function(result) {
            var projectConfig = JSON.parse(result);
            stimulusList = projectConfig["stimulusList"];
            appState = projectConfig["appState"];
            // Save application state to session variable.
            sessionStorage.setObject(appState.projectId, appState);
        });
        $.when(fetchProject).done(function() {
            // Launch application.
            $(".app").show();
            appController = new AppController(stimulusList, appState);
        });
    }
    </script>    
</body>
</html>