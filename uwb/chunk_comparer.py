#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>

'''
Script to compare ids between different source texts.
'''

import os
import sys
import json
import codecs
import argparse


def getList(json_book):
    fr_list = []
    for chp in json_book['chapters']:
        for fr in chp['frames']:
            fr_list.append(fr['id'])
    return fr_list

def main(base_file, comp_file):
    base = codecs.open(base_file, 'r', encoding='utf-8').read()
    base_json = json.loads(base)
    base_ids = getList(base_json)
    comp = codecs.open(comp_file, 'r', encoding='utf-8').read()
    comp_json = json.loads(comp)
    comp_ids = getList(comp_json)
    missing_comp = (set(base_ids) - set(comp_ids))
    if missing_comp:
        print 'Missing from comp file: %s' % missing_comp
    missing_base = (set(comp_ids) - set(base_ids))
    if missing_base:
        print 'Missing from base file: %s' % missing_base
    if not missing_comp and not missing_base:
        print 'Same ids!'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-b', '--base', dest="base", default=False,
        required=True, help="Base Text")
    parser.add_argument('-c', '--comparison', dest="comp", default=False,
        required=True, help="Comparison text")

    args = parser.parse_args(sys.argv[1:])
    main(args.base, args.comp)
