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
    BOOK_HTML="/tmp/$1.html"
    BOOK_PDF="/tmp/$1.pdf"
    rm -f $BOOK_HTML
    cd $NOTES
    # Get all the pages
    for f in `find "$1" -type f | grep -v 'home.txt' | sort`; do
        wget -U 'me' "$NOTES_URL/${f%%.txt}" -O - \
            | grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' \
            | grep -v ' href="\/tag\/' \
            >> $BOOK_HTML
    done
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

    pandoc --template=$TEMPLATE -S --toc --toc-depth=1 -o $BOOK_PDF $BOOK_HTML
    echo "See $BOOK_PDF"
}

book_export $1

# Remove tmp files
rm -f /tmp/$$.*
