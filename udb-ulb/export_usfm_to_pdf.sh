#!/usr/bin/env bash
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  dboerschlein
#  Jesse Griffin <jesse@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>
#  Richard Mahn <rich.mahn@unfoldingword.org>

## GET SET UP ##

# Fail if _any_ command goes wrong
set -e

help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "    -r       Resourc ID of the Bible (e.g. ulb or udb) (required)"
    echo "    -l       Language code (e.g. en) (required)"
    echo "    -b       Book of the Bible (e.g. rev), 'ot': compiled Old Testament, 'nt': compiled New Testament, "
    echo "             none: PDF for each book of the Bible, 'full': compiled full Bible"
    echo "    -d       Show debug messages while running script"
    echo "    -o DIR   Add output location(s) for final PDF"
	echo "    -c COL#  Number of Columns (defaults to 2)"
	echo "    -f SIZE  Font size in pt"
    echo "    -h       Show this help"
	echo "    --chunk-divider HTML   Adds the given HTML between chunks"
    echo "Notes:"
    echo "    Option flags whose values are marked '(s)' may be specified multiple times"
}

while test $# -gt 0; do
    case "$1" in
        -l|--lang) shift; LANGUAGE=$1;;
        -r|--resource) shift; RESOURCE=$1;;
        -b|--book) shift; BOOKS=("${BOOKS[@]}" "$1");;
        -o|--output) shift; OUTPUTS=("${OUTPUTS[@]}" "$1");;
        -d|--debug) DEBUG=true;;
        -c) shift; NUM_COLS=$1;;
        -f) shift; FONT_SIZE=$1;;
        --chunk-divider) shift;CHUNK_DIVIDER=$1;;
        -[h?]) help && exit 1;;
    esac
    shift;
done

# Setup variable defaults in case flags were not set
: ${DEBUG=false}
: ${LANGUAGE='en'}
: ${RESOURCE='udb'}
: ${BOOKS[0]=""}
: ${OUTPUTS[0]=$(pwd)}
: ${CHUNK_DIVIDER=''}
: ${NUM_COLS=2}
: ${FONT_SIZE=12}

# Note out base location and create a temporary workspace
MYDIR=$(cd $(dirname "$0") && pwd)
TOOLSDIR=$(cd $(dirname "$0")/.. && pwd)
BUILDDIR=$(mktemp -d --tmpdir "uwb_${LANGUAGE}_build_pdf.XXXXXX")
LOG="$BUILDDIR/shell.log"
TEMPLATE="tools/uwb/tex/uwb_template.tex"
NOTOFILE="tools/udb-ulb/tex/noto-${LANGUAGE}.tex"

if [ "$NUM_COLS" == "2" ];
then
  MULTICOLS='-V multicols="true"'
else
  MULTICOLS=""
fi

# Output info about every command (and don't clean up on exit) if in debug mode
$DEBUG && set -x
$DEBUG || trap 'cd "$MYDIR";rm -rf "$BUILDDIR"' EXIT SIGHUP SIGTERM


# Reload fonts in case any were added recently
export OSFONTDIR="/usr/share/fonts/google-noto;/usr/share/fonts/noto-fonts/hinted;/usr/local/share/fonts;/usr/share/fonts"
#mtxrun --script fonts --reload
if ! mtxrun --script fonts --list --all | grep -q noto; then
    mtxrun --script fonts --reload
    context --generate
    if ! mtxrun --script fonts --list --all | grep -q noto; then
        echo 'Noto fonts not found, bailing...'
        exit 1
    fi
fi

pushd "$BUILDDIR"
ln -sf "$TOOLSDIR"

if [ -z "${BOOKS// }" ];
then
    # If no -b was used, we want to generate a PDF for EACH BOOK of the Bible
    BOOKS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
fi

