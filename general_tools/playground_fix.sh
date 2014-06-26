#!/bin/bash
#
#  Ensures that the playground page says "Feel free to edit this page."
#  Ensures that permissions are correct in playground, too.

PAGE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/playground.txt
MSG="Feel free to edit this page."

chown -R apache:door43 "${PAGE%/*}"

grep -q "$MSG" "$PAGE" && exit 0

echo "$MSG" >"$PAGE"
chown apache:door43 "$PAGE"

exit 0
