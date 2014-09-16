#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>


"""
"""

import os
import sys
import codecs
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException

link = 'https://pad.door43.org/p/{0}-{1}-{2}-{3}'
nextfmt = 'https://pad.door43.org/p/en-udb-luk-01'


if __name__ == '__main__':
    if len(sys.argv) > 1:
        chapterfile = str(sys.argv[1]).strip()
        if not os.path.exists(chapterfile):
            print 'File not found: {0}'.format(chapterfile)
            sys.exit(1)
    else:
        print 'Please specify the file to load.'
        sys.exit(1)
    try:
        pw = open('/root/.ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw})
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    chapter_text = open(chapterfile, 'r').read()
    parts = chapterfile.split('/')
    lang = parts[9]
    ver = parts[10]
    bk = parts[12]
    chp = parts[13].replace('.usfm.txt', '')
    if 'psa' not in chapterfile:
        chp = chp.lstrip('0').zfill(2)
    pad_name = '-'.join([lang, ver, bk, chp])

    i = int(chp)
    next = link.format(lang, ver, bk, str(i + 1).zfill(2))
    if i == 1:
        prev = ''
    else:
        prev = link.format(lang, ver, bk, str(i - 1).zfill(2))

    pad_text = '\n'.join([prev, chapter_text, next])

    try:
        ep.createPad(padID=pad_name, text=pad_text)
    except EtherpadException as e:
        print '{0}: {1}'.format(e, pad_name)
