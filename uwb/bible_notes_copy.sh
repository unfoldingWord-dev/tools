#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

COMPLETED_BOOKS="rut luk tit"

help() {
    echo
    echo "Copies Bible Notes from English to specified language"
    echo
    echo "Usage:"
    echo "   $PROGNAME -l <LangCode> [--src <LangCode>]"
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
        --src)
            SRC_LANG="$2"
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
[ "$LANG" == 'en' ] && echo "Will not copy to en." && exit 1
[ -z "$SRC_LANG" ] && SRC_LANG="en"

[ "$SRC_LANG" != 'en' ] && echo "Non en source not implemented" && exit 1

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"
SRC="$PAGES/$SRC_LANG"
DST="$PAGES/$LANG"
NOTES="bible/notes"
SRC_NOTES="$SRC/$NOTES"
DST_NOTES="$DST/$NOTES"

if [ ! -d "$DST" ]; then
    echo "Language namespace does not exist: $DST"
    exit 1
fi

if [ ! -d "$DST_NOTES" ]; then
    mkdir -p "$DST_NOTES"
fi

# Copy pages that don't already exist
for BOOK in $COMPLETED_BOOKS; do
    cd "$SRC_NOTES/$BOOK/"
    for f in `grep -rIe '{{tag.*publish ' * | cut -f 1 -d ':'`; do
        DST_DIR="$DST_NOTES/$BOOK/${f%/*}"
        FILE="${f##*/}"
        [ -d "$DST_DIR" ] || mkdir -p "$DST_DIR"
        cp -vn "$f" "$DST_DIR/$FILE"
    done
done

# Update links
for f in `find "$DST_NOTES" -type f -name '*.txt'`; do
    sed -i -e "s/$SRC_LANG\/bible\/notes/$LANG\/bible\/notes/g" \
           -e "s/$SRC_LANG:bible:notes/$LANG:bible:notes/g" \
           "$f"
done

gitPush () {
    cd "$1"
    git add . >/dev/null
    git commit -am "$2" >/dev/null
    git push origin master >/dev/null
    cd -
}

#gitPush "$DST_NOTES" "Import of Bible notes from $SRC_LANG"

# Set permissions
chown -R apache:apache "$DST_NOTES"
