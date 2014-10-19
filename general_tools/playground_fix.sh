#!/bin/bash
#
#  Ensures that the playground page says "Feel free to edit this page."
#  Ensures that permissions are correct in playground, too.

PDIR=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground
PAGE="$PDIR/playground.txt"
MSG="Feel free to edit this page."

[ -z $PDIR ] && mkdir -p $PDIR

echo "$MSG" >"$PAGE"

chown -R apache:apache "$PDIR"
