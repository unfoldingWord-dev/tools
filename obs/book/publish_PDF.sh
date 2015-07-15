#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>
#-----------------------------------------------------------------------------
# Help message
help() {
    echo
    echo "Creates a PDF for specified language code."
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <LangCode> -v <version> -o <output directory>"
    echo "   $PROGNAME --help"
    echo
    exit 1
}

#-----------------------------------------------------------------------------
# Parse the command-line
if [ $# -lt 1 ]; then
    help
fi
while test -n "$1"; do
    case "$1" in
        --help|-h)
            help
            ;;
        --lang|-l)
            LANG="$2"
            shift
            ;;
        --out|-o)
            OUTDIR="$2"
            shift
            ;;
        --ver|-v)
            VER="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

set -e
fail () {
    echo "Error: $@"
    exit 1
}

[[ -n "$LANG" ]] || fail "Please specify language code."
[[ -d "$OUTDIR" ]] || fail "Please specify a valid output directory."

# Certain variables and paths
: ${api:=/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/$LANG}
: ${FILENAME:=OBS-$LANG-v$VER}

# Add a debug mode and echo commands to the terminal if the environment var set
: ${debug:=false}
$debug && set -x

BASE_DIR=$(cd $(dirname "$0")/../../ && pwd)
pushd $OUTDIR

# The ConTeXt templates expect to find a few buinding blocks in the main repo,
# so we give our temp space a link back there so it can find them
ln -sf $BASE_DIR/obs

# Run python (export.py) to generate the .tex file from template .tex files
$BASE_DIR/obs/export.py -l $LANG -f tex -o $OUTDIR/$FILENAME.tex \
    || fail "Failed to generate ${FILENAME}.tex"

# Make sure ConTeXt is installed and our environment is passable, if not
# make a basic attempt to fix it before going on...
if ! command -v context; then
    if [[ -d $BASE_DIR/tex ]]; then
        source $BASE_DIR/tex/setuptex
    fi
fi
if ! mtxrun --script fonts --list --all | grep -q noto; then
    export OSFONTDIR="/usr/local/share/fonts;/usr/share/fonts"
    mtxrun --script fonts --reload
    context --generate
fi

# Run ConTeXt (context) to generate stories from .tex file output by python
context $FILENAME.tex || fail "Unable to compile ${FILENAME}.tex"

# Install the files into $OUTDIR and make readable by all
install -Dm 0644 $OUTDIR/$FILENAME.pdf $api/$FILENAME.pdf
