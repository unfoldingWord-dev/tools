#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

LANG="$1"

[ -z "$LANG" ] && echo "Please specify language code." && exit 1

OBSMETA="/var/www/vhosts/door43.org/httpdocs/data/meta/$LANG/obs"

echo "Contributors for $LANG:"
cut -f 5 $OBSMETA/[0-5][0-9]-*.changes | sort | uniq | paste -s -d ';'
