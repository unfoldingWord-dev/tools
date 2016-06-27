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

repos=(en-ta-intro en-ta-process en-ta-translate-vol1 en-ta-translate-vol2)

for repo in "${repos[@]}"
do
    if [ ! -e "$WORKING_DIR/$repo" ]; then
        cd "$WORKING_DIR"
        git clone "https://git.door43.org/Door43/$repo.git"
    else
        cd "$WORKING_DIR/$repo"
        git pull
    fi
done

"$MY_DIR/md_to_html_export.py" -i "$WORKING_DIR" -o "$OUTPUT_DIR"

for repo in "${repos[@]}"
do
     wkhtmltopdf --encoding utf-8 -O portrait -L 15 -R 15 -T 15 -B 15 --header-left '[section]' --header-right '[subsection]' --header-line --header-spacing 5 --footer-center '[page]' cover "file://$OUTPUT_DIR/${repo}-cover.html" toc --disable-dotted-lines --xsl-style-sheet "$TEMPLATE" "file://$OUTPUT_DIR/$repo.html" "$OUTPUT_DIR/$repo.pdf"
done
