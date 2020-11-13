<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Resource list</title>
  </head>
<body>
<?php
date_default_timezone_set('US/Eastern');
$dirs = array();
$dir = opendir("."); // open the cwd..also do an err check.
while(false != ($file = readdir($dir))) {
        if(($file != ".") && ($file != "..") && ($file != "index.php") && is_dir($file)) {
                $dirs[] = $file; // put in array.
        }
}

natsort($dirs); // sort.

// print.
foreach($dirs as $dir) {
    $files = array();
    $subdir = opendir($dir); // open the cwd..also do an err check.
    while(false != ($subfile = readdir($subdir))) {
        $filepath= './'.$dir.'/'.$subfile;
        if(($subfile != ".") && ($subfile != "..") && ($subfile != "index.php") && is_link($filepath) && !is_dir($filepath)) {
                $files[] = $subfile; // put in array.
        }
    }

    if ($files) {
        natsort($files); // sort.

        echo "<h2>".$dir."</h2>\n";
        echo "<p>\n";
        foreach($files as $file) {
            $filepath = './'.$dir.'/'.$file;
            $realfile = basename(readlink($filepath));
            echo '<a href="'.$filepath.'">'.$realfile.'</a> <em>('.date ("Y-m-d H:i:s", filemtime($filepath)).')</em><br/>'."\n";
        }
        echo "</p>\n";
    }
}
?>
</body>
</html>
