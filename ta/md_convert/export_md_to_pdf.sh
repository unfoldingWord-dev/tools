#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>
#
#  Execute export_md_to_pdf.sh to run
#  Set WORKING_DIR, otherwise will be a temp dir
#  Set OUTPUT_DIR, otherwise will be the current dir

set -e # die if errors

: ${DEBUG:=false}

: ${MY_DIR:=$(cd $(dirname "$0") && pwd)} # Tools dir relative to this script
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:="$MY_DIR/toc_template.xsl"}
: ${TEMPLATE_ALL:="$MY_DIR/toc_template_all.xsl"}
: ${VERSION:=5}

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "export_md_to_pdf.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

# Change to own own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR" > /dev/null

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

repos=(en-ta-intro en-ta-process en-ta-translate-vol1 en-ta-translate-vol2 en-ta-checking-vol1 en-ta-checking-vol2 en-ta-gl en-ta-audio)
#repos=(en-ta-process en-ta-translate-vol1 en-ta-translate-vol2 en-ta-audio)

cp "$MY_DIR/style.css" "$OUTPUT_DIR/html"

for repo in "${repos[@]}"
do
    echo $repo
    if [ ! -e "$WORKING_DIR/$repo" ]; then
        cd "$WORKING_DIR"
        git clone "https://git.door43.org/Door43/$repo.git"
        cd "$repo"
    else
        cd "$WORKING_DIR/$repo"
    fi
    git checkout tags/v5
done

"$MY_DIR/md_to_html_export.py" -i "$WORKING_DIR" -o "$OUTPUT_DIR/html"

for repo in "${repos[@]}"
do
     headerfile="file://$OUTPUT_DIR/html/${repo}-header.html"
     coverfile="file://$OUTPUT_DIR/html/${repo}-cover.html"
     licensefile="file://$OUTPUT_DIR/html/${repo}-license.html"
     bodyfile="file://$OUTPUT_DIR/html/${repo}-body.html"
     outfile="$OUTPUT_DIR/pdf/${repo}-v5.pdf"
     echo "GENERATING $outfile"
     wkhtmltopdf --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$bodyfile" "$outfile"
done

headerfile="file://$OUTPUT_DIR/html/en-ta-complete-header.html"
coverfile="file://$OUTPUT_DIR/html/en-ta-complete-cover.html"
licensefile="file://$OUTPUT_DIR/html/en-ta-complete-license.html"
bodyfile="file://$OUTPUT_DIR/html/en-ta-complete-body.html"
outfile="$OUTPUT_DIR/pdf/en-ta-v5.pdf"
echo "GENERATING $outfile"
wkhtmltopdf --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$bodyfile" "$outfile"
