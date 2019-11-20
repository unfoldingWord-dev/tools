#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <rich.mahn@unfoldingword.org>
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
# BASE_URL - URL for the _export/xhtmlbody to get Dokuwiki content, defaults to 'https://door43.org/_export/xhtmlbody'
# TEMPLATE - Location of the TeX template for Pandoc, defaults to "$TOOLS_DIR/general_tools/pandoc_pdf_template.tex

# Instantiate a DEBUG flag (default to false). This enables output usful durring
# script development or later DEBUGging but not normally needed durring
# production runs. It can be used by calling the script with the var set, e.g.:
#     $ DEBUG=true ./uwb/pdf_create.sh <book>

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}

export PATH=$PATH:/usr/local/texlive/2015/bin/x86_64-linux

FILE_TYPES=()
BOOKS_TO_PROCESS=()

VALID_FILE_TYPES=(pdf docx html tex txt text)

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

#gather command-line arguments
while [[ $# > 0 ]]
do
    arg="$1"
    case $arg in
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
        *)
            if [ ! ${BOOK_NAMES[${arg,,}]+_} ];
            then
                if [ ${arg,,} = "ot" ];
                then
                    BOOKS_TO_PROCESS+=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal)
                elif [ ${arg,,} = "nt" ];
                then
                    BOOKS_TO_PROCESS+=(mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
                elif [ ${arg,,} = "all" ];
                then
                    BOOKS_TO_PROCESS+=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
                else
                    echo "Invalid book given: $arg"
                    exit 1;
                fi
            else
                BOOKS_TO_PROCESS+=("$arg")
            fi
        ;;
    esac
    shift # past argument or value
done

: ${DEBUG:=false}
: ${LANGUAGE:=en}

: ${TEMPLATE:=$TOOLS_DIR/general_tools/pandoc_pdf_template.tex}

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}

: ${CL_DIR:=$LANGUAGE/legal/license}
: ${TN_DIR:=$LANGUAGE/bible/notes}
: ${TQ_DIR:=$LANGUAGE/bible/questions/comprehension}
: ${TW_DIR:=$LANGUAGE/obe}
: ${TA_DIR:=$LANGUAGE/ta}
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

