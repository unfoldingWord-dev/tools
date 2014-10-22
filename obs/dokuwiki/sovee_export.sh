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
DOKU2HTML=/usr/local/sbin/doku2html
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages

help() {
    echo
    echo "Export Translation Notes and optionally OBS to a single text file."
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <LangCode> [--obs]"
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
        --obs)
            obs="YES"
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

outputfile="/tmp/sovee-obs-$lang-`date +%F`.html"
echo "Exporting to $outputfile"
rm -f "$outputfile"

export_file () {
    f=`echo $1 | sed "s/en/$lang/"`
    echo -e "\n<!-- filename: $f -->" >> "$outputfile"
    $DOKU2HTML "$1" | \
        sed -e "s/en\/obs\/notes/$lang\/obs\/notes/g" \
            -e "s/en:obs:notes/$lang:obs:notes/g" \
            -e 's/<a href.*title="https:\/\/api/<img src="https:\/\/api/'\
            -e 's/<img src="\/lib.*//' \
        | grep -v '^<!--' \
        >> "$outputfile"
}

export_file $PAGES/en/statement-of-faith.txt
export_file $PAGES/en/translation-guidelines.txt

if [ "$obs" == "YES" ]; then
    for f in `find $PAGES/en/obs -type f -name '[0-5][0-9].txt' | sort`; do
        export_file $f
    done
fi

for f in `find $PAGES/en/obs/notes -type f -name '*.txt' | sort`; do
    export_file $f
done
