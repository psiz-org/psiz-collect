// Returns a random integer between min (included) and max (excluded)
// Using Math.round() will give you a non-uniform distribution!
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}

function range0toNminus1(N) {
    var foo = [];
    for (var i = 0; i <= N-1; i++) {
        foo.push(i);
    }
    return foo
}

function getRandomSubarray(arr, size) {
    var shuffled = arr.slice(0), i = arr.length, temp, index;
    while (i--) {
        index = Math.floor((i + 1) * Math.random());
        temp = shuffled[index];
        shuffled[index] = shuffled[i];
        shuffled[i] = temp;
    }
    return shuffled.slice(0, size);
}

// Create Array or Matrix of zeros
function zeros(nRows, nColumns) {
    var newRowArray = [];
    if (arguments.length == 1) {
        // Create 1D array of zeros
        for (var iRow = 0; iRow < nRows; iRow++) {
            newRowArray[iRow] = 0;
        }
    } else if (arguments.length == 2) {
        // Create 2D array of zeros
        for (var iRow = 0; iRow < nRows; iRow++) {
            var newColArray = [];
            for (var iCol = 0; iCol < nColumns; iCol++) {
                newColArray[iCol] = 0;
            }
            newRowArray[iRow] = newColArray;
        }
    }
    return newRowArray;
}

// Create array or matrix of ones
function ones(nRows, nColumns) {
    var newRowArray = [];
    if (arguments.length == 1) {
        // Create 1D array of zeros
        for (var iRow = 0; iRow < nRows; iRow++) {
            newRowArray[iRow] = 1;
        }
    } else if (arguments.length == 2) {
        // Create 2D array of zeros
        for (var iRow = 0; iRow < nRows; iRow++) {
            var newColArray = [];
            for (var iCol = 0; iCol < nColumns; iCol++) {
                newColArray[iCol] = 1;
            }
            newRowArray[iRow] = newColArray;
        }
    }
    return newRowArray;
}

function drawFromMultinomial(weights) {
    // Returns index [0, n-1] (i.e., Javascript array index formatting)
    // Normalize weights
    var nCat =  weights.length;
    var normFactor = sumArray(weights);
    var normWeights = [];
    var totalCdf = 0;
    var randDraw = Math.random(); // between 0 and 1
    var drawnCat;
    // see which bin the random number falls in
    for (var i = 0; i < nCat; i++) {
        normWeights[i] = weights[i] / normFactor;
        totalCdf = totalCdf + normWeights[i];
        if (randDraw <= totalCdf) {
            // This is your bin, and thus your drawn category
            drawnCat = i;
            break;
        }
    }
    if (isNaN(drawnCat)) {
        debug('NaN value for drawnCat in function drawFromMultinomial')
    }
    return drawnCat;
}

function Multiply_Array(someArray, scalar) {
    var newArray = [];
    for (var i = 0; i < someArray.length; i++) {
        newArray[i] = someArray[i] * scalar;
    }
    return newArray;
}

// see http://www.javascripter.net/faq/browsern.htm
function userSystemInfo() {

    var nVer = navigator.appVersion;
    var nAgt = navigator.userAgent;
    var browserName  = navigator.appName;
    var fullVersion  = ''+parseFloat(navigator.appVersion);
    var majorVersion = parseInt(navigator.appVersion,10);
    var nameOffset,verOffset,ix;

    // In Opera 15+, the true version is after "OPR/"
    if ((verOffset=nAgt.indexOf("OPR/"))!=-1) {
     browserName = "Opera";
     fullVersion = nAgt.substring(verOffset+4);
    }
    // In older Opera, the true version is after "Opera" or after "Version"
    else if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
     browserName = "Opera";
     fullVersion = nAgt.substring(verOffset+6);
     if ((verOffset=nAgt.indexOf("Version"))!=-1)
       fullVersion = nAgt.substring(verOffset+8);
    }
    // In MSIE, the true version is after "MSIE" in userAgent
    else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
     browserName = "Microsoft Internet Explorer";
     fullVersion = nAgt.substring(verOffset+5);
    }
    // In Chrome, the true version is after "Chrome"
    else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
     browserName = "Chrome";
     fullVersion = nAgt.substring(verOffset+7);
    }
    // In Safari, the true version is after "Safari" or after "Version"
    else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
     browserName = "Safari";
     fullVersion = nAgt.substring(verOffset+7);
     if ((verOffset=nAgt.indexOf("Version"))!=-1)
       fullVersion = nAgt.substring(verOffset+8);
    }
    // In Firefox, the true version is after "Firefox"
    else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
     browserName = "Firefox";
     fullVersion = nAgt.substring(verOffset+8);
    }
    // In most other browsers, "name/version" is at the end of userAgent
    else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) <
              (verOffset=nAgt.lastIndexOf('/')) )
    {
     browserName = nAgt.substring(nameOffset,verOffset);
     fullVersion = nAgt.substring(verOffset+1);
     if (browserName.toLowerCase()==browserName.toUpperCase()) {
      browserName = navigator.appName;
     }
    }
    // trim the fullVersion string at semicolon/space if present
    if ((ix=fullVersion.indexOf(";"))!=-1)
       fullVersion=fullVersion.substring(0,ix);
    if ((ix=fullVersion.indexOf(" "))!=-1)
       fullVersion=fullVersion.substring(0,ix);

    majorVersion = parseInt(''+fullVersion,10);
    if (isNaN(majorVersion)) {
     fullVersion  = ''+parseFloat(navigator.appVersion);
     majorVersion = parseInt(navigator.appVersion,10);
    }

    userPlatform = navigator.platform;
    browserLanguage = navigator.language;

    return {browserName: browserName, userPlatform: userPlatform, browserLanguage: browserLanguage};
}

function Console_Debug(debugOn, msg) {
    if (debugOn == true) {
        console.log(msg);
    }
}

function basename(path) {
   return path.split(/[\\/]/).pop();
}

// Local and Session Storage helpers for objects
Storage.prototype.setObject = function(key, value) {
    this.setItem(key, JSON.stringify(value));
}

Storage.prototype.getObject = function(key) {
    var value = this.getItem(key);
    return value && JSON.parse(value);
}

function preload(arrayOfImages) {
    $(arrayOfImages).each(function(){
        $('<img/>')[0].src = this;
        // Alternatively you could use:
        // (new Image()).src = this;
    });
}

function onlyUnique(value, index, self) { 
    return self.indexOf(value) === index;
}