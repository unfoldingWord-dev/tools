#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  tw_pdf_create.sh - generates a PDF for translationWords, including all words from
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#  Caleb Maclennan <caleb@alerque.com>

# Set script to die if any of the subprocesses exit with a fail code. This
# catches a lot of scripting mistakes that might otherwise only show up as side
# effects later in the run (or at a later time). This is especially important so
# we know out temp dir situation is sane before we get started.
set -e

# ENVIRONMENT VARIABLES:
# DEBUG - true/false -  If true, will run "set -x"
# TOOLS_DIR - Directory of the "tools" repo where scripts and templates resides. Defaults to the parent directory of this script
# WORKING_DIR - Directory where all HTML files for tN, tQ, tW, tA are collected and then a full HTML file is made before conversion to PDF, defaults to a system suggested temp location
# OUTPUT_DIR - Directory to put the PDF, defaults to the current working directory
# BASE_URL - URL for the _export/xhtmlbody to get Dokuwiki content, defaults to 'https://door43.org/_export/xhtmlbody'
# NOTES_URL - URL for getting translationNotes, defaults to $BASE_URL/en/bible/notes
# TEMPLATE - Location of the TeX template for Pandoc, defaults to "$TOOLS_DIR/general_tools/pandoc_pdf_template.tex

# Instantiate a DEBUG flag (default to false). This enables output usful durring
# script development or later DEBUGging but not normally needed durring
# production runs. It can be used by calling the script with the var set, e.g.:
#     $ DEBUG=true ./uwb/pdf_create.sh <book>
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

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/$LANGUAGE}
: ${D43_CL_DIR:=$D43_BASE_DIR/legal}
: ${D43_TW_DIR:=$D43_BASE_DIR/obe}

: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody/$LANGUAGE}
: ${D43_CL_URL:=$D43_BASE_URL/legal}
: ${D43_TW_URL:=$D43_BASE_URL/obe}

if [ ! -e $D43_BASE_DIR ];
then
    echo "The directory $D43_TW_DIR does not exist. Can't continue. Exiting."
    exit 1;
fi

DATE=`date +"%Y-%m-%d"`

CL_FILE="${LANGUAGE}_tw_cl.html" # Copyrights & Licensing
KT_FILE="${LANGUAGE}_tw_kt.html" # Key Terms file
OT_FILE="${LANGUAGE}_tw_ot.html" # Other Terms file
HTML_FILE="${LANGUAGE}_tw_all.html" # Compilation of all above HTML files
PDF_FILE="$OUTPUT_DIR/tW_${LANGUAGE^^}_$DATE.pdf" # Outputted PDF file

generate_term_file () {
    subdir=$1
    outfile=$2

    echo "GENERATING $outfile"

    rm -f $outfile

    WORKING_SUB_DIR="$WORKING_DIR/$LANGUAGE/tw/$subdir"
    mkdir -p "$WORKING_SUB_DIR"

    find "$D43_TW_DIR/$subdir" -type f -name "*.txt" -exec grep -q 'tag>.*publish' {} \; -printf '%P\n' |
        sort -u |
        while read f; do
            term=${f%%.txt}
            # If the file doesn't exit or the file is older than (-ot) the Door43 repo one, fetch it
            if [ ! -e "$WORKING_SUB_DIR/$term.html" ] || [ "$WORKING_SUB_DIR/$term.html" -ot "$D43_TW_DIR/$subdir/$term.txt" ];
            then
                wget -U 'me' "$D43_TW_URL/$subdir/$term" -O - |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    >> "$WORKING_SUB_DIR/$term.html"
            fi
            cat "$WORKING_SUB_DIR/$term.html" >> "$outfile"
        done

    # Quick fix for getting rid of these Bible References lists in a table, removing table tags
    sed -i -e 's/^\s*<table class="ul">/<ul>/' "$outfile"
    sed -i -e 's/^\s*<tr>//' "$outfile"
    sed -i -e 's/^\s*<td class="page"><ul>\(.*\)<\/ul><\/td>/\1/' "$outfile"
    sed -i -e 's/^\s*<\/tr>//' "$outfile"
    sed -i -e 's/^\s*<\/table>/<\/ul>/' "$outfile"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$outfile"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$outfile"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$outfile"
}

# ---- MAIN EXECUTION BEGINS HERE ----- #
    rm -f $CL_FILE $KT_FILE $OT_FILE $HTML_FILE # We start fresh, only files that remain are any files retrieved with wget

    # ----- START GENERATE CL PAGE ----- #
    echo "GENERATING $CL_FILE"

    WORKING_SUB_DIR="$LANGUAGE/legal/license"
    mkdir -p "$WORKING_SUB_DIR"

    # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
    if [ ! -e "$WORKING_SUB_DIR/uw.html" ] || [ "$WORKING_SUB_DIR/uw.html" -ot "D43_CL_DIR/license/uw.txt" ];
    then
        wget -U 'me' "$D43_CL_URL/license/uw" -O - > "$WORKING_SUB_DIR/uw.html"
    fi

    cat "$WORKING_SUB_DIR/uw.html" > "$CL_FILE"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$CL_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$CL_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$CL_FILE"
    # ----- END GENERATE CL PAGES ------- #

    # ----- GENERATE KT PAGES --------- #
    generate_term_file 'kt' $KT_FILE
    # ----- EMD GENERATE KT PAGES ----- #

    # ----- GENERATE OTHRR PAGES --------- #
    generate_term_file 'other' $OT_FILE
    # ----- EMD GENERATE OTHER PAGES ----- #

    # ----- GENERATE COMPLETE HTML PAGE ----------- #
    echo "GENERATING $HTML_FILE"

    echo '<h1>Copyrights & Licensing</h1>' >> $HTML_FILE
    cat $CL_FILE >> $HTML_FILE

    echo '<h1>Key Terms</h1>' >> $HTML_FILE
    cat $KT_FILE >> $HTML_FILE

    echo '<h1>Other Terms</h1>' >> $HTML_FILE
    cat $OT_FILE >> $HTML_FILE
    # ----- END GENERATE COMPLETE HTML PAGE --------#

    # ----- START LINK FIXES AND CLEANUP ----- #
    sed -i \
        -e 's/<\/span>/<\/span> /g' \
        -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
        $HTML_FILE
    # ----- END LINK FIXES AND CLEANUP ------- #

    # ----- START GENERATE PDF FILE ----- #
    echo "GENERATING $PDF_FILE";

    TITLE='translationWords'

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
