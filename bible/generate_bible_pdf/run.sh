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
python -m tools.bible.generate_bible_pdf.generate_bible_pdf $@
