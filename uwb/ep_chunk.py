#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

'''
This script takes grabs the ULB text from etherpad and splits it based on
custom \s5 markers.  Then it pulls in the UDB and TFT text for the same
range and ouputs DokuWiki files for the Notes team.  If the notes page
exists then it only updates the Bible texts and does not alter other content.
'''

import os
import re
import sys
import codecs
import urllib2
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException


NP = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes'
TFTURL = 'https://door43.org/_export/raw/en/udb/v1/{0}/{1}.usfm'
refre = re.compile(ur'\\v.([0-9][0-9]?[0-9]?)')
httpsre = re.compile(ur'https://pad.door43.org.*', re.UNICODE)
tftp = re.compile(ur'(TFT: =====.*?<usfm>\n).*?(\n</usfm>)', re.DOTALL | re.UNICODE)
udbp = re.compile(ur'(UDB: =====.*?<usfm>\n).*?(\n</usfm>)', re.DOTALL | re.UNICODE)
ulbp = re.compile(ur'(ULB: =====.*?<usfm>\n).*?(\n</usfm>)', re.DOTALL | re.UNICODE)
books = { u'GEN': [ u'Genesis' ],
          u'EXO': [ u'Exodus' ],
          u'LEV': [ u'Leviticus' ],
          u'NUM': [ u'Numbers' ],
          u'DEU': [ u'Deuteronomy' ],
          u'JOS': [ u'Joshua' ],
          u'JDG': [ u'Judges' ],
          u'RUT': [ u'Ruth' ],
          u'1SA': [ u'1 Samuel' ],
          u'2SA': [ u'2 Samuel' ],
          u'1KI': [ u'1 Kings' ],
          u'2KI': [ u'2 Kings' ],
          u'1CH': [ u'1 Chronicles' ],
          u'2CH': [ u'2 Chronicles' ],
          u'EZR': [ u'Ezra' ],
          u'NEH': [ u'Nehemiah' ],
          u'EST': [ u'Esther' ],
          u'JOB': [ u'Job' ],
          u'PSA': [ u'Psalms' ],
          u'PRO': [ u'Proverbs' ],
          u'ECC': [ u'Ecclesiastes' ],
          u'SNG': [ u'Song of Solomon' ],
          u'ISA': [ u'Isaiah' ],
          u'JER': [ u'Jeremiah' ],
          u'LAM': [ u'Lamentations' ],
          u'EZK': [ u'Ezekiel' ],
          u'DAN': [ u'Daniel' ],
          u'HOS': [ u'Hosea' ],
          u'JOL': [ u'Joel' ],
          u'AMO': [ u'Amos' ],
          u'OBA': [ u'Obadiah' ],
          u'JON': [ u'Jonah' ],
          u'MIC': [ u'Micah' ],
          u'NAM': [ u'Nahum' ],
          u'HAB': [ u'Habakkuk' ],
          u'ZEP': [ u'Zephaniah' ],
          u'HAG': [ u'Haggai' ],
          u'ZEC': [ u'Zechariah' ],
          u'MAL': [ u'Malachi' ],
          u'MAT': [ u'Matthew' ],
          u'MRK': [ u'Mark' ],
          u'LUK': [ u'Luke' ],
          u'JHN': [ u'John' ],
          u'ACT': [ u'Acts' ],
          u'ROM': [ u'Romans' ],
          u'1CO': [ u'1 Corinthians' ],
          u'2CO': [ u'2 Corinthians' ],
          u'GAL': [ u'Galatians' ],
          u'EPH': [ u'Ephesians' ],
          u'PHP': [ u'Philippians' ],
          u'COL': [ u'Colossians' ],
          u'1TH': [ u'1 Thessalonians' ],
          u'2TH': [ u'2 Thessalonians' ],
          u'1TI': [ u'1 Timothy' ],
          u'2TI': [ u'2 Timothy' ],
          u'TIT': [ u'Titus' ],
          u'PHM': [ u'Philemon' ],
          u'HEB': [ u'Hebrews' ],
          u'JAS': [ u'James' ],
          u'1PE': [ u'1 Peter' ],
          u'2PE': [ u'2 Peter' ],
          u'1JN': [ u'1 John' ],
          u'2JN': [ u'2 John' ],
          u'3JN': [ u'3 John' ],
          u'JUD': [ u'Jude' ],
          u'REV': [ u'Revelation' ]
}
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
  * example
  * example
  * example
 

