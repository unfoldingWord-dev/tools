#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  dboerschlein
#  Caleb Maclennan <caleb@alerque.com>
set -e

tagver=3dpbTEST
yyyymmdd=$(date +%Y%m%d)
#langlist="am ru tr fr pt-br en es"
langlist="ru tr"
n=$(egrep '^MAX' obs/export.py | tail -1 | awk '{print $3}')
[[ $n -eq 0 ]] && zipB=full || zipB=samples-first-$n-chapters
zipE=$zipB.zip
rm -f /tmp/$zipE /tmp/tmp.*$tagver* /tmp/[A-Za-z]*$tagver*[a-z]
for lang in $langlist
do
    obs/book/publish_PDF.sh -l $lang -v $tagver
    zip -9rj /tmp/$zipE /tmp/*${lang}*json.tmp
done
{
    formatA="%-10s%-30s%s\n"
    formatD="%-10s%-10s%-10s%-10s%s\n"
    printf "$formatA" "language" "link-counts-each-matter-part  possibly-rogue-links-in-JSON-files"
    printf "$formatA" "--------" "----------------------------  --------------------------------------------------------"
    for lang in $langlist
    do
	{
        cat /tmp/OBS-${lang}*${tagver}*tex \
            | egrep 'start.*matter|goto' \
            | sed -e 's/goto/~goto~/g' \
            | tr '~' '\n' \
            | egrep 'matter|\.com|goto' \
            | tee /tmp/$$.part \
            | egrep 'matter|goto' \
	    | tee /tmp/$$.matter-goto \
            | awk 'BEGIN{tag="none"}
                {
                    if (sub("^.*start","",$0) && sub("matter.*$","",$0)) {tag = $0 }
                    if ($0 ~ goto) { count[tag]++ }
                }
                END { for (g in count) { printf "%s=%d\n", g, count[g]; } }' \
            | sort -ru \
            > /tmp/$$.tmp
        cat /tmp/$$.part \
            | sed -e 's/[^ ]*https*:[^ ]*]//' \
            | tr ' ()' '\n' \
            | egrep 'http|\.com' \
            > /tmp/$$.bad
        printf "$formatD" "$lang" $(cat /tmp/$$.tmp) "$(echo $(cat /tmp/$$.bad))"
	}
        rm -f /tmp/$$.*
    done
} > /tmp/OBS-${tagver}-report.txt
cat /tmp/OBS-${tagver}-report.txt
zip -9rj /tmp/$zipE /tmp/[A-Za-z]*$tagver*[a-z]  /tmp/OBS-${tagver}-report.txt 
chown dboerschlein /tmp/$zipE
chmod 664 /tmp/$zipE
for lang in $langlist
do
    creE=OBS-${lang}-v${tagver}.pdf
    outE=OBS-${lang}-v${tagver}-${yyyymmdd}.pdf
    outD=/tmp/httpdocs/draft
    cp -pf /tmp/$creE $outD/$outE
    chmod 666 $outD/$outE
    chown dboerschlein $outD/$outE
    echo Created: http://test.door43.org/draft/$outE
done
