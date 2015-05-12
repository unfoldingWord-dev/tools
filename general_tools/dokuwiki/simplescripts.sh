# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#
# These are short snippets that are useful for accomplishing certain tasks.
#


# Remove lame zero width junk (​) with
    sed -i 's/\xe2\x80\x8b//g' inputfile



sed -i "s/topic>/topic>:en:bible?/" $f

ktupdater () {
    cd /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obe/$1
    for x in `ls`; do
       name=${x%%.txt}
       for f in `grep -re "en:bible:notes:key-terms:$name" ../../bible/* | grep txt | cut -f 1 -d ':'`; do
           sed -i "s/en:bible:notes:key-terms:$name/en:obe:$1:$name/g" $f
           echo "$name in $f"
       done
    done
}

ktupdater kt
ktupdater other

cd /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en
for x in `grep -re 'en:obs:notes:key-terms:home' * | grep txt | cut -f 1 -d ':'`; do
    sed -i "s/en:obs:notes:key-terms:home/en:obe:ktobs/g" $x
done

cd /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obe/kt
for x in `ls`; do
    if [ -f "../../obs/notes/key-terms/$x" ]; then
       name=${x%%.txt}
       for f in `grep -re "en:obs:notes:key-terms\/$name" ../../* | grep txt | cut -f 1 -d ':'`; do
           sed -i "s/en:obs:notes:key-terms\/$name/en:obe:kt:$name/g" $f
       done
    fi
done

cd /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/obe/other
for x in `ls`; do
    if [ -f "../../obs/notes/key-terms/$x" ]; then
       name=${x%%.txt}
       for f in `grep -re "en:obs:notes:key-terms\/$name" ../../* | grep txt | cut -f 1 -d ':'`; do
           sed -i "s/en:obs:notes:key-terms\/$name/en:obe:other:$name/g" $f
       done
    fi
done

replacer () { 
    cd /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/
    for f in `grep -re "en:obs:notes:key-terms\/$1" * | grep txt | cut -f 1 -d ':'`; do
        echo $f
        sed -i "s/en:obs:notes:key-terms\/$1/en:obe:$3:$2/g" $f
    done
}

# Seds to fix image links and Zim Wiki content headers
sed -i -e 's/..\/..\/images/https:\/\/api.unfoldingword.org\/obs\/jpg\/1\/en\/360px/' \
    -e 's/obs-/obs-fa-/' -e '/Content-Type/d' -e '/Wiki-Format/d'
# Adds DW italic (reference) markers to last line of file.
sed -i -e '$s/^/\/\//' -e '$s/$/\/\//'

# Adds comprehension questions for Bible books
for f in `find . -maxdepth 1 -type d`; do
    [ -d "$f/questions/comprehension" ] && continue
    bk="${f##*/}"
    [ "$bk" == "key-terms" ] && continue
    [ "$bk" == "checking" ] && continue
    [ "$bk" == "." ] && continue

    book=`python /var/www/vhosts/door43.org/tools/general_tools/get_bible_book.py $bk`
    echo $book

    mkdir -p $bk/questions/comprehension
    for chp in `ls $bk`; do
        cp /tmp/qt.txt $bk/questions/comprehension/${chp}.txt
        sed -i -e "s/book_name/$book/" \
               -e "s/chp_num/$chp/" \
               -e "s/bk_name/$bk/" \
               $bk/questions/comprehension/${chp}.txt
    done
    rm -f $bk/questions/comprehension/questions.txt
    echo -e "~~NOCACHE~~\n\n<nspages en:bible:notes:$bk:questions:comprehension -title -naturalOrder -simpleList -exclude:home -textPages=\"$book Comprehension Questions\">" > $bk/questions/comprehension/home.txt
done

# Add '~~DISCUSSION~~' to pages that don't already have it
for f in `ls`; do
    grep -q 'DISCUSSION' $f && continue
    echo -e '\n~~DISCUSSION~~' >>$f;
done

# Add '~~NOCACHE~~' to pages that are using tags and don't already have it
for f in `grep -re '^{{tag' * | cut -f 1 -d ':'`; do
    grep -q 'NOCACHE' $f && continue
    echo -e '\n~~NOCACHE~~' >>$f;
done

# Cycles through all namespaces and does something
for x in `find /var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages -maxdepth 1 -type d`; do
    [ "$x" == "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages" ] && continue
    [ "$x" == "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground" ] && continue
    [ "$x" == "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/templates" ] && continue
    [ "$x" == "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/.git" ] && continue
    cd $x
    LCODE="${x##*/}"
    # This bit adds a link to the sidebar
    grep -q ethnologue sidebar.txt && continue
    echo -e "\n**Language Information**\n\n[[http://www.ethnologue.com/language/$LCODE|Ethnologue data]]" >>sidebar.txt
    git commit sidebar.txt -m 'Added ethnologue link'
    git push origin master
    chown -R apache:apache .
done


# Find files owned by root and chown them to apache
find meta/ -uid 0 -exec chown 48:48 {} \;
