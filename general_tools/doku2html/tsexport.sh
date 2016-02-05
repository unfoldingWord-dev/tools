#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>

# Exports Key Terms, Translation Notes, and Translation Academy to HTML
# for the Translation Studio app.

BASEDIR=$(cd $(dirname "$0")/../../ && pwd)
D2H="$BASEDIR/general_tools/doku2html/dokuwiki2html.sh"
SRCBASE="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en"
DSTBASE="/var/www/vhosts/door43.org/ts-exports"

echo "Converting to HTML..."
"$D2H" -s "$SRCBASE/obs/notes/" -d "$DSTBASE/notes/" &
"$D2H" -s "$SRCBASE/obs/key-terms/" -d "$DSTBASE/key-terms/" &
"$D2H" -s "$SRCBASE/ta/" -d "$DSTBASE/ta/" &

wait

echo "Updating Links..."
for f in `find "$DSTBASE" -type f -name '*.html'`; do
    sed -i -e 's/en\/obs\/notes\/frames/en\/notes\/frames/g' $f
done
echo "Done."
