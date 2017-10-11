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
    echo "    -r ID       Resource ID of the Bible (e.g. ulb or udb) (required)"
    echo "    -l LANG     Language code (e.g. en) (required)"
    echo "    -b BOOK(s)  Book of the Bible (e.g. rev), 'ot': compiled Old Testament, 'nt': compiled New Testament, "
    echo "                'full': compiled full Bible. If not set, a PDF will be made for each book of the Bible"
    echo "    -o DIR      Add output location(s) for final PDF"
	echo "    -c COL#     Number of Columns (defaults to 2)"
	echo "    -f SIZE     Font size in pt"
	echo "    -t TAG      Tag of the repo to be checked out on DCS"
	echo "    -k HTML     Adds the given HTML between chunks"
    echo "    -d          Show debug messages while running script"
    echo "    -h -?       Show this help"
}

while getopts "t:l:r:m:b:o:df:k:h?" opt; do
    case $opt in
        l) LANGUAGE=$OPTARG;;
        r) RESOURCE=$OPTARG;;
        b) BOOKS+=("$OPTARG");;
        o) OUTPUTS+=("$OPTARG");;
        d) DEBUG=true;;
        c) NUM_COLS=$OPTARG;;
        f) FONT_SIZE=$OPTARG;;
        k) CHUNK_DIVIDER=$OPTARG;;
        t) TAG=$OPTARG;;
        [h?]) help && exit 1;;
    esac
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
: ${TOC_DEPTH=1}
: ${TAG='v11'}

$DEBUG && set -x

# Note out base location and create a temporary workspace
MY_DIR=$(cd $(dirname "$0") && pwd)
TOOLS_DIR=$(cd $(dirname "$0")/.. && pwd)
BUILD_DIR=$(mktemp -d --tmpdir "uwb_${LANGUAGE}_build_pdf.XXXXXX")
LOG="$BUILD_DIR/shell.log"
TEMPLATE="tools/uwb/tex/uwb_template.tex"
NOTOFILE="tools/udb-ulb/tex/noto-${LANGUAGE}.tex"

source "$MY_DIR/../general_tools/bible_books.sh"

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "export_md_to_pdf.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

echo $WORKING_DIR

# Change to our own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR" > /dev/null

# link tools folder
ln -sf "${MY_DIR}/.." ./tools

repo="${LANGUAGE}_${RESOURCE}"
url="https://git.door43.org/Door43/${repo}/archive/${TAG}.zip"

wget $url -O "./${repo}.zip"
unzip -qo "./${repo}.zip"

echo "Checked out repo files:"
ls "${repo}"

version=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.version'`
issued_date=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.issued'`
title=`yaml2json "${repo}/manifest.yaml" | jq -r '.dublin_core.title'`
checking_level=`yaml2json "${repo}/manifest.yaml" | jq -r '.checking.checking_level'`

echo "Current '$repo' Resource is at: ${url}"
echo "Current '$repo' Version is at: ${version}"

if [ "$NUM_COLS" == "2" ];
then
  multicols='-V multicols="true"'
else
  multicols=""
fi

# Reload fonts in case any were added recently
export OSFONTDIR="/usr/share/fonts/google-noto;/usr/share/fonts/noto-fonts/hinted;/usr/local/share/fonts;/usr/share/fonts"
#mtxrun --script fonts --reload
#if ! mtxrun --script fonts --list --all | grep -q noto; then
#    mtxrun --script fonts --reload
#    context --generate
#    if ! mtxrun --script fonts --list --all | grep -q noto; then
#        echo 'Noto fonts not found, bailing...'
#        exit 1
#    fi
#fi

pushd "$BUILD_DIR"
ln -sf "$TOOLS_DIR"

if [ -z "${BOOKS// }" ];
then
    # If no -b was used, we want to generate a PDF for EACH BOOK of the Bible
    BOOKS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
fi

for book in "${BOOKS[@]}"; do
    if [ -z "${RESOURCE// }" ];
    then
        print "Cannot get the resource id for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${title// }" ];
    then
        print "Cannot get the title for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${issued_date// }" ];
    then
        print "Cannot get the publish date for the Bible '$RESOURCE'"
        exit 1
    elif [ -z "${checking_level// }" ];
    then
        print "Cannot get the checking level for the Bible '$RESOURCE'"
        exit 1
    fi

    if [ "${book}" == "full" ];
    then
        subtitle="Old \\& New Testaments"
        book_arg=""
        basename="${LANGUAGE}_${RESOURCE}_v${version}"
    elif [ $book == 'ot' ];
    then
        book_arg='-b gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal'
        subtitle="Old Testament"
        basename="${LANGUAGE}_${RESOURCE}_v${version}_ot"
    elif [ $book == 'nt' ];
    then
        book_arg='-b mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev'
        subtitle='New Testament'
        basename="${LANGUAGE}_${RESOURCE}_v${version}_nt"
    else
        book_arg="-b $book"
        usfm_num=${BOOK_NUMBERS[$book]}
        sort_num=usfm_num
        if [ $sort_num -gt 40 ];
        then
            sort_num=$sort_num-1
        fi
        project_index=$sort_num-1
        book_name=`yaml2json "${repo}/manifest.yaml" | jq -r ".projects[${project_index}].title"`
        if [ -z "${book_name// }" ];
        then
            print "Cannot get the name of the book for '${book}'"
            exit 1
        fi
        subtitle=$book_name
        basename="${LANGUAGE}_$(printf "%02d" ${usfm_num})_${book^^}_v${version}"
        TOC_DEPTH=2
    fi

    # Run python (helpers/export_usfm_to_html.py) to generate the .html files
    python -m tools.udb-ulb.helpers.export_usfm_to_html -s "${WORKING_DIR}/${repo}" -l $LANGUAGE -r ${RESOURCE} $book_arg -o "$BUILD_DIR/$basename.html"

    sed -i -e "s/<span class=\"chunk-break\"\/>/<span class=\"chunk-break\"\/>$CHUNK_DIVIDER/g" "$BUILD_DIR/$basename.html"

    # Generate PDF with PANDOC
    LOGO="https://unfoldingword.org/assets/img/icon-${RESOURCE}.png"
    response=$(curl --write-out %{http_code} --silent --output logo.png "$LOGO");
    if [ $response -eq "200" ];
    then
      LOGO_FILE="-V logo=logo.png"
    fi

    CHECKING="https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level${checking_level}-128px.png"
    response=$(curl --write-out %{http_code} --silent --output checking.png "$CHECKING")
    if [ $response -eq "200" ];
    then
      CHECKING_FILE="-V checking_level=checking.png"
    fi

    echo "$title" > title.txt
    echo "$subtitle" > subtitle.txt

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
        $multicols \
        $LOGO_FILE \
        $CHECKING_FILE \
        -V notofile="$NOTOFILE" \
        -V version="$version" \
        -V publish_date="$issued_date" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o "${basename}.pdf" "${basename}.html"

    # Send to requested output location(s)
    for dir in "${OUTPUTS[@]}"; do
        install -Dm 0644 "${basename}.pdf" "$dir/${basename}.pdf"
        echo "GENERATED FILE: $dir/${basename}.pdf"
    done
done
