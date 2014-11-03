#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PROGNAME="${0##*/}"
PANDOC="/usr/bin/pandoc"
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages
TEMPLATE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/media/en/obs-templates/obs-book-template.odt
OBS_EXPORT="/var/www/vhosts/door43.org/tools/obs/export.py"

help() {
    echo
    echo "Export to a print ready ODT file."
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <LangCode>"
    echo "   $PROGNAME --help"
    echo
    exit 1
}

if [ $# -lt 1 ]; then
    help
fi
while test -n "$1"; do
    case "$1" in
        --help|-h)
            help
            ;;
        --lang|-l)
            lang="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

if [ -z "$lang" ]; then
    echo "Error: language to export must be specified."
    help
fi
if [ ! -x "$OBS_EXPORT" ]; then
    echo "Error: $OBS_EXPORT not found."
    help
fi

outputfile="/tmp/obs-$lang-`date +%F`.html"
echo "Exporting to $outputfile"
rm -f "$outputfile"

$OBS_EXPORT -l $lang -f html -o "/tmp/obs.html"

echo "<img src="https://api.unfoldingword.org/obs/jpg/1/uWOBSverticallogo600w.png"></img>" >>"$outputfile"
doku2html "$PAGES/$lang/obs/front-matter.txt" >>"$outputfile"
cat "/tmp/obs.html" >>"$outputfile"
doku2html "$PAGES/$lang/obs/back-matter.txt" >>"$outputfile"

echo pandoc-dev -S -o "${outputfile%%.html}.odt" --reference-odt=$TEMPLATE "$outputfile"
