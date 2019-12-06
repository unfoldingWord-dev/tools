#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>

set -e

my_dir=$(cd $(dirname "$0") && pwd)

converter="${1%.*}"
converter_file="${converter}.py"
if [ ! -e "${my_dir}/${converter_file}" ]; then
  echo "Converter file does not exist: ${my_dir}/${converter_file}. Exiting..."
  exit 1
fi
shift
echo "Running converter: ${converter} with these args: ${@}"

cd "${my_dir}/../.."
python3 -m "py3.converters.${converter}" $@
