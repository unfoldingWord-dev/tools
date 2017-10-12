#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>
#
#  Execute export_md_to_pdf.sh to run
#  Set OUTPUT_DIR, otherwise will be the current dir

if [ -z $1 ]; then
    echo "Please specify the TAG or COMMIT ID for the en_ta repo."
    exit 1
fi

set -e # die if errors

: ${DEBUG:=false}

: ${MY_DIR:=$(cd $(dirname "$0") && pwd)} # Tools dir relative to this script
: ${RESOURCE:='ta'}
: ${LANGUAGE:='en'}
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:="$MY_DIR/toc_template.xsl"}
: ${TAG:=$1}

pushd "$OUTPUT_DIR"

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

mkdir -p "./html"
mkdir -p "./pdf"

repo="${LANGUAGE}_${RESOURCE}"
print_url="https://api.door43.org/tx/print?id=Door43/${repo}/${TAG}"
archive_url="https://git.door43.org/Door43/${repo}/archive/${TAG}.zip"

wget "$print_url" -O "./html/ta_orig.html"
wget "$archive_url" -O "./${repo}.zip"

unzip -qo "./${repo}.zip"

echo "Checked out repo files:"
ls "./${repo}"

version=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.version'`
issued_date=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.issued'`
title=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.title'`
checking_level=`yaml2json "${repo}/manifest.yaml" | jq -r '.checking.checking_level'`

echo "Current '$repo' print page is at: ${print_url}"
echo "Current '$repo' archive file is at: ${archive_url}"
echo "Current '$repo' Version is at: ${version}"

"$MY_DIR/massage_ta_html.py" -i "./html/ta_orig.html" -o "./html/ta.html" \
                             -s "$MY_DIR/style.css" -v $version

echo '<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="file://'$MY_DIR'/style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="http://unfoldingword.org/assets/img/icon-ta.png" width="120">
    <span class="h1">translationAcademy</span>
    <span class="h3">Version '${version}'</span>
  </div>
</body>
</html>
' > "./html/cover.html"

echo '<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="file://'$MY_DIR'/style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
<h2>Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)</h2>
<p>This is a human-readable summary of (and not a substitute for) the <a href="http://creativecommons.org/licenses/by-sa/4.0/">license</a>.</p>
<h3>You are free to:</h3>
<ul>
<li><strong>Share</strong> — copy and redistribute the material in any medium or format</li>
<li><strong>Adapt</strong> — remix, transform, and build upon the material </li>
</ul>
<p>for any purpose, even commercially.</p>
<p>The licensor cannot revoke these freedoms as long as you follow the license terms.</p>
<h3>Under the following conditions:</h3>
<ul>
<li><strong>Attribution</strong> — You must attribute the work as follows: "Original work available at https://door43.org/." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.</li>
<li><strong>ShareAlike</strong> — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.</li>
</ul>
<p><strong>No additional restrictions</strong> — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.</p>
<h3>Notices:</h3>
<p>You do not have to comply with the license for elements of the material in the public domain or where your use is permitted by an applicable exception or limitation.</p>
<p>No warranties are given. The license may not give you all of the permissions necessary for your intended use. For example, other rights such as publicity, privacy, or moral rights may limit how you use the material.</p>
    <p>
      <strong>Date:</strong> '${issued_date}'<br/>
      <strong>Version:</strong> '${version}'
    </p>
  </div>
</body>
</html>
' > "./html/license.html"

    echo '<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
    <link href="file://'$MY_DIR'/style.css" rel="stylesheet"/>
    <script>
        function subst() {
            var vars = {};

            var valuePairs = document.location.search.substring(1).split("&");
            for (var i in valuePairs) {
                var valuePair = valuePairs[i].split("=", 2);
                vars[valuePair[0]] = decodeURIComponent(valuePair[1]);
            }
            var replaceClasses = ["frompage","topage","page","webpage","section","subsection","subsubsection"];

            for (var i in replaceClasses) {
                var hits = document.getElementsByClassName(replaceClasses[i]);

                for (var j = 0; j < hits.length; j++) {
                    hits[j].textContent = vars[replaceClasses[i]];
                }
            }
        }
    </script>
</head>
<body style="border:0; margin: 0px;" onload="subst()">
<div style="font-style:italic;height:1.5em;"><span class="section" style="display;block;float:left;"></span><span class="subsection" style="float:right;display:block;"></span></div>
</body>
</html>
' > "./html/header.html"

headerfile="file://$OUTPUT_DIR/html/header.html"
coverfile="file://$OUTPUT_DIR/html/cover.html"
licensefile="file://$OUTPUT_DIR/html/license.html"
tafile="file://$OUTPUT_DIR/html/ta.html"
outfile="./pdf/en_ta_v${version}.pdf"
echo "GENERATING $outfile"
wkhtmltopdf --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15 --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$tafile" "$outfile"

popd