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

// TODO erase session variable when assignment is completed
// TODO make sure new assignment isn't created on page reload
// TODO add optional comments input at end of experiment (need to add table to database as well)
// TODO variable and function names as camel case
// TODO session storage
// sessionStorage.setObject(controllerState.projectId, controllerState);

class Stopwatch {

    constructor() {
      this.totalMs = 0;
      this.startMs = 0;
    }
  
    start() {
        this.startMs = new Date().getTime();
    }
    
    stop() {
        var stopMs = new Date().getTime();
        this.totalMs = this.totalMs + (stopMs - this.startMs);
        // alert("Total: " + this.totalMs);
    }

    total() {
        return this.totalMs;
    }

    reset() {
        this.totalMs = 0;
        this.startMs = 0;
    }
  
}
  
var AppController = function(stimulusList, controllerState) {

    // Constants.
    var CHOICE_TILES = ['choice-tile-A', 'choice-tile-B', 'choice-tile-C', 'choice-tile-D', 'choice-tile-E', 'choice-tile-F', 'choice-tile-G', 'choice-tile-H'];
    var N_CHOICE_TILE = CHOICE_TILES.length;
    var RANKING_TEXT = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'];

    // Variables.
    var controllerState = controllerState;
    var selectionState;
    var loaderArray;
    var startTimeMs;
    var totalTimeMs;
    let stopwatch = new Stopwatch();

    // Start preloading images.
    loaderArray = preloadStimuli(controllerState.docket)

    // Startup settings.
    $('.total-number-screens').text(controllerState.docket.length);
    $('.grid__row-placeholder').show()
    $('#query-tile').show()
    $('#choice-tile-A').show()
    $('#choice-tile-B').show()

    // Check specifications.
    //  check nReference <= nTile
    //  check nStimuli > nTile
    //  check nSelect < nChoice
    //  check current trialIdx is not larger than docket
    
    // $('.survey').show();

    // Obtain consent.
    // $('.consent').show(); TODO

    // Show instructions. TODO
    $('.instructions').show();

    // Show survey. TODO

    function preloadStimuli(docket) {
        // Create list of all image IDs in order of appearance
        var idxList = [];
        for (var iTrial = 0; iTrial < controllerState.docket.length; iTrial++) {
            idxList = idxList.concat(
                [controllerState.docket[iTrial].query]
            );
            idxList = idxList.concat(
                controllerState.docket[iTrial].references
            );
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
        } else if ($.inArray(extension, ['jpg', 'png']) >= 0) {
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
        audio.oncanplay = function() {  // TODO
            deferred.resolve();
        };
        audio.setAttribute("src", fname);
        // audio.setAttribute("type", "audio/" + extension);
        return deferred.promise();
    }

    function next(controllerState) {
        if (controllerState.trialIdx >= controllerState.docket.length) {
            // Experimet done: update status. TODO
            // postAssignmentUpdate();
            // Show debriefing
            // $('.overlay_content_debriefing').show('fast');
            // TODO clear session variables
        } else {
            startTrial(controllerState);
        }
    }

    function startTrial(controllerState) {
        var trial = controllerState.docket[controllerState.trialIdx];
        var loaders = getTrialLoaders(trial, loaderArray);

        uiResetTrial(trial);

        // Update progress indicator.
        $('#grid__progress-counter').text(controllerState.trialIdx);
        // Set instructions.
        if (trial.nSelect == 1) {
            $(".text-n-select").text("")
            $(".text-tile-grammar").text("tile")
            // $(".grid__prompt-text").text("Select a tile")
        } else {
            $(".text-n-select").text(trial.nSelect)
            $(".text-tile-grammar").text("tiles")
            // $(".grid__prompt-text").text("Select " + trial.nSelect + " tiles")
            if (trial.isRanked) {
                $(".is-ranked").show();
            }
        }
        
        $.when.apply(null, loaders).done(function() {
        // Callback when everything has finished loading.
            uiSetStimuli(trial);
            uiShowTiles(trial);
            startTimeMs = new Date().getTime();
            stopwatch.reset();
            stopwatch.start();
        });
    }

    function uiResetTrial(trial) {
        // Reset grid.
        // $("#grid__sound-button").hide(0);
        // Reset tiles.
        $(".tile").hide(0);
        // Reset stimuli.
        $(".tile__text").hide(0);
        $(".tile__text").html("");
        $(".tile__img").hide(0);
        $(".tile__video").hide(0);
        $(".tile__video-source").attr('src', "");
        $(".tile__audio").hide(0);
        $(".tile__audio-source").attr('src', "");
        $(".tile__progress-bar").hide(0);
        $(".tile__progress-value").width("0%");
    
        // Reset selection.
        selectionState = uiResetSelection(trial);
    }

    function uiResetSelection(trial) {
        $('.tile--choice').removeClass('tile--choice-selected');
        $('.tile--choice').addClass('tile--choice-unselected')
        $('.tile__banner').hide();

        $('#grid__submit-button').removeClass('custom-button--enabled');
        $('#grid__submit-button').addClass('custom-button--disabled');
        $('#grid__submit-button').addClass('unselectable')
        
        // TODO is hard-coded N_CHOICE_TILE an issue?
        var selectionState = {
            nChoice: trial.references.length,
            nSelect: trial.nSelect,
            isRanked: trial.isRanked,
            nSelected: 0,
            isTileSelected: zeros(N_CHOICE_TILE)
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
        uiSetTile("#query-tile", stimulusList[trial.query]);

        // Update choice tiles.
        var nChoice = trial.references.length;
        for (var iChoiceTileIdx = 0; iChoiceTileIdx < nChoice; iChoiceTileIdx++) {
            uiSetTile(
                "#" + CHOICE_TILES[iChoiceTileIdx],
                stimulusList[trial.references[iChoiceTileIdx]]
            );
        }
    }

    function uiSetTile(tileId, fname) {
        var media = mediaType(fname);
        switch (media) {
            case "text":
                uiSetText(tileId, fname);
                break;
            case "image":
                uiSetImage(tileId, fname);
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

    function uiSetImage(tileId, fname) {
        var img = $(tileId).find(".tile__img");
        $(img).attr('src', fname);
        $(img).attr('alt', fname);
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

    function uiTileSelect(tileId, selectionState) {
        var tileIdx = CHOICE_TILES.indexOf(tileId);
        selectionState.nSelected = selectionState.nSelected + 1;
        var order = selectionState.nSelected;
        selectionState.isTileSelected[tileIdx] = order;

        $('#' + tileId).removeClass('tile--choice-unselected');
        $('#' + tileId).addClass('tile--choice-selected');

        var $tileBanner = $("#" + tileId).find(".tile__banner");
        if (selectionState.isRanked) {
            $tileBanner.text(RANKING_TEXT[order-1] + ' Most Similar');
        } else {
            $tileBanner.text('Similar');
        }
        $tileBanner.show();

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

    function uiTileUnselect(tileId, selectionState) {
        var doReEnableChoices = false;
        if (selectionState.nSelected >= selectionState.nSelect) {
            doReEnableChoices = true;
        }

        var tileIdx = CHOICE_TILES.indexOf(tileId);
        var oldSelectionOrder = selectionState.isTileSelected[tileIdx];

        selectionState.isTileSelected[tileIdx] = 0;
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
        if (selectionState.isTileSelected[tileIdx] === 0) {
            if (selectionState.nSelected < selectionState.nSelect) {
                selectionState = uiTileSelect(tileId, selectionState);
            }
        } else {
            selectionState = uiTileUnselect(tileId, selectionState);
        }
        return selectionState;
    }

    function gradeCatchTrial(trial, selectionState) {
        var nReference = trial.choices.filename.length;
        var isCatchTrialCorrect = 0;
        var queryFilename = basename(trial.query.filename);
        for (var iReference=0; iReference < nReference; iReference++){
            if (selectionState.isTileSelected[iReference] != 0) {
                if (basename(trial.choices.filename[iReference]) === queryFilename) {
                    isCatchTrialCorrect = 1;
                }
            }
        }
        return isCatchTrialCorrect;
    }

    function inferFilenameReferences(trial, selectionState) {
        var nReference = trial.choices.filename.length;
        var nSelected = 0;

        // Assemble array of ranked image ids and unselected image ids
        var rankedImageFilename = [];
        var unselectedImageFilename = [];
        for (var iReference=0; iReference < nReference; iReference++){
            if (selectionState.isTileSelected[iReference] != 0) {
                var rankedIdx = selectionState.isTileSelected[iReference] - 1; //minus one to account for zero indexing
                rankedImageFilename[rankedIdx] =  basename( trial.choices.filename[iReference] );
                nSelected = nSelected + 1;
            } else {
                unselectedImageFilename.push( basename( trial.choices.filename[iReference] ));
            }
        }

        var referenceList = []
        // Add selected references
        for (var iSelection = 0; iSelection < nSelected; iSelection++) {
            var currentReference = {
                imageFilename: rankedImageFilename[iSelection],
                rankOrder: iSelection + 1, // plus 1 for 1 indexing
            }
            referenceList.push(currentReference);
        }
        // Add unselected references
        for (var iSelection = 0; iSelection < (nReference - nSelected); iSelection++) {
            var currentReference = {
                imageFilename: unselectedImageFilename[iSelection],
                rankOrder: iSelection + 1 + nSelected, // plus 1 for 1 indexing
            }
            referenceList.push(currentReference);
        }
        return {referenceList: referenceList, nReference: nReference, nSelected: nSelected};
    }

    function postObs(){
        var dataToPost = {
            projectId: controllerState.projectId,
            assignmentId: cfg.dbAssignmentId,
            obs: controllerState.docket
        };

        var postData = $.post( "../psiz-collect/php/postObs.php", controllerState.docket, function(result) {
        });
    }

    function postTrial(queryFilename, nReference, nSelected, isCatchTrial, isCatchTrialCorrect, referenceJson) {
        if (cfg.doRecord) {
            var dataToPost = {
                website: cfg.website,
                assignmentId: cfg.dbAssignmentId,
                nReference: nReference,
                nSelected: nSelected,
                isRanked: cfg.isRankedSelection,
                queryFilename: queryFilename,
                startTimeMs: String(startTimeMs),
                totalTimeMs: String(totalTimeMs),
                isCatchTrial: isCatchTrial,
                isCatchTrialCorrect: isCatchTrialCorrect,
                referenceJson: referenceJson
            };

            $.post("php/post-display-selection.php", dataToPost, function( data ) {
                Console_Debug(cfg.debugOn, data);
            }).fail( function () {
                Console_Debug(cfg.debugOn, "Failed to create display and/or triplet entries in database.");
            });
        } // end if
    }

    function postAssignmentUpdate() {
        if (cfg.doRecord) {
            status = 'completed'
            var dataToPost = {
                website: cfg.website,
                assignmentId: cfg.dbAssignmentId,
                endHit: String(new Date().getTime()),
                status: status
            };

            $.post("php/update-assignment.php", dataToPost, function( data ) {
                Console_Debug(cfg.debugOn, data);
            }).fail( function () {
                Console_Debug(cfg.debugOn, "Failed to update assignment entry in database.");
            });
        } // end if
    }

    function postAssignmentWorkerUpdate(workerId) {
        if (cfg.doRecord) {
            var dataToPost = {
                website: cfg.website,
                assignmentId: cfg.dbAssignmentId,
                workerId: workerId,
            };

            $.post("php/update-assignment-worker-id.php", dataToPost, function( data ) {
                Console_Debug(cfg.debugOn, data);
            }).fail( function () {
                Console_Debug(cfg.debugOn, "Failed to update assignment entry in database.");
            });
        } // end if
    }

    $("#consent-button").click( function() {
        $(".consent").hide();
        $(".instructions").show();
    })

    $("#instructions-button").click( function () {
        $(".instructions").hide();
        $(".tile__video").prop('muted', false);
        $(".tile__audio").prop('muted', false);
        $(".grid").show();
        // Start next trial.
        next(controllerState);        
    })

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
            totalTimeMs = stopwatch.total();

            // Re-arrange trial docket into observation format.
            var trial = controllerState.docket[controllerState.trialIdx];
            // console.log("references: " + trial.references)
            // console.log("selectionState: " + selectionState.isTileSelected)
            var obsIdx = []
            for (var iSelection = 1; iSelection <= trial.nSelect; iSelection++) {
                var idx = selectionState.isTileSelected.indexOf(iSelection)
                obsIdx.push(trial.references[idx])
            }
            for (var iReference = 0; iReference < trial.references.length; iReference++) {
                if (selectionState.isTileSelected[iReference] == 0) {
                    obsIdx.push(trial.references[iReference])
                }
            }
            trial.references = obsIdx
            // console.log("references: " + controllerState.docket[controllerState.trialIdx].references)
            trial.rt_ms = totalTimeMs
            // trial.isCatchTrialCorrect = gradeCatchTrial(trial) TODO

            controllerState.trialIdx += 1;
            // Now that trial is finished, update sessionStorage to save progress.
            // sessionStorage.setObject(controllerState.projectId, controllerState); TODO
            next(controllerState);
        }
    });

    // $("#login-button").click( function() {
    //     $(".overlay_content_login").hide(0);
    //     $('.overlay_content_intro').show(0);
    //     // Update assignment database with login name
    //     loginName = $("#overlay__login-input").val();
    //     postAssignmentWorkerUpdate(loginName);
    // });

    // $("#overlay__login-input").on('keyup', function(e) {
    //     if (!e) var e = window.event;

    //     if (e.which == 13 || e.keyCode === 13) {
    //         $(".overlay_content_login").hide(0);
    //         $('.overlay_content_intro').show(0);
    //         // Update assignment database with login name
    //         loginName = $("#overlay__login-input").val();
    //         postAssignmentWorkerUpdate(loginName);
    //     }

    // 	e.cancelBubble = true;
    // 	if (e.stopPropagation) e.stopPropagation();
    // });

    // $('#debrief-button').click( function() {
    //     if (cfg.mode === 'turkExp') {
    //         if (window.opener) {
    //             // Parent window still open
    //             window.opener.Submit_Hit( cfg.submitUrl );
    //             window.close();
    //         } else {
    //             // Parent window is not opens
    //             document.getElementById("mturk_form").submit();
    //         }
    //     } else {
    //         $('.overlay_content_debriefing').hide(0);
    //         $(".overlay_content_done").show(0);
    //     }
    // });

}
