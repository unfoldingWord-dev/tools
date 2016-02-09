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
    echo "Convert DokuWiki files to Zim files."
    echo
    echo "Usage:"
    echo -n "   $PROGNAME -s <dokuwikisourcedir> -d <zimdestinationdir> "
    echo "[-u <depth(1|2|3|4|5)>]"
    echo
    echo "   e.g. $PROGNAME -s /tmp/dokuwiki -d /tmp/zim -u 2"
    echo
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
        --up|-u)
            up="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

# Verify we have good variables
if [ ! -d "$src" ]; then
    echo "Error: source must be a directory."
    help
fi
if [ ! -d "$dst" ]; then
    echo "Error: destination must be a directory."
    help
fi
if [ -n "up" ]; then
    depth="..\/"
    for x in `seq 2 $up`; do
        depth+="..\/"
    done
else
    depth="..\/..\/..\/"
fi

# Create Zim files from DokuWiki source files
for f in `ls "$src"`; do
    [ -d "$src/$f" ] && continue
    sed -e "s/:en:obs:obs-/${depth}images\/obs-/g" \
        -e 's/<[^>]*>//g' \
        -e 's/jpg\?.*$/jpg}}/g' \
        -e 's/\(\[\[:en:obs:notes.*|\)\({{.*$\)/\2\n\1/g' \
        -e 's/\].*$/\]\]\]/g' \
        -e 'N;/|\n/s/|\n/|/;P;D' \
        "$src/$f" > "$dst/$f"
done
