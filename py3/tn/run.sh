#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

cd $(dirname "$0")/../..
python3 -m py3.tn.generate_pdf $@

