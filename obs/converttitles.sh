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

ROOT=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages

changefiles () {
    for f in `find "$1" -maxdepth 1 -type f -name '[0-9][0-9]-*.txt'`; do
        mv "$f" ${f%/*}/`echo ${f##*/} | grep -o '[0-9][0-9]'`.txt
    done
}

for l in `find $ROOT -type d -name 'obs'`; do
    changefiles $l
done

for l in `find $ROOT -type d -name 'obs-training'`; do
    changefiles $l
done

# Update links
for x in `find $ROOT -type f -name '*.txt'`; do
    sed -i  -e 's/\(obs:[0-9][0-9]\)-[a-z\-]*/\1/g' \
            -e 's/\(training:[0-9][0-9]\)-[a-z\-]*/\1/g' $x
done