book_export () {
    book=$1

    if [ ! ${BOOK_NAMES[$book]+_} ];
    then
        echo "Invalid book given: $book"
        exit 1;
    fi

    TN_FILE="${LANGUAGE}_${book}_tn.html" # translationNotes
    TQ_FILE="${LANGUAGE}_${book}_tq.html" # translationQuestions
    TW_FILE="${LANGUAGE}_${book}_tw.html" # translationWords
    TA_FILE="${LANGUAGE}_${book}_ta.html" # translationAcademy
    BAD_LINKS_FILE="${LANGUAGE}_${book}_bad_links.txt"

    if $REGENERATE_HTML_FILES; then
        rm -f "$TN_FILE" "$TQ_FILE" "$TW_FILE" "$TA_FILE" "$BAD_LINKS_FILE" # We start fresh, only files that remain are any files retrieved with wget
    fi

    touch "$BAD_LINKS_FILE"

    # ----- START GENERATE tN PAGES ----- #
    if [ ! -e "$TN_FILE" ];
    then
        echo "GENERATING $TN_FILE"
        
        touch "$TN_FILE"
        
        find "$D43_BASE_DIR/$TN_DIR/$book" -mindepth 1 -maxdepth 1 -type d -name "[0-9]*" -printf '%P\n' |
            sort -u |
            while read chapter;
            do
                dir="$TN_DIR/$book/$chapter";
                mkdir -p "$dir"
        
                find "$D43_BASE_DIR/$dir" -mindepth 1 -maxdepth 1 -type f \( -name "[0-9]*.txt" -or -name "intro.txt" -or -name "tatopics.txt" -or -name "words.txt" \) \( -exec grep -q 'tag>.*publish' {} \; -or -not -exec grep -q 'tag>.*draft' {} \; \) -printf '%P\n' |
                    grep -v 'asv-ulb' |
                    sort -u |
                    while read f; do
                        section=${f%%.txt}
        
                        # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
                        if $REDOWNLOAD_FILES || [ ! -e "$dir/$section.html" ] || [ "$dir/$section.html" -ot "$D43_BASE_DIR/$dir/$section.txt" ];
                        then
                            set +e
                            wget -U 'me' "$D43_BASE_URL/$dir/$section" -O "$dir/$section.html"
        
                            if [ $? != 0 ];
                            then
                                rm "$dir/$section.html";
                                echo "$D43_BASE_URL/$dir/$section ($TN_FILE)" >> "$BAD_LINKS_FILE"
                            fi
                            set -e
                        fi
        
                        if [ -e "$dir/$section.html" ];
                        then
                            cat "$dir/$section.html" >> "$TN_FILE"
                        else
                            echo "<h1>$book $chapter:$section - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$dir/$section - page does not exist</p>"
                        fi
                    done
            done
    else
        echo "NOTE: $TN_FILE already generated."
    fi
    # ----- END GENERATE tN PAGES ------- #

    # ----- START GENERATE tQ PAGES ----- #
    if [ ! -e "$TQ_FILE" ];
    then
        echo "GENERATING $TQ_FILE"
        
        touch "$TQ_FILE"
        
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
                    echo "<h1>$book $chapter - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$dir/$chapter - page does not exist</p>" 
                fi
            done
    else
        echo "NOTE: $TQ_FILE already generated."
    fi
    # ----- END GENERATE tQ PAGES ------- #

    # ----- START GENERATE tW PAGES ----- #
    if [ ! -e "$TW_FILE" ];
    then
        echo "GENERATING $TW_FILE"
        
        touch "$TW_FILE"
        
        # Get the linked key terms
        for url in $(grep -oPh "\"\/$LANGUAGE\/obe.*?\"" "$TN_FILE" | tr -d '"' | sort -u);
        do
            dir=${url#/} # remove preceeding /
            dir=${dir%/*} # remove term from dir
            term=${url##*/}
        
            mkdir -p "$dir"
        
            # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
            if $REDOWNLOAD_FILES || [ ! -e "$dir/$term.html" ] || [ "$dir/$term.html" -ot "$D43_BASE_DIR/$dir/$term.txt" ];
            then
                set +e
                wget -U 'me' "$D43_BASE_URL/$dir/$term" -O "$dir/$term.html"
        
                if [ $? != 0 ];
                then
                    rm "$dir/$term.html";
                    echo "$D43_BASE_URL/$dir/$term ($TW_FILE)" 
                    echo "$D43_BASE_URL/$dir/$term ($TW_FILE)" >> "$BAD_LINKS_FILE"
                fi
                set -e
            fi
        
            if [ -e "$dir/$term.html" ];
            then
		cat "$dir/$term.html" >> "$TW_FILE"
            else
                echo "<h1>$term - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$dir/$term - page does not exist</p>"
            fi
        done
    else
        echo "NOTE: $TW_FILE already generated."
    fi
    # ----- END GENERATE tW PAGES ------- #

    # ----- START GENERATE tA PAGES ----- #
    if [ ! -e "$TA_FILE" ];
    then
        echo "GENERATING $TA_FILE"
        
        touch "$TA_FILE"
        
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
                if $REDOWNLOAD_FILES || [ ! -e "$dir/$term.html" ] || [ "$dir/$term.html" -ot "$D43_BASE_DIR/$dir/$term.txt" ];
                then
                    set +e
                    wget -U 'me' "$D43_BASE_URL/$dir/$term" -O "$dir/$term.html"
        
                    if [ $? != 0 ];
                    then
                        rm "$dir/$term.html";
                        echo "$D43_BASE_URL/$dir/$term ($TA_FILE)" 
                        echo "$D43_BASE_URL/$dir/$term ($TA_FILE)" >> "$BAD_LINKS_FILE"
                    fi
                    set -e
                fi
        
                if [ -e "$dir/$term.html" ];
                then
                    cat "$dir/$term.html" |
                        grep -v ' href="\/tag\/' >> "$TA_FILE"
                else
                    echo "<h1>$term - MISSING - CONTENT UNAVAILABLE</h1><p>Unable to get content from $D43_BASE_URL/$dir/$section - page does not exist</p>" 
                fi
            done
    else
        echo "NOTE: $TA_FILE already generated."
    fi
    # ----- END GENERATE tA PAGES ------- #
}

# ---- EXECUTION BEGINS HERE ----- #

if [ ${#BOOKS_TO_PROCESS[@]} -eq 0 ];
then
    echo "Please specify one or more books by adding their abbreviations, separated by spaces. Book abbreviations are as follows:";

    for key in "${!BOOK_NAMES[@]}"
    do
        echo "$key: ${BOOK_NAMES[$key]}";
    done |
    sort -n -k3

    exit 1;
fi

if [ ${#FILE_TYPES[@]} -eq 0 ];
then
    FILE_TYPES=(pdf)
fi

for book in "${BOOKS_TO_PROCESS[@]}"
do
    book_export ${book,,}
done

echo "Done!"
