#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#
# Exports translation notes to Markdown

PROGNAME="${0##*/}"
PANDOC=/usr/bin/pandoc
SRCBASE="/var/www/vhosts/door43.org/ts-exports"
DSTBASE="/var/www/vhosts/door43.org/md-exports"

echo "Converting to Markdown..."
for f in `find "$SRCBASE" -type f -name '*.html'`; do
    dstf="$DSTBASE${f##$SRCBASE}"
    dstdir="${dstf%/*}"
    if [ ! -d "$dstdir" ]; then
        mkdir -p "$dstdir"
    fi
    cat $f | $PANDOC -f html -s -t markdown | \
      sed -e '/obs-.*jpg/d' \
          -e '/en:obs:notes/d' \
          -e 's/(.*)//g' \
          -e 's/\[//g' \
          -e 's/\]//g' | \
      fmt | \
      sed -e 's/ ===/\n===/' \
          -e 's/ ---/\n---/' \
      > ${dstf%.html}.md
done

echo "Unifying..."
MDOBS="$DSTBASE/notes/obs-en-with-notes.md"
rm -f "$MDOBS"
for f in `find "$DSTBASE/notes/frames" -type f -name '*.md' | sort`; do
    cat $f >> "$MDOBS"
done

$PANDOC -f markdown -S -t docx -o ${MDOBS%.md}.docx $MDOBS
#$PANDOC -f markdown -S -t odt -o ${MDOBS%.md}.odt $MDOBS
#$PANDOC -f markdown -S -t pdf -o ${MDOBS%.md}.pdf $MDOBS

#sed  -e 's/?w=640&h=360&tok=[a-z0-9][a-z0-9][a-z0-9][a-z0-9][a-z0-9][a-z0-9]//' -e 's:_media:var/www/vhosts/door43.org/httpdocs/data/gitrepo/media:' 
