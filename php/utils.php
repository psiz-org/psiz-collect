<?php

// NOTE: You must change the filepath to reflect your server setup.
$mysqlCredentialsPath = '/home/bdroads/.mysql/credentials';
// Parse MySQL configuration.
$config = parse_ini_file($mysqlCredentialsPath, true);

/**
 * Join paths in a manner similar to python os.path.join(*).
 *
 * See: https://stackoverflow.com/a/1557529
 * 
 * @param array $arg  An array of strings.
 * @return str
 */
function joinPaths() {
    $paths = array();

    foreach (func_get_args() as $arg) {
        if ($arg !== '') { $paths[] = $arg; }
    }

    return preg_replace('#/+#','/',join('/', $paths));
}

?>