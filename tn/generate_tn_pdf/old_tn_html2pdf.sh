#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>

#npm i
#node getResources ./
cd $(dirname "$0")/../../..
python -m tools.tn.generate_tn_pdf.export_md_to_pdf $@
