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


### To do:
# -> Fix pandoc to support images, or fix pandoc-dev list spacing
# -> Fix ulem not on server

# ENVIRONMENT VARIABLES:
# DEBUG - true/false -  If true, will run "set -x", will make $USE_EXISTING_FILES true by default
# USE_EXISTING_FILES - true/false - If true will keep & use existing .html files in $WORKING_DIR (won't fentch them again) so you need to remove them yourself if you want them regenerated
#
# TOOLS_DIR - Directory of the "tools" repo where scripts and templates resides. Defaults to the parent directory of this script
# WORKING_DIR - Directory where all HTML files for tN, tQ, tW, tA are collected and then a full HTML file is made before conversion to PDF, defaults to a system suggested temp location
# OUTPUT_DIR - Directory to put the PDF, defaults to the current working directory
# BASE_URL - URL for the _export/xhtmlbody to get Dokuwiki content, defaults to 'https://door43.org/_export/xhtmlbody'
# NOTES_URL - URL for getting translationNotes, defaults to $BASE_URL/en/bible/notes
# TEMPLATE - Location of the TeX template for Pandoc, defaults to "$TOOLS_DIR/general_tools/pandoc_pdf_template.tex

# Set script to die if any of the subprocesses exit with a fail code. This
# catches a lot of scripting mistakes that might otherwise only show up as side
# effects later in the run (or at a later time). This is especially important so
# we know out temp dir situation is sane before we get started.
set -e

# Instantiate a DEBUG flag (default to false). This enables output usful durring
# script development or later DEBUGging but not normally needed durring
# production runs. It can be used by calling the script with the var set, e.g.:
#     $ DEBUG=true ./uwb/pdf_create.sh <book>
: ${DEBUG:=false}

