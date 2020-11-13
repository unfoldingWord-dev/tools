#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>

cd $(dirname "$0")/../..
pwd
python3 -m py3.ta.generate_pdf $@
