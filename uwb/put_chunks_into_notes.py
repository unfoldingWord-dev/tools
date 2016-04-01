#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

'''
This script takes grabs the ULB text from the local git repo and splits it based on
custom \s5 markers.  Then it pulls in the UDB and TFT text for the same
range and ouputs DokuWiki files for the Notes team.  If the notes page
exists then it only updates the Bible texts and does not alter other content.
'''

import os
import re
import sys
import glob
import codecs
import argparse
import urllib2
import unicode_string_utils

CHAPTERFILE = '/var/www/vhosts/door43.org/{0}-{1}/{2}-{3}/{4}.usfm'
NP = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/bible/notes'
TFTURL = 'https://door43.org/_export/raw/en/udb/v1/{0}/{1}.usfm'
hyphenfixre = re.compile(ur'[ ]?--[ ]?')
refre = re.compile(ur'\\v.([0-9][0-9]?[0-9]?)')
httpsre = re.compile(ur'https://pad.door43.org.*', re.UNICODE)
sectionre = re.compile(ur'\\s.*', re.UNICODE)
tftp = re.compile(ur'(TFT: =====.*?<usfm>).*?(</usfm>)', re.DOTALL | re.UNICODE)
udbp = re.compile(ur'(UDB: =====.*?<usfm>).*?(</usfm>)', re.DOTALL | re.UNICODE)
ulbp = re.compile(ur'(ULB: =====.*?<usfm>).*?(</usfm>)', re.DOTALL | re.UNICODE)
books = { u'GEN': [ u'Genesis', '01' ],
          u'EXO': [ u'Exodus', '02' ],
          u'LEV': [ u'Leviticus', '03' ],
          u'NUM': [ u'Numbers', '04' ],
          u'DEU': [ u'Deuteronomy', '05' ],
          u'JOS': [ u'Joshua', '06' ],
          u'JDG': [ u'Judges', '07' ],
          u'RUT': [ u'Ruth', '08' ],
          u'1SA': [ u'1 Samuel', '09' ],
          u'2SA': [ u'2 Samuel', '10' ],
          u'1KI': [ u'1 Kings', '11' ],
          u'2KI': [ u'2 Kings', '12' ],
          u'1CH': [ u'1 Chronicles', '13' ],
          u'2CH': [ u'2 Chronicles', '14' ],
          u'EZR': [ u'Ezra', '15' ],
          u'NEH': [ u'Nehemiah', '16' ],
          u'EST': [ u'Esther', '17' ],
          u'JOB': [ u'Job', '18' ],
          u'PSA': [ u'Psalms', '19' ],
          u'PRO': [ u'Proverbs', '20' ],
          u'ECC': [ u'Ecclesiastes', '21' ],
          u'SNG': [ u'Song of Solomon', '22' ],
          u'ISA': [ u'Isaiah', '23' ],
          u'JER': [ u'Jeremiah', '24' ],
          u'LAM': [ u'Lamentations', '25' ],
          u'EZK': [ u'Ezekiel', '26' ],
          u'DAN': [ u'Daniel', '27' ],
          u'HOS': [ u'Hosea', '28' ],
          u'JOL': [ u'Joel', '29' ],
          u'AMO': [ u'Amos', '30' ],
          u'OBA': [ u'Obadiah', '31' ],
          u'JON': [ u'Jonah', '32' ],
          u'MIC': [ u'Micah', '33' ],
          u'NAM': [ u'Nahum', '34' ],
          u'HAB': [ u'Habakkuk', '35' ],
          u'ZEP': [ u'Zephaniah', '36' ],
          u'HAG': [ u'Haggai', '37' ],
          u'ZEC': [ u'Zechariah', '38' ],
          u'MAL': [ u'Malachi', '39' ],
          u'MAT': [ u'Matthew', '41' ],
          u'MRK': [ u'Mark', '42' ],
          u'LUK': [ u'Luke', '43' ],
          u'JHN': [ u'John', '44' ],
          u'ACT': [ u'Acts', '45' ],
          u'ROM': [ u'Romans', '46' ],
          u'1CO': [ u'1 Corinthians', '47' ],
          u'2CO': [ u'2 Corinthians', '48' ],
          u'GAL': [ u'Galatians', '49' ],
          u'EPH': [ u'Ephesians', '50' ],
          u'PHP': [ u'Philippians', '51' ],
          u'COL': [ u'Colossians', '52' ],
          u'1TH': [ u'1 Thessalonians', '53' ],
          u'2TH': [ u'2 Thessalonians', '54' ],
          u'1TI': [ u'1 Timothy', '55' ],
          u'2TI': [ u'2 Timothy', '56' ],
          u'TIT': [ u'Titus', '57' ],
          u'PHM': [ u'Philemon', '58' ],
          u'HEB': [ u'Hebrews', '59' ],
          u'JAS': [ u'James', '60' ],
          u'1PE': [ u'1 Peter', '61' ],
          u'2PE': [ u'2 Peter', '62' ],
          u'1JN': [ u'1 John', '63' ],
          u'2JN': [ u'2 John', '64' ],
          u'3JN': [ u'3 John', '65' ],
          u'JUD': [ u'Jude', '66' ],
          u'REV': [ u'Revelation', '67' ],
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

  * **[[en/bible/notes:{bk}/questions/comprehension/{chp}|{book} Chapter {chp} Comprehension Questions]]**

 

**[[en/bible/notes/{bk}/{prvchp}/{prv}|<<]] | [[en/bible/notes/{bk}/{nxtchp}/{nxt}|>>]]**

~~DISCUSSION~~


{{{{tag>draft}}}}
'''

def getText(resource, lang, bk, chp):
    return fix_text(codecs.open(CHAPTERFILE.format(resource, lang, books[bk.upper()][1], bk.upper(), chp), "r", "utf-8").read())

def splice(ulb, udb, tft, bk, chp):
    chunks = {}
    book = books[bk.upper()][0]
    for i in ulb.split('\n\\s5'):
        if i.startswith('https') and len(i) < 50: continue
        ref_list = refre.findall(i)
        if not ref_list:
            continue
        ref = ref_list[0]
        refrng = '{0}-{1}'.format(ref_list[0], ref_list[-1])
        if ref_list[0] == ref_list[-1]:
            refrng = ref_list[0]
        chunks[ref] = { 'bk': bk,
                        'chp': chp,
                        'book': book,
                        'ref_list': ref_list,
                        'refrng': refrng,
                        'filepath': getPath(bk, chp, ref),
                      }
        i = httpsre.sub(u'', i)
        i = sectionre.sub(u'', i)
        chunks[ref]['ulb'] = i.strip()
        chunks[ref]['udb'] = getTXT(ref_list, udb)
        chunks[ref]['tft'] = getTXT(ref_list, tft)
    return chunks

def getTXT(refs, txt):
    chunks = []
    for r in refs:
        versep = ur'\\v.?{0}[- ].*?\\v'.format(r)
        versepend = ur'\\v.?{0}[- ].*?$'.format(r)
        try:
            verse = re.search(versep, txt, re.DOTALL).group(0)
        except AttributeError:
            try:
                verse = re.search(versepend, txt, re.DOTALL).group(0)
            except:
                print 'Warning: reference not found: {0}'.format(r)
                continue
        verse = httpsre.sub(u'', verse)
        verse = sectionre.sub(u'', verse)
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
        content, has_non_ascii_chars, errors = unicode_string_utils.open_file_read_unicode(f)
        content = tftp.sub(ur'\1\n TFTSUB \n\2', content)
        content = udbp.sub(ur'\1\n UDBSUB \n\2', content)
        content = ulbp.sub(ur'\1\n ULBSUB \n\2', content)
        content = ( content.replace(u' TFTSUB ', chunk['tft'])
                           .replace(u' UDBSUB ', chunk['udb'])
                           .replace(u' ULBSUB ', chunk['ulb']) )
    else:
        content = TMPL.format(**chunk)
    writeFile(f, content)

def writeChunks(chunked):
    fill = getFill(bk)
    refs = [k for k in chunked.iterkeys()]
    refs.sort(key=int)
    for k in refs:
        i = refs.index(k)
        chunked[k]['prv'] = getNav(refs, i-1, chunked)
        chunked[k]['nxt'] = getNav(refs, i+1, chunked)
        chunked[k]['prvchp'] = chp
        chunked[k]['nxtchp'] = chp
        if i == 0:
            chunked[k]['prvchp'] = str(int(chp) - 1).zfill(fill)
            chunked[k]['prv'] = getLastSection(bk, chunked[k]['prvchp'])
        if i == (len(refs) - 1):
            chunked[k]['nxtchp'] = str(int(chp) + 1).zfill(fill)
            chunked[k]['nxt'] = '1'.zfill(fill)
        writeOrAppend(chunked[k]['filepath'], chunked[k])

def getLastSection(bk, chp):
    dirpath = os.path.join(NP, bk, chp)
    if not os.path.exists(dirpath):
        return chp
    seclist = glob.glob('{0}/[0-9]*.txt'.format(dirpath))
    ref = chp
    if len(seclist):
        seclist.sort()
        ref = seclist[-1].rpartition('/')[-1].rstrip('.txt')
    return ref

def getNav(refs, i, chunked):
    fill = getFill(bk)
    if i == -1:
        return ''
    elif i >= len(refs):
        return '1'.zfill(fill)
    return chunked[refs[i]]['ref_list'][0].zfill(fill)

def getURL(url):
    try:
        request = urllib2.urlopen(url)
        content = request.read()
        encoding = request.headers['content-type'].split('charset=')[-1]
        ucontent = unicode(content, encoding)
    except:
        print "  => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    return ucontent


def fix_text(source_text):
    """
    Removes and replaces specific characters and sequences
    :param source_text: string
    :return: string
    """

    fixed_text = hyphenfixre.sub(u'—', source_text)
    fixed_text = fixed_text.replace(u' — ', u'—')

    return fixed_text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--language', dest="lang", default="en",
        required=False, help="Book to convert")
    parser.add_argument('-b', '--book', dest="book",
        required=True, help="Book to convert")
    parser.add_argument('-c', '--chapter', dest="chapter",
        required=True, help="Chapter to convert")

    args = parser.parse_args(sys.argv[1:])

    lang = args.lang.lower()
    bk = args.book.lower()
    chp = args.chapter.lower()

    ulb = getText('ulb', lang, bk, chp)
    udb = getText('udb', lang, bk, chp)
    tft = getURL(TFTURL.format(bk, chp.zfill(3)))

    chunked = splice(ulb, udb, tft, bk, chp)
    writeChunks(chunked)
