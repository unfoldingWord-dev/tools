#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

# Still testing, so exit here
echo 'running' >>/tmp/publish.out
id >>/tmp/publish.out
exit 0

# Run export of OBS to JSON
/var/www/vhosts/door43.org/tools/obs/json/json_export.py \
    --unfoldingwordexport >>/tmp/$$.json_export

# Find exported languages, exit if none
LANGS=`grep "Exporting to unfoldingWord" /tmp/$$.json_export | cut -f 5 -d ' '`
[ -z "$LANGS" ] && exit 0

# Create PDF via TeX for languages exported
for LANG in $LANGS; do
    /var/www/vhosts/door43.org/tools/obs/book/publish_PDF.sh -l $LANG
done

# Create web reveal.js viewer
/var/www/vhosts/door43.org/tools/obs/js/reveal_export.py

# Cleanup
rm -f /tmp/$$.*
