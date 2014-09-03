#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

#Should be safe to run, but just in case:
exit 1

PROGNAME="${0##*/}"
PAGES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/

changelinks () {
    for f in `find "$1" -maxdepth 1 -type f -name '[0-5][0-9].txt'`; do

        sed -i -e "s/:en:obs:obs-/https:\/\/api.unfoldingword.org\/obs\/jpg\/1\/en\/360px\/obs-en-/g"  \
            -e 's/?nolink&640x360//'  \
            $f
    done
}

for d in `find $PAGES -type d -name 'obs' -not -path "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/uwadmin/*"`; do
    changelinks $d
done

