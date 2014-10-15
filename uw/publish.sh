#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

# Run export of OBS to JSON
/var/www/vhosts/door43.org/tools/obs/json/json_export.py \
    --unfoldingwordexport >>/tmp/$$.json_export

# Find exported languages, exit if none
LANGS=`grep "Exporting to unfoldingWord" /tmp/$$.json_export | cut -f 5 -d ' '`
[ -z "$LANGS" ] && exit 0

for LANG in $LANGS; do
    VER=`/var/www/vhosts/door43.org/tools/uw/get_ver.py $LANG`
    # Create PDF via TeX for languages exported
    /var/www/vhosts/door43.org/tools/obs/book/publish_PDF.sh -l $LANG -v $VER

    # Create image symlinks on api.unfoldingword.org
    /var/www/vhosts/door43.org/tools/uw/makejpgsymlinks.sh -l $LANG
done

# Create web reveal.js viewer
/var/www/vhosts/door43.org/tools/obs/js/reveal_export.py

# Cleanup
rm -f /tmp/$$.*