for BOOK in "${BOOKS[@]}"; do
    TITLE=$(tools/catalog/v3/catalog_query.py -l ${LANGUAGE} -r ${RESOURCE} -k title);
    PUBLISH_DATE=$(date -d $(tools/catalog/v3/catalog_query.py -l ${LANGUAGE} -r ${RESOURCE} -k issued) +"%Y-%m-%d")
    VERSION=$(tools/catalog/v3/catalog_query.py -l ${LANGUAGE} -r ${RESOURCE} -k version)
    CHECKING_LEVEL=$(tools/catalog/v3/catalog_query.py -l ${LANGUAGE} -r ${RESOURCE} -k checking:checking_level)
    TOC_DEPTH=1

    if [ -z "${RESOURCE// }" ];
    then
        print "Cannot get the resource id for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${TITLE// }" ];
    then
        print "Cannot get the title for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${PUBLISH_DATE// }" ];
    then
        print "Cannot get the publish date for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${CHECKING_LEVEL// }" ];
    then
        print "Cannot get the checking level for the Bible '$RESOURCE'"
        exit 1
    fi

    if [ $BOOK == 'full' ];
    then
        SUBTITLE="Old \\& New Testaments"
        BOOK_ARG=""
        BASENAME="${LANGUAGE}_${RESOURCE}_v${VERSION}"
    elif [ $BOOK == 'ot' ];
    then
        BOOK_ARG='-b gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal'
        SUBTITLE="Old Testament"
        BASENAME="${LANGUAGE}_${RESOURCE}_v${VERSION}_ot"
    elif [ $BOOK == 'nt' ];
    then
        BOOK_ARG='-b mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev'
        SUBTITLE='New Testament'
        BASENAME="${LANGUAGE}_${RESOURCE}_v${VERSION}_nt"
    else
        BOOK_ARG="-b $BOOK"
        NAME=$(tools/catalog/v3/catalog_query.py -l $LANGUAGE -r $RESOURCE -p $BOOK -k title);
        SORT=$(tools/catalog/v3/catalog_query.py -l $LANGUAGE -r $RESOURCE -p $BOOK -k sort);
        if [ -z "${NAME// }" ] || [ -z "${SORT}" ];
        then
            print "Cannot get the name of the book for '${BOOK}'"
            exit 1
        fi
        SUBTITLE=$NAME
        BASENAME="${LANGUAGE}_$(printf "%02d" ${SORT})_${BOOK^^}_v${VERSION}"
        TOC_DEPTH=2
    fi

    # Run python (helpers/export_usfm_to_html.py) to generate the .html files
    python -m tools.udb-ulb.helpers.export_usfm_to_html -l $LANGUAGE -r ${RESOURCE} $BOOK_ARG -o "$BUILDDIR/$BASENAME.html"

    sed -i -e "s/<span class=\"chunk-break\"\/>/<span class=\"chunk-break\"\/>$CHUNK_DIVIDER/g" "$BUILDDIR/$BASENAME.html"

    # Generate PDF with PANDOC
    LOGO="https://unfoldingword.org/assets/img/icon-${RESOURCE}.png"
    response=$(curl --write-out %{http_code} --silent --output logo.png "$LOGO");
    if [ $response -eq "200" ];
    then
      LOGO_FILE="-V logo=logo.png"
    fi

    CHECKING="https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level${CHECKING_LEVEL}-128px.png"
    response=$(curl --write-out %{http_code} --silent --output checking.png "$CHECKING")
    if [ $response -eq "200" ];
    then
      CHECKING_FILE="-V checking_level=checking.png"
    fi

    echo "$TITLE" > title.txt
    echo "$SUBTITLE" > subtitle.txt

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
        -V title="title.txt" \
        -V subtitle="subtitle.txt" \
        -V fontsize="$FONT_SIZE" \
        $MULTICOLS \
        $LOGO_FILE \
        $CHECKING_FILE \
        -V notofile="$NOTOFILE" \
        -V version="$VERSION" \
        -V publish_date="$PUBLISH_DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o "${BASENAME}.pdf" "${BASENAME}.html"

    # Send to requested output location(s)
    for dir in "${OUTPUTS[@]}"; do
        install -Dm 0644 "${BASENAME}.pdf" "$dir/${BASENAME}.pdf"
        echo "GENERATED FILE: $dir/${BASENAME}.pdf"
    done
done
