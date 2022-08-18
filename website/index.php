<!DOCTYPE html>
<html lang="en">

<head>
	<title>Collect - PsiZ</title>
	<meta charset="utf-8">
	<meta name="keywords" content="HTML, CSS, XML, XHTML, JavaScript">
	<meta name="description" content="PsiZ Collect">
    <meta name="author" content="B. D. Roads">
    <meta name="viewport" content="width=device-width, initial-scale=1">


    <!-- jQuery library -->
    <script src="https://code.jquery.com/jquery-3.3.1.js" integrity="sha256-2Kok7MbOyxpgUVvAk/HJ2jigOSYS2auK4Pfzbm7uH60=" crossorigin="anonymous"></script>
    <!-- Bootstap - Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">

    <!-- Note: psiz-collection assets must be loaded by going up a directory
    since re-write rule places the active experiment in a subdirectory. -->
    <link rel='stylesheet' href='/static/css/general-001.css'>
</head>

<body>
    <noscript>
        <h1>Warning: Javascript seems to be disabled</h1>
        <p>This website requires that Javascript be enabled on your browser.</p>
        <p>Instructions for enabling Javascript in your browser can be found <a href="http://support.google.com/bin/answer.py?hl=en&answer=23852">here</a></p>
    </noscript>
    
    <div class="container login">
        <div class="row">
            <div class="col"></div>
            <div class="col-6">
                <h1 class="login__heading">Login</h1>
                <input id="login__input" type="text" size="40" placeholder="Enter your participant code." onblur="this.focus()" autocomplete="off" autofocus="true" spellcheck="false"/>
            </div>
            <div class="col"></div>
        </div>
        <div class="row">
            <div class="col"></div>
            <div class="col-xs-3 col-md-2">
                <div id='login__button' class='custom-button custom-button--enabled'>OK</div>
            </div>
            <div class="col"></div>
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

    <script src="/static/js/AppController.js" charset="UTF-8"></script>
    <script src="/static/js/utils.js" charset="UTF-8"></script>
    
    <script type="text/javascript" charset="UTF-8">
    </script>
    
    <script type="text/javascript" charset="UTF-8">
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
        // If there is no workerId show login, otherwise proceed.
        if (appState['workerId'] == "") {
            $(".login").show(0);
        } else {
            launchController();
        }
    });

    $("#login__button").click( function() {
        $(".login").hide(0);
        var workerId = $("#login__input").val();
        if (workerId == "") {
            workerId = "guest";
        }
        appState['workerId'] = workerId;
        launchController();
    });

    $("#login__input").on('keypress',function(e) {
        if (!e) var e = window.event;

        if(e.which == 13 || e.keyCode === 13) {
            $(".login").hide(0);
            var workerId = $("#login__input").val();
            if (workerId == "") {
                workerId = "guest";
            }
            appState['workerId'] = workerId;
            launchController();
        }
    });

    function launchController() {
        var dataToPost = {
            appState: JSON.stringify(appState)
        }
        var fetchProject = $.post("/php/initialize.php", dataToPost, function(result) {
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