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
    echo "Setup OBS for a new language."
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
            SRC="$2"
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
[ -z "$SRC" ] && SRC="en"

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"
SRCNOTES="$PAGES/$SRC/obs/notes"
DEST="$PAGES/$LANG/obs"

if [ ! -d "$DEST" ]; then
    echo "Run \`obs-creator.sh -l $LANG --notes\` instead."
    exit 1
fi

# Copy Notes and Key-Terms
rsync -ha $SRCNOTES* $DEST/

# Replace LANGCODE placeholder with destination language code
for f in `find "$DEST" -type f -name '*.txt'`; do
    sed -i -e "s/LANGCODE/$LANG/g" \
           -e "s/$SRC\/obs\/notes/$LANG\/obs\/notes/g" \
           -e "s/$SRC:obs:notes/$LANG:obs:notes/g" \
        "$f"
done

# function for git work
gitPush () {
    cd "$1"
    git add . >/dev/null
    git commit -am "$2" >/dev/null
    git push origin master >/dev/null
    cd -
}

if [ -d "$PAGES/$LANG/.git" ]; then
    gitPush "$DEST" "Added source for notes and key terms."
fi

# Set permissions
chown -R apache:apache "$DEST"
