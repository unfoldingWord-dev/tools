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
    echo "   $PROGNAME -l <LangCode> [--notes] [--src <LangCode>]"
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
        --notes)
            NOTES="YES"
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

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/"
TMPL="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/templates/obs3/"
DEST="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/$LANG/"
LANGNAMES="/var/www/vhosts/door43.org/httpdocs/lib/plugins/translation/lang/langnames.txt"
OBS="$DEST/obs/"

if [ ! -d "$DEST" ]; then
    /var/www/vhosts/door43.org/tools/obs/dokuwiki/ns-creator.sh -l "$LANG"
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

if [ -d "$OBS" ]; then
    echo "OBS directory exists: $OBS"
    echo -n "Do you want to overwrite it with new OBS content? N/y "
    read OVERWRITE
    if [ ! "$OVERWRITE" == "y" ]; then
        echo "Please manually copy the files you want from"
        echo "$TMPL to"
        echo "$OBS"
        exit 1
    fi
fi

# Make OBS
rsync -ha "$TMPL" "$DEST"

# Update home and sidebar for langauge to include OBS information
echo '
===== Resources =====

  * **[[LANGCODE:obs|Open Bible Stories (LANGCODE)]]**' >> "$DEST/home.txt"
echo '
**Resources**

  * [[LANGCODE:obs|Open Bible Stories (LANGCODE)]]

**Latest OBS Status**
{{page>en:uwadmin:LANGCODE:obs:status}}' >> "$DEST/sidebar.txt"

cp "$DEST/sidebar.txt" "$OBS"

# Replace LANGCODE placeholder with destination language code
for f in `find "$DEST" -type f -name '*.txt'`; do
    sed -i -e "s/LANGCODE/$LANG/g" "$f"
done

# Make uwadmin status page
mkdir -p "$PAGES/en/uwadmin/$LANG/obs"
cp -i "${TMPL%%/obs3/}/status.txt" "$PAGES/en/uwadmin/$LANG/obs/"
sed -i "s/ORIGDATE/`date +%F`/" "$PAGES/en/uwadmin/$LANG/obs/status.txt"

# Update the changes pages
/var/www/vhosts/door43.org/tools/obs/dokuwiki/obs-gen-changes-pages.sh

# function for git work
gitPush () {
    cd "$1"
    git add . >/dev/null
    git commit -am "$2" >/dev/null
    git push origin master >/dev/null
    cd -
}

gitPush "$PAGES/en/uwadmin/" "Added uwadmin obs page for $LANG"
gitPush "$DEST" "Initial import of OBS"

# Copy Notes and Key-Terms if requested
if [ "$NOTES" == "YES" ]; then
    /var/www/vhosts/door43.org/tools/obs/dokuwiki/obs-notes-creator.sh -l "$LANG" --src "$SRC"
fi

# Set permissions
chown -R apache:apache "$DEST"
