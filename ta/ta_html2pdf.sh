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
#  Execute ta_html2pdf.sh to run
#  Set OUTPUT_DIR, otherwise will be the current dir

set -e # die if errors

: ${DEBUG:=false}

: ${MY_DIR:=$(cd $(dirname "$0") && pwd)} # Tools dir relative to this script
: ${RESOURCE:='ta'}
: ${LANGUAGE:='en'}
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:="$MY_DIR/toc_template.xsl"}
: ${OWNER=unfoldingWord}

if [ -z $1 ]; then
    echo "Please specify the TAG or COMMIT ID for the ${LANGUAGE}_ta repo."
    exit 1
fi

: ${TAG:=$1}

pushd "$OUTPUT_DIR"

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

mkdir -p "./html"
mkdir -p "./pdf"

repo="${LANGUAGE}_${RESOURCE}"
print_url="https://api.door43.org/tx/print?id=${OWNER}/${repo}/${TAG}"
archive_url="https://git.door43.org/${OWNER}/${repo}/archive/${TAG}.zip"

cdn_url=$(wget -qO- $print_url)
echo $cdn_url
wget "$cdn_url" -O "./html/ta_orig.html"
wget "$archive_url" -O "./${repo}.zip"

unzip -qo "./${repo}.zip"

echo "Checked out repo files:"
ls "./${repo}"

license=$(markdown2 "${repo}/LICENSE.md")
version=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.version'`
issued_date=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.issued'`
title=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.title'`
checking_level=`yaml2json "${repo}/manifest.yaml" | jq -r '.checking.checking_level'`
publisher=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.publisher'`
contributors=$(echo `js-yaml "${repo}/manifest.yaml" | jq -c '.dublin_core.contributor[]'`)
contributors=${contributors//\" \"/; }
contributors=${contributors//\"/}

echo "Current '$repo' print page is at: ${print_url}"
echo "Current '$repo' archive file is at: ${archive_url}"
echo "Current '$repo' Version is at: ${version}"
echo "Current '$repo' Publisher is: ${publisher}"
echo "Current '$repo' Contributors are: ${contributors}"

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
    <img src="https://cdn.door43.org/assets/uw-icons/logo-uta-256.png" width="120">
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
    <p>
      <strong>Date:</strong> '$issued_date'<br/>
      <strong>Version:</strong> '$version'<br/>
      <strong>Contributors:</strong> '$contributors'<br/>
      <strong>Published by:</strong> '$publisher'<br/>
    </p>
    '$license'
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
outfile="./pdf/${LANGUAGE}_ta_v${version}.pdf"
echo "GENERATING $outfile"
wkhtmltopdf --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15 --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$tafile" "$outfile"

popd
