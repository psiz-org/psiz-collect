<div class="container grid">
    <div class="row gutter-20">
        <div class="grid__row-placeholder"></div>
    </div>
    <div class="row gutter-20">
        <div class="col-xs-1 col-md-1"></div>
        <div class="col-xs-10 col-md-10">
            <div class="grid__prompt">
                <span class="grid__prompt-text">
                    Select the <span class="text-n-select"></span> most similar <span class="text-tile-grammar"></span>.
                </span>
            </div>
        </div>
        <div class="col-xs-1 col-md-1"></div>
    </div>

    <div class="row gutter-20">
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "E"; require "templates/choice-tile.php"; ?>
        </div>
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "C"; require "templates/choice-tile.php"; ?>
        </div>
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "F"; require "templates/choice-tile.php"; ?>
        </div>
    </div>

    <div class="row gutter-20">
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "A"; require "templates/choice-tile.php"; ?>
        </div>
        <div class="col-xs-4 col-md-4">
            <div id="query-tile" class="tile tile--query">
                <div class="tile__stimulus-placeholder">
                    <div class="tile__text"></div>
                    <img class="tile__img unselectable">
                    <video class="tile__video" loop muted>
                        <source class="tile__video-source">
                        Your browser does not support the video tag.
                    </video>
                    <audio class="tile__audio" loop muted>
                        <source class="tile__audio-source">
                        Your browser does not support the audio tag.
                    </audio>
                </div>
                <div class="tile__progress-bar">
                    <div class="tile__progress-value"></div>
                </div>
            </div>
        </div>
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "B"; require "templates/choice-tile.php"; ?>
        </div>
    </div>

    <div class="row gutter-20">
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "G"; require "templates/choice-tile.php"; ?>
        </div>
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "D"; require "templates/choice-tile.php"; ?>
        </div>
        <div class="col-xs-4 col-md-4">
            <?php $choiceTileX = "H"; require "templates/choice-tile.php"; ?>
        </div>
    </div>

    <div class="row gutter-20">
        <div class="col-xs-1 col-md-1">
            <div id="grid__info-button" class="custom-button custom-button--enabled">
                    <i class="fas fa-question"></i>
            </div>    
        </div>
        <!-- <div class="col-xs-1 col-md-1">
            <div id="grid__sound-button" class="custom-button custom-button--enabled audio-content">
                <i class="fas fa-volume-mute"></i>
            </div>
        </div> -->
        <div class="col-xs-3 col-md-3"></div>
        <div class="col-xs-4 col-md-4">
            <div id='grid__submit-button' class='custom-button custom-button--disabled unselectable'>
                Submit Selection
            </div>
        </div>
        <div class="col-xs-4 col-md-4">
            <div class='grid__screen-progress'>
                Completed: <span id='grid__progress-counter'>0</span> / <span class='total-number-screens'>50</span>
            </div>
        </div>
    </div>
</div>