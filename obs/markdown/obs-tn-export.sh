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
DOKU2HTML=/usr/local/bin/doku2html
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages

help() {
    echo
    echo "Export Translation Notes files to a single text file."
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

outputfile="/tmp/obs-tn-$lang-`date +%F`.md"
echo "Exporting to $outputfile"
rm -f "$outputfile"

# Export from DokuWiki to HTML to Markdown function
tnexport () {
    for f in `find "$1" -type f -name '*.txt'`; do
        echo "filename: $f" >> "$outputfile"
        $DOKU2HTML "$f" | $PANDOC -f html -s -t markdown | \
            sed -e 's/ ===/\n===/' \
                -e 's/ ---/\n---/' \
            >> "$outputfile"
    done
}

# Run the exports
tnexport $PAGES/$lang/obs/notes/key-terms
tnexport $PAGES/$lang/obs/notes/frames
tnexport $PAGES/$lang/obs/notes/questions
