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
TEMPLATE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/media/en/obs-templates/obs-book-template.odt

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

outputfile="/tmp/obs-$lang-`date +%F`.html"
echo "Exporting to $outputfile"
rm -f "$outputfile"

# Export from DokuWiki to HTML to Markdown function
htmlexport () {
    $DOKU2HTML "$1/front-matter.txt" >>"$outputfile"
    for f in `find "$1" -maxdepth 1 -type f -name '[0-5][0-9].txt' | sort`; do
        sed -e 's/{{https/<p><img src="https/' \
            -e 's/jpg}}/jpg" \/><\/p>/' \
            -e 's/\/\/A Bible/<p><em>A Bible/' \
            -e 's/\/\/$/<\/em><\/p>/' \
            -e 's/^====== /<h1>/' \
            -e 's/ ======$/<\/h1>/' \
            "$f" \
            >> "$outputfile"
    done
    $DOKU2HTML "$1/back-matter.txt" >>"$outputfile"
}

# Run the exports
htmlexport $PAGES/$lang/obs/

echo pandoc -S -o "${outputfile}.odt" --reference-odt=$TEMPLATE "$outputfile"
