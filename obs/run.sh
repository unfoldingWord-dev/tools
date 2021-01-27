#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>

set -e

my_dir=$(cd $(dirname "$0") && pwd)

cd "${my_dir}/.."
python3 -m "obs.txt_to_md" $@
