<?php
// NOTE: You must change the filepath to reflect your server setup.
$mysqlCredentialsPath = '/home/bdroads/.mysql/credentials';

$amtAssignmentId = $_POST['amtAssignmentId'];
$amtWorkerId = $_POST['amtWorkerId'];
$amtHitId = $_POST['amtHitId'];

// Function to generate random alpha-numeric string of specific length.
// SEE: https://stackoverflow.com/a/31284266/2224584
function randomString($length) {
    $keyspace = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $str = '';
    $max = strlen($keyspace) - 1;
    if ($max < 1) {
        throw new Exception('$keyspace must be at least two characters long');
    }
    for ($i = 0; $i < $length; ++$i) {
        $str .= $keyspace[random_int(0, $max)];
    }
    return $str;
}

// Parse MySQL configuration.
$config = parse_ini_file($mysqlCredentialsPath, true);

// Connect to the voucher database.
$link = mysqli_connect($config['amt_voucher']['servername'], $config['amt_voucher']['username'], $config['amt_voucher']['password'], $config['amt_voucher']['database']);
// Check the connection.
if (mysqli_connect_errno()) {
    printf("Connect failed: %s\n", mysqli_connect_error());
    exit();
}

// To prevent abuse, check if the worker (workerId) already has a voucher for
// the particular assignment (assignmentId).
$query = "SELECT COUNT(voucher_id) AS 'count' FROM voucher WHERE amt_assignment_id=? AND amt_worker_id=?";
if ($stmt = mysqli_prepare($link, $query)) {
    mysqli_stmt_bind_param($stmt, 'ss', $amtAssignmentId, $amtWorkerId);
    mysqli_stmt_execute($stmt);
    mysqli_stmt_bind_result($stmt, $count);
    mysqli_stmt_fetch($stmt);
    mysqli_stmt_close($stmt);
}

if ($count == 0) {
    // Create a new voucher code.
    $voucherCode = randomString(12);
    $voucherHash = hash('sha512', $voucherCode);
    // Insert voucher into table.
    $query = "INSERT INTO voucher (amt_assignment_id, amt_worker_id, amt_hit_id, voucher_hash) VALUES (?, ?, ?, ?)";
    $stmt = mysqli_prepare($link, $query);
    mysqli_stmt_bind_param($stmt, 'ssss', $amtAssignmentId, $amtWorkerId, $amtHitId, $voucherHash);
    mysqli_stmt_execute($stmt);
    mysqli_stmt_close($stmt);
} else {
    // Worker already has a voucher for this assignment, do not generate
    // another one.
    $voucherCode = "0";
}

mysqli_close($link);
echo $voucherCode;
?>