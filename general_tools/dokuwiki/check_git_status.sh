#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PROGNAME="${0##*/}"
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/

for d in `find $PAGES -maxdepth 1 -type d`; do
    cd $d
    DIRNAME=${d##*/}
    [ "$DIRNAME" == ".git" ] && continue
    [ "$DIRNAME" == "playground" ] && continue
    [ "$DIRNAME" == "" ] && DIRNAME="pages"
    STATUS=`git status --porcelain 2>&1`
    if [ "$?" != "0" ]; then
        echo "Problem in $DIRNAME"
    fi
    MODIFIED=`printf "$STATUS" | grep "^ M" | wc -l`
    if [ $MODIFIED -gt 0 ]; then
        echo "Uncommitted files in $DIRNAME"
    fi
    UNTRACKED=`printf "$STATUS" | grep "??" | wc -l`
    if [ $UNTRACKED -gt 0 ]; then
        echo "Untracked files in $DIRNAME"
    fi
done
