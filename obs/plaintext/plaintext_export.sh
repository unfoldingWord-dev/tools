#!/bin/bash

###############################################################################
#
#  `plaintext_export` is a script that exports the complete text of Open
#  Bible Stories in every language on Door43 (in which it is available) as
#  plain text and ODT.
#
#  It is intended to help facilitate the recording of the audio files for
#  Open Bible Stories
#
###############################################################################

ROOT=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages
FILE=$ROOT/en/obs/01-the-creation.txt
DEST=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/exports
TMP=/tmp/tmpfile.txt

#
# remove extra info from images
#
cat $FILE | \
grep -v ".jpg" > $TMP

#
# convert wiki text markdown
#
#doku2html $TMP | \
#sed 's/_media/var\/www\/vhosts\/door43\.org\/httpdocs\/data\/media/g' | \
#pandoc -f html -s -t odt -o file.odt

doku2html $TMP | \
pandoc -f html -s -t markdown -o /tmp/tmpfile.md

exit 0