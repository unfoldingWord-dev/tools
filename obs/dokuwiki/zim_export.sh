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
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages

help() {
    echo
    echo "Export Translation Notes and optionally OBS to a Zim Wiki."
    echo
    echo "Usage:"
    echo "   $PROGNAME -s <sourcelangcode> -d <zimdestinationdir> "
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
            srclang="$2"
            shift
            ;;
        --destination|-d)
            DEST="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

if [ -z "$srclang" ]; then
    echo "Error: language to export must be specified."
    help
fi

# NEEDED?
depth="..\/..\/..\/"


echo -n "Remove and export to $DEST? [N/y] "
read CONT
[ "$CONT" != 'y' ] && exit 1
rm -rf "$DEST"
mkdir "$DEST"

export_file () {
    mkdir -p `echo "$DEST/${1##$PAGES/}" | grep -o '.*/'`
    sed -e 's/\\\\/\n/g' \
        -e 's/|{{.*|/|/g' \
        -e 's/}}\]\]/\]\]/g' \
        -e 's/\*\*\[\[/\[\[/g' \
        -e 's/]\]\*\*/\]\]/g' \
        -e 's/^ *\*/\*/g' \
        -e 's/^\*\[/\* \[/g' \
        -e 's/\]\]\/\//\]\]/' \
        -e 's/\/\/see/see/' \
        "$1" | grep -v -e ":playground:" -e '^~~' \
        > "$DEST/${1##$PAGES/}"
}

export_file $PAGES/$srclang/statement-of-faith.txt
export_file $PAGES/$srclang/translation-guidelines.txt
export_file $PAGES/$srclang/obs/front-matter.txt
export_file $PAGES/$srclang/obs/back-matter.txt
export_file $PAGES/$srclang/obs/app_words.txt
export_file $PAGES/$srclang/legal/license.txt
export_file $PAGES/$srclang/get-started.txt
export_file $PAGES/$srclang/tips-tricks.txt
export_file $PAGES/$srclang/obs-training/get-started/switching_editors.txt

for f in `find $PAGES/$srclang/obs -maxdepth 1 -type f -name '[0-5][0-9].txt' | sort`; do
    export_file $f
done

for f in `find $PAGES/$srclang/obs/notes -type f -name '*.txt' | sort`; do
    [ "$f" == "$PAGES/$srclang/obs/notes/key-terms/home" ] && continue
    [ "$f" == "$PAGES/$srclang/obs/notes/key-terms/1-discussion-topic.txt" ] && continue
    export_file $f
done
