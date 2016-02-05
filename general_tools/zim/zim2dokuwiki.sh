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
    echo "Convert Zim files to DokuWiki files."
    echo
    echo "Usage:"
    echo "   $PROGNAME -s <zimsourcedir> -d <dokuwikidestinationdir>"
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
            src=$2
            shift
            ;;
        --destination|-d)
            dst=$2
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

# Verify we have a good path names
if [ ! -d "$src" -o ! -d "$dst" ]; then
    echo "Error: source and destination must be directories."
    help
fi

# Create DokuWiki files from Zim source files
for f in `ls "$src"`; do
    sed -e 's/..\/..\/..\/images\//:en:obs:/g' \
        -e 's/..\/..\/images\//:en:obs:/g' \
        -e '1,3d' \
        "$src/$f" > "$dst/$f"
done
