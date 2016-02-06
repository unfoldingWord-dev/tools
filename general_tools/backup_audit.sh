#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

ROOT=/mnt/backups/home/backups/
MAILTO=jesse@unfoldingword.org

cd "$ROOT"

DIRS=`find . -type d -maxdepth 1`

for x in $DIRS; do
    [ "$x" == "./collaborate" ] && continue
    [ "$x" == "./.ssh" ] && continue
    [ "$x" == "./sfows02" ] && continue
    [ "$x" == "./s3" ] && continue
    [ "$x" == "./vts" ] && continue
    FILES=""
    FILES=`find $x -type f -maxdepth 3 -mtime -1`
    if [ -z "$FILES" ]; then
        FAIL+=" $x"
    fi
done

# Email if there are any failures
if [ "$FAIL" != "" ]; then
  echo Check Backups on "${FAIL}". | mail -s "Backup Failure Detected" $MAILTO
fi
