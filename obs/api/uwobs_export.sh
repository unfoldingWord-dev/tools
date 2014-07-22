#!/bin/bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

LANG="$1"

if [ -z "$LANG" ]; then
    echo "Please specify language to export."
    exit 1
fi

echo "Exporting Images..."
MEDIADIR="/var/www/vhosts/door43.org/media/en/obs/"
MEDIADIRHD="/var/www/vhosts/door43.org/media/en/obs/"
LANGDIR="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/$LANG/360px"
LANGDIRHD="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/$LANG/2160px"

mkdir -p "$LANGDIR" "$LANGDIRHD"

for x in `ls "$MEDIADIR"/*[0-9].jpg`; do
    IMGNAME=`echo ${x/obs-/obs-en-} | grep -o "obs-en.*" | \
             sed "s/-en-/-$LANG-/"`
    ln -s $x $LANGDIR/$IMGNAME
done

for x in `ls "$MEDIADIR"/*hd.jpg`; do
    IMGNAME=`echo ${x/obs-/obs-en-} | grep -o "obs-en.*" | \
             sed "s/-en-/-$LANG-/" | sed "s/_hd//"`
    ln -s $x $LANGDIRHD/$IMGNAME
done

echo "Images linked to $LANGDIR"
echo "Exporting Text..."

/var/www/vhosts/door43.org/tools/obs/json/json_export.py --unfoldingwordexport
