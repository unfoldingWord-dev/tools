#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

UTBDW='/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/udb/ep'
UTBUSFM='/tmp/UTB-USFM'

rm -rf "$UTBUSFM"
mkdir -p "$UTBUSFM"

for f in `find "$UTBDW" -type f -name '[0-9]*-[a-z]*.usfm.txt'`; do
    filename=$(basename $f)
    filename=${filename%.*}
    cat "$f" | \
    sed -e 's/\\add\*/ /g' \
        -e 's/\\add/ /g' \
       >> "$UTBUSFM/$filename.usfm"
done

# Run the python script in the same directory as this to rename books
#python "${0%/*}/uwb_usfm_rename.py" "$UTBUSFM"
