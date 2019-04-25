# ![Alt](static/icon/favicon-32x32.png "PsiZ Logo") PsiZ Collect

PsiZ Collect is intended to be a template for creating a web-based application for collecting human similarity judgments. It has been designed to minimize deployment effort. Since it is a web-based application, some assembly is required. Once data is collected, it can be analyzed using the *psiz* python package which can be cloned from [GitHub](https://github.com/roads/psiz).

## How it works
1. Install application.
2. Craete a new collection project.
3. Start collecting your data.

## 1. Install application
<!-- This focuses on general setup TODO -->
* 1.1 Clone webfiles to desired location.
* 1.2 Set DIR_COLLECT.
* 1.3 Set up re-write rules. 
* 1.4 Set up MySQL database.
* 1.5 (optional) Set AWS and AMT credentials (only necessary if using AMT)

### 1.1 Clone webfiles to desired location.
<!-- TODO -->

### 1.2 Set DIR_COLLECT
```
DIR_COLLECT
+-- \php
+-- \projects
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
If the PsiZ Collect website resides at the root of the website, then DIR_COLLECT will have the same path as DOCUMENT_ROOT. If you do not have control of the vhost file, you can set the variable in a `.htaccess` file. However, this approach requires that `SetEnv` be allowed in `.htaccess` files, which is specified using the `AllowOverride` directive. If neither of these is an option, you can change the relevant lines of PHP code contained in postProject:
```
// Change this line...
$dirCollect = getenv('DIR_COLLECT');
// to ..
$dirCollect = joinPaths($_SERVER['DOCUMENT_ROOT'], $theRestOfYourPath);
```

### 1.3 Set up re-write rules.
<!-- TODO -->
Modify the .htaccess file at the root of the host website.
```
RewriteEngine on
RewriteRule ^collect/([A-Za-z0-9]+)/$ collect/psiz-collect/index.php?projectId=$1 [QSA]
```

### 1.4 Set up MySQL database.
<!-- TODO -->
Set MySQL credentials.
Set credentials path in php files.

Create the MySQL database on the host server. After logging into MySQL, execute:
``mysql> SOURCE db_install.sql;``

status_code
    0 - created, not completed, not expired
    1 - created, completed
    2 - created, not completed, expired

### 1.5 (optional) Set AWS and AMT credentials
<!-- TODO -->
<!-- store credentials at ~/.aws/credentials -->


<!-- TODO hello world -->
<!-- TODO test script Success!, Hello world!, much wow, wubba lubba dub dub, It's working!-->

## 2. Create a new collection project.
<!-- TODO describe creation of directory inside "projects", descfribe when should you create a new project, a unique project id, no spaces -->

For each project, you must supply the following items:
1. A set of stimuli.
2. One or more collection protocols.
3. (optional) custom instructions
4. (optional) consent form
5. (optional) survey

### 2.1 Stimuli
The stimuli are the media that you will ask participants to judge. Raw text, images, audio and video can be used.

Supported file formats:
 * images: 'png', 'jpg'
 * audio: 'mp3', 'wav', 'ogg'
 * video: 'mp4', 'webm', 'ogv' <!-- TODO verify ogv actually works-->

NOTE: It is assumed that .ogv indicates a video file while .ogg indicates an audio file (as per the current recommendation by the developer).

<!-- TODO Any stimuli that you wish to be judged should be listed in a file called `stimuli.txt` ...  -->
<!-- `stimuli.txt` and protocols in directory, actual files can be placed anywhere on the server -->
A file containing the complete filepaths to all stimuli (one stimulus per line). The application will assume:
1. That each line points to a unique stimulus.
2. Stimuli filenames are assumed to be unique (i.e., the last part of the filepath).
    * When behavior is logged, only the filenames will be saved to the database (not the full filepath).
3. No other stimuli should be used other than what is on the list.
4. All stimulus filepaths end with an appropriate file extension.
    * Filepaths without file extensions will be treated as raw text.

If you are looking for a quick way to create this file from a directory of stimuli, one option is to use the GNU or BSD `find` command. For example, the following command finds all files with .jpg and .png file extensions within the `path/to/dataset` directory:

```
find path/to/dataset -type f -iname "*.jpg" -o -iname "*.png" > stimuli.txt
```

Note it is important that the order of the stimuli in stimuli.txt file not change once you have started collecting data. Instead of storing filenames, only the indices are stored. It's fine to add additional lines for new stimuli, but do not alter existing lines.

### 2.2 Collection Protocol(s)
A JSON file specifying an experiment protocol. There are two types of protocols: *stochastic* and *deterministic*. A stochastic protocol requires the following fields:
* "generator": "stochastic",
* "pages": array,
* "docket": object

* "nTrial": int,
* "nCatch": int,
* "nReference": int,
* "nSelect": int,
* "isRanked": bool

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
* specifying breaks TODO
* make clear that if no consent is provided in project directory, there is no default, i.e., assumes that it has been obtained some other way

For clarity to the participant, it is probably best not to mix unranked and ranked trials within a session.


## Additional Details

A trial is only shown once all of the assets have been loaded in the browser. This behavior enforces the constaint that participants are presented with all trial content simultaneously. To reduce time spent waiting for stimuli to load, the application starts loading all stimuli, in the order of their occurrence, after the first page has loaded.

## Python Scripts

A python script is included to check the validity of a protocol. If a protocol is specified incorrectly, the application will do it's best to recover but may yield dockets that differ from what was intended. For example, if a protocol requests more catch trials `nCatch` than the total number of trials `nTrial`, the docket will contain `nTrial` catch trials.
