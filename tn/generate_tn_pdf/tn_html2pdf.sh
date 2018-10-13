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
#  Execute tn_html2pdf.sh to run
#  Set OUTPUT_DIR, otherwise will be the current dir

if [ -z $1 ]; then
    echo "Please specify the TAG or COMMIT ID for the en_tn repo."
    exit 1
fi

set -e # die if errors

: ${DEBUG:=false}

: ${MY_DIR:=$(cd $(dirname "$0") && pwd)} # Tools dir relative to this script
: ${RESOURCE:='tn'}
: ${LANGUAGE:='en'}
: ${WORKING_DIR:=$(pwd)}
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:="$MY_DIR/toc_template.xsl"}
: ${TAG:=$1}

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

repo="${LANGUAGE}_${RESOURCE}"

mkdir -p "$OUTPUT_DIR/tn_html"
mkdir -p "$OUTPUT_DIR/tn_pdf"

cd ../../..
pwd
python -m tools.tn.generate_tn_pdf.generate_tn_html -w "$WORKING_DIR" -o "$OUTPUT_DIR/tn_html" --contributors "$contributors"

cd "$WORKING_DIR"
echo "Have out repo files:"
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

echo "Current '$repo' Version is at: ${version}"
echo "Current '$repo' Publisher is: ${publisher}"
echo "Current '$repo' Contributors are: ${contributors}"

cd "$OUTPUT_DIR"

echo '<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="https://unfoldingword.org/assets/img/icon-tn.png" width="120">
    <span class="h1">translationNotes</span>
    <span class="h3">Version '${version}'</span>
  </div>
</body>
</html>
' > "./tn_html/cover.html"

echo '<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
    <p>
      <strong>Date:</strong> '$issued_date'<br/>
      <strong>Version:</strong> '$version'<br/>
      <strong>Published by:</strong> '$publisher'<br/>
    </p>
    '$license'
  </div>
</body>
</html>
' > "./tn_html/license.html"

cp "$MY_DIR/header.html" "./tn_html/header.html"

cp "$MY_DIR/style.css" "./tn_html"

headerfile="$OUTPUT_DIR/tn_html/header.html"
coverfile="$OUTPUT_DIR/tn_html/cover.html"
licensefile="$OUTPUT_DIR/tn_html/license.html"
bodyfile="$OUTPUT_DIR/tn_html/en_tn_57-TIT_v13.html"
outfile="./tn_pdf/en_tn_57-TIT_v13.pdf"

echo "GENERATING $outfile"
wkhtmltopdf --javascript-delay 2000 --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$bodyfile" "$outfile"
