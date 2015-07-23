#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <rmahn@getmealticket.com>
#  Caleb Maclennan <caleb@alerque.com>


### To do:
# -> Fix TOC to support 3 digit chapter numbers (or remove chp nums)
# -> Fix pandoc to support images, or fix pandoc-dev list spacing
# -> Fix ulem not on server

set -e
: ${debug:=false}
$debug && set -x
BASEDIR=$(cd $(dirname "$0")/../ && pwd)
TMPDIR=$(mktemp -d --tmpdir "ubw_pdf_create.XXXXXX")
$debug || trap 'cd "$BASEDIR"; rm -rf "$TMPDIR"' EXIT SIGHUP SIGTERM

: ${UW_NOTES_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes}
: ${OUTPUT_DIR:=$(pwd)}
BASE_URL='https://door43.org/_export/xhtmlbody'
NOTES_URL="$BASE_URL/en/bible/notes"
TEMPLATE="$BASEDIR/general_tools/pandoc_pdf_template.tex"

pushd $TMPDIR

book_export () {
    BOOK_TMP="$TMPDIR/book.html"
    BOOK_HTML="$TMPDIR/$1.html"
    BOOK_PDF="$OUTPUT_DIR/$1.pdf"
    rm -f $BOOK_HTML

    # Get license page - using <h0> just so we can make these <h1> (see below) and bump up all other headers by one
    echo '<h0>Copyrights & Licensing</h0>' >> $BOOK_HTML
    curl -s -L "$BASE_URL/en/legal/license" >> $BOOK_HTML

    # Get all the pages
    find "$UW_NOTES_DIR/$1" -type f -name '[0-9]*.txt' -printf '%P\n' |
        grep -v 'asv-ulb' |
        sort |
        while read f; do
            curl -s -L "$NOTES_URL/$1/${f%%.txt}" |
                grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                grep -v ' href="\/tag\/' \
                >> $BOOK_TMP
        done

    echo '<h0>Notes</h0>' >> $BOOK_HTML

     # Remove TFT
    TFT=false
    while read line; do
        if [[ "$line" == '<h2 class="sectionedit2" id="tft">TFT:</h2>' ]]; then
            TFT=true
            continue
        fi
        if [[ "${line:0:25}" == '<!-- EDIT2 SECTION "TFT:"' ]]; then
            TFT=false
            continue
        fi
        $TFT && continue
        echo "$line" >> $BOOK_HTML
    done < $BOOK_TMP

    # put a hr before ever h1
    sed -i 's/<h1/<br\/><br\/><hr\/><br\/><h1/g' $BOOK_HTML

    echo '<h0>Key Terms</h0>' >> $BOOK_HTML
    # Get the linked key terms
    for term in $(grep -oP '"\/en\/obe.*?"' $BOOK_HTML | tr -d '"' | sort -u ); do
        curl -s -L "${BASE_URL}${term}" |
            grep -v ' href="\/tag\/' \
            > out.tmp

        linkname=$(head -3 out.tmp | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
        echo -n 's/' >> out.sed
        echo -n $term | sed -e 's/[]\/$*.^|[]/\\&/g' >> out.sed
        echo -n '"/#' >> out.sed
        echo -n "$linkname" >> out.sed
        echo '"/g' >> out.sed

        cat out.tmp >> $BOOK_HTML
    done

    echo '<h0>translationAcademy</h0>' >> $BOOK_HTML
    # Get the linked tA
    grep -oP '"\/en\/ta.*?"' $BOOK_HTML |
        tr -d '"' |
        sort -u |
        sed 's!door43.org/en/!door43.org/_export/xhtmlbody/en/!' |
        while read ta; do
            curl -s -L "${BASE_URL}${ta}" |
                grep -v ' href="\/tag\/' \
                > out.tmp

            linkname=$(head -3 out.tmp | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo -n 's/' >> out.sed
            echo -n $ta | sed -e 's/[]\/$*.^|[]/\\&/g' >> out.sed
            echo -n '"/#' >> out.sed
            echo -n "$linkname" >> out.sed
            echo '"/g' >> out.sed

            cat out.tmp >> $BOOK_HTML
        done

    # Link Fixes
    sed -i -f out.sed $BOOK_HTML
    sed -i 's/\/en\/bible.*"/"/' $BOOK_HTML
    sed -i 's/\/en\/obs.*"/"/' $BOOK_HTML

    # Put in Comprehension Questions header
    sed -i '/<h2.*Comprehension Questions and Answers<\/h2>/d' $BOOK_HTML
    awk '/sectionedit1.*id=.*chapter-/ && !x {print "<h0>Comprehension Questions and Answers</h0>"; x=1} 1' $BOOK_HTML > $BOOK_TMP && mv $BOOK_TMP $BOOK_HTML

    # increase all headers by one so that our new <h0> headers are <h1> (sections) and <h1> headers becomes <h2> (subsections) etc.
    sed -i 's/<\(\/\)\{0,1\}h3/<\1h4/g' $BOOK_HTML
    sed -i 's/<\(\/\)\{0,1\}h2/<\1h3/g' $BOOK_HTML
    sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $BOOK_HTML
    sed -i 's/<\(\/\)\{0,1\}h0/<\1h1/g' $BOOK_HTML

    # Cleanup
    sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
        -e 's/<\/span>/<\/span> /g' -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e '/jpg"/d' \
        -e 's/"\/_media/"https:\/\/door43.org\/_media/g' \
        $BOOK_HTML

    BOOK_NAME=$(grep -m 1 'Chapter 01 Comp' $BOOK_HTML | cut -f 5 -d '>' | cut -d 'C' -f 1)
    # Create PDF
    pandoc --template=$TEMPLATE -S --toc --toc-depth=2 -V toc-depth=1 \
        -V documentclass="memoir" \
        -V title="$BOOK_NAME Text and Notes" \
        -V mainfont="Noto Sans" \
        -o $BOOK_PDF $BOOK_HTML
    echo "See $BOOK_PDF"
}

book_export $1
