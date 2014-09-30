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
TMPL = u'''====== {book} {chp}:{refrng} ======


===== TFT: =====

<usfm>
{tft}
</usfm>


===== UDB: =====

<usfm>
{udb}
</usfm>


===== ULB: =====

<usfm>
{ulb}
</usfm>


===== Important Terms: =====

  * example
 

===== Translation Notes: =====


    * **bold words**  - explanation
    * **bold words**  - explanation
  
===== Links: =====

  * **[[en/bible/notes:{bk}/questions/comprehension/{chp}|Luke Chapter {chp} Checking Questions]]**
  * **[[en/bible/notes:{bk}/questions/checking/{book}-checking|{book} Checking Questions]]**

 

**[[en/bible/notes/{bk}/{chp}/{prv}|<<]] | [[en/bible/notes/{bk}/{chp}/{nxt}|>>]]**'''
refre = re.compile(ur'\\v.([0-9][0-9]?[0-9]?)')


def splice(ulb, udb, tft, bk, chp):
    chunks = {}
    book = bk
    for i in ulb.split('\n\\s5'):
        if i.startswith('https') and len(i) < 50: continue
        ref_list = refre.findall(i)
        if not ref_list:
            continue
        ref = ref_list[0]
        chunks[ref] = { 'bk': bk,
                        'chp': chp,
                        'book': book,
                        'ref_list': ref_list,
                        'refrng': '{0}-{1}'.format(ref_list[0], ref_list[-1]),
                        'filepath': getpath(bk, chp, ref),
                      }
        chunks[ref]['ulb'] = i.strip()
        chunks[ref]['udb'] = getTXT(ref_list, udb)
        chunks[ref]['tft'] = getTXT(ref_list, tft)
    return chunks

def getTXT(refs, txt):
    chunks = []
    for r in refs:
        versep = ur'\\v.{0}.*?\\v'.format(r)
        versepend = ur'\\v.{0}.*?$'.format(r)
        try:
            verse = re.search(versep, txt, re.DOTALL).group(0)
        except AttributeError:
            verse = re.search(versepend, txt, re.DOTALL).group(0)
        chunks.append(verse.rstrip('\\v').strip())
    return '\n'.join(chunks)

def getpath(bk, chp, ref):
    fill = 2
    if 'psa' in bk.lower():
       fill = 3
    return '{0}/{1}/{2}.txt'.format(bk, chp.zfill(fill), ref.zfill(fill))

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

def writeChunks(chunked):
    refs = [k for k in chunked.iterkeys()]
    refs.sort(key=int)
    for k in refs:
        i = refs.index(k)
        chunked[k]['prv'] = getNav(refs, i-1, chunked)
        chunked[k]['nxt'] = getNav(refs, i+1, chunked)
        writeFile(chunked[k]['filepath'], TMPL.format(**chunked[k]))

def getNav(refs, i, chunked):
    fill = 2
    if 'psa' in bk.lower():
       fill = 3
    if i == -1:
        return ''
    elif i >= len(refs):
        return ''
    return chunked[refs[i]]['ref_list'][0].zfill(fill)

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
        if 'ulb' not in pad_name:
            print 'Please specify ULB pad to chunk.'
            sys.exit(1)
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

    chunked = splice(ulb['text'], udb['text'], tft, bk, chp)
    writeChunks(chunked)
