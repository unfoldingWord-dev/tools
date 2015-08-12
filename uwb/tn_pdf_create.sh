#!/usr/bin/env bash
# -*- coding: utf8 -*-
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
# NOTES_URL - URL for getting translationNotes, defaults to $D43_BASE_URL/en/bible/notes
# TEMPLATE - Location of the TeX template for Pandoc, defaults to "$TOOLS_DIR/general_tools/pandoc_pdf_template.tex

# Instantiate a DEBUG flag (default to false). This enables output usful durring
# script development or later DEBUGging but not normally needed durring
# production runs. It can be used by calling the script with the var set, e.g.:
#     $ DEBUG=true ./uwb/pdf_create.sh <book>
: ${DEBUG:=false}

: ${LANGUAGE:=en}

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/general_tools/pandoc_pdf_template.tex}

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}

: ${CL_DIR:=$LANGUAGE/legal/license}
: ${TN_DIR:=$LANGUAGE/bible/notes}
: ${TQ_DIR:=$LANGUAGE/bible/questions/comprehension}
: ${TW_DIR:=$LANGUAGE/obe}
: ${TA_DIR:=$LANGUAGE/ta}

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

# Create a temorary diretory using the system default temp directory location
# in which we can stash any files we want in an isolated namespace. It is very
# important that this dir actually exist. The set -e option should always be used
# so that if the system doesn't let us create a temp directory we won't contintue.
if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "ubw_pdf_create.XXXXXX")
    # If _not_ in DEBUG mode, _and_ we made our own temp directory, then
    # cleanup out temp files after every run. Running in DEBUG mode will skip
    # this so that the temp files can be inspected manually
    $DEBUG || trap 'popd; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

# Change to own own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR"

DATE=`date +"%Y-%m-%d"`

if [ ! -e $D43_BASE_DIR ];
then
    echo "The directory $D43_BASE_DIR does not exist. Can't continue. Exiting."
    exit 1;
fi

# Gets us an associative array called $BOOKS
source "$TOOLS_DIR/general_tools/bible_books.sh"

