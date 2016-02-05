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
#  Upgrades the OBS stories from the Translation Notes

PROGNAME="${0##*/}"
OBSSTRUCTURE="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obs/"
SRCBASE="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obs/notes/frames"
DSTBASE="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/obs"

[ ! -d "$DSTBASE" ] && mkdir -p "$DSTBASE"

# Make skeleton files
for f in `find "$OBSSTRUCTURE" -maxdepth 1 -type f -name '[0-5][0-9]-*.txt'`; do
    head -1 "$f" > "$DSTBASE/${f##*/}"
done

# Merge frames into stories
for f in `ls $SRCBASE/*.txt`; do
    fname="${f##*/}"
    storynum="${fname%%-*}"
    storyf=`find "$DSTBASE" -maxdepth 1 -type f -name "$storynum-*.txt"`
    sed -e '/^===== Translation/,$d' \
        -e '/^=====/d' \
        -e 's/\*\*//g' \
        -e 's/\[\[:[A-Za-z:\-]*|//g' \
        -e 's/\]\]//g' \
        -e 's/  / /g' \
        -e 's/[”“]/"/g' \
        -e "s/[’‘]/'/g" \
        "$f" >> "$storyf"
done
