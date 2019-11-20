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
RESOURCE_DIR="/tmp/tn_resources"

pip3 install -r "${MY_DIR}/../requirements.txt"
mkdir -p "${RESOURCE_DIR}"
cp package.json "${RESOURCE_DIR}"
cp getResources.js "${RESOURCE_DIR}"
cd "${RESOURCE_DIR}"
npm i
node ./getResources.js ./
