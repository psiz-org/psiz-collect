/* AppController.js
*
* Author: BD Roads
*
* Controller for similarity judgment application.
*
* The application controller is responsible for:
* 1) All user-interaction functionality.
* 2) Creating and clearing session variables (but not loading).
* 3) Recovering and logging imcompatible specifications such as 
*    non-existent stimuli or improper dockets.
*/

// TODO add optional comments input at end of experiment (need to add table to database as well)

class Stopwatch {

    constructor() {
      this.totalMs = 0;
      this.startMs = 0;
      this.running = false;
    }
  
    start() {
        this.startMs = new Date().getTime();
        this.running = true;
    }
    
    stop() {
        var stopMs = new Date().getTime();
        this.totalMs = this.totalMs + (stopMs - this.startMs);
        this.running = false;
        // alert("Total: " + this.totalMs);
    }

    read() {
        var elapsedMs = 0;
        if (this.running) {
            var nowMs = new Date().getTime();
            elapsedMs = this.totalMs + (nowMs - this.startMs);
        } else {
            elapsedMs = this.totalMs;
        }
        return elapsedMs
    }

    reset() {
        this.totalMs = 0;
        this.startMs = 0;
        this.running = false;
    }
  
}

var AppController = function(stimulusList, appState) {

    // Constants.
    var CHOICE_TILES = ['choice-tile-A', 'choice-tile-B', 'choice-tile-C', 'choice-tile-D', 'choice-tile-E', 'choice-tile-F', 'choice-tile-G', 'choice-tile-H'];
    var N_CHOICE_TILE = CHOICE_TILES.length;
    var RANKING_TEXT = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'];

    // Variables.
    var appState = appState;
    var selectionState;
    var loaderArray;
    var startTimestamp = "";
    let stopwatch = new Stopwatch();

    // Start preloading images.
    loaderArray = preloadStimuli(appState.docket)

    // Startup settings.
    $('.docket-progress__total').text(appState.docket.length);
    uiUpdateDocketProgress();
    $('.grid__row-placeholder').show();
    $('#query-tile').show();
    $('#choice-tile-A').show();
    $('#choice-tile-B').show();
    uiResetGrid();

    // Start next part of docket.
    next(appState);

    function preloadStimuli(docket) {
        // Create list of all image IDs in order of appearance
        var idxList = [];
        for (var iPart = 0; iPart < appState.docket.length; iPart++) {
            if (appState.docket[iPart].content == "trial") {
                idxList = idxList.concat(
                    [appState.docket[iPart].query]
                );
                idxList = idxList.concat(
                    appState.docket[iPart].references
                );
            }
        }

        // Filter down to unique IDs while preserving order.
        var idxList = idxList.filter(onlyUnique);

        // Create loaders.
        var loaderArray = []
        for (j = 0; j < idxList.length; j++) {
            loaderArray[idxList[j]] = loadStimulus(
                stimulusList[idxList[j]]
            );
        }
        return loaderArray;
    }

    function mediaType(fname) {
        // Route based on filename extension.
        // See: https://stackoverflow.com/a/12900504/1249581
        var extension = fname.slice((fname.lastIndexOf(".") - 1 >>> 0) + 2);
        extension = extension.toLowerCase();

        var media = "";
        if (extension == "") {
            media = "text";
        } else if ($.inArray(extension, ['jpg', 'jpeg', 'png']) >= 0) {
            media = "image";
        } else if ($.inArray(extension, ['mp4', 'webm', 'ogv']) >= 0) {
            media = "video"
        } else if (($.inArray(extension, ['mp3', 'wav', 'ogg']) >= 0)) {
            media = "audio"
        }
        return media;
    }

    function loadStimulus(fname) {
        // Route based on filename extension.
        // See: https://stackoverflow.com/a/12900504/1249581
        var extension = fname.slice((fname.lastIndexOf(".") - 1 >>> 0) + 2);
        extension = extension.toLowerCase();

        var media = mediaType(fname);
        var loader;
        switch (media) {
            case "text":
                loader = null;
                break;
            case "image":
                loader = loadImage(fname);
                break;
            case "video":
                loader = loadVideo(fname, extension);
                break;
            case "audio":
                loader = loadAudio(fname, extension);
                break;
        }
        return loader;
    }

    function loadImage(fname) {
        // This function returns a deferred promise which can be used in a callback
        // see: http://stackoverflow.com/questions/8645143/wait-for-image-to-be-loaded-before-going-on
        var deferred = $.Deferred();
        var img = new Image();
        img.onload = function() {
            deferred.resolve();
        };
        img.src = fname;
        return deferred.promise();
    }

    function loadVideo(fname, extension) {
        // This function returns a deferred promise which can be used in a callback
        // see: http://stackoverflow.com/questions/8645143/wait-for-image-to-be-loaded-before-going-on
        var deferred = $.Deferred();
        var video = document.createElement("video");
        video.oncanplay = function() {
            deferred.resolve();
        };
        video.setAttribute("src", fname);
        // video.setAttribute("type", "video/" + extension);
        return deferred.promise();
    }

    function loadAudio(fname, extension) {
        // This function returns a deferred promise which can be used in a callback
        // see: http://stackoverflow.com/questions/8645143/wait-for-image-to-be-loaded-before-going-on
        var deferred = $.Deferred();
        var audio = document.createElement("AUDIO");
        audio.oncanplay = function() {
            deferred.resolve();
        };
        audio.setAttribute("src", fname);
        // audio.setAttribute("type", "audio/" + extension);
        return deferred.promise();
    }

    function next(appState) {
        if (appState.docketIdx >= appState.docket.length) {
            finishSession(appState);
        } else {
            // Session not finished, get next page.
            var page = appState.docket[appState.docketIdx];
            switch (page.content) {
                case "message":
                    $(".grid").hide(0);
                    $(".message__content").html(page.html)
                    $(".message").show(0);
                    break;
                case "trial":
                    $(".message").hide(0);
                    $(".grid").show(0);
                    startTrial(appState);
                    break;
            }            
        }
    }

    function startTrial(appState) {
        var trial = appState.docket[appState.docketIdx];
        var loaders = getTrialLoaders(trial, loaderArray);

        selectionState = uiResetSelection(trial);

        // Set instructions.
        if (trial.nSelect == 1) {
            $(".text-n-select").text("")
            $(".text-tile-grammar").text("tile")
        } else {
            $(".text-n-select").text(trial.nSelect)
            $(".text-tile-grammar").text("tiles")
            if (trial.isRanked) {
                $(".is-ranked").show();
            }
        }
        
        $.when.apply(null, loaders).done(function() {
        // Callback when everything has finished loading.
            uiSetStimuli(trial);
            uiShowTiles(trial);
            stopwatch.reset();
            stopwatch.start();
            startTimestamp = clientTimestamp();
        });
    }

    function finishSession(appState) {
        // Session finished.
        postSession(appState);
        
        // Get voucher code.
        if (appState.amtAssignmentId != "") {
            $(".voucher").show();
            if (appState.voucherCode == "") {
                var dataToPost = {
                    amtIsLive: appState.amtIsLive,
                    amtAssignmentId: appState.amtAssignmentId,
                    amtWorkerId: appState.workerId,
                    amtHitId: appState.amtHitId,
                };
                // Create new voucher entry in database.
                $.post("../php/post-voucher.php", dataToPost, function(voucherStatus) {
                    console.log("voucher status: " + voucherStatus);
                    if (voucherStatus != "0") {
                        appState.voucherCode = voucherStatus;
                        sessionStorage.setObject(appState.projectId, appState);
                        $("#voucher__code").text(appState.voucherCode);
                    }
                }).fail( function (xhr, status, error) {
                    console.log("Post using post-voucher.php failed.");
                    console.log(status);
                    console.log(error);
                    console.log(xhr.responseText);
                }); // end post
            } else {
                $("#voucher__code").text(appState.voucherCode);
            }
        } else {
            $(".voucher__alt").show();
        }

        // Show final page.
        $(".grid").hide(0);
        $(".message").hide(0);
        $('.final').show(0);
    }

    function uiResetGrid() {
        // Reset grid.
        // $(".grid").hide(0);
        // $("#grid__sound-button").hide(0);
        // Reset tiles.
        $(".tile").hide(0);
        // Reset stimuli.
        $(".tile__text").hide(0);
        $(".tile__text").html("");
        $(".tile__img").hide(0);
        $(".tile__img").removeClass('tile__img--flipped');
        $(".tile__video").hide(0);
        $(".tile__video-source").attr('src', "");
        $(".tile__audio").hide(0);
        $(".tile__audio-source").attr('src', "");
        $(".tile__progress-bar").hide(0);
        $(".tile__progress-value").width("0%");
        // Reset selections.
        $('.tile--choice').removeClass('tile--choice-selected');
        $('.tile--choice').addClass('tile--choice-unselected')
        $('.tile__banner').hide();
        // Reset submit button.
        $('#grid__submit-button').removeClass('custom-button--enabled');
        $('#grid__submit-button').addClass('custom-button--disabled');
        $('#grid__submit-button').addClass('unselectable');
    }

    function uiResetSelection(trial) {
        var selectionState = {
            nChoice: trial.references.length,
            nSelect: trial.nSelect,
            isRanked: trial.isRanked,
            nSelected: 0,
            isTileSelected: zeros(N_CHOICE_TILE),
            tileRtMs: zeros(N_CHOICE_TILE)
        }
        return selectionState;
    }

    function uiShowTiles(trial) {
        var nChoice = trial.references.length;

        $("#query-tile").show();

        for (var iChoice=0; iChoice < N_CHOICE_TILE; iChoice++) {
            if (iChoice < nChoice) {
                $('#' + CHOICE_TILES[iChoice]).show();
            } else {
                $('#' + CHOICE_TILES[iChoice]).hide();
            }
        }
        if (nChoice === 2) {
            $('.grid__row-placeholder').show()
        } else {
            $('.grid__row-placeholder').hide()
        }
    }

    function getTrialLoaders(trial, loaderArray) {
        var loaders = []
        loaders.push(loaderArray[trial.query])

        var nChoice = trial.references.length;
        for (var iChoiceTileIdx = 0; iChoiceTileIdx < nChoice; iChoiceTileIdx++) {
            loaders.push(loaderArray[trial.references[iChoiceTileIdx]]);
        }
        return loaders;
    }

    function uiSetStimuli(trial) {
        // Update query tile.
        uiSetTile("#query-tile", stimulusList[trial.query], trial.isCatch);

        // Update choice tiles.
        var nChoice = trial.references.length;
        for (var iChoiceTileIdx = 0; iChoiceTileIdx < nChoice; iChoiceTileIdx++) {
            uiSetTile(
                "#" + CHOICE_TILES[iChoiceTileIdx],
                stimulusList[trial.references[iChoiceTileIdx]],
                false
            );
        }
    }

    function uiSetTile(tileId, fname, isCatch) {
        var media = mediaType(fname);
        switch (media) {
            case "text":
                uiSetText(tileId, fname);
                break;
            case "image":
                uiSetImage(tileId, fname, isCatch);
                break;
            case "video":
                uiSetVideo(tileId, fname);
                break;
            case "audio":
                uiSetAudio(tileId, fname);
                break;
        }
    }

    function uiSetText(tileId, fname) {
        var txt = $(tileId).find(".tile__text");
        txt.html(fname)
        txt.show(0)
    }

    function uiSetImage(tileId, fname, isCatch) {
        var img = $(tileId).find(".tile__img");
        $(img).attr('src', fname);
        $(img).attr('alt', fname);
        if (isCatch) {
            $(img).addClass('tile__img--flipped');
        }
        $(img).show(0);
    }

    function uiSetVideo(tileId, fname) {
        var video = $(tileId).find(".tile__video");
        var vidSrc = $(tileId).find(".tile__video-source");
        var fileInfo = $(tileId).find(".tile__progress-bar");

        var extension = fname.slice((fname.lastIndexOf(".") - 1 >>> 0) + 2);
        extension = extension.toLowerCase();

        $(video)[0].pause();
        $(vidSrc).attr('src', fname);
        $(vidSrc).attr('type', "video/" + extension);
        $(video)[0].load();
        $(video).show(0);
        $(fileInfo).show(0);
    }

    function uiSetAudio(tileId, fname) {
        var audio = $(tileId).find(".tile__audio");
        var audioSrc = $(tileId).find(".tile__audio-source");
        var fileInfo = $(tileId).find(".tile__progress-bar");

        var extension = fname.slice((fname.lastIndexOf(".") - 1 >>> 0) + 2);
        extension = extension.toLowerCase();

        $(audio)[0].pause();
        $(audioSrc).attr('src', fname);
        $(audioSrc).attr('type', "audio/" + extension);
        $(audio)[0].load();
        $(audio).show(0);
        $(fileInfo).show(0);

        uiSetText(tileId, '<i class="fas fa-music"></i>')
    }

    function uiTileSelect(tileId, selectionState, elapsedMs) {
        var tileIdx = CHOICE_TILES.indexOf(tileId);
        selectionState.nSelected = selectionState.nSelected + 1;
        var order = selectionState.nSelected;
        selectionState.isTileSelected[tileIdx] = order;
        selectionState.tileRtMs[tileIdx] = elapsedMs;

        // Add selected styling.
        $('#' + tileId).removeClass('tile--choice-unselected');
        $('#' + tileId).addClass('tile--choice-selected');

        // Add selected text.
        var $tileBanner = $("#" + tileId).find(".tile__banner");
        if (selectionState.isRanked) {
            $tileBanner.text(RANKING_TEXT[order-1] + ' Most Similar');
        } else {
            $tileBanner.text('Similar');
        }
        $tileBanner.show();

        // Disable choice tiles if enough selected.
        var $choiceTile;
        if (selectionState.nSelected >= selectionState.nSelect) {
            for (var iChoiceTile = 0; iChoiceTile < selectionState.nChoice; iChoiceTile++) {
                $choiceTile = $("#" + CHOICE_TILES[iChoiceTile]);
                if ($choiceTile.hasClass("tile--choice-unselected")) {
                    $choiceTile.removeClass("tile--choice-unselected");
                    $choiceTile.addClass("tile--choice-disabled");
                }
            }
        }

        return selectionState;
    }

    function uiTileUnselect(tileId, selectionState, elapsedMs) {
        var doReEnableChoices = false;
        if (selectionState.nSelected >= selectionState.nSelect) {
            doReEnableChoices = true;
        }

        var tileIdx = CHOICE_TILES.indexOf(tileId);
        var oldSelectionOrder = selectionState.isTileSelected[tileIdx];

        selectionState.isTileSelected[tileIdx] = 0;
        selectionState.tileRtMs[tileIdx] = 0;
        selectionState.nSelected = selectionState.nSelected - 1;

        // Loop over all tiles to move any currently selected tiles up in ranking if they came after unselected tile
        for (var iTile = 0; iTile < selectionState.nChoice; iTile++) {
            if ((selectionState.isTileSelected[iTile] != 0) & (selectionState.isTileSelected[iTile] > oldSelectionOrder) ) {
                var order = selectionState.isTileSelected[iTile] - 1;
                var $tileBanner = $("#" + CHOICE_TILES[iTile]).find(".tile__banner");
                if (selectionState.isRanked) {
                    $tileBanner.text(RANKING_TEXT[order-1] + ' Most Similar');
                } else {
                    $tileBanner.text('Similar');
                }
                selectionState.isTileSelected[iTile] = order;
            }
        }

        $('#' + tileId).removeClass('tile--choice-selected');
        $('#' + tileId).addClass('tile--choice-unselected')
        var $tileBanner = $("#" + tileId).find(".tile__banner");
        $tileBanner.hide();

        if (doReEnableChoices) {
            var $choiceTile;
            for (var iChoiceTile = 0; iChoiceTile < selectionState.nChoice; iChoiceTile++) {
                $choiceTile = $("#" + CHOICE_TILES[iChoiceTile]);
                if ($choiceTile.hasClass("tile--choice-disabled")) {
                    $choiceTile.removeClass("tile--choice-disabled");
                    $choiceTile.addClass("tile--choice-unselected");
                }
            }
        }

        return selectionState;
    }

    function uiTileToggle(tileId, selectionState) {
        var tileIdx = CHOICE_TILES.indexOf(tileId);
        var elapsedMs = stopwatch.read();
        if (selectionState.isTileSelected[tileIdx] === 0) {
            if (selectionState.nSelected < selectionState.nSelect) {
                selectionState = uiTileSelect(tileId, selectionState, elapsedMs);
            }
        } else {
            selectionState = uiTileUnselect(tileId, selectionState, elapsedMs);
        }
        return selectionState;
    }

    function uiUpdateDocketProgress() {
        $('#docket-progress__counter').text(appState.docketIdx);
        var progressValue = (100 / appState.docket.length) * appState.docketIdx;
        $('.docket-progress__bar').width(progressValue + "%");
    }

    function postSession(appState){
        // Post obs, update status.
        if (appState.postStatus == ""){
            var dataToPost = {
                appState: JSON.stringify(appState)
            }
            var postData = $.post( "../php/postObs.php", dataToPost, function(result) {
                var returnedMsg = JSON.parse(result);
                console.log(returnedMsg);
                appState.postStatus = 1;
                sessionStorage.setObject(appState.projectId, appState);
            }).fail(function(err, status) {
                console.log(err);
                console.log(status);
            });
        }
    }

    function appendBehavior(trial, startTimestamp, submitTimeMs, selectionState) {
        // Reformat from docket format to observation format.
        var obsIdx = [];
        var choiceRtMs = [];
        for (var iSelection = 1; iSelection <= trial.nSelect; iSelection++) {
            var idx = selectionState.isTileSelected.indexOf(iSelection)
            obsIdx.push(trial.references[idx]);
            choiceRtMs.push(selectionState.tileRtMs[idx]);
        }
        for (var iReference = 0; iReference < trial.references.length; iReference++) {
            if (selectionState.isTileSelected[iReference] == 0) {
                obsIdx.push(trial.references[iReference]);
                choiceRtMs.push(selectionState.tileRtMs[iReference]);
            }
        }
        // Add placeholders for unused references.
        nReference = trial.references.length
        for (var iReference = nReference; iReference < N_CHOICE_TILE; iReference++) {
            trial.references.push(-1);
            obsIdx.push(-1);
            choiceRtMs.push(0);
        }

        trial.choices = obsIdx;
        trial.startTimestamp = startTimestamp;
        trial.choiceRtMs = choiceRtMs;
        trial.submitRtMs = submitTimeMs;
    }

    $("#grid__info-button").click( function() {
        stopwatch.stop();
        $('.overlay-instructions').show();
    });

    $("#overlay-instructions-button").click( function () {
        stopwatch.start();
        $('.overlay-instructions').hide();
    });

    $("#grid__sound-button").click( function() {
        if( $("video").prop('muted') ) {
            $("video").prop('muted', false);
            $("#grid__sound-button").html('<i class="fas fa-volume-up"></i>')
        } else {
            $("video").prop('muted', true);
            $("#grid__sound-button").html('<i class="fas fa-volume-mute"></i>')
      }
    });

    $(".tile").hover(
        function() {
            var tileId = this.id;
            var video = $("#" + tileId).find(".tile__video");
            var videoSrcVal = $(video).find('.tile__video-source').attr('src');
            var audio = $("#" + tileId).find(".tile__audio");
            var audioSrcVal = $(audio).find('.tile__audio-source').attr('src');
            if (videoSrcVal != "") {
                $(video)[0].play();            
            }
            if (audioSrcVal != "") {
                $(audio)[0].play();            
            }
        }, function(){
            var tileId = this.id;
            var video = $("#" + tileId).find(".tile__video");
            var videoSrcVal = $(video).find('.tile__video-source').attr('src');
            var audio = $("#" + tileId).find(".tile__audio");
            var audioSrcVal = $(audio).find('.tile__audio-source').attr('src');
            if (videoSrcVal != "") {
                $(video)[0].pause();
            }
            if (audioSrcVal != "") {
                $(audio)[0].pause();            
            }
    });

    // Update the seek bar as the video plays
    $('.tile__video').on('timeupdate', function() {
        var video = $(this);
        // Calculate the slider value
        var value = (100 / video[0].duration) * video[0].currentTime;
        // Update the slider value
        var progressBar = video.closest(".tile").find(".tile__progress-value");
        progressBar.width(value + "%");
    });

    $('.tile__audio').on('timeupdate', function() {
        var audio = $(this);
        // Calculate the slider value
        var value = (100 / audio[0].duration) * audio[0].currentTime;
        // Update the slider value
        var progressBar = audio.closest(".tile").find(".tile__progress-value");
        progressBar.width(value + "%");
    });

    $(".tile--choice").click( function () {
        selectionState = uiTileToggle(this.id, selectionState);

        /* Enable / Disable submit button */
        if (selectionState.nSelected >= selectionState.nSelect) {
            $('#grid__submit-button').removeClass('custom-button--disabled');
            $('#grid__submit-button').addClass('custom-button--enabled');
            $('#grid__submit-button').removeClass('unselectable');
        } else {
            $('#grid__submit-button').removeClass('custom-button--enabled');
            $('#grid__submit-button').addClass('custom-button--disabled');
            $('#grid__submit-button').addClass('unselectable')
        }
    });

    $("#grid__submit-button").click( function() {
        if ($("#grid__submit-button").hasClass("custom-button--enabled")) {
            stopwatch.stop()
            submitTimeMs = stopwatch.read();

            var trial = appState.docket[appState.docketIdx];
            appendBehavior(trial, startTimestamp, submitTimeMs, selectionState)
            // console.log("trial: " + appState.docket[appState.docketIdx])

            appState.docketIdx += 1;

            uiResetGrid();

            // Update progress indicator.
            uiUpdateDocketProgress();

            // Now that trial is finished, update sessionStorage to save progress.
            sessionStorage.setObject(appState.projectId, appState);
            next(appState);
        }
    });

    // Note that we're using on instead of click since message_button is 
    // added dynamically.
    $('.message__content').on('click', '.message__button', function() {
        if ($(".message__button").hasClass("custom-button--enabled")) {
            appState.docketIdx += 1;
            uiUpdateDocketProgress();

            // Now that page is finished, update sessionStorage to save progress.
            sessionStorage.setObject(appState.projectId, appState);
            next(appState);
        }
    });

    $("#voucher__box").click( function() {
        $("#voucher__code").focus();
        $("#voucher__code").select();
    });
}
