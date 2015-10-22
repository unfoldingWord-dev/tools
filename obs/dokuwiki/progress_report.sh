#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>

PUB_URL="https://api.unfoldingword.org/obs/txt/1/obs-catalog.json"
CHANGES_URL="https://door43.org/en/dev/changes"
PROGRESS_FILE='/tmp/obs_progress_report.txt'
LANGS_FILE='/tmp/progress_langs.txt'
TABLE="/tmp/OBS-Progress-`date +%F`.csv"

echo 'Open Bible Stories' >"$PROGRESS_FILE"
echo '==================' >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
date +%F >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
echo 'Online' >>"$PROGRESS_FILE"
echo '------' >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"

echo -n "Published languages (" >>"$PROGRESS_FILE"
wget -U 'd43' -q -O - $PUB_URL | grep 'language' >/tmp/published_langs.txt
PUB_LANGS=`cat /tmp/published_langs.txt | tr '}' '\n' | grep -c language`
echo -n "$PUB_LANGS): " >>"$PROGRESS_FILE"
cat /tmp/published_langs.txt | tr '}' '\n' | grep -o "language.*" | cut -f 2 -d ' ' | tr '\n' ' ' | tr '\n' ' ' | tr -d '"' | tr -d ',' >>"$PROGRESS_FILE"

echo >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
echo -n "Percentange of all languages: " >>"$PROGRESS_FILE"
echo "scale=2; $PUB_LANGS * 100 / 7106" | bc | tr -d '\n' >>"$PROGRESS_FILE"
echo "%" >>"$PROGRESS_FILE"

echo >>"$PROGRESS_FILE"
echo -n "Active in the last month (" >>"$PROGRESS_FILE"
wget -U 'd43' -q -O - $CHANGES_URL | grep -o '\/[a-zA-Z0-9\-]*\/obs\/[0-5][0-9]' >/tmp/changes.txt
cut -f 2 -d '/' /tmp/changes.txt | sort | uniq >"$LANGS_FILE"
PROGRESS_LANGS=`wc -l $LANGS_FILE | grep -o "[0-9]*"`
echo -n "$PROGRESS_LANGS): " >>"$PROGRESS_FILE"
cat "$LANGS_FILE" | tr '\n' ' ' >>"$PROGRESS_FILE"

echo -n "Lang," >$TABLE
seq -w 1 50 | tr '\n' ',' >>$TABLE
for x in `cat $LANGS_FILE`; do
    echo -en "\n$x," >>$TABLE
    for y in `seq -w 1 50`; do
        grep "$x" /tmp/changes.txt | grep -q "$y$" && echo -n 'X'>>$TABLE
        echo -n "," >>$TABLE
    done
done

cat $PROGRESS_FILE | mail -s "Open Bible Stories Progress Report" -a $TABLE \
    ben@unfoldingword.org kwesi_opokudebrah@wycliffeassociates.org \
    jesse@unfoldingword.org russ_perry@wycliffeassociates.org \
    gene_foltz@wycliffeassociates.org gary_anderson@wycliffeassociates.org \
    eric_steggerda@wycliffeassociates.org david_byron@wycliffeassociates.org \
    tammy_white@wycliffeassociates.org

rm -f "$PROGRESS_FILE"
rm -f "$LANGS_FILE"
rm -f "$TABLE"