book_export () {
    BOOK=$1

    if [ ! ${BOOKS[$BOOK]+_} ];
    then
        echo "Invalid book given: $BOOK"
        exit 1;
    fi

    CL_FILE="${LANGUAGE}_${BOOK}_cl.html" # Copyrights & Licensing
    TN_FILE="${LANGUAGE}_${BOOK}_tn.html" # translationNotes
    TQ_FILE="${LANGUAGE}_${BOOK}_tq.html" # translationQuestions
    TW_FILE="${LANGUAGE}_${BOOK}_tw.html" # translationWords
    TA_FILE="${LANGUAGE}_${BOOK}_ta.html" # translationAcademy
    HTML_FILE="${LANGUAGE}_${BOOK}_all.html" # Compilation of all above HTML files
    LINKS_FILE="${LANGUAGE}_${BOOK}_links.sed" # SED commands for links
    PDF_FILE="$OUTPUT_DIR/tN_${BOOK^^}_${LANGUAGE^^}_$DATE.pdf"

    rm -f "$CL_FILE" "$TN_FILE" "$TQ_FILE" "$TA_FILE" "$LINKS_FILE" "$HTML_FILE" # We start fresh, only files that remain are any files retrieved with wget

    # ----- START GENERATE CL PAGE ----- #
    echo "GENERATING $CL_FILE"

    mkdir -p "$CL_DIR"

    # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
    if [ ! -e "$CL_DIR/uw.html" ] || [ "$CL_DIR/uw.html" -ot "$D43_BASE_DIR/$CL_DIR/uw.txt" ];
    then
        wget -U 'me' "$D43_BASE_URL/$CL_DIR/uw" -O "$CL_DIR/uw.html"
    fi

    cat "$CL_DIR/uw.html" > "$CL_FILE"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$CL_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$CL_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$CL_FILE"
    # ----- END GENERATE CL PAGES ------- #

    # ----- START GENERATE tN PAGES ----- #
    echo "GENERATING $TN_FILE"

    find "$D43_BASE_DIR/$TN_DIR/$BOOK" -type d -name "[0-9]*" -printf '%P\n' |
        while read chapter;
        do
            dir="$TN_DIR/$BOOK/$chapter";
            mkdir -p "$dir"

            find "$D43_BASE_DIR/$dir" -type f -name "[0-9]*.txt" -printf '%P\n' |
                grep -v 'asv-ulb' |
                sort -u |
                while read f; do
                    section=${f%%.txt}

                    # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
                    if [ ! -e "$dir/$section.html" ] || [ "$dir/$section.html" -ot "$D43_BASE_DIR/$dir/$section.txt" ];
                    then
                        wget -U 'me' "$D43_BASE_URL/$dir/$section" -O - |
                            grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                            grep -v ' href="\/tag\/' \
                            >> "$dir/$section.html"
                    fi

                    # Remove TFT
                    TFT=false
                    while read line; do
                        if [[ $line == '<h2 class="sectionedit2" id="tft">TFT:</h2>' ]]; then
                            TFT=true
                            continue
                        fi
                        if [[ ${line:0:25} == '<!-- EDIT2 SECTION "TFT:"' ]]; then
                            TFT=false
                            continue
                        fi
                        $TFT && continue
                        echo $line >> "$TN_FILE"
                    done < "$dir/$section.html"
                done
        done

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$TN_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$TN_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$TN_FILE"
    # ----- END GENERATE tN PAGES ------- #

    # ----- START GENERATE tQ PAGES ----- #
    echo "GENERATING $TQ_FILE"

    dir="$TQ_DIR/$BOOK"
    mkdir -p "$dir"

    find "$D43_BASE_DIR/$TQ_DIR/$BOOK" -type f -name "[0-9]*.txt" -printf '%P\n' |
        sort |
        while read f;
        do
            chapter=${f%%.txt}

            # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
            if [ ! -e "$dir/$chapter.html" ] || [ "$dir/$chapter.html" -ot "$D43_BASE_DIR/$dir/$chapter.txt" ];
            then
                wget -U 'me' "$D43_BASE_URL/$dir/$chapter" -O - |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    > "$dir/$chapter.html"
            fi

            cat "$dir/$chapter.html" >> "$TQ_FILE"

            linkname=$(head -3 "$dir/$chapter.html" | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo "s@/$dir/$chapter\"@#$linkname\"@g" >> "$LINKS_FILE"
        done

    # REMOVE Comprehension Questions and Answers title
    sed -i -e '\@<h2.*Comprehension Questions and Answers<\/h2>@d' "$TQ_FILE"

    # REMOVE links at end of quesiton page to return to question home page
    sed -i -e "\@/$dir/home@d" "$TQ_FILE"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$TQ_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$TQ_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$TQ_FILE"
    # ----- END GENERATE tQ PAGES ------- #

    # ----- START GENERATE tW PAGES ----- #
    echo "GENERATING $TW_FILE"

    # Get the linked key terms
    for url in $(grep -oPh "\"\/$LANGUAGE\/obe.*?\"" "$TN_FILE" | tr -d '"' | sort -u );
    do
        dir=${url#/} # remove preceeding /
        dir=${dir%/*} # remove term from dir
        term=${url##*/}

        mkdir -p "$dir"

        # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
        if [ ! -e "$dir/$term.html" ] || [ "$dir/$term.html" -ot "$D43_BASE_DIR/$dir/$term.txt" ];
        then
            wget -U 'me' "$D43_BASE_URL/$dir/$term" -O - |
                grep -v ' href="\/tag\/' \
                > "$dir/$term.html"
        fi

        cat "$dir/$term.html" >> "$TW_FILE"

        linkname=$(head -3 "$dir/$term.html" | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
        echo "s@/$dir/$term\"@#$linkname\"@g" >> "$LINKS_FILE"
    done

    # Quick fix for getting rid of these Bible References lists in a table, removing table tags
    sed -i -e 's/^\s*<table class="ul">/<ul>/' "$TW_FILE"
    sed -i -e 's/^\s*<tr>//' "$TW_FILE"
    sed -i -e 's/^\s*<td class="page"><ul>\(.*\)<\/ul><\/td>/\1/' "$TW_FILE"
    sed -i -e 's/^\s*<\/tr>//' "$TW_FILE"
    sed -i -e 's/^\s*<\/table>/<\/ul>/' "$TW_FILE"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$TW_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$TW_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$TW_FILE"
    # ----- END GENERATE tW PAGES ------- #

    # ----- START GENERATE tA PAGES ----- #
    echo "GENERATING $TA_FILE"

    # Get the linked tA
    grep -oPh "\"\/$LANGUAGE\/ta\/.*?\"" "$TN_FILE" "$TW_FILE" "$TQ_FILE" |
        tr -d '"' |
        sort -u |
        while read url;
        do
            dir=${url#/} # remove preceeding /
            dir=${dir%/*} # remove term from dir
            term=${url##*/}

            mkdir -p "$dir"

            # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
            if [ ! -e "$dir/$term.html" ] || [ "$dir/$term.html" -ot "$D43_BASE_DIR/$dir/$term.txt" ];
            then
                wget -U 'me' "$D43_BASE_URL/$dir/$term" -O - |
                    grep -v ' href="\/tag\/' \
                    > "$dir/$term.html"
            fi

            cat "$dir/$term.html" >> "$TA_FILE"

            linkname=$(head -3 "$dir/$term.html" | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo "s@/$dir/$term\"@#$linkname\"@g" >> "$LINKS_FILE"
        done

    # get rid of the pad.door43.org links and the <hr> with it
    sed -i -e 's/^\s*<a href="https:\/\/pad\.door43\.org.*//' "$TA_FILE"
    sed -i -e 's/^<hr \/>//' "$TA_FILE"

    # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
    sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$TA_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$TA_FILE"
    sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$TA_FILE"
    # ----- END GENERATE tA PAGES ------- #

    # ----- START GENERATE HTML PAGE ----- #

     # Compile all the above CL, tN, tQ, tW, and tA HTML files into one with headers
     echo "GENERATING $HTML_FILE"

     echo '<h1>Copyrights & Licensing</h1>' >> "$HTML_FILE"
     cat "$CL_FILE" >> "$HTML_FILE"

     echo '<h1>translationNotes</h1>' >> "$HTML_FILE"
     cat "$TN_FILE" >> "$HTML_FILE"

     echo '<h1>translationQuestions</h1>' >> "$HTML_FILE"
     cat "$TQ_FILE" >> "$HTML_FILE"

     echo '<h1>translationWords</h1>' >> "$HTML_FILE"
     cat "$TW_FILE" >> "$HTML_FILE"

     echo '<h1>translationAcademy</h1>' >> "$HTML_FILE"
     cat "$TA_FILE" >> "$HTML_FILE"
    # ----- END GENERATE HTML PAGES ------- #

    # ----- START LINK FIXES AND CLEANUP ----- #
    # Link Fixes
    sed -i -f "$LINKS_FILE" "$HTML_FILE"
    sed -i -e 's/\/en\/bible.*"/"/' "$HTML_FILE"
    sed -i -e 's/\/en\/obs.*"/"/' "$HTML_FILE"

    # Cleanup
    sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
        -e 's/<\/span>/<\/span> /g' -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
        "$HTML_FILE"
#        -e '/jpg"/d' \
#        -e 's/"\/_media/"https:\/\/door43.org\/_media/g' \
    # ----- END LINK FIXES AND CLEANUP ------- #

    # ----- START GENERATE PDF FILE ----- #
    echo "GENERATING $PDF_FILE";

    TITLE=${BOOKS[$BOOK]}
    SUBTITLE="translationNotes"

    # Create PDF
    pandoc --template=$TEMPLATE -S --toc --toc-depth=2 -V toc-depth=1 \
        --latex-engine="xelatex" \
        -V documentclass="scrartcl" \
        -V classoption="oneside" \
        -V geometry='hmargin=2cm' \
        -V geometry='vmargin=3cm' \
        -V title="$TITLE" \
        -V subtitle="$SUBTITLE" \
        -V date="$DATE" \
        -V tocdepth="2" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o "$PDF_FILE" "$HTML_FILE"

    echo "PDF FILE: $PDF_FILE"
    # ----- END GENERATE PDF FILE ------- #
}

# ---- EXECUTION BEGINS HERE ----- #

if [ -z "$1" ];
then
    echo "Please specify one or more books by adding their abbreviations, separated by spaces. Book abbreviations are as follows:";

    for key in "${!BOOKS[@]}"
    do
        echo "$key: ${BOOKS[$key]}";
    done |
    sort -n -k3

    exit 1;
fi

#first check all books given are valid
for arg in "$@"
do
    if [ ! ${BOOKS[${arg,,}]+_} ];
    then
        echo "Invalid book given: $arg"
        exit 1;
    fi
done

for arg in "$@"
do
    book_export ${arg,,}
done

echo "Done!"

