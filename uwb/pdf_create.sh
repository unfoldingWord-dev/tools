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
# -> Fix pandoc to support images, or fix pandoc-dev list spacing
# -> Fix ulem not on server

#set -e
#: ${debug:=false}
#$debug && set -x
BASEDIR=$(cd $(dirname "$0")/../ && pwd)
: ${TMPDIR=$(mktemp -d --tmpdir "ubw_pdf_create.XXXXXX")}
#$debug || trap 'cd "$BASEDIR"; rm -rf "$TMPDIR"' EXIT SIGHUP SIGTERM

: ${UW_NOTES_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes}
: ${OUTPUT_DIR:=$(pwd)}
BASE_URL='https://door43.org/_export/xhtmlbody'
NOTES_URL="$BASE_URL/en/bible/notes"
TEMPLATE="$BASEDIR/general_tools/pandoc_pdf_template.tex"

pushd $TMPDIR

book_export () {
    CL_FILE="$TMPDIR/cl.html"
    TN_FILE="$TMPDIR/tn.html"
    TQ_FILE="$TMPDIR/tq.html"
    TW_FILE="$TMPDIR/tw.html"
    TA_FILE="$TMPDIR/ta.html"
    TMP_FILE="$TMPDIR/temp.html"
    SED_FILE="$TMPDIR/out.sed"
    HTML_FILE="$TMPDIR/$1.html"
    PDF_FILE="$OUTPUT_DIR/$1.pdf"

    touch $SED_FILE

    if [ -e $TMP_FILE ]
    then
        rm -f $TMP_FILE
    fi

    # Get Copyrights & Licensing page - using <h1> just so we can make these <h1> (see below) and bump up all other headers by one
    if [ ! -e $CL_FILE ]
    then
        curl -s -L "$BASE_URL/en/legal/license" > $CL_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $CL_FILE
    fi

    # Get all the note
    if [ ! -e $TN_FILE ]
    then
        echo "GENERATING $TN_FILE"
        touch $TMP_FILE

        find "$UW_NOTES_DIR/$1" -type f -path "*[0-9]/*[0-9]*.txt" -printf '%P\n' |
            grep -v 'asv-ulb' |
            sort -u |
            while read f; do
                curl -s -L "$NOTES_URL/$1/${f%%.txt}" |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    >> $TMP_FILE
            done

        touch $TN_FILE

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
            echo "$line" >> $TN_FILE
        done < $TMP_FILE

        rm -f $TMP_FILE

        # put a hr before ever h1 except the first one
        sed -i 's/<h1/<br\/><hr\/><h1/' $TN_FILE
        sed -i '0,/<br\/><hr\/><h1/ s/<br\/><hr\/><h1/<h1/' $TN_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TN_FILE
        sed -i 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TN_FILE
        sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TN_FILE
    fi

    if [ ! -e $TQ_FILE ]
    then
        echo "GENERATING $TQ_FILE"
        touch $TQ_FILE

        find "$UW_NOTES_DIR/$1" -type f -path "*questions/*[0-9].txt" -printf '%P\n' |
            sort |
            while read f; do
                curl -s -L "$NOTES_URL/$1/${f%%.txt}" |
                    grep -v '<strong>.*&gt;&gt;<\/a><\/strong>' |
                    grep -v ' href="\/tag\/' \
                    >> $TQ_FILE
            done

        # REMOVE Comprehension Questions and Answers title
        sed -i '/<h2.*Comprehension Questions and Answers<\/h2>/d' $TQ_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TQ_FILE
    fi

    if [ ! -e $TW_FILE ]
    then
        echo "GENERATING $TW_FILE"
        touch $TW_FILE

        # Get the linked key terms
        for term in $(grep -oP '"\/en\/obe.*?"' $TN_FILE | tr -d '"' | sort -u ); do
            curl -s -L "${BASE_URL}${term}" |
                grep -v ' href="\/tag\/' \
                > $TMP_FILE

            linkname=$(head -3 $TMP_FILE | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
            echo -n 's/' >> $SED_FILE
            echo -n $term | sed -e 's/[]\/$*.^|[]/\\&/g' >> $SED_FILE
            echo -n '"/#' >> $SED_FILE
            echo -n "$linkname" >> $SED_FILE
            echo '"/g' >> $SED_FILE

            cat $TMP_FILE >> $TW_FILE
        done

        rm -f $TMP_FILE

        # put a hr before ever h1 except the first one
        sed -i 's/<h1/<p>\&nbsp; <\/p><h1/' $TW_FILE
        sed -i '0,/<p>\&nbsp; <\/p><h1/ s/<p>\&nbsp; <\/p><h1/<h1/' $TW_FILE

        # increase all headers by one so that the headers we add when making the HTML_FILE are the only h1 headers
        sed -i 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TW_FILE
        sed -i 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TW_FILE
        sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TW_FILE
    fi

    if [ ! -e $TA_FILE ]
    then
        echo "GENERATING $TA_FILE"
        touch $TA_FILE

        # Get the linked tA
        grep -oPh '"\/en\/ta.*?"' $TN_FILE $TW_FILE $TQ_FILE |
            tr -d '"' |
            sort -u |
            sed 's!door43.org/en/!door43.org/_export/xhtmlbody/en/!' |
            while read ta; do
                curl -s -L "${BASE_URL}${ta}"  |
                    grep -v ' href="\/tag\/' \
                    > $TMP_FILE

                linkname=$(head -3 $TMP_FILE | grep -o 'id=".*"' | cut -f 2 -d '=' | tr -d '"')
                echo -n 's/' >> $SED_FILE
                echo -n $ta | sed -e 's/[]\/$*.^|[]/\\&/g' >> $SED_FILE
                echo -n '"/#' >> $SED_FILE
                echo -n "$linkname" >> $SED_FILE
                echo '"/g' >> $SED_FILE

                cat $TMP_FILE >> $TA_FILE
            done

        rm -f $TMP_FILE

        sed -i 's/<h1/<br\/><br\/><hr\/><br\/><h1/g' $TA_FILE
        sed -i '0,/<br\/><br\/><hr\/><br\/><h1/ s/<br\/><br\/><hr\/><br\/><h1/<h1/' $TA_FILE

        sed -i 's/<\(\/\)\{0,1\}h3/<\1h4/g' $TA_FILE
        sed -i 's/<\(\/\)\{0,1\}h2/<\1h3/g' $TA_FILE
        sed -i 's/<\(\/\)\{0,1\}h1/<\1h2/g' $TA_FILE
     fi

     rm -f $HTML_FILE

     echo '<h1>Copyrights & Licensing</h1>' >> $HTML_FILE
     cat $CL_FILE >> $HTML_FILE

     echo '<h1>translationNotes</h1>' >> $HTML_FILE
     cat $TN_FILE >> $HTML_FILE

     echo '<h1>translationQuestions</h1>' >> $HTML_FILE
     cat $TQ_FILE >> $HTML_FILE

     echo '<h1>translationWords</h1>' >> $HTML_FILE
     cat $TW_FILE >> $HTML_FILE

     echo '<h1>translationAcademy</h1>' >> $HTML_FILE
     cat $TA_FILE >> $HTML_FILE

    # Link Fixes
    sed -i -f $SED_FILE $HTML_FILE
    sed -i 's/\/en\/bible.*"/"/' $HTML_FILE
    sed -i 's/\/en\/obs.*"/"/' $HTML_FILE

    # Cleanup
    sed -i -e 's/\xe2\x80\x8b//g' -e '/^<hr>/d' -e '/&lt;&lt;/d' \
        -e 's/<\/span>/<\/span> /g' -e 's/jpg[?a-zA-Z=;&0-9]*"/jpg"/g' \
        -e '/jpg"/d' \
        -e 's/"\/_media/"https:\/\/door43.org\/_media/g' \
        $HTML_FILE

    TITLE=$(grep -m 1 'Chapter 01 Comp' $HTML_FILE | cut -f 5 -d '>' | cut -d 'C' -f 1)
    SUBTITLE="Notes and Text"
    DATE=`date +"%m/%d/%Y"`

    # Create PDF
    pandoc --template=$TEMPLATE -S --toc --toc-depth=2 -V toc-depth=1 \
        --latex-engine=xelatex \
        -V documentclass="memoir" \
        -V geometry='hmargin=2cm' \
        -V geometry='vmargin=2cm' \
        -V title="$TITLE" \
        -V subtitle="$SUBTITLE" \
        -V date="$DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -o $PDF_FILE $HTML_FILE

    echo "See $PDF_FILE (generated files: $TMPDIR)"
}

book_export $1
