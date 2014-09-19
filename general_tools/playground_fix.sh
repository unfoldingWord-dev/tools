#!/bin/bash
#
#  Ensures that the playground page says "Feel free to edit this page."
#  Ensures that permissions are correct in playground, too.

PAGE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/playground.txt
MSG="Feel free to edit this page."

chown -R apache:apache "${PAGE%/*}"

grep -q "$MSG" "$PAGE" && exit 0

echo "$MSG" >"$PAGE"
chown apache:apache "$PAGE"

exit 0
