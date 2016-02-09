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

help() {
    echo
    echo "Export DokuWiki files to HTML files."
    echo
    echo "Usage:"
    echo "   $PROGNAME -s <DokuWikiDir> -d <HTMLExportDir>"
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
        --source|-s)
            src="$2"
            shift
            ;;
        --destination|-d)
            dst="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

if [ ! -d "$src" -o ! -d "$dst" ]; then
    echo "Error: source and destination must be directories."
    help
fi

# Export from DokuWiki to HTML
for f in `find "$src" -type f -name '*.txt'`; do
    dstf="$dst${f##$src}"
    dstdir="${dstf%/*}"
    if [ ! -d "$dstdir" ]; then
        mkdir -p "$dstdir"
    fi
    /usr/local/bin/doku2html "$f" > "${dstf%.txt}.html"
done
