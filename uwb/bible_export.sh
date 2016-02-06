#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#
#  Description:
#  Gathers the HTML for ALL specified books on the command line ("ot" and "nt" and "all" work too) and compiles them into one file, then exports
#  them into a PDF or DOCX (specified with --type on the command line, defaults to PDF)
#
#  USAGE: bible_export.sh [-l|--language <language code>] [-t|--type pdf|docx|txt] [-b|-bible ulb|udb] [-v|--version v1|v2|ep] [<bible book code>|all|ot|nt]
#

set -e

# ENVIRONMENT VARIABLES:
# DEBUG - true/false -  If true, will run "set -x"
# TOOLS_DIR - Directory of the "tools" repo where scripts and templates resides. Defaults to the parent directory of this script
# WORKING_DIR - Directory where all HTML files for tN, tQ, tW, tA are collected and then a full HTML file is made before conversion to PDF, defaults to a system suggested temp location
# OUTPUT_DIR - Directory to put the PDF, defaults to the current working directory
# BASE_URL - URL for the _export/xhtmlbody to get Dokuwiki content, defaults to 'https://door43.org/_export/xhtmlbody'
# TEMPLATE - Location of the TeX template for Pandoc, defaults to "$TOOLS_DIR/general_tools/pandoc_pdf_template.tex

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

: ${DEBUG:=false}
: ${LANGUAGE:=en}
: ${BIBLE:=udb}
: ${VERSION:=ep}
: ${TOCDEPTH:=1}

FILE_TYPES=()
BOOKS_TO_PROCESS=()

#gather command-line arguments
while [[ $# > 0 ]]
do
    arg="$1"
    case $arg in
        --debug)
            DEBUG=true
        ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift # skip the next argument
        ;;
        -w|--working)
            WORKING_DIR="$2"
            shift # skip the next argument
        ;;
        -l|--lang|--language)
            LANGUAGE="$2"
            shift # skip the next argument
        ;;
        -v|--version)
            VERSION="${2,,}"
            shift # skip the next argument
        ;;
        -b|--bible)
            BIBLE="${2,,}"
            shift # skip the next argument
        ;;
        --tocdepth)
            TOCDEPTH=$2
            shift # past arguemnt
        ;;
        --title)
            TITLE=$2
            shift # past arguemnt
        ;;
        --subtitle)
            SUBTITLE=$2
            shift # past arguemnt
        ;;
        -t|--type)
            FILE_TYPES+=("${2,,}")
            shift # skip the next argument
        ;;
        *)
            if [ ! ${BOOK_NAMES[${arg,,}]+_} ];
            then
                if [ ${arg,,} = "all" ];
                then
                    BOOKS_TO_PROCESS+=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
                elif [ ${arg,,} = "ot" ];
                then
                    BOOKS_TO_PROCESS+=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal)
                elif [ ${arg,,} = "nt" ];
                then
                    BOOKS_TO_PROCESS+=(mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
                else
                    echo "Invalid book: $arg"
                    echo "Valid books: gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev"
                    exit 1;
                fi
            else
                BOOKS_TO_PROCESS+=("$arg")
            fi
        ;;
    esac
    shift # skip the next argument or value
done

: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/general_tools/pandoc_pdf_template.tex}

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}

: ${CL_DIR:=$LANGUAGE/legal/license}
: ${BIBLE_DIR:=$LANGUAGE/$BIBLE/$VERSION}


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
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

# Change to own own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR" > /dev/null

DATE=`date +"%Y-%m-%d"`

if [ ! -e $D43_BASE_DIR ];
then
    echo "The directory $D43_BASE_DIR does not exist. Can't continue. Exiting."
    exit 1;
fi

