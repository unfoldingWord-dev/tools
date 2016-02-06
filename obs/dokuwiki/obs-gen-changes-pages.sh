#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/"
WEEKLY="$PAGES/en/uwadmin/weeklychanges.txt"
MONTHLY="$PAGES/en/uwadmin/monthlychanges.txt"

echo -e "====== Weekly Changes in OBS Namespaces ======\n\n" >$WEEKLY
echo -e "====== Monthly Changes in OBS Namespaces ======\n\n" >$MONTHLY

# Replace LANGCODE placeholder with destination language code
for f in `find "$PAGES" -maxdepth 1 -type d | sort`; do
    [ ! -d "$f/obs" ] && continue
    LANG="${f##*/}"
    echo "**[[:$LANG:obs|$LANG OBS]]**" >>$WEEKLY
    echo "{{changes>ns=$LANG:obs&maxage=604800&render=pagelist(header,date,user,nocomments)}}
" >>$WEEKLY
    echo "**[[:$LANG:obs|$LANG OBS]]**" >>$MONTHLY
    echo "{{changes>ns=$LANG:obs&maxage=25920000&render=pagelist(header,date,user,nocomments)}}" >>$MONTHLY
done
