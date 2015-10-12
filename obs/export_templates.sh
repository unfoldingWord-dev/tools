#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>

# exit this script if there is an error
set -e

PROGNAME="${0##*/}"

showhelp() {
    echo
    echo "Export OBS templates."
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <lang_code> [-o <output_directory>] [--noimages] [--test]"
    echo "   $PROGNAME --help"
    echo
    echo "If the -o option is not specified, the output directory is the current directory (pwd)."
    echo
    echo "If the -noimages option is present, the output will contain no images."
    echo
    echo "If the --test option is present, the templates will be generated on http://test.door43.org rather than https://door43.org."
    echo
    exit 1
}

if [ $# -lt 1 ]; then
    showhelp
fi

SOURCE="https://door43.org"
IMAGES="1"

while test -n "$1"; do
    case "$1" in
        --help|-h)
            help
            ;;
        --lang|-l)
            LANG="$2"
            shift
            ;;
        --outdir|-o)
            OUTDIR="$2"
            shift
            ;;
        --noimages)
            IMAGES="0"
            ;;
        --test)
            SOURCE="http://test.door43.org"
            ;;
        *)
            echo "Unknown argument: $1"
            showhelp
            ;;
    esac
    shift
done

if [ -z "$LANG" ]; then
    echo "Error: language to export must be specified."
    showhelp
fi

# set the output directory
if [ ! -z "$OUTDIR" ]; then
    CURRDIR=$(pwd)
    cd "$OUTDIR"
fi

# get DOCX template
# curl parameters:
#   -O = write output to file, not stdout
#   -J = use filename from Content-Disposition header to name the file
echo "Getting the DOCX template..."
curl -O -J "$SOURCE/lib/exe/ajax.php?call=download_obs_template_docx&lang=$LANG&img=$IMAGES&draft=0"

# getting the ODT template
echo "Getting the ODT template..."
curl -O -J "$SOURCE/lib/exe/ajax.php?call=download_obs_template_odt&lang=$LANG&img=$IMAGES&draft=0"

# reset the current directory
if [ ! -z "$OUTDIR" ]; then
    cd "$CURRDIR"
fi

# finished
echo
echo "Finished."
echo
