#!/bin/bash
#

### exclude admin-reports

index () {
    cd $1
    for f in `find * -type f | sort -r`; do
        f=${f%%.txt}
        f=${f//\//%3A}
        #echo "https://door43.org/lib/exe/indexer.php?id=en%3A$2%3A$f"
        wget -q -U 'd43' -O /dev/null "https://door43.org/lib/exe/indexer.php?id=en%3A$2%3A$f"
    done
}

index /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obe obe
index /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ta ta
index /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible bible
