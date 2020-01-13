<?php
$dirs = array();
$dir = opendir('.'); // open the cwd..also do an err check.
while(false != ($file = readdir($dir))) {
        if(($file != ".") and ($file != "..") and ($file != "index.php") && is_dir($file)) {
                $dirs[] = $file; // put in array.
        }
}

natsort($dirs); // sort.

// print.
foreach($dirs as $dir) {
    $files = array();
    $subdir = opendir($dir); // open the cwd..also do an err check.
    while(false != ($subfile = readdir($dir))) {
        if(($subfile != ".") and ($subfile != "..") and is_link($subfile)) {
                $files[] = $subfile; // put in array.
        }
    }

    natsort($files); // sort.

    echo '<h2>'.$dir.'</h2>'
    echo '<p>'
    foreach($files as $file) {
        echo("<a href='$file'>$file</a> <br />\n");
    }
    echo '</p>'
}
