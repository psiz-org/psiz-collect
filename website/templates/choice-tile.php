<?php
    $choiceTileId = "choice-tile-" . $choiceTileX;
    echo '<div id="', htmlspecialchars($choiceTileId, ENT_QUOTES, 'UTF-8'), '" class="tile tile--choice tile--choice-unselected" data-choice-tile="', htmlspecialchars($choiceTileX, ENT_QUOTES, 'UTF-8'), '">', PHP_EOL;
?>
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
    <div class="tile__banner unselectable"></div>
</div>
