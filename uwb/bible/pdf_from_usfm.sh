#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

set -e

# Process command line options
while getopts "dl:v:b:s:o:w:t:u:i:f:" opt; do
    case $opt in
        d) DEBUG=true;;
        l) lang=$OPTARG;;
        v) ver=$OPTARG;;
        b) book=$OPTARG;;
        f) SPECIAL_FONT=$OPTARG;;
        w) WORKING_DIR=$OPTARG;;
        o) OUTPUT_DIR=$OPTARG;;
        t) BOOK_TITLE=$OPTARG;;
        u) USFM_TOOLS_DIR=$OPTARG;;
        i) USFM_DIR=$OPTARG;;
    esac
done

: ${DEBUG:=false}

$DEBUG && set -x

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../.. && pwd)}

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "uwb_pdf_from_usfm.${lang}.${ver}.${book}.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi
pushd "$WORKING_DIR"

: ${USFM_TOOLS_DIR:=$(cd $TOOLS_DIR/../USFM-Tools && pwd)}

: ${OUTPUT_DIR:=$(pwd)}

case $ver in
  udb) VERSION_TITLE="Unlocked Dynamic Bible";;
  ulb) VERSION_TITLE="Unlocked Literal Bible";;
  *) VERSION_TITLE=${ver^^}
esac

source "$TOOLS_DIR/general_tools/bible_books.sh"

if [ $book ];
then
    BASENAME="${lang}-${ver}-${book}"
    if [ ${BOOK_NAMES[$book]+_} ];
    then
        : ${BOOK_TITLE:="${BOOK_NAMES[$book]}"}
    fi
else
    BASENAME="${lang}-${ver}"
fi

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

python ${USFM_TOOLS_DIR}/transform.py --target=singlehtml --usfmDir=${USFM_DIR} --builtDir=${WORKING_DIR} --name=${BASENAME}

PUBLISH_DATE=$(date +"%Y-%m-%d")
VERSION=1
CHECKING_LEVEL=1
TOC_DEPTH=2
TEMPLATE="$TOOLS_DIR/uwb/tex/uwb_from_usfm_template.tex"
NOTOFILE="$TOOLS_DIR/uwb/tex/noto-${lang}.tex"

# Generate PDF with PANDOC
curl -o "logo.png" "https://unfoldingword.org/assets/img/icon-${ver}.png"
curl -o "checking.png" "https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level${CHECKING_LEVEL}-128px.png"

# Create PDF
pandoc \
    -S \
    --latex-engine="xelatex" \
    --template="$TEMPLATE" \
    --toc \
    --toc-depth="$TOC_DEPTH" \
    -V documentclass="scrartcl" \
    -V classoption="oneside" \
    -V geometry='hmargin=2cm' \
    -V geometry='vmargin=3cm' \
    -V logo="logo.png" \
    -V title="$VERSION_TITLE" \
    -V subtitle="$BOOK_TITLE" \
    -V checking_level="$CHECKING_LEVEL" \
    -V version="$VERSION" \
    -V publish_date="$PUBLISH_DATE" \
    -V mainfont="Noto Serif" \
    -V sansfont="Noto Sans" \
    -V specialfont="$SPECIAL_FONT" \
    -V notofile="$NOTOFILE" \
    -o "${OUTPUT_DIR}/${BASENAME}.pdf" "${WORKING_DIR}/${BASENAME}.html" && echo "\nDone. PDF created at ${OUTPUT_DIR}/${BASENAME}.pdf"


