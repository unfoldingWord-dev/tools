#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"

CODES=`wget -O - http://vd725.gondor.co/exports/codes-d43.txt`

for LANG in $CODES; do

    DEST="$PAGES/$LANG"
    [ -d "$DEST" ] && continue

    /var/www/vhosts/door43.org/tools/obs/dokuwiki/ns-creator.sh -l $LANG

done
