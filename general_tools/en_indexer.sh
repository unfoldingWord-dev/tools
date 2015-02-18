#!/bin/bash
#

BIBLE=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible

cd $BIBLE

for f in `find * -type f | sort -r`; do
    echo "wget -q -U 'd43' -O /dev/null http://door43.org/en/bible/${f%%.txt}"
    wget -q -U 'd43' -O /dev/null http://door43.org/en/bible/${f%%.txt}
done
