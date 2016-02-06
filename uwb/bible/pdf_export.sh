#!/usr/bin/env bash
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  dboerschlein
#  Jesse Griffin <jesse@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>

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
    echo "    -h       Show this help"
    echo "Notes:"
    echo "    Option flags whose values are marked '(s)' may be specified multiple times"
}

# Process command line options
while getopts l:v:b:c:o:r:t:d:C opt; do
    case $opt in
        l) LANGUAGE=$OPTARG;;
        v) VER=$OPTARG;;
        b) BOOKS=("${BOOKS[@]}" "$OPTARG");;
        o) OUTPUTS=("${OUTPUTS[@]}" "$OPTARG");;
        r) REPORTTO=("${REPORTTO[@]}" "$OPTARG");;
        t) TAG=$OPTARG;;
        d) DEBUG=true;;
        C) HR_BETWEEN_CHUNKS=true;;
        [h?]) help && exit 1;
    esac
done

# Setup variable defaults in case flags were not set
: ${DEBUG=false}
: ${LANGUAGE='en'}
: ${VER='udb'}
: ${BOOKS[0]=""}
: ${OUTPUTS[0]=$(pwd)}
: ${REPORTTO[0]=}
: ${TAG=}
: ${HR_BETWEEN_CHUNKS=false}

# Note out base location and create a temporary workspace
BASEDIR=$(cd $(dirname "$0")/../../ && pwd)
BUILDDIR=$(mktemp -d --tmpdir "uwb_${LANGUAGE}_build_pdf.XXXXXX")
LOG="$BUILDDIR/shell.log"
TEMPLATE="$BASEDIR/uwb/tex/uwb_template.tex"
if $HR_BETWEEN_CHUNKS;
then
  TEMPLATE="$BASEDIR/uwb/tex/uwb_chunk_template.tex"
fi
NOTOFILE="$BASEDIR/uwb/tex/noto-${LANGUAGE}.tex"

# Capture all console output if a report-to flag has been set
[[ -n "$REPORTTO" ]] && exec 2>&1 > $LOG

# Output info about every command (and don't clean up on exit) if in debug mode
$DEBUG && set -x
$DEBUG || trap 'cd "$BASEDIR"; rm -rf "$BUILDDIR"' EXIT SIGHUP SIGTERM

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
ln -sf "$BASEDIR/uwb"

if [ -z "${BOOKS// }" ];
then
    # If no -b was used, we want to generate a PDF for EACH BOOK of the Bible
    BOOKS=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
fi

for BOOK in "${BOOKS[@]}"; do
    TITLE=$(uwb/catalog_query.py -l $LANGUAGE -v $VER -k name);
    PUBLISH_DATE=$(date -d $(uwb/catalog_query.py -l $LANGUAGE -v $VER -k publish_date) +"%Y-%m-%d")
    VERSION=$(uwb/catalog_query.py -l $LANGUAGE -v $VER -k version)
    CHECKING_LEVEL=$(uwb/catalog_query.py -l $LANGUAGE -v $VER -k checking_level)
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
        BASENAME="${VER^^}-OT"
    elif [ $BOOK == 'nt' ];
    then
        BOOK_ARG='-b mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev'
        SUBTITLE='New Testament'
        BASENAME="${VER^^}-NT"
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
        BASENAME="${SORT}-${BOOK^^}"
        TOC_DEPTH=2
    fi

    # Run python (export.py) to generate the .tex file from template .tex files
    uwb/export.py -l $LANGUAGE -v $VER $BOOK_ARG -f html -o "$BUILDDIR/$BASENAME.html"
    # Run python (export.py) to generate the .tex file from template .tex files
    #uwb/export.py -l $LANGUAGE -v $VER $BOOK_ARG -f tex -o "$BUILDDIR/$BASENAME.tex"

    if $HR_BETWEEN_CHUNKS;
    then
        sed -i -e 's/<span class="chunk-break"\/>/<hr\/>/g' "$BUILDDIR/$BASENAME.html"
    fi

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
        -V geometry="hmargin=1cm" \
        -V geometry="vmargin=1cm" \
        -V title="title.txt" \
        -V subtitle="subtitle.txt" \
        -V fontsize="12" \
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
