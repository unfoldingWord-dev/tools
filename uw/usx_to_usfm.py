#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Converts a given USX file to USFM. This is a work in progress, supporting the tags that transationStudio used for USX.
'''

import sys
import re

def convert(filepath):
    newcontent = '';

    with open(filepath) as f:
        for line in f:
            newcontent += re.sub(r'<verse number="(\d+)" style="v" />', '\\\\v \g<1> ', line)
    return newcontent

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: usx_to_usfm.py </path/to/file>"
        exit(1)

    filepath = sys.argv[1]

    print convert(filepath)


