#!/usr/bin/env sh
# -*- coding: utf8 -*-
#  Copyright (c) 2013 Jesse Griffin
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

# Exports Key Terms, Translation Notes, and Translation Academy to HTML
# for the Translation Studio app.

PROGNAME="${0##*/}"
D2H="/var/www/vhosts/door43.org/tools/general_tools/doku2html/dokuwiki2html.sh"
SRCBASE="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en"
DSTBASE="/var/www/vhosts/door43.org/ts-exports"

echo "Converting to HTML..."
"$D2H" -s "$SRCBASE/obs/notes/" -d "$DSTBASE/notes/" &
"$D2H" -s "$SRCBASE/key-terms/" -d "$DSTBASE/key-terms/" &
"$D2H" -s "$SRCBASE/ta/" -d "$DSTBASE/ta/" &

wait

echo "Updating Links..."
for f in `find "$DSTBASE" -type f -name '*.html'`; do
    sed -i -e 's/en\/obs\/notes\/frames/en\/notes\/frames/g' $f
done
echo "Done."
