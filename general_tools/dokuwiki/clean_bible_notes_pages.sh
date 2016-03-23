#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#
# This script is to clean up the Dokuwiki pages in the en/bible/notes namespace
#

: ${BIBLE_NOTES_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes}

for f in `find $BIBLE_NOTES_DIR -type f -name '[0-9]*.txt'`; do
    sed -i -e 's/\(:\(ta\|other\|kt\):[^]]\+\)|[^]]\+]]/\1]]/g' $f
done
