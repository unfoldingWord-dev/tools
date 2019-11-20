#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  tw_pdf_create.sh - generates a PDF for translationWords, including all words from KT and Other
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <rich.mahn@unfoldingword.org>
#  Caleb Maclennan <caleb@alerque.com>

set -e # die if errors

export PATH=/usr/local/texlive/2016/bin/x86_64-linux:$PATH

FILE_TYPES=()
VALID_FILE_TYPES=(pdf docx html tex txt text)

#gather command-line arguments
while [[ $# > 0 ]]
do
    arg="$1"
    case $arg in
        -o|--output)
            OUTPUT_DIR="$2"
            shift # past argument
        ;;
        -w|--working)
            WORKING_DIR="$2"
            shift # past argument
        ;;
        -l|--lang|-language)
            LANGUAGE="$2"
            shift # past argument
        ;;
        -d|--debug)
            DEBUG=true
        ;;
        -t|--type)
            arg2=${2,,}

            if [ ! ${VALID_FILE_TYPES[$arg2]+_} ];
            then
                echo "Invalid type: $arg2"
                echo "Valid types: pdf, docx, html, tex, txt, text"
                exit 1
            fi

            FILE_TYPES+=("$arg2")

            shift # past argument
        ;;
    esac
    shift # past argument or value
done

# Instantiate a DEBUG flag (default to false). This enables output usful durring
# script development or later DEBUGging but not normally needed durring
# production runs. It can be used by calling the script with the var set, e.g.:
#     $ DEBUG=true ./uwb/pdf_create.sh <book>
: ${DEBUG:=false}

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)} # Tools dir relative to this script
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/uwb/tex/tn_tw_tq_template.tex}
: ${VERSION:=3}
: ${REGENERATE_HTML_FILES:=true}
: ${REDOWNLOAD_FILES:=false}
: ${COMBINED_LISTS:=false}

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

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}

: ${TW_DIR:=$LANGUAGE/obe}

if [ ! -e $D43_BASE_DIR ];
then
    echo "The directory $D43_BASE_DIR does not exist. Can't continue. Exiting."
    exit 1;
fi

DATE=`date +"%Y-%m-%d"`

KT_FILE="${LANGUAGE}_tw_kt.html" # Key Terms file
OTHER_FILE="${LANGUAGE}_tw_ot.html" # Other Terms file
HTML_FILE="${LANGUAGE}_tw_all.html" # Compilation of all above HTML files
OUTPUT_FILE="$OUTPUT_DIR/tw-v${VERSION}" # Outputted PDF file
LINKS_FILE="${LANGUAGE}_tw_links.sed" # SED commands for links
BAD_LINKS_FILE="${LANGUAGE}_tw_bad_links.txt"