===== Translation Notes: =====


    * **bold words**  - explanation
    * **bold words**  - explanation
    * **bold words**  - explanation
    * **bold words**  - explanation
    * **bold words**  - explanation
    * **bold words**  - explanation
  
===== Links: =====

  * **[[en/bible/notes:{bk}/questions/comprehension/{chp}|Luke Chapter {chp} Checking Questions]]**
  * **[[en/bible/notes:{bk}/questions/checking/{book}-checking|{book} Checking Questions]]**

 

**[[en/bible/notes/{bk}/{chp}/{prv}|<<]] | [[en/bible/notes/{bk}/{chp}/{nxt}|>>]]**

~~DISCUSSION~~

{{{{tag>draft}}}}
'''


def splice(ulb, udb, tft, bk, chp):
    chunks = {}
    book = books[bk.upper()][0]
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
                        'filepath': getPath(bk, chp, ref),
                      }
        i = httpsre.sub(u'', i)
        chunks[ref]['ulb'] = i.strip()
        chunks[ref]['udb'] = getTXT(ref_list, udb)
        chunks[ref]['tft'] = getTXT(ref_list, tft)
    return chunks

def getTXT(refs, txt):
    chunks = []
    for r in refs:
        versep = ur'\\v.?{0}.*?\\v'.format(r)
        versepend = ur'\\v.?{0}.*?$'.format(r)
        try:
            verse = re.search(versep, txt, re.DOTALL).group(0)
        except AttributeError:
            try:
                verse = re.search(versepend, txt, re.DOTALL).group(0)
            except:
                print 'Warning: reference not found: {0}'.format(r)
        verse = httpsre.sub(u'', verse)
        chunks.append(verse.rstrip('\\v').strip())
    return '\n'.join(chunks)

def getPath(bk, chp, ref):
    fill = getFill(bk)
    return os.path.join(NP, bk, chp.zfill(fill),
                                            '{0}.txt'.format(ref.zfill(fill)))

def getFill(bk):
    if 'psa' in bk.lower():
       return 3
    return 2
    
def writeFile(f, content):
    makeDir(f.rpartition('/')[0])
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()
    os.chown(f, 48, 48)

def makeDir(d):
    '''
    Simple wrapper to make a directory if it does not exist.
    '''
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def writeOrAppend(f, chunk):
    if os.path.exists(f):
        content = codecs.open(f, encoding='utf-8', mode='r').read()
        content = tftp.sub(ur'\1 TFTSUB \2', content)
        content = udbp.sub(ur'\1 UDBSUB \2', content)
        content = ulbp.sub(ur'\1 ULBSUB \2', content)
        content = ( content.replace(u' TFTSUB ', chunk['tft'])
                           .replace(u' UDBSUB ', chunk['udb'])
                           .replace(u' ULBSUB ', chunk['ulb']) )
    else:
        content = TMPL.format(**chunk)
    writeFile(f, content)

def writeChunks(chunked):
    refs = [k for k in chunked.iterkeys()]
    refs.sort(key=int)
    for k in refs:
        i = refs.index(k)
        chunked[k]['prv'] = getNav(refs, i-1, chunked)
        chunked[k]['nxt'] = getNav(refs, i+1, chunked)
        writeOrAppend(chunked[k]['filepath'], chunked[k])

def getNav(refs, i, chunked):
    fill = getFill(bk)
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
