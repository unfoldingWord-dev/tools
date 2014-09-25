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
import re
import sys
import codecs
import urllib2
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException
## Import the bookKeys mapping from USFM-Tools
USFMTools='/var/www/vhosts/door43.org/USFM-Tools/support'
sys.path.append(USFMTools)
try:
    from books import bookKeys
except ImportError:
    print "Please ensure that {0}/books.py exists.".format(USFMTools)
    sys.exit(1)


TFTURL = 'https://door43.org/_export/raw/en/udb/v1/{0}/{1}.usfm'
TMPL = u'''====== {1} ======


===== TFT: =====

<usfm>
{0}
</usfm>


===== UDB: =====

<usfm>
{7}
</usfm>


===== ULB: =====

<usfm>
{8}
</usfm>


===== Important Terms: =====

  * **[[:en:uwb:notes:key-terms:example|example]]**
  * **[[:en:uwb:notes:key-terms:example|example]]**
 

===== Translation Notes: =====


    * **bold words**  - explanation
    * **bold words**  - explanation
  
===== Links: =====

  * **[[en/bible-training/notes:{6}/questions/comprehension/{4}|Luke Chapter {4} Checking Questions]]**
  * **[[en/bible-training/notes:{6}/questions/checking/{5}-checking|{5} Checking Questions]]**

 

**[[en/bible-training/notes:{2}|<<]] | [[en/bible-training/notes:{3}|>>]]**'''
refre = re.compile(ur'\\v.([0-9][0-9]?[0-9]?)')


def splice(ulb, udb, tft):
    chunks = {}
    for i in ulb.split('\n\\s5'):
        if i.startswith('https'): continue
        ref_list = refre.findall(i)
        ref = ','.join(ref_list)
        print ref
        chunks[ref] = {}
        chunks[ref]['ulb'] = i.strip()
        chunks[ref]['udb'] = getTXT(ref_list, udb)
        chunks[ref]['tft'] = getTXT(ref_list, tft)
    return chunks

def getTXT(refs, txt):
    chunks = []
    for r in refs:
        ## Need to match end of string where \v doesn't start new verse
        versep = ur'\\v.{0}.*?\\v'.format(r)
        verse = re.search(versep, txt, re.DOTALL).group(0)
        chunks.append(verse.rstrip('\\v').strip())
    return '\n'.join(chunks)

def getpath(r):
    fill = 2
    try:
        book, ref = r.split(' ')
        #bk = books[book]
        c, vv = ref.split(':')
        v = vv.split('-')[0]
        if 'psa' in book.lower():
           fill = 3
        return '{0}/{1}/{2}.txt'.format(book, c.zfill(fill), v.zfill(fill))
    except:
        return False

def writeFile(f, content):
    makeDir(f.rpartition('/')[0])
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()

def makeDir(d):
    '''
    Simple wrapper to make a directory if it does not exist.
    '''
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def genNav(chunked, usfmbk):
    '''
    Walks the generated folder and creates next and previous links.
    '''
    for e in chunked:
        #e[0] is filepath, e[1] is text, e[2] is ref
        i = chunked.index(e)
        prv = getNav(chunked, i-1)
        nxt = getNav(chunked, i+1)
        chp = e[2].split()[1].split(':')[0]
        bk = e[2].split()[0]
        writeFile(e[0], TMPL.format(e[1], e[2], prv, nxt, chp, bk, usfmbk))

def getNav(chunked, i):
    if i == -1:
        return ''
    elif i >= len(chunked):
        return ''
    return chunked[i][0]

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
    except:
        print "  => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    return request


if __name__ == '__main__':
    if len(sys.argv) > 1:
        pad_name = str(sys.argv[1]).strip()
    else:
        print 'Please specify the pad to chunk.'
        sys.exit(1)
    try:
        pw = open('/root/.ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw})
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    lang,ver,bk,chp = pad_name.split('-')
    ulb = ep.getText(padID=pad_name)
    udb = ep.getText(padID=pad_name.replace('ulb', 'udb'))
    tft = getURL(TFTURL.format(bk, chp.zfill(3)))

    chunked = splice(ulb['text'], udb['text'], tft)
    #genNav(chunked, filetochunk.replace('.txt', ''))
