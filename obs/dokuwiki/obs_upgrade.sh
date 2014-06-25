#!/usr/bin/env sh
# -*- coding: utf8 -*-
#  Copyright (c) 2014 Jesse Griffin
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

# Upgrades the OBS stories from the Translation Notes

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
        -e 's/\[\[:[a-z:\-]*|//g' \
        -e 's/\]\]//g' \
        -e 's/  / /g' \
        -e 's/[”“]/"/g' \
        -e "s/[’‘]/'/g" \
        "$f" >> "$storyf"
done
