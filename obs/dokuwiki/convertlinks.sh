#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PROGNAME="${0##*/}"
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/

changelinks () {
    for f in `find "$1" -type f -name '*.txt'`; do

        sed -i -e "s/{{:en:obs:obs-/{{https:\/\/api.unfoldingword.org\/obs\/jpg\/1\/en\/360px\/obs-en-/g"  \
            -e 's/?nolink&640x360/?nolink/'  \
            -e 's/:https:api.unfoldingword.org:obs:jpg:1:en:360px:/https:\/\/api.unfoldingword.org\/obs\/jpg\/1\/en\/360px\//g'  \
            -e 's/{{:https:/{{https:/g'  \
            $f
    done
}

for d in `find $PAGES -type d -name 'obs' -not -path "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/uwadmin/*"`; do
    changelinks $d
    cd $d
    STATUS=`git status -s | grep "^ M" | wc -l`
    if [ $STATUS -gt 0 ]; then
        git commit -am 'Updated image links'
        git push origin master
    fi
done

# In case script is run as root, change perms back to apache
chown -R apache:apache $PAGES
