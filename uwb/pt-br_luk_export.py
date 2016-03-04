#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>
#

'''
Exports the pt-br Luke translation from the Notes pages, formats as USFM.
'''

import os
import re
import glob
import codecs


targetULBre = re.compile(ur'=====? ?Tara?get ULB:? ?=====?(.*?)----', 
                                                      re.UNICODE | re.DOTALL)
digitre = re.compile(ur'([0-9][0-9]?)', re.UNICODE | re.DOTALL)


def getText(f):
    page = codecs.open(f, 'r', encoding='utf-8').read()
    text = targetULBre.search(page).group(1)
    text = convertVerses(text)
    return u'\n{0}\n'.format(text.strip())

def convertVerses(t):
    return digitre.sub(ur'\n\\v \1', t)


if __name__ == '__main__':
    root = '/home/jesse/vcs/d43-pt-br/bible/notes/luk'
    luk = []
    chunks = glob.glob('{0}/*/*.txt'.format(root))
    chunks.sort()
    for f in chunks:
        if 'home.txt' in f: continue
        if '00/intro.txt' in f: continue
        luk.append(u'\n\s5')
        if f.endswith('01.txt'):
          luk.append(u'\n\c {0}'.format(int(f.split('/')[8])))
        luk.append(getText(f))

    f = codecs.open('{0}/luk.usfm'.format(root), 'w', encoding='utf-8')
    f.write(u''.join(luk))
    f.close()
    print '{0}/luk.usfm'.format(root)
