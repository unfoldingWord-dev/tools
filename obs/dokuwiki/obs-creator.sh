#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

LANG="$1"

[ -z "$LANG" ] && echo "Please specify language code." && exit 1

PAGES="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/"
TMPL="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/templates/obs3/"
DEST="/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/$LANG/"
LANGNAMES="/var/www/vhosts/door43.org/httpdocs/lib/plugins/translation/lang/langnames.txt"
OBS="$DEST/obs/"

if [ ! -d "$DEST" ]; then
    /var/www/vhosts/door43.org/tools/obs/dokuwiki/ns-creator.sh "$LANG"
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
mkdir -p "$OBS"
rsync -ha "$TMPL" "$OBS"

############ Make Notes and Key-Terms if requested

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
    sed -i "s/LANGCODE/$LANG/g" "$f"
done

# Set permissions
chown -R apache:apache "$DEST"

# Make uwadmin status page
mkdir -p "$PAGES/en/uwadmin/$LANG/obs"
cp -i "${TMPL%%/obs3/}/status.txt" "$PAGES/en/uwadmin/$LANG/obs/"
sed -i "s/ORIGDATE/`date +%F`/" "$PAGES/en/uwadmin/$LANG/obs/status.txt"

# Update the changes pages
/var/www/vhosts/door43.org/tools/obs/dokuwiki/obs-gen-changes-pages.sh

# function for git work
gitPush () {
    cd "$1"
    git add .
    git commit -am "$2"
    git push
    cd -
}

gitPush "$PAGES/en/uwadmin/" "Added uwadmin obs page for $LANG"
gitPush "$OBS" "Initial import of OBS"
