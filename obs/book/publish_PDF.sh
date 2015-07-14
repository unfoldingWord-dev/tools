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

fail () {
    echo "Error: $@"
    exit 1
}

[[ -n "$LANG" ]] || fail "Please specify language code."
[[ -d "$OUTDIR" ]] || fail "Please specify a valid output directory."

# Certain variables and paths
: ${MAILTO:=publishing@unfoldingword.org}
: ${api:=/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/$LANG}
: ${api_url:=https://api.unfoldingword.org/obs/txt/1/$LANG}
: ${FILENAME:=OBS-$LANG-v$VER}

# Link the httpdocs folder in $OUTDIR
myhost=$(uname -n)
[[ $myhost == test.door43.org ]] && ln -sf /var/www/vhosts/door43.org/httpdocs $OUTDIR/httpdocs
BASE_DIR=$(cd $(dirname "$0")/../../ && pwd)
for folder in httpdocs includes; do
    ln -sf $BASE_DIR/$folder $OUTDIR/$folder
done

# Run python (export.py) to generate the .tex file from template .tex files
pushd $OUTDIR
$BASE_DIR/obs/export.py -l $LANG -f tex -o $OUTDIR/$FILENAME.tex 2>&1 \
    || fail "Failed to generate ${FILENAME}.tex"

# Run ConTeXt (context) to generate stories from .tex file output by python
context $FILENAME.tex || fail "Unable to compile ${FILENAME}.tex"

# Install the files into $OUTDIR and make readable by all
install -Dm 0644 $OUTDIR/$FILENAME.pdf $api/$FILENAME.pdf

URL="${api_url}/$FILENAME.pdf"
#echo "A PDF for $LANG at version $VER has been created.  " \
    #"Please download it from $URL." \
    #| mail -s "PDF Generated for $LANG" "$MAILTO"
