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
# These are short snippets that are useful for accomplishing certain tasks.
#

: ${BIBLE_NOTES_DIR:=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes}

for f in `find $BIBLE_NOTES_DIR -type f -name '[0-9]*.txt'`; do
    sed -i -e '/:kt:/s/|[^]]*\]\]/\]\]/g' \
        -e '/:other:/s/|[^]]*\]\]/\]\]/g' \
        -e '/:ta:/s/|[^]]*\]\]/\]\]/g' \
        $f
done
