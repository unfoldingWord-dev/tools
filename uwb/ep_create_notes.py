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
import fnmatch
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException

link = 'https://pad.door43.org/p/{0}'
nextfmt = 'https://pad.door43.org/p/en-udb-luk-01'
notes = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes/'


def find(pattern, top):
    # Based off of http://www.dabeaz.com/generators-uk/genfind.py
    for path, dirlist, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, pattern):
            yield os.path.join(path, name)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        book = str(sys.argv[1]).strip()
    else:
        print 'Please specify the book to load.'
        sys.exit(1)
    try:
        pw = open('/root/.ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw})
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    book_notes = '{0}/{1}'.format(notes, book)
    for f in find('*.txt', book_notes):
        if 'questions' in f: continue
        pad_text = codecs.open(f, 'r', encoding='utf-8').read()
        parts = f.split('/')
        pad_name = '-'.join(['en', 'bible', book, parts[-2],
                                               parts[-1].replace('.txt', '')])
        try:
            ep.createPad(padID=pad_name, text=pad_text)
            print link.format(pad_name)
        except EtherpadException as e:
            print '{0}: {1}'.format(e, pad_name)
        break
