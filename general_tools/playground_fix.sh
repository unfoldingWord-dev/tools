#!/bin/bash
#
#  Ensures that the playground page says "Feel free to edit this page."

PAGE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/playground.txt
MSG="Feel free to edit this page."

grep -q "$MSG" "$PAGE" && exit 0

echo "$MSG" >"$PAGE"

exit 0
