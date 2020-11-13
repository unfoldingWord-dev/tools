#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

set -e
set -x

MY_DIR=$(cd $(dirname "$0") && pwd)

pip3 install --upgrade -r "${MY_DIR}/../requirements.txt"

cd resources
npm i
node ./getResources.js ./

rm -rf en/translationHelps en/bibles/t4t en/bibles/udb en/bibles/ulb
rm -rf kn/translationHelps
rm -rf hbo/bibles
rm -rf el-x-koine/bibles
