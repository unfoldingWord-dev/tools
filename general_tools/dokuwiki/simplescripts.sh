#
# These are short snippets that are useful for accomplishing certain tasks.
#

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
