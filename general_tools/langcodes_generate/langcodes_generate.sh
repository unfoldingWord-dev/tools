#!/bin/bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Tim Jore <tim@distantshores.org>

###############################################################################
#
#  This script dumps the language codes configured in Door43 (Dokuwiki).
#
###############################################################################

LANGCODES=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/media/exports/meta/langcodes.txt
TOOLS=/var/www/vhosts/door43.org/tools
HELPER="general_tools/langcodes_generate/helper.php"

php $TOOLS/$HELPER > $LANGCODES

chmod -w $LANGCODES

exit 0
