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
    echo "Publish OBS."
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
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

if [ -z "$lang" ]; then
    echo "Error: language to export must be specified."
    help
fi
# Run export of OBS to JSON
/var/www/vhosts/door43.org/tools/obs/json/json_export.py -l $LANG -e
RETCODE=$?
[ $RETCODE -ne 0 ] && exit 1

VER=`/var/www/vhosts/door43.org/tools/uw/get_ver.py $LANG`

# Create PDF via TeX for languages exported
#/var/www/vhosts/door43.org/tools/obs/book/publish_PDF.sh -l $LANG -v $VER
/var/www/vhosts/door43.org/tools/obs/book/odt_export.sh -l $LANG

# Create image symlinks on api.unfoldingword.org
/var/www/vhosts/door43.org/tools/uw/makejpgsymlinks.sh -l $LANG

# Create web reveal.js viewer
/var/www/vhosts/door43.org/tools/obs/js/reveal_export.py

# Run update of v2 API
/var/www/vhosts/door43.org/tools/uw/update_catalog.py
