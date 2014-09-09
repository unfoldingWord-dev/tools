#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PUB_URL="https://api.unfoldingword.org/obs/txt/1/obs-catalog.json"
CHANGES_URL="https://door43.org/en/dev/changes"
PROGRESS_FILE='/tmp/obs_progress_report.txt'


echo 'Open Bible Stories' >"$PROGRESS_FILE"
echo '==================' >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
date +%F >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
echo 'Online' >>"$PROGRESS_FILE"
echo '------' >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"

echo -n "Published languages: " >>"$PROGRESS_FILE"
wget -q -O - $PUB_URL | grep 'language' >/tmp/published_langs.txt
cat /tmp/published_langs.txt | cut -f 2 -d ':' | cut -f 2 -d '"' | tr '\n' ' ' >>"$PROGRESS_FILE"

echo >>"$PROGRESS_FILE"
echo >>"$PROGRESS_FILE"
NUM_LANGS=`wc -l /tmp/published_langs.txt | grep -o "[0-9]"`
echo -n "Percentange of all languages: " >>"$PROGRESS_FILE"
echo "scale=2; $NUM_LANGS * 100 / 7106" | bc | tr -d '\n' >>"$PROGRESS_FILE"
echo "%" >>"$PROGRESS_FILE"

echo >>"$PROGRESS_FILE"
echo -n "Active in the last month: " >>"$PROGRESS_FILE"
wget -q -O - $CHANGES_URL | grep -o '\/[a-zA-Z0-9\-]*\/obs\/' | cut -f 2 -d '/' | sort | uniq | tr '\n' ' ' >>"$PROGRESS_FILE"

cat $PROGRESS_FILE | mail -s "Open Bible Stories Progress Report" ben@distantshores.org
