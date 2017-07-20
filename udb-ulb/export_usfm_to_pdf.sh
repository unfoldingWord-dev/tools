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
    echo "    -d       Show debug messages while running script"
    echo "    -o DIR   Add output location(s) for final PDF"
    echo "    -r LOC   Send build report to directory(s) or email address(s)"
    echo "    -t TAG   Add a tag to the output filename"
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
        -v|--version) shift; VER=$1;;
        -b|--bible) shift; BOOKS=("${BOOKS[@]}" "$1");;
        -o|--output) shift; OUTPUTS=("${OUTPUTS[@]}" "$1");;
        -r|--reportto) shift; REPORTTO=("${REPORTTO[@]}" "$1");;
        -t|--tag) shift; TAG=$1;;
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
: ${VER='udb'}
: ${BOOKS[0]=""}
: ${OUTPUTS[0]=$(pwd)}
: ${REPORTTO[0]=}
: ${TAG=}
: ${CHUNK_DIVIDER=''}
: ${NUM_COLS=2}
: ${FONT_SIZE=12}

# Note out base location and create a temporary workspace
MYDIR=$(cd $(dirname "$0") && pwd)
BUILDDIR=$(mktemp -d --tmpdir "uwb_${LANGUAGE}_build_pdf.XXXXXX")
LOG="$BUILDDIR/shell.log"
TEMPLATE="$MYDIR/uwb/tex/uwb_template.tex"
NOTOFILE="$MYDIR/uwb/tex/noto-${LANGUAGE}.tex"

if [ "$NUM_COLS" == "2" ];
then
  MULTICOLS='-V multicols="true"'
else
  MULTICOLS=""
fi

# Capture all console output if a report-to flag has been set
[[ -n "$REPORTTO" ]] && exec 2>&1 > $LOG

cd "$MYDIR"

# Output info about every command (and don't clean up on exit) if in debug mode
$DEBUG && set -x
$DEBUG || trap 'rm -rf "$BUILDDIR"' EXIT SIGHUP SIGTERM


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
ln -sf "$MYDIR/uwb"

if [ -z "${BOOKS// }" ];
then
    # If no -b was used, we want to generate a PDF for EACH BOOK of the Bible
    BOOKS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
fi

for BOOK in "${BOOKS[@]}"; do
    TITLE=$(helpers/catalog_query.py -l $LANGUAGE -v ${VER}-${LANGUAGE} -k name);
    PUBLISH_DATE=$(date -d $(helpers/catalog_query.py -l $LANGUAGE -v ${VER}-${LANGUAGE} -k publish_date) +"%Y-%m-%d")
    VERSION=$(helpers/catalog_query.py -l $LANGUAGE -v ${VER}-${LANGUAGE} -k version)
    CHECKING_LEVEL=$(helpers/catalog_query.py -l $LANGUAGE -v ${VER}-${LANGUAGE} -k checking_level)
    TOC_DEPTH=1

    if [ -z "${VER// }" ];
    then
        print "Cannot get the version for the Bible '$VER'"
        exit 1
    elif [ -z "${TITLE// }" ];
    then
        print "Cannot get the title for the Bible '$VER'"
        exit 1
    elif [ -z "${PUBLISH_DATE// }" ];
    then
        print "Cannot get the publish date for the Bible '$VER'"
        exit 1
    elif [ -z "${CHECKING_LEVEL// }" ];
    then
        print "Cannot get the checking level for the Bible '$VER'"
        exit 1
    fi

    if [ $BOOK == 'full' ];
    then
        SUBTITLE="Old \\& New Testaments"
        BOOK_ARG=""
        BASENAME="${VER^^}"
    elif [ $BOOK == 'ot' ];
    then
        BOOK_ARG='-b gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal'
        SUBTITLE="Old Testament"
        BASENAME="${VER^^}_ot"
    elif [ $BOOK == 'nt' ];
    then
        BOOK_ARG='-b mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev'
        SUBTITLE='New Testament'
        BASENAME="${VER^^}_nt"
    else
        BOOK_ARG="-b $BOOK"
        NAME=$(uwb/status_query.py -l $LANGUAGE -v $VER -b $BOOK -k name);
        SORT=$(uwb/status_query.py -l $LANGUAGE -v $VER -b $BOOK -k sort);
        if [ -z "${NAME// }" ] || [ -z "${SORT}" ];
        then
            print "Cannot get the name of the book for '${BOOK}'"
            exit 1
        fi
        SUBTITLE=$NAME
        BASENAME="${SORT}_${BOOK^^}"
        TOC_DEPTH=2
    fi

    # Run python (helpers/export_usfm_to_html.py) to generate the .html files
    helpers/export_usfm_to_html.py -l $LANGUAGE -v ${VER}-${LANGUAGE} $BOOK_ARG -f html -o "$BUILDDIR/$BASENAME.html"

    sed -i -e "s/<span class=\"chunk-break\"\/>/<span class=\"chunk-break\"\/>$CHUNK_DIVIDER/g" "$BUILDDIR/$BASENAME.html"

    # Generate PDF with PANDOC
    LOGO="https://unfoldingword.org/assets/img/icon-${VER}.png"
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

    # This reporting bit could probably use a rewrite but since I'm not clear on what
    # the use case is I'm only fixing the file paths and letting it run as-is...
    # (originally from export_all_DBP.sh)
    if [[ -n "$REPORTTO" ]]; then
        (
            if [[ -s "$BASENAME-report.txt" ]]; then
                formatA="%-10s%-30s%s\n"
                formatD="%-10s%-10s%-10s%-10s%s\n"
                printf "$formatA" "language" "link-counts-each-matter-part  possibly-rogue-links-in-JSON-files"
                printf "$formatA" "--------" "----------------------------  --------------------------------------------------------"
            fi
            egrep 'start.*matter|goto' $BASENAME.tex |
                sed -e 's/goto/~goto~/g' |
                tr '~' '\n' |
                egrep 'matter|\.com|goto' |
                tee part |
                egrep 'matter|goto' |
                awk 'BEGIN{tag="none"}
                    {
                        if (sub("^.*start","",$0) && sub("matter.*$","",$0)) {tag = $0 }
                        if ($0 ~ goto) { count[tag]++ }
                    }
                    END { for (g in count) { printf "%s=%d\n", g, count[g]; } }' |
                sort -ru > tmp
            sed -e 's/[^ ]*https*:[^ ]*]//' part |
                tr ' ()' '\n' |
                egrep 'http|\.com' > bad
            printf "$formatD" "$LANGUAGE" $(cat tmp) "$(echo $(cat bad))"
        ) > "$BUILDDIR/$BASENAME-report.txt" || : # Don't worry about exiting if report items failed
    fi
done

## SEND REPORTS ##

if [[ -n $REPORTTO ]];
then
    report_package="$BUILDDIR/$VER-$LANGUAGE-report-$(date +%s)${TAG:+-$TAG}.zip"
    zip -9yrj "$report_package" "$BUILDDIR"
    for target in "${REPORTTO[@]}"; do
        if [[ -d "$target" ]]; then
            install -m 0644 "$report_package" "$target/"
        elif [[ "$target" =~ @ ]]; then
            mailx -s "UWB build report ${TAG:+($TAG)}" -a "$report_package" "$target" < $LOG
        fi
    done
fi
