#!/bin/ksh
tagver=3testDPB
tagver=20150522-draft-samples-DPB
n=$(egrep '^MAX' obs/export.py| awk '{print $3}')
[[ $n -eq 0 ]] && zipE=full.zip || zipE=samples.zip
rm -f /tmp/$zipE /tmp/tmp.*$tagver* /tmp/[A-Za-z]*$tagver*[a-z]
#for lang in en es fr pt-br ru
for lang in am ru fr pt-br en es
do
    obs/book/publish_PDF.sh -l $lang -v $tagver
    zip -9rj /tmp/$zipE /tmp/*${lang}*json.tmp
done
{
    formatA="%-10s%-30s%s\n"
    formatD="%-10s%-10s%-10s%-10s%s\n"
    printf "$formatA" "language" "link-counts-each-matter-part  possibly-rogue-links-in-JSON-files"
    printf "$formatA" "--------" "----------------------------  --------------------------------------------------------"
    for lang in am ru fr pt-br en es
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
exit
