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

if [ -d "$DEST" ]; then
    echo "Language directory $DEST exists, going to interactive mode."
    exit 1
else
    mkdir -p "$DEST"
    rsync -ha "$TMPL" "$DEST"
    echo "--> Created new Open Bible Stories 3.0 template for: $LANG"
fi

# Replace LANGCODE placeholder with destination language code
for f in `find "$DEST" -type f -name '*.txt'`; do
    sed -i "s/LANGCODE/$LANG/g" "$f"
done

# Set permissions
chown -R apache:apache "$DEST"
