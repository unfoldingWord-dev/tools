#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

UWBDW='/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/uwb/v1/'
UWBUSFM='/tmp/UWB-USFM'

rm -rf "$UWBUSFM"
mkdir -p "$UWBUSFM"

for d in `find "$UWBDW" -type d -name '[a-z0-9][a-z0-9][a-z0-9]'`; do
    bk="${d##*/}"
    for f in `ls "$d" | sort -n`; do
        [ -d "$d/$f" ] && continue
        cat "$d/$f" | \
         sed -e 's/\\add\*//g' \
             -e 's/\\add//g' \
          >> "$UWBUSFM/$bk.usfm"
    done
done

# Run the python script in the same directory as this to rename books
python "${0%/*}/uwb_usfm_rename.py" "$UWBUSFM"
