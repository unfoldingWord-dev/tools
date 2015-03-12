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
