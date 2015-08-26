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
    echo "    -c       Override checking level (1, 2 or 3)"
    echo "    -d       Show debug messages while running script"
    echo "    -l LANG  Add language(s) to process"
    echo "    -o DIR   Add output location(s) for final PDF"
    echo "    -r LOC   Send build report to directory(s) or email address(s)"
    echo "    -t TAG   Add a tag to the output filename"
    echo "    -v VER   Override the version field in the output"
    echo "    -h       Show this help"
    echo "Notes:"
    echo "    Option flags whose values are marked '(s)' may be specified multiple times"
}

# Process command line options
while getopts c:dl:o:r:t:v:h opt; do
    case $opt in
        c) checking=$OPTARG;;
        d) debug=true;;
        l) langs=("${langs[@]}" "$OPTARG");;
        o) outputs=("${outputs[@]}" "$OPTARG");;
        r) reportto=("${reportto[@]}" "$OPTARG");;
        t) tag=$OPTARG;;
        v) version=$OPTARG;;
        h) help && exit 0;;
        ?) help && exit 1;;
    esac
done

# Setup variable defaults in case flags were not set
: ${checking=}
: ${debug=false}
: ${langs[0]=${LANG%_*}}
: ${outputs[0]=$(pwd)}
: ${reportto[0]=}
: ${tag=}
: ${version=}

# Note out base location and create a temporary workspace
BASEDIR=$(cd $(dirname "$0")/../../ && pwd)
BUILDDIR=$(mktemp -d --tmpdir "obs_build_pdf.XXXXXX")
LOG="$BUILDDIR/shell.log"

# Capture all console output if a report-to flag has been set
[[ -n "$reportto" ]] && exec 2>&1 > $LOG

# Output info about every command (and don't clean up on exit) if in debug mode
$debug && set -x
$debug || trap 'cd "$BASEDIR"; rm -rf "$BUILDDIR"' EXIT SIGHUP SIGTERM

# Make sure ConTeXt is installed and our environment is passable, if not
# make a basic attempt to fix it before going on...
if ! command -v context >/dev/null; then
    if [[ -d "$BASEDIR/tex" ]]; then
        source "$BASEDIR/tex/setuptex"
    else
        echo "Please run $BASEDIR/tex_bootstrap.sh or install ConTeXt" && exit 1
    fi
fi
if ! mtxrun --script fonts --list --all | grep -q noto; then
    export OSFONTSDIR=${OSFONTDIR:="/usr/local/share/fonts;/usr/share/fonts"}
    mtxrun --script fonts --reload
    context --generate
fi

## PROCESS LANGUAGES AND BUILD PDFS ##

# The ConTeXt templates expect to find a few buinding blocks in the main repo,
# but we're going to be working in a temp space, se once we are there link back
# to the obs tools so these snippets can be found.
pushd "$BUILDDIR"
ln -sf "$BASEDIR/obs"

for lang in "${langs[@]}"; do
    # Get the version for this language (if not forced from an option flag)
    LANGVER=${version:-$("$BASEDIR"/uw/get_ver.py $lang)}

    # Pick a filename based on all the parts we have
    BASENAME="OBS-${lang}-v${LANGVER}${tag:+-$tag}"

    # Run python (export.py) to generate the .tex file from template .tex files
    ./obs/export.py -l $lang -f tex -o ${checking:+-c $chekcing} "$BASENAME.tex"

    # Run ConTeXt (context) to generate stories from .tex file output by python
    $debug && trackers="afm.loading,fonts.missing,fonts.warnings,fonts.names,fonts.specifications,fonts.scaling,system.dump"
    context --paranoid --batchmode --noconsole ${trackers:+--trackers=$trackers} "$BASENAME.tex"

    # Send to requested output location(s)
    for dir in "${outputs[@]}"; do
        install -Dm 0644 "${BASENAME}.pdf" "$(eval echo $dir)/${BASENAME}.pdf"
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

## SEND REPORTS ##

if [[ -n "$reportto" ]]; then
    report_package="$BUILDDIR/OBS-build-report-$(date +%s)${tag:+-$tag}.zip"
    zip -9yrj "$report_package" "$BUILDDIR"
    for target in "${reportto[@]}"; do
        if [[ -d "$target" ]]; then
            install -m 0644 "$report_package" "$target/"
        elif [[ "$target" =~ @ ]]; then
            mailx -s "OBS build report ${tag:+($tag)}" -a "$report_package" "$target" < $LOG
        fi
    done
fi
