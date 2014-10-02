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
    echo "Creates a namespace for door43."
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

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/"
TMPL="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/templates/"
DEST="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/$LANG/"
LANGNAMES="/var/www/vhosts/door43.org/httpdocs/lib/plugins/translation/lang/langnames.txt"

grep -qw "$LANG" "$LANGNAMES"
RET=$?
if [ $RET -ne 0 ]; then
    echo "The $LANG language code is not configured in DokuwWiki at:"
    echo "$LANGNAMES"
    echo "Please add it and run this script again"
    exit 1
fi

if [ -d "$DEST" ]; then
    echo "Language directory exists: $DEST"
    echo -n "Do you want to overwrite it $DEST/home.txt? N/y "
    read OVERWRITE
    if [ ! "$OVERWRITE" == "y" ]; then
        echo "Please manually copy the files you want from"
        echo "$TMPL to"
        echo "$DEST"
        exit 1
    fi
fi

mkdir -p "$DEST"
cp -f "$TMPL/home.txt" "$DEST"
cp -f "$TMPL/sidebar.txt" "$DEST"

# Replace LANGCODE placeholder with destination language code
for f in `find "$DEST" -type f -name '*.txt'`; do
    sed -i "s/LANGCODE/$LANG/g" "$f"
done

# Set permissions
chown -R apache:apache "$DEST"

# Create a github repo for this language
/var/www/vhosts/door43.org/tools/obs/dokuwiki/d43-git-init.py "$LANG"
