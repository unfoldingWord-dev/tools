#!/bin/bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

ROOT=/var/www/vhosts/door43.org/httpdocs
touch $ROOT/conf/local.php
touch $ROOT/inc/parser/xhtml.php

wget -O /dev/null -q https://door43.org/lib/exe/js.php?purge=true
wget -O /dev/null -q https://door43.org/lib/exe/css.php?purge=true
