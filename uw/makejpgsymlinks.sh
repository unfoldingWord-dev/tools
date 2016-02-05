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
    echo "Creates image symlinks for a new language."
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

[ -z "$LANG" ] && echo "Please specify language code." && exit 1

SRC="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/en"
LANGDIR="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/$LANG"

[ -d $LANGDIR ] && echo 'Image links already exist...' && exit 0

# Make directories
for d in `find $SRC -type d`; do 
    [ "$SRC" == "$d" ] && continue
    ld="${d##*/}"
    mkdir -p "$LANGDIR/$ld"
done

# Make symlinks
for x in `find $SRC -type f`; do 
    lf=`echo $x | sed "s/en/$LANG/g"`
    ln -s $x $lf
done
