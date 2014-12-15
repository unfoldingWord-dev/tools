#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

help() {
    echo
    echo "Creates a PDF for specified language code."
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <LangCode>"
    echo "   $PROGNAME --help"
    echo
    exit 1
}

if [ $# -lt 1 ]; then
    help
fi
while test -n "$1"; do
    case "$1" in
        --help|-h)
            help
            ;;
        --lang|-l)
            LANG="$2"
            shift
            ;;
        --ver|-v)
            VER="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

[ -z "$LANG" ] && echo "Please specify language code." && exit 1

MAILTO="publishing@unfoldingword.org"
TOOLS="/var/www/vhosts/door43.org/tools"
API="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/$LANG"
FILENAME="OBS-$LANG-v$VER"

$TOOLS/obs/export.py -l $LANG -f tex -o /tmp/$$.$FILENAME.tex

. /opt/context/tex/setuptex

cd /tmp
context $$.$FILENAME.tex

mkdir -p $API
mv -f /tmp/$$.$FILENAME.pdf $API/$FILENAME.pdf

rm -f /tmp/$$.*

URL="https://api.unfoldingword.org/obs/txt/1/$LANG/$FILENAME.pdf"
#echo "A PDF for $LANG at version $VER has been created.  " \
    #"Please download it from $URL." \
    #| mail -s "PDF Generated for $LANG" "$MAILTO"