if [ ${#BOOKS_TO_PROCESS[@]} -eq 0 ];
then
    BOOKS_TO_PROCESS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
fi

if [ ${#FILE_TYPES[@]} -eq 0 ];
then
    FILE_TYPES=(pdf)
fi

if [ -z $TITLE ];
then
    if [ ${#BOOKS_TO_PROCESS[@]} == 66 ];
    then
        TITLE="HOLY BIBLE"
        FILENAME_TITLE="BIBLE"
    else
        if [ ${#BOOKS_TO_PROCESS[@]} == 39 ];
        then
            TITLE="OLD TESTAMENT"
            FILENAME_TITLE="OT"
        elif [ ${#BOOKS_TO_PROCESS[@]} == 27 ];
        then
            TITLE="NEW TESTAMENT"
            FILENAME_TITLE="NT"
        else
            TITLE=""
            FILENAME_TITLE=""
            for book in "${BOOKS_TO_PROCESS[@]}"
            do
                if [ ${#TITLE} -gt 0 ];
                then
                    TITLE+=", "
                    FILENAME_TITLE+="_"
                fi
                TITLE+="${BOOK_NAMES[$book]^^}"
                FILENAME_TITLE+="${book^^}"
            done
        fi
    fi
fi

if [ -z $SUBTITLE ];
then
    SUBTITLE="${BIBLE^^} ($VERSION)"
fi

if [ -z $FILENAME_TITLE ];
then
    FILENAME_TITLE=$TITLE
fi

FILENAME_TITLE=${FILENAME_TITLE//[^a-zA-Z0-9]/_}
FILENAME_TITLE=${FILENAME_TITLE:0:80}

CL_FILE="${LANGUAGE}_${BIBLE}_${VERSION}_${FILENAME_TITLE}_cl.html" # Copyrights & Licensing
BIBLE_FILE="${LANGUAGE}_${BIBLE}_${VERSION}_${FILENAME_TITLE}_bible.html" # Bible Text
HTML_FILE="${LANGUAGE}_${BIBLE}_${VERSION}_${FILENAME_TITLE}_all.html" # All Content
OUTPUT_FILE="$OUTPUT_DIR/${BIBLE^^}-${VERSION}-${FILENAME_TITLE}-${LANGUAGE^^}-$DATE"

rm -f "$CL_FILE" "$BIBLE_FILE" "$HTML_FILE" # We start fresh, only files that remain are any files retrieved with wget

# ----- START GENERATE CL PAGE ----- #
echo "GENERATING $CL_FILE"

touch "$CL_FILE"

mkdir -p "$CL_DIR"

# If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
if [ ! -e "$CL_DIR/uw.html" ] || [ "$CL_DIR/uw.html" -ot "$D43_BASE_DIR/$CL_DIR/uw.txt" ];
then
    set +e
    wget -U 'me' "$D43_BASE_URL/$CL_DIR/uw" -O "$CL_DIR/uw.html"

    if [ $? != 0 ];
    then
        rm "$CL_DIR/uw.html";
        echo "$D43_BASE_URL/$CL_DIR/uw ($CL_FILE)" >> "$BAD_LINKS_FILE"
    fi
    set -e
fi

if [ -e "$CL_DIR/uw.html" ];
then
    cat "$CL_DIR/uw.html" > "$CL_FILE"
else
    echo "<h1>Copyrights & Licensing - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$CL_DIR/uw - page does not exist</p>" >> "$TN_FILE"
fi

# increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$CL_FILE"
sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$CL_FILE"
sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h2/g' "$CL_FILE"
# ----- END GENERATE CL PAGES ------- #

# ----- START GENERATE BIBLE TEXT PAGES ----- #
echo "GENERATING $BIBLE_FILE"

touch "$HTML_FILE"

mkdir -p "$BIBLE_DIR"

for book in "${BOOKS_TO_PROCESS[@]}"
do
    if [ ! ${BOOK_NAMES[$book]+_} ];
    then
        echo "Invalid book given: $book"
        exit 1;
    fi

    usfm_file="$BIBLE_DIR/${BOOK_NUMBERS[$book]}-${book}.usfm"
    html_file="$BIBLE_DIR/${BOOK_NUMBERS[$book]}-${book}.html"

    # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
    if [ ! -e "$html_file" ] || [ "$html_file" -ot "$D43_BASE_DIR/$$usfm_file" ];
    then
        set +e
        wget -U 'me' "$D43_BASE_URL/$usfm_file" -O "$html_file"
    fi

    cat "$html_file" >> "$BIBLE_FILE"
done

# Makes all Chapter numbers into <h2> tags and write "Chapter" before the number
sed -i -e "s@<p class='usfm-flush' align='justify'><span class='usfm-c'><big class='usfm-c'><big class='usfm-c'><big class='usfm-c'><big class='usfm-c'>\([0-9]\+\)</big></big></big></big></span>\s*@<h2>Chapter \1</h2> <p class='usfm-flush' align='justify'>@ig" "$BIBLE_FILE"
# ----- END GENERATE BIBLE TEXT PAGES ------- #

# ----- START GENERATE HTML PAGE ----- #
 echo "GENERATING $HTML_FILE"

 echo '<h1>Copyrights & Licensing</h1>' > "$HTML_FILE"
 cat "$CL_FILE" >> "$HTML_FILE"

 cat "$BIBLE_FILE" >> "$HTML_FILE"
# ----- END GENERATE HTML PAGES ------- #

# ----- START LINK FIXES AND CLEANUP ----- #
# Cleanup
sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
    -e 's/<\/span>/<\/span> /g' -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
    -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' \
    -e "s/<hr>//ig" \
    "$HTML_FILE"
# ----- END LINK FIXES AND CLEANUP ------- #

# ----- START GENERATE OUTPUT FILES ----- #
for type in "${FILE_TYPES[@]}"
do
    echo "GENERATING $OUTPUT_FILE.$type";

    # Create PDF
    pandoc \
        -S \
        --template="$TEMPLATE" \
        --toc \
        --toc-depth="$TOCDEPTH" \
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
        -o "$OUTPUT_FILE.$type" "$HTML_FILE"

    echo "GENERATED FILE: $OUTPUT_FILE.$type"
done
# ----- END GENERATE OUTPUT FILES ------- #

echo "Done!"
