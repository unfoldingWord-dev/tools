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

set -e # die if errors

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)} # Tools directory, relative to this script

export PATH=/usr/local/texlive/2016/bin/x86_64-linux:$PATH

FILE_TYPES=()
VALID_FILE_TYPES=(pdf docx html tex txt text)

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

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

: ${DEBUG:=false}
: ${LANGUAGE:=en}

: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/uwb/tex/tn_tw_tq_template.tex}

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}

: ${TQ_DIR:=$LANGUAGE/bible/questions/comprehension}
: ${VERSION:=2}
: ${REGENERATE_HTML_FILES:=true}
: ${REDOWNLOAD_FILES:=false}

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

if [ ${#FILE_TYPES[@]} -eq 0 ];
then
    FILE_TYPES=(pdf)
fi

TQ_FILE="${LANGUAGE}_tq.html" # translationQuestions
HTML_FILE="${LANGUAGE}_tq_all.html" # Compilation of all above HTML files
OUTPUT_FILE="$OUTPUT_DIR/tq-v${VERSION}"
BOOKS_TO_PROCESS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)

if $REGENERATE_HTML_FILES; then
    rm -f "$TQ_FILE" "$HTML_FILE" "$OUTPUT_FILE".*  # We start fresh, only files that remain are any files retrieved with wget
fi

# ----- START GENERATE tQ PAGES ----- #
if [ ! -e "$TQ_FILE" ];
then
    echo "GENERATING $TQ_FILE"

    touch "$TQ_FILE"

    for book in "${BOOKS_TO_PROCESS[@]}"
    do
        dir="$TQ_DIR/$book"
        mkdir -p "$dir"

        find "$D43_BASE_DIR/$TQ_DIR/$book" -type f -name "[0-9]*.txt" -exec grep -q 'tag>.*publish' {} \; -printf '%P\n' |
            sort |
            while read f;
            do
                chapter=${f%%.txt}

                # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
                if $REDOWNLOAD_FILES || [ ! -e "$dir/$chapter.html" ] || [ "$dir/$chapter.html" -ot "$D43_BASE_DIR/$dir/$chapter.txt" ];
                then
                    set +e
                    wget -U 'me' "$D43_BASE_URL/$dir/$chapter" -O "$dir/$chapter.html"

                    if [ $? != 0 ];
                    then
                        rm "$dir/$chapter.html";
                        echo "$D43_BASE_URL/$dir/$chapter ($TQ_FILE)" >> "$BAD_LINKS_FILE"
                    fi
                    set -e
                fi

                if [ -e "$dir/$chapter.html" ];
                then
                    grep -v '<strong>.*&gt;<\/a><\/strong>' "$dir/$chapter.html" |
                        grep -v ' href="\/tag\/' >> "$TQ_FILE"
                else
                    echo "<h1>$book $chapter - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$dir/$chapter - page does not exist</p>" >> "$TQ_FILE"
                fi
            done

        # REMOVE Comprehension Questions and Answers title
        sed -i -e '\@<h2.*Comprehension Questions and Answers<\/h2>@d' "$TQ_FILE"
        sed -i -e 's@^A\.\(.*\)$@A.\1\n</p>\n\n<p>\n<hr/>@' "$TQ_FILE"
        sed -i -e 's@^\(Q?\|A\.\) @<b>\1</b> @' "$TQ_FILE"
        sed -i -e 's@>\([^>]\+\) 0*\([0-9]\+\) Translation Questions@>\1 \2@' "$TQ_FILE"

        # REMOVE links at end of quesiton page to return to question home page
        sed -i -e "\@/$dir/home@d" "$TQ_FILE"
    done
else
    echo "NOTE: $TQ_FILE already generated."
fi
# ----- END GENERATE tQ PAGES ------- #

# ----- START GENERATE HTML PAGE ----- #
if [ ! -e "$HTML_FILE" ];
then
    # Compile all the CL, & tQ HTML files into one with headers
    echo "GENERATING $HTML_FILE"

    echo '<h1>translationQuestions</h1>' >> "$HTML_FILE"
    cat "$TQ_FILE" >> "$HTML_FILE"
else
    echo "NOTE: $HTML_FILE already generated."
fi
# ----- END GENERATE HTML PAGES ------- #

# ----- START GENERATE OUTPUT FILES ----- #
TITLE="translationQuestions"

LOGO="https://unfoldingword.org/assets/img/icon-tq.png"
response=$(curl --write-out %{http_code} --silent --output logo-tq.png "$LOGO");
if [ $response -eq "200" ];
then
  LOGO_FILE="-V logo=logo-tq.png"
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
            -V subtitle="$SUBTITLE" \
            $LOGO_FILE \
            -V date="$DATE" \
            -V version="$VERSION.0" \
            -V mainfont="Noto Serif" \
            -V sansfont="Noto Sans" \
            -V linkcolor="Magenta" \
            -H "$FORMAT_FILE" \
            -o "$OUTPUT_FILE.$type" "$HTML_FILE"

        echo "GENERATED FILE: $OUTPUT_FILE.$type"
    else
        echo "NOTE: $OUTPUT_FILE.$type already generated."
    fi
done
# ----- END GENERATE OUTPUT FILES ------- #

echo "Done!"
