#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

LANG="$1"

[ -z "$LANG" ] && echo "Please specify language code." && exit 1

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/"
TMPL="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/templates/obs3/"
DEST="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/$LANG/"
LANGNAMES="/var/www/vhosts/door43.org/httpdocs/lib/plugins/translation/lang/langnames.txt"

grep -qw "$LANG" "$LANGNAMES"
RET=$?
if [ $RET -ne 0 ]; then
    echo "The $LANG language code is not configured in DokuwWiki at:"
    echo "$LANGNAMES"
    echo "Please add it and run this script again"
    exit 1
fi

if [ -d "$DEST" ]; then
    echo "Language directory exists: $DEST"
    echo -n "Do you want to overwrite it with new OBS content? N/y "
    read OVERWRITE
    if [ ! "$OVERWRITE" == "y" ]; then
        echo "Please manually copy the files you want from"
        echo "$TMPL to"
        echo "$DEST"
        exit 1
    fi
fi

mkdir -p "$DEST"
rsync -ha "$TMPL" "$DEST"
echo "--> Created new Open Bible Stories 3.0 template for: $LANG"

# Replace LANGCODE placeholder with destination language code
for f in `find "$DEST" -type f -name '*.txt'`; do
    sed -i "s/LANGCODE/$LANG/g" "$f"
done

# Set permissions
chown -R apache:apache "$DEST"
