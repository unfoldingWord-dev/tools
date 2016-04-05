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
This script exports the ULB and UDB from Etherpad by each book into given directory.
'''

import os
import re
import sys
import json
import codecs
import datetime
import argparse
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException

COMPLETE = [ 'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA',
             '2SA', '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB',
             'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN',
             'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
             'HAG', 'ZEC', 'MAL',
             'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL',
             'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM',
             'HEB', 'JAS', '1PE', '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV'
           ]
names = { 'ULB': 'Unlocked Literal Bible',
          'UDB': 'Unlocked Dynamic Bible'
        }
outdir = '/var/www/vhosts/door43.org/{0}-{1}'

_digits = re.compile('\d')
httpsre = re.compile(ur'https://pad.door43.org.*', re.UNICODE)
srre = re.compile(ur'\\sr.*', re.UNICODE)
s1re = re.compile(ur'\\s1.*', re.UNICODE)
s_re = re.compile(ur'\\s .*', re.UNICODE)
basis = { 'UDB': u'This work is based on \em Translation 4 Translators \em*, which is licensed CC-BY-SA (http://creativecommons.org/licenses/by-sa/4.0/).',
          'ULB': u'This work is based on \em The American Standard Version \em*, which is in the public domain.'
        }
LICENSE = u'''\mt {0}

\p \\bd an unrestricted Bible intended for translation into any language \\bd*

\p \em http://unfoldingWord.org/bible \em*

\p {0}

{1}


\p License:

\p This work is made available under a Creative Commons Attribution-ShareAlike 4.0 International License (http://creativecommons.org/licenses/by-sa/4.0/).

\p You are free:

\p \\bd Share \\bd* — copy and redistribute the material in any medium or format
\p \\bd Adapt \\bd* — remix, transform, and build upon the material for any purpose, even commercially.

\p Under the following conditions:

\p \\bd Attribution \\bd* — You must attribute the work as follows: "Original work available at http://openbiblestories.com." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
\p \\bd ShareAlike \\bd* — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.
'''
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


def contains_digits(d):
    return bool(_digits.search(d))

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def writeFile(outfile, content):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(content)
    f.close()

def writeJSON(outfile, p):
    '''
    Simple wrapper to write a file as JSON.
    '''
    makeDir(outfile.rsplit('/', 1)[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(json.dumps(p, sort_keys=True))
    f.close()

def main():
    try:
        pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                                         api_version='1.2.10')
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    all_pads = ep.listAllPads()['padIDs']

    for p in all_pads:
        # Skips pad that WA uses for communication (e.g. 'en-ulb-1ti')
        if len(p.split('-')) < 4:
            continue
        content = u''+ep.getText(padID=p)['text']
        if 'Welcome to Etherpad!' in content or 'ATTENTION' in content:
            continue
        print p
        parts = p.split('-')
        lang = parts[0]
        resource = parts[1]
        bk = parts[2]
        chp = parts[3]
        bk = bk.upper()
        if not bk in books:
            continue
        booknum = books[bk][1]
        content = u'''——————————————————————————————————————
!!!!
!!!!                                                           ATTENTION!!
!!!!          *** THESE FILE ARE NO LONGER EDITED ON ETHERPAD! ***
!!!!
!!!! PLEASE CREATE AN ACCOUNT AT http://github.com AND LET US KNOW YOUR USERNAME
!!!! ON SLACK IN THE #resources CHANNEL OR EMAIL help@door43.org
!!!!
!!!! ONCE YOU HAVE ACCESS, YOU CAN EDIT THIS FILE AT
!!!! https://github.com/Door43/{0}-{1}/blob/master/{2}-{3}/{4}.usfm
!!!!
——————————————————————————————————————

{5}
'''.format(resource, lang, booknum, bk, chp, content)
        print p
        ep.setText(padID=p, text=content.encode('utf-8'))

if __name__ == '__main__':
    main()
