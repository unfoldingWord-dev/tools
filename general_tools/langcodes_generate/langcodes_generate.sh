#!/bin/bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Tim Jore <tim@distantshores.org>
#  Caleb Maclennan <caleb@alerque.com>

###############################################################################
#
#  This script dumps the language codes configured in Door43 (Dokuwiki).
#
###############################################################################

LANGCODES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/media/exports/meta/langcodes.txt
BASEDIR=$(cd $(dirname "$0")/../../ && pwd)
HELPER="general_tools/langcodes_generate/helper.php"

php $BASEDIR/$HELPER > $LANGCODES

chmod -w $LANGCODES

exit 0
