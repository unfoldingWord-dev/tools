<?php

// where the PHP array with the language codes is located
$vars = "/var/www/vhosts/door43.org/httpdocs/conf/local.php";

require_once("$vars");

// dump the language codes from the array 
print_r ($conf['plugin']['translation']['translations']);

?>
