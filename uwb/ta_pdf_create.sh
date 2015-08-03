#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  ta_pdf_create.sh - generates a PDF for translationAcademy, simple getting the HTML from https://api.unfoldingword.org/ta_export.html
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

set -e

: ${DEBUG:=false}
: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/general_tools/pandoc_pdf_template.tex}

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

# Create a temorary diretory using the system default temp directory location
# in which we can stash any files we want in an isolated namespace. It is very
# important that this dir actually exist. The set -e option should always be used
# so that if the system doesn't let us create a temp directory we won't contintue.
if [[ -z "$WORKING_DIR" ]]; then
    WORKING_DIR=$(mktemp -d -t "ubw_pdf_create.XXXXXX")
    # If _not_ in DEBUG mode, _and_ we made our own temp directory, then
    # cleanup out temp files after every run. Running in DEBUG mode will skip
    # this so that the temp files can be inspected manually
    $DEBUG || trap 'popd; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d "$WORKING_DIR" ]]; then
    mkdir -p "$WORKING_DIR"
fi

# Change to own own temp dir but note our current dir so we can get back to it
pushd $WORKING_DIR

if [ -z "$1" ];
then
    : ${LANGUAGE:='en'}
else
    LANGUAGE=$1
fi

: ${TA_EXPORT_URL:=https://api.unfoldingword.org/ta_export.html}

#if [ ! -e $D43_BASE_DIR ];
#then
#    echo "The directory $D43_TA_DIR does not exist. Can't continue. Exiting."
#    exit 1;
#fi

DATE=`date +"%Y-%m-%d"`

TA_FILE="${LANGUAGE}_ta_kt.html" # Key Terms file
HTML_FILE="${LANGUAGE}_tw_all.html" # Compilation of all above HTML files
PDF_FILE="$OUTPUT_DIR/tA_${LANGUAGE^^}_$DATE.pdf" # Outputted PDF file

# ---- MAIN EXECUTION BEGINS HERE ----- #
    rm -f $TA_FILE $HTML_FILE # We start fresh, only files that remain are any files retrieved with wget

    # ----- GENERATE TA PAGES --------- #
    echo "GENERATING $TA_FILE"

    wget -U 'me' "$TA_EXPORT_URL" -O - > "$TA_FILE"

    # Don't need the \newpage lines as we break on <h1>
    sed -i -e '/\\newpage/d' "$TA_FILE"
    # ----- EMD GENERATE KT PAGES ----- #

    # ----- GENERATE COMPLETE HTML PAGE ----------- #
    echo "GENERATING $HTML_FILE"

    cat $TA_FILE >> $HTML_FILE
    # ----- END GENERATE COMPLETE HTML PAGE --------#

    # ----- START LINK FIXES AND CLEANUP ----- #
    sed -i \
        -e 's/<\/span>/<\/span> /g' \
        -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
        $HTML_FILE
    # ----- END LINK FIXES AND CLEANUP ------- #

    # ----- START GENERATING PDF FILE ----- #
    echo "GENERATING $PDF_FILE";

    TITLE='translationAcadamy'

    # Create PDF
    pandoc --template=$TEMPLATE -S --toc --toc-depth=2 -V toc-depth=1 \
        --latex-engine="xelatex" \
        -V documentclass="scrartcl" \
        -V classoption="oneside" \
        -V geometry='hmargin=2cm' \
        -V geometry='vmargin=3cm' \
        -V title="$TITLE" \
        -V date="$DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o $PDF_FILE $HTML_FILE

    echo "See $PDF_FILE (generated files: $WORKING_DIR)"