if [ ${#FILE_TYPES[@]} -eq 0 ];
then
    FILE_TYPES=(pdf)
fi

generate_term_file () {
    dir=$1
    out_file=$2

    echo "GENERATING $out_file"

    rm -f $out_file
    touch $out_file

    find $dir -type f -name "*.txt" \( -exec grep -q 'tag>.*publish' {} \; -or -not -exec grep -q 'tag>.*draft' {} \; \) -print | awk -vFS=/ -vOFS=/ '{ print $NF,$0 }' |
        sort -u -t / | cut -f2- -d/ |
        while read f; do
            filename=$(basename $f)
            term=${filename%%.txt}
            dir="$TW_DIR/$(basename $(dirname $f))"

            mkdir -p "$dir" # creates the dir path in $WORKING_DIR

            # If the file doesn't exit or the file is older than (-ot) the Door43 repo one, fetch it
            if $REDOWNLOAD_FILES || [ ! -e "$dir/$term.html" ] || [ "$dir/$term.html" -ot "$D43_BASE_DIR/$dir/$term.txt" ];
            then
                wget -U 'me' "$D43_BASE_URL/$dir/$term" -O "$dir/$term.html"
            fi

            grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' "$dir/$term.html" |
                    grep -v ' href="\/tag\/' >> "$out_file"

            echo "<hr/>" >> "$out_file"

            linkname=$(head -3 "$dir/$term.html" | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo "s@\"[^\"]*/$dir/$term\"@\"#$linkname\"@g" >> "$LINKS_FILE"
        done

    # Quick fix for getting rid of these Bible References lists in a table, removing table tags
    sed -i -e 's/^\s*<table class="ul">/<ul>/' "$out_file"
    sed -i -e 's/^\s*<tr>//' "$out_file"
    sed -i -e 's/^\s*<td class="page"><ul>\(.*\)<\/ul><\/td>/\1/' "$out_file"
    sed -i -e 's/^\s*<\/tr>//' "$out_file"
    sed -i -e 's/^\s*<\/table>/<\/ul>/' "$out_file"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$out_file"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$out_file"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$out_file"
}

# ---- MAIN EXECUTION BEGINS HERE ----

if $REGENERATE_HTML_FILES; then
    rm -f "$KT_FILE" "$OTHER_FILE" "$HTML_FILE" "$OUTPUT_FILE".*  # We start fresh, only files that remain are any files retrieved with wget
fi

touch "$LINKS_FILE"
touch "$BAD_LINKS_FILE"

if ! $COMBINED_LISTS;
then
    # ----- GENERATE KT PAGES --------- #
    if [ ! -e "$KT_FILE" ];
    then
        generate_term_file "$D43_BASE_DIR/$TW_DIR/kt" $KT_FILE
    fi
    # ----- EMD GENERATE KT PAGES ----- #
    
    # ----- GENERATE OTHER PAGES --------- #
    if [ ! -e "$OTHER_FILE" ];
    then
    generate_term_file "$D43_BASE_DIR/$TW_DIR/other" $OTHER_FILE
    fi
    # ----- EMD GENERATE OTHER PAGES ----- #
else
    # ----- GENERATE ALL PAGES --------- #
    if [ ! -e "$OTHER_FILE" ];
    then
        generate_term_file "$D43_BASE_DIR/$TW_DIR/other $D43_BASE_DIR/$TW_DIR/kt" $OTHER_FILE
    fi
    # ----- EMD GENERATE ALL PAGES ----- #
fi

# ----- GENERATE COMPLETE HTML PAGE ----------- #
if [ ! -e "$HTML_FILE" ];
then
    echo "GENERATING $HTML_FILE"
        
    if ! $COMBINED_LISTS;
    then
        echo '<h1>Key Terms</h1>' >> $HTML_FILE
        cat $KT_FILE >> $HTML_FILE
        
        echo '<h1>Other Terms</h1>' >> $HTML_FILE
        cat $OTHER_FILE >> $HTML_FILE
    else
        echo '<h1>translationWords</h1>' >> $HTML_FILE
        cat $OTHER_FILE >> $HTML_FILE
    fi

    # ----- START LINK FIXES AND CLEANUP ----- #
    sed -i \
        -e 's/<\/span>/<\/span> /g' \
        -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
        $HTML_FILE
        
    # Link Fixes
    sed -i -f "$LINKS_FILE" "$HTML_FILE"
    # ----- END LINK FIXES AND CLEANUP ------- #
else
    echo "NOTE: $HTML_FILE already generated."
fi
# ----- END GENERATE COMPLETE HTML PAGE --------#

# ----- START GENERATE FILES ----- #
TITLE='translationWords'

LOGO="https://unfoldingword.org/assets/img/icon-tw.png"
response=$(curl --write-out %{http_code} --silent --output logo-tw.png "$LOGO");
if [ $response -eq "200" ];
then
  LOGO_FILE="-V logo=logo-tw.png"
fi

FORMAT_FILE="$TOOLS_DIR/uwb/tex/format.tex"

for type in "${FILE_TYPES[@]}"
do
    if [ ! -e "$OUTPUT_FILE.$type" ];
    then
        echo "GENERATING $OUTPUT_FILE.$type";
        pandoc \
            -S \
            --latex-engine="xelatex" \
            --template="$TEMPLATE" \
            --toc \
            --toc-depth=2 \
            -V documentclass="scrartcl" \
            -V classoption="oneside" \
            -V geometry='hmargin=2cm' \
            -V geometry='vmargin=3cm' \
            -V title="$TITLE" \
            $LOGO_FILE \
            -V date="$DATE" \
            -V version="$VERSION" \
            -V mainfont="Noto Serif" \
            -V sansfont="Noto Sans" \
            -V linkcolor="ForestGreen" \
            -H "$FORMAT_FILE" \
            -o "$OUTPUT_FILE.$type" "$HTML_FILE"

        echo "GENERATED FILE: $OUTPUT_FILE.$type"
    fi
done
# ----- END GENERATE FILES ----- #

echo "Done!"
