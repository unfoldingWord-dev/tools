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

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"
LANGDIR="$PAGES/$LANG"
ZIPNAME="$LANG-obs-`date +%F`"

cd $LANGDIR

find obs -maxdepth 1 -type f -name '[0-9][0-9].txt' | zip $ZIPNAME -@

zip -r $ZIPNAME obs/front-matter.txt obs/back-matter.txt obs/app_words.txt \
    statement-of-faith.txt legal/license.txt translation-guidelines.txt

mv $ZIPNAME.zip /tmp/
echo "Zip at: /tmp/$ZIPNAME.zip"

# To add the notes afterward, you could run this:
# find obs/notes -type f -name '*.txt' | zip -r $ZIPNAME -@
