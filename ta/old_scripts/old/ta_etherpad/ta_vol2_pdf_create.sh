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
#  Richard Mahn <rich.mahn@unfoldingword.org>

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

: ${D43_BASE_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages}
: ${D43_CL_DIR:=$D43_BASE_DIR/legal}
: ${D43_TA_DIR:=$D43_BASE_DIR/ta}

: ${D43_BASE_URL:=https://door43.org/_export/xhtmlbody}
: ${D43_CL_URL:=$D43_BASE_URL/$LANGUAGE/legal}

: ${D43_TA_CHECKING_URL:=$LANGUAGE/ta/vol2/checking/toc_checkvol2}
: ${D43_TA_TRANSLATION_URL:=$LANGUAGE/ta/vol2/translate/toc_transvol2}
: ${D43_TA_TECH_URL:=$LANGUAGE/ta/vol2/tech/toc_techvol2}

#if [ ! -e $D43_BASE_DIR ];
#then
#    echo "The directory $D43_TA_DIR does not exist. Can't continue. Exiting."
#    exit 1;
#fi

DATE=`date +"%Y-%m-%d"`

CL_FILE="${LANGUAGE}_ta_vol2_cl.html" # Copyrights & License
TA_CHECKING_FILE="${LANGUAGE}_ta_vol2_checking.html"
TA_TRANSLATION_FILE="${LANGUAGE}_ta_vol2_translation.html"
TA_TECH_FILE="${LANGUAGE}_ta_vol2_tech.html"
HTML_FILE="${LANGUAGE}_ta_vol2_all.html" # Compilation of all above HTML files
LINKS_FILE="${LANGUAGE}_ta_vol2_links.sed" # SED commands for links
PDF_FILE="$OUTPUT_DIR/tA_Vol2_${LANGUAGE^^}_$DATE.pdf" # Outputted PDF file
TMP_FILE="${LANGUAGE}_ta_vol2_temp.html"

generate_file_from_toc () {
    toc_url=$1
    out_file=$2

    echo "GENERATING $out_file FROM $toc_url"

    mkdir -p "${toc_url%/*}"

    rm -f $out_file
    touch $out_file

    # If the file doesn't exist or is older than (-ot) the file in the Door43 repo, fetch the file
    if true || [ ! -e "${toc_url}.html" ] || [ "${toc_url}.html" -ot "${D43_BASE_DIR}/${toc_url}.txt" ];
    then
        wget -U 'me' "${D43_BASE_URL}/${toc_url}" -O "${toc_url}.html";
    fi

    while IFS='' read -r line || [[ -n "$line" ]]; do
        echo $line
        url=$(echo $line | grep -oP 'href=".*?"' | cut -f 2 -d '=' | tr -d '"')

        if [[ ! -z $url ]];
        then
            url=${url#/}
            level=$(echo $line | grep -oP 'class="level.*?"' | awk -F'level' '{print $2}' | tr -d '"')

            if [[ ! -z $level ]];
            then
                if [ ! -e "${url}.html" ] || [ "${url}.html" -ot "${D43_BASE_DIR}/${url}.txt" ];
                then
                    mkdir -p "${url%/*}"
                    wget -U 'me' "${D43_BASE_URL}/${url}" -O "${url}.html";
                fi

                linkname=$(head -3 "${url}.html" | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
                echo "s@/$url\"@#$linkname\"@g" >> "$LINKS_FILE"

                cat "${url}.html" > "$TMP_FILE"

                # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
                sed -i -e 's/<\(\/\)\{0,1\}h3/<\1h4/g' "$TMP_FILE"
                sed -i -e 's/<\(\/\)\{0,1\}h2/<\1h3/g' "$TMP_FILE"
                sed -i -e 's/<\(\/\)\{0,1\}h1/<\1h3/g' "$TMP_FILE"

                # now we inject the level of this page by changing the first to occurances of h# with h<level+1> to change open and closing tags
                sed -i -e "0,/<h[0-9]/s//<h$((level+1))/" "$TMP_FILE"
                sed -i -e "0,/<\\/h[0-9]/s//<\\/h$((level+1))/" "$TMP_FILE"

                cat "$TMP_FILE" >> "$out_file"
            fi
        fi
    done < "${toc_url}.html"
}

# ---- MAIN EXECUTION BEGINS HERE ----- #
    rm -f $CL_FILE $TA_CHECKING_FILE $TA_TRANSLATION_FILE $TA_TECH_FILE $TMP_FILE $LINKS_FILE $HTML_FILE # We start fresh, only files that remain are any files retrieved with wget

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

    # ----- GENERATE TA SECTIONS --------- #
    generate_file_from_toc $D43_TA_CHECKING_URL $TA_CHECKING_FILE
    generate_file_from_toc $D43_TA_TRANSLATION_URL $TA_TRANSLATION_FILE
    generate_file_from_toc $D43_TA_TECH_URL $TA_TECH_FILE
    # ----- EMD GENERATE TA INFO SECTION ----- #


    # ----- GENERATE COMPLETE HTML PAGE ----------- #
    echo "GENERATING $HTML_FILE"

    echo '<h1>Copyrights & Licensing</h1>' >> $HTML_FILE
    cat $CL_FILE >> $HTML_FILE

    echo '<h1>Checking Manual</h1>' >> $HTML_FILE
    cat $TA_CHECKING_FILE >> $HTML_FILE

    echo '<h1>Translation Manual</h1>' >> $HTML_FILE
    cat $TA_TRANSLATION_FILE >> $HTML_FILE

    echo '<h1>Technology Manual</h1>' >> $HTML_FILE
    cat $TA_TECH_FILE >> $HTML_FILE
    # ----- END GENERATE COMPLETE HTML PAGE --------#

    # ----- START LINK FIXES AND CLEANUP ----- #
    # Link Fixes
    sed -i -f "$LINKS_FILE" "$HTML_FILE"

    # Cleanup
    sed -i -e 's/<\/span>/<\/span> /g' $HTML_FILE
    sed -i -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' $HTML_FILE
    sed -i -e 's/ \(src\|href\)="\// \1="https:\/\/door43.org\//g' $HTML_FILE
    # ----- END LINK FIXES AND CLEANUP ------- #

    # ----- START GENERATING PDF FILE ----- #
    echo "GENERATING $PDF_FILE";

    TITLE='translationAcademy'

    SUBTITLE='Volume 2'

    # Create PDF
    pandoc \
        -S \
        --latex-engine="xelatex" \
        --template="$TEMPLATE" \
        --toc \
        --toc-depth=3 \
        -V documentclass="scrartcl" \
        -V classoption="oneside" \
        -V geometry='hmargin=2cm' \
        -V geometry='vmargin=3cm' \
        -V title="$TITLE" \
        -V subtitle="$SUBTITLE" \
        -V date="$DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o $PDF_FILE $HTML_FILE


    echo "PDF FILE: $PDF_FILE"
    echo "Done!"
