# ![Alt](static/icon/favicon-32x32.png "PsiZ Logo") PsiZ Collect

PsiZ Collect is intended to be a template for creating a web-based application for collecting human similarity judgments. It has been designed to minimize deployment effort. Since it is a web-based application, some assembly is required. Once data is collected, it can be analyzed using the *psiz* python package which can be cloned from [GitHub](https://github.com/roads/psiz).

## Installation
<!-- TODO -->
 * Move webfiles to desired location.
 * Set DIR_COLLECT

## How it works
1. Set up backbone code.
2. Craete a new collection project.
3. Collect data.

A trial is only shown once all of the assets have been loaded in the browser. This behavior enforces the constaint that participants are presented with all trial content simultaneously. To reduce time spent waiting for stimuli to load, the application starts loading all stimuli, in the order of their occurrence, after the first page has loaded.

## Directory structure
```
DIR_COLLECT
+-- \php
+-- \static
+-- \templates
+-- collect.php
```

Instead of assuming that DIR_COLLECT will also be the root of the website, the PHP code uses the environment variable DIR_COLLECT. This environment variable can be set by editing your vhost file under `/etc/apache2/sites-available/`. Don't forget to call `sudo service apache2 restart` when you are done modifying the vhost.
```
ServerAdmin admin@host
DocumentRoot /var/www/my_website
ServerName local.server
ServerAlias local.alias.server
SetEnv DIR_COLLECT /var/www/my_website/path_to_collect
```
If the PsiZ Collect website resides at the root of the website, then DIR_COLLECT will have the same path as DOCUMENT_ROOT. If you do not have control of the vhost file, you can set the variable in a `.htaccess` file. However, this approach requires that `SetEnv` be allowed in `.htaccess` files, which is specified using the `AllowOverride` directive. If neither of these is an option, you can change the relevant lines of PHP code contained in fetch-experiment.php:
```
// Change this line...
$dirCollect = getenv('DIR_COLLECT');
// to ..
$dirCollect = joinPaths($_SERVER['DOCUMENT_ROOT'], $theRestOfYourPath);
```

## User responsibilites
The User must supply the following items:
1. A set of stimuli.
2. A complete list of stimuli filepaths. `stimuli.txt`
3. One or more protocols.
4. deployment configuration file.
5. MySQL credentials
6. (optional) AMT configuration file (only necessary if using AMT)
7. (optional) AWS credentials (only necessary if using AMT)

### 1. Stimuli
The stimuli are the media that you will ask participants to judge. Images, audio and video can be used. Supported image formats include 'png' and 'jpg'. Supported video formats include all HTML5 standards: 'mp4', 'ogg', and 'webm'.
<!-- TODO -->
assumes ogv for video vs ogg for audio. (as per the current recommendation by the developer)

### 2. Stimuli filepaths `stimuli.txt`
A file containing the complete filepaths to all stimuli (one stimulus per line). The application will assume (a) that each line points to a unique stimulus, (b) no other stimuli should be used, (c) all stimulus filepaths end with a file extension. Acceptable extensions are jpg and png.

If you are looking for a quick way to create this file, one option is to use the GNU or BSD `find` command. For example, the following command finds all files with .jpg and .png file extensions.

```
find path/to/dataset -type f -iname "*.jpg" -o -iname "*.png" > stimuli.txt
```

### 3. Protocol
A JSON file specifying an experiment protocol. There are two types of protocols: *stochastic* and *deterministic*. A stochastic protocol requires the following fields:
* "generator": "stochastic",
* "pages": array,
* "docket": object

* "n_trial": int,
* "n_catch": int,
* "n_reference": int,
* "n_select": int,
* "is_ranked": bool

    shuffle: shuffle order of trials
        shuffle (should this always occur? no, because of spacing for catch trials
* Stimuli are reference by their index of occurence in `stimuli.txt`. The index is assumed to start at 0 and go to N-1 where N indicates the total number of stimuli listed in `stimuli.txt`.
* protocol names MUST follow the format `protocol*.json` in order to be detected. The `*` character indicates the typical wildcard format.
* protocols no longer in use, can be removed from the EXPERIMENT_DIR. Doing so may
    improve page loading speed for subjects if there are hundreds of protocols.
* Within an experiment, each protocol should have a unique name, do not re-use
    names even if the directory no longer contains that protocol since protocols
    are assigned by looking up usage history in a database.
* protocols may reference other pages to display before (?)
* no default protocol since money may be on the line
* Each trial can have a different configuration (number of references, number of choices, ranked) by using a deterministic protocol.
* Protocols will need to be created by the user but can be checked for validity using the provided python script `check_protocol.py`.

### 4. Website configuration file
	htdocsUrl

### 5. AMT configuration file (optional)
	????