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
while getopts l:v:b:c:del:o:r:t:h opt; do
    case $opt in
        l) langs=("${langs[@]}" "$OPTARG");;
        v) vers=("${vers[@]}" "$OPTARG");;
        b) books=("${books[@]}" "$OPTARG");;
        d) debug=true;;
        o) outputs=("${outputs[@]}" "$OPTARG");;
        r) reportto=("${reportto[@]}" "$OPTARG");;
        t) tag=$OPTARG;;
        h) help && exit 0;;
        ?) help && exit 1;;
    esac
done

# Setup variable defaults in case flags were not set
: ${debug=false}
: ${langs[0]='en'}
: ${vers[0]='udb'}
: ${books[0]=""}
: ${max_chapters=0}
: ${outputs[0]=$(pwd)}
: ${reportto[0]=}
: ${tag=}

# Note out base location and create a temporary workspace
BASEDIR=$(cd $(dirname "$0")/../../ && pwd)
BUILDDIR=$(mktemp -d --tmpdir "uwb_build_pdf.XXXXXX")
LOG="$BUILDDIR/shell.log"
TEMPLATE="$BASEDIR/uwb/tex/uwb_template.tex"

# Capture all console output if a report-to flag has been set
[[ -n "$reportto" ]] && exec 2>&1 > $LOG

# Output info about every command (and don't clean up on exit) if in debug mode
$debug && set -x
$debug || trap 'cd "$BASEDIR"; rm -rf "$BUILDDIR"' EXIT SIGHUP SIGTERM

# Reload fonts in case any were added recently
export OSFONTDIR="/usr/share/fonts/google-noto;/usr/share/fonts/noto-fonts/hinted;/usr/local/share/fonts;/usr/share/fonts"
#mtxrun --script fonts --reload
if ! mtxrun --script fonts --list --all | grep -q noto; then
    echo 'Noto fonts not found, bailing...'
    exit 1
fi

## PROCESS LANGUAGES AND BUILD PDFs ##

pushd "$BUILDDIR"
ln -sf "$BASEDIR/uwb"

for lang in "${langs[@]}"; do
for ver in "${vers[@]}"; do
for book in "${books[@]}"; do
    # Pick a filename based on all the parts we have
    BASENAME="$lang-${ver}${book:+-$book}"
    TITLE=$(uwb/catalog_query.py -l $lang -v $ver -k name);
    PUBLISH_DATE=$(date -d $(uwb/catalog_query.py -l $lang -v $ver -k publish_date) +"%Y-%m-%d")
    VERSION=$(uwb/catalog_query.py -l $lang -v $ver -k version)
    CHECKING_LEVEL=$(uwb/catalog_query.py -l $lang -v $ver -k checking_level)
    TOC_DEPTH=1

    if [ -z "${TITLE// }" ];
    then
        print "Cannot get the title for the Bible '$ver'"
        exit 1
    elif [ -z "${PUBLISH_DATE// }" ];
    then
        print "Cannot get the publish date for the Bible '$ver'"
        exit 1
    elif [ -z "${VERSION// }" ];
    then
        print "Cannot get the version for the Bible '$ver'"
        exit 1
    elif [ -z "${CHECKING_LEVEL// }" ];
    then
        print "Cannot get the checking level for the Bible '$ver'"
        exit 1
    fi

    if [ $book == 'ot' ];
    then
       BOOK_ARG='-b gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal'
       SUBTITLE="Old Testament"
    elif [ $book == 'nt' ];
    then
        BOOK_ARG='-b mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev'
        SUBTITLE='New Testament'
    elif [ ! -z "${book// }" ];
    then
        BOOK_ARG="-b $book"
        SUBTITLE=$(uwb/catalog_query.py -l $lang -v $ver -b $book -k title);
        if [ -z "${SUBTITLE// }" ];
        then
            print "Cannot get the name of the book for '$book'"
            exit 1
        fi
        TOC_DEPTH=2
    fi

    # Run python (export.py) to generate the .tex file from template .tex files
    uwb/export.py -l $lang -v $ver $BOOK_ARG -f html -o "$BUILDDIR/$BASENAME.html"
    # Run python (export.py) to generate the .tex file from template .tex files
#    uwb/export.py -l $lang -v $ver $BOOK_ARG -f tex -o "$BUILDDIR/$BASENAME.tex"

    # Send to requested output location(s)
    for dir in "${outputs[@]}"; do
        install -Dm 0644 "$BUILDDIR/${BASENAME}.html" "$dir/${BASENAME}.html"
#        install -Dm 0644 "$BUILDDIR/${BASENAME}.tex" "$dir/${BASENAME}.tex"
    done

    # Generate PDF with PANDOC
    LOGO="https://unfoldingword.org/assets/img/icon-${ver}.png"

    curl -o logo.png "$LOGO"
    curl -o checking.png "https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level${CHECKING_LEVEL}-128px.png"

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
        -V title="$TITLE" \
        -V subtitle="$SUBTITLE" \
        -V checking_level="$CHECKING_LEVEL" \
        -V version="$VERSION" \
        -V publish_date="$PUBLISH_DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o "${BASENAME}.pdf" "${BASENAME}.html"

    # Send to requested output location(s)
    for dir in "${outputs[@]}"; do
        install -Dm 0644 "${BASENAME}.pdf" "$dir/${BASENAME}.pdf"
        echo "GENERATED FILE: $dir/${BASENAME}.pdf"
    done

    # This reporting bit could probably use a rewrite but since I'm not clear on what
    # the use case is I'm only fixing the file paths and letting it run as-is...
    # (originally from export_all_DBP.sh)
    if [[ -n "$reportto" ]]; then
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
            printf "$formatD" "$lang" $(cat tmp) "$(echo $(cat bad))"
        ) > "$BUILDDIR/$BASENAME-report.txt" || : # Don't worry about exiting if report items failed
    fi
done
done
done

## SEND REPORTS ##

if [[ -n "$reportto" ]]; then
    report_package="$BUILDDIR/$BIBLE-report-$(date +%s)${tag:+-$tag}.zip"
    zip -9yrj "$report_package" "$BUILDDIR"
    for target in "${reportto[@]}"; do
        if [[ -d "$target" ]]; then
            install -m 0644 "$report_package" "$target/"
        elif [[ "$target" =~ @ ]]; then
            mailx -s "UWB build report ${tag:+($tag)}" -a "$report_package" "$target" < $LOG
        fi
    done
fi