: ${USE_EXISTING_FILES:=$DEBUG}
: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}
: ${UW_NOTES_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes}
: ${UW_QUESTIONS_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/questions/comprehension}
: ${OUTPUT_DIR:=$(pwd)}
: ${BASE_URL:=https://door43.org/_export/xhtmlbody}
: ${NOTES_URL:=$BASE_URL/en/bible/notes}
: ${QUESTIONS_URL:=$BASE_URL/en/bible/questions/comprehension}
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

DATE=`date +"%Y-%m-%d"`

declare -A BOOKS
BOOKS=(
    ['gen']='Genesis'
    ['exo']='Exodus'
    ['lev']='Leviticus'
    ['num']='Numbers'
    ['deu']='Deuteronomy'
    ['jos']='Joshua'
    ['jdg']='Judges'
    ['rut']='Ruth'
    ['1sa']='1 Samuel'
    ['2sa']='2 Samuel'
    ['1ki']='1 Kings'
    ['2ki']='2 Kings'
    ['1ch']='1 Chronicles'
    ['2ch']='2 Chronicles'
    ['ezr']='Ezra'
    ['neh']='Nehemiah'
    ['est']='Esther'
    ['job']='Job'
    ['psa']='Psalms'
    ['pro']='Proverbs'
    ['ecc']='Ecclesiastes'
    ['sng']='Song of Solomon'
    ['isa']='Isaiah'
    ['jer']='Jeremiah'
    ['lam']='Lamentations'
    ['ezk']='Ezekiel'
    ['dan']='Daniel'
    ['hos']='Hosea'
    ['jol']='Joel'
    ['amo']='Amos'
    ['oba']='Obadiah'
    ['jon']='Jonah'
    ['mic']='Micah'
    ['nam']='Nahum'
    ['hab']='Habakkuk'
    ['zep']='Zephaniah'
    ['hag']='Haggai'
    ['zec']='Zechariah'
    ['mal']='Malachi'
    ['mat']='Matthew'
    ['mrk']='Mark'
    ['luk']='Luke'
    ['jhn']='John'
    ['act']='Acts'
    ['rom']='Romans'
    ['1co']='1 Corinthians'
    ['2co']='2 Corinthians'
    ['gal']='Galatians'
    ['eph']='Ephesians'
    ['php']='Philippians'
    ['col']='Colossians'
    ['1th']='1 Thessalonians'
    ['2th']='2 Thessalonians'
    ['1ti']='1 Timothy'
    ['2ti']='2 Timothy'
    ['tit']='Titus'
    ['phm']='Philemon'
    ['heb']='Hebrews'
    ['jas']='James'
    ['1pe']='1 Peter'
    ['2pe']='2 Peter'
    ['1jn']='1 John'
    ['2jn']='2 John'
    ['3jn']='3 John'
    ['jud']='Jude'
    ['rev']='Revelation'
)

book_export () {
    BOOK=$1

    if [ ! ${BOOKS[$BOOK]+_} ];
    then
        echo "Invalid book given: $BOOK"
        exit 1;
    fi

    CL_FILE="${BOOK}_cl.html" # Copyrights & Licensing
    TN_FILE="${BOOK}_tn.html" # translationNotes
    TQ_FILE="${BOOK}_tq.html" # translationQuestions
    TW_FILE="${BOOK}_tw.html" # translationWords
    TA_FILE="${BOOK}_ta.html" # translationAcademy
    HTML_FILE="${BOOK}_all.html" # Compilation of all above HTML files
    TMP_FILE="${BOOK}_temp.html" # temp stuff
    LINKS_FILE="${BOOK}_links.sed" # SED commands for links
    PDF_FILE="$OUTPUT_DIR/tN_${BOOK^^}_$DATE.pdf"

    if ! $USE_EXISTING_FILES;
    then
        echo rm -f $CL_FILE $TN_FILE $TQ_FILE $TA_FILE $TMP_FILE $LINKS_FILE $HTML_FILE
    fi

    # HTML_FILE AND TMP_FILE need to be removed, and make sure there is a LINKS_FILE for links
    rm -f $HTML_FILE
    rm -f $TMP_FILE
    touch $LINKS_FILE

    # Get Copyrights & Licensing page
    if ! $USE_EXISTING_FILES || [ ! -e $CL_FILE ];
    then
        echo "GENERATING $CL_FILE"

        wget -U 'me' "$BASE_URL/en/legal/license" -O - >> $CL_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' $CL_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' $CL_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' $CL_FILE
    fi

    # Get all the translationNots for the given book
    if ! $USE_EXISTING_FILES || [ ! -e $TN_FILE ];
    then
        echo "GENERATING $TN_FILE"

        touch $TMP_FILE

        find "$UW_NOTES_DIR/$BOOK" -type f -path "*[0-9]/*[0-9]*.txt" -printf '%P\n' |
            grep -v 'asv-ulb' |
            sort -u |
            while read f; do
                wget -U 'me' "$NOTES_URL/$BOOK/${f%%.txt}" -O - |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    >> $TMP_FILE
            done

        touch $TN_FILE

        # Remove TFT
        TFT=false
        while read line; do
            if [[ "$line" == '<h2 class="sectionedit2" id="tft">TFT:</h2>' ]]; then
                TFT=true
                continue
            fi
            if [[ "${line:0:25}" == '<!-- EDIT2 SECTION "TFT:"' ]]; then
                TFT=false
                continue
            fi
            $TFT && continue
            echo "$line" >> $TN_FILE
        done < $TMP_FILE

        rm -f $TMP_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TN_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TN_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TN_FILE
    fi

    # Get all the translationQuestions for the given book
    if ! $USE_EXISTING_FILES || [ ! -e $TQ_FILE ];
    then
        echo "GENERATING $TQ_FILE"

        touch $TQ_FILE

        find "$UW_QUESTIONS_DIR/$BOOK" -type f -path "*[0-9].txt" -printf '%P\n' |
            sort |
            while read f; do
                wget -U 'me' "$QUESTIONS_URL/$BOOK/${f%%.txt}" -O - |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    > $TMP_FILE

                linkname=$(head -3 $TMP_FILE | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
                echo "s@/en/bible/questions/comprehension/$BOOK/${f%%.txt}\"@#$linkname\"@g" >> $LINKS_FILE

                cat $TMP_FILE >> $TQ_FILE
            done

        # REMOVE Comprehension Questions and Answers title
        sed -i -e '\@<h2.*Comprehension Questions and Answers<\/h2>@d' $TQ_FILE

        # REMOVE links at end of quesiton page to return to question home page
        sed -i -e "\@/en/bible/questions/comprehension/$BOOK/home@d" $TQ_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TQ_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TQ_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TQ_FILE
    fi

    # Get all the translationWords that exist in the already fetched translationNotes for the given book
    if ! $USE_EXISTING_FILES || [ ! -e $TW_FILE ];
    then
        echo "GENERATING $TW_FILE"

        touch $TW_FILE

        # Get the linked key terms
        for term in $(grep -oPh '"\/en\/obe.*?"' $TN_FILE | tr -d '"' | sort -u ); do
            wget -U 'me' ${BASE_URL}${term} -O - |
                grep -v ' href="\/tag\/' \
                > $TMP_FILE

            linkname=$(head -3 $TMP_FILE | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo "s@$term\"@#$linkname\"@g" >> $LINKS_FILE

            cat $TMP_FILE >> $TW_FILE
        done

        rm -f $TMP_FILE

        # Quick fix for getting rid of these Bible References lists in a table, removing table tags
        sed -i -e 's/^\s*<table class="ul">/<ul>/' $TW_FILE
        sed -i -e 's/^\s*<tr>//' $TW_FILE
        sed -i -e 's/^\s*<td class="page"><ul>\(.*\)<\/ul><\/td>/\1/' $TW_FILE
        sed -i -e 's/^\s*<\/tr>//' $TW_FILE
        sed -i -e 's/^\s*<\/table>/<\/ul>/' $TW_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TW_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TW_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TW_FILE
    fi

    # Get all the translationAcademy entries that exist in the already fetched translationNotes and translationWords for the given book
    if ! $USE_EXISTING_FILES || [ ! -e $TA_FILE ];
    then
        echo "GENERATING $TA_FILE"

        touch $TA_FILE

        # Get the linked tA
        grep -oPh '"\/en\/ta.*?"' $TN_FILE $TW_FILE $TQ_FILE |
            tr -d '"' |
            sort -u |
            sed 's!door43.org/en/!door43.org/_export/xhtmlbody/en/!' |
            while read ta; do
                wget -U 'me' ${BASE_URL}${ta} -O - |
                    grep -v ' href="\/tag\/' \
                    > $TMP_FILE

                linkname=$(head -3 $TMP_FILE | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
                echo -n 's/' >> $LINKS_FILE
                echo -n $ta | sed -e 's/[]\/$*.^|[]/\\&/g' >> $LINKS_FILE
                echo -n '"/#' >> $LINKS_FILE
                echo -n "$linkname" >> $LINKS_FILE
                echo '"/g' >> $LINKS_FILE

                cat $TMP_FILE >> $TA_FILE
            done

        rm -f $TMP_FILE

        # get rid of the pad.door43.org links and the <hr> with it
        sed -i -e 's/^\s*<a href="https:\/\/pad\.door43\.org.*//' $TA_FILE
        sed -i -e 's/^<hr \/>//' $TA_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TA_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TA_FILE
        sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TA_FILE
     fi

     # Compile all the above CL, tN, tQ, tW, and tA HTML files into one with headers
     echo "GENERATING $HTML_FILE"

     echo '<h1>Copyrights & Licensing</h1>' >> $HTML_FILE
     cat $CL_FILE >> $HTML_FILE

     echo '<h1>translationNotes</h1>' >> $HTML_FILE
     cat $TN_FILE >> $HTML_FILE

     echo '<h1>translationQuestions</h1>' >> $HTML_FILE
     cat $TQ_FILE >> $HTML_FILE

     echo '<h1>translationWords</h1>' >> $HTML_FILE
     cat $TW_FILE >> $HTML_FILE

     echo '<h1>translationAcademy</h1>' >> $HTML_FILE
     cat $TA_FILE >> $HTML_FILE

    # Link Fixes
    sed -i -f $LINKS_FILE $HTML_FILE
    sed -i -e 's/\/en\/bible.*"/"/' $HTML_FILE
    sed -i -e 's/\/en\/obs.*"/"/' $HTML_FILE

    # Cleanup
    sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
        -e 's/<\/span>/<\/span> /g' -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
        $HTML_FILE
#        -e '/jpg"/d' \
#        -e 's/"\/_media/"https:\/\/door43.org\/_media/g' \

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
        -V mainfont="Noto Sans" \
        -V sansfont="Noto Sans" \
        -o $PDF_FILE $HTML_FILE

    echo "See $PDF_FILE (generated files: $WORKING_DIR)"
}

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

