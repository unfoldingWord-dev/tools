#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

NOTES='/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes'
NOTES_URL='https://door43.org/_export/xhtmlbody/en/bible/notes'
OBE_URL='https://door43.org/_export/xhtmlbody/'
TEMPLATE=/var/www/vhosts/door43.org/tools/general_tools/pandoc_pdf_template.tex

book_export () {
    BOOK_TMP="/tmp/$$.html"
    BOOK_HTML="/tmp/$1.html"
    BOOK_PDF="/tmp/$1.pdf"
    cd $NOTES
    # Get all the pages
    for f in `find "$1" -type f | grep -v 'home.txt' | sort`; do
        wget -U 'me' "$NOTES_URL/${f%%.txt}" -O - \
            | grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' \
            | grep -v ' href="\/tag\/' \
            >> $BOOK_TMP
    done
    # Remove TFT
    TFT=false
    while read line; do
        if [ "$line" == '<h2 class="sectionedit2" id="tft">TFT:</h2>' ]; then
            TFT=true
            continue
        fi
        if [ "${line:0:25}" == '<!-- EDIT2 SECTION "TFT:"' ]; then
            TFT=false
            continue
        fi
        $TFT && continue
        echo "$line" >>$BOOK_HTML
    done < $BOOK_TMP

    echo '<h1>Key Terms</h1>' >> $BOOK_HTML
    # Get the linked key terms
    for term in `grep -oP '"\/en\/obe.*?"' $BOOK_HTML | tr -d '"' | sort | uniq`; do
        wget -U 'me' ${OBE_URL}${term} -O - \
            | grep -v ' href="\/tag\/' \
            > /tmp/$$.tmp

        linkname=`head -3 /tmp/$$.tmp | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"'`
        echo -n 's/' >> /tmp/$$.sed
        echo -n $term | sed -e 's/[]\/$*.^|[]/\\&/g' >> /tmp/$$.sed
        echo -n '/#' >> /tmp/$$.sed
        echo "$linkname/g" >> /tmp/$$.sed

        cat /tmp/$$.tmp >> $BOOK_HTML
    done

    # Link Fixes
    sed -i -f /tmp/$$.sed $BOOK_HTML
    sed -i 's/\/en\/bible.*"/"/' $BOOK_HTML
    sed -i 's/\/en\/obs.*"/"/' $BOOK_HTML

    # Cleanup
    sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
        -e 's/<\/span>/<\/span> /g' \
        $BOOK_HTML

    BOOK_NAME=`grep -m 1 'Chapter 01 Comp' $BOOK_HTML | cut -f 5 -d '>' | cut -f 1 -d ' '`
    # Create PDF
    pandoc --template=$TEMPLATE -S --toc --toc-depth=1 -V toc-depth=0 \
        -V documentclass=memoir -V title="$BOOK_NAME Text and Notes" \
        -o $BOOK_PDF $BOOK_HTML
    echo "See $BOOK_PDF"
}

book_export $1

# Remove tmp files
rm -f /tmp/$$.*
