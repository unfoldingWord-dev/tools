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
This script exports the ULB and UDB from Etherpad.
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


names = { 'ULB': 'unfoldingWord Literal Bible',
          'UDB': 'unfoldingWord Dynamic Bible'
        }
baseout = '/var/www/vhosts/api.unfoldingword.org/httpdocs/{0}/txt/1/{0}-{1}'
draftout = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/{1}/{0}/ep/'
_digits = re.compile('\d')
httpsre = re.compile(ur'https://pad.door43.org.*', re.UNICODE)
srre = re.compile(ur'\\sr.*', re.UNICODE)
LICENSE = u'''\mt {1}

\p \\bd an unrestricted Bible intended for translation into any language \\bd*

\p \em http://unfoldingWord.org/Bible \em*

\p {1}, v. {0}

This work is based on \em The American Standard Version \em*, which is in the public domain.


\p License:

\p This work is made available under a Creative Commons Attribution-ShareAlike 4.0 International License (http://creativecommons.org/licenses/by-sa/4.0/).

\p You are free:

\p \\bd Share \\bd* — copy and redistribute the material in any medium or format
\p \\bd Adapt \\bd* — remix, transform, and build upon the material for any purpose, even commercially.

\p Under the following conditions:

\p \\bd Attribution \\bd* — You must attribute the work as follows: "Original work available at http://openbiblestories.com." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
\p \\bd ShareAlike \\bd* — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

\p Use of trademarks: \\bd unfoldingWord \\bd* is a trademark of Distant Shores Media and may not be included on any derivative works created from this content.  Unaltered content from http://unfoldingWord.org must include the \\bd unfoldingWord \\bd* logo when distributed to others. But if you alter the content in any way, you must remove the \\bd unfoldingWord \\bd* logo before distributing your work.
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
          u'MAT': [ u'Matthew', '40' ],
          u'MRK': [ u'Mark', '41' ],
          u'LUK': [ u'Luke', '42' ],
          u'JHN': [ u'John', '43' ],
          u'ACT': [ u'Acts', '44' ],
          u'ROM': [ u'Romans', '45' ],
          u'1CO': [ u'1 Corinthians', '46' ],
          u'2CO': [ u'2 Corinthians', '47' ],
          u'GAL': [ u'Galatians', '48' ],
          u'EPH': [ u'Ephesians', '49' ],
          u'PHP': [ u'Philippians', '50' ],
          u'COL': [ u'Colossians', '51' ],
          u'1TH': [ u'1 Thessalonians', '52' ],
          u'2TH': [ u'2 Thessalonians', '53' ],
          u'1TI': [ u'1 Timothy', '54' ],
          u'2TI': [ u'2 Timothy', '55' ],
          u'TIT': [ u'Titus', '56' ],
          u'PHM': [ u'Philemon', '57' ],
          u'HEB': [ u'Hebrews', '58' ],
          u'JAS': [ u'James', '59' ],
          u'1PE': [ u'1 Peter', '60' ],
          u'2PE': [ u'2 Peter', '61' ],
          u'1JN': [ u'1 John', '62' ],
          u'2JN': [ u'2 John', '63' ],
          u'3JN': [ u'3 John', '64' ],
          u'JUD': [ u'Jude', '65' ],
          u'REV': [ u'Revelation', '66' ],
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
    f.write(json.dumps(p, indent=2, sort_keys=True))
    f.close()

def save(pads, outdir, slug, ep, ver):
    books_published = []
    for bk in books.iterkeys():
        if ver.lower() != 'draft':
            if bk not in ['RUT', 'LUK', 'TIT']: continue
        bk_pads = [x for x in pads if bk.lower() in x and contains_digits(x)]
        bk_pads.sort()
        content = []
        for p in bk_pads:
            # Skips pad that WA uses for communication (e.g. 'en-ulb-1ti')
            if len(p.split('-')) < 4:
                continue
            p_content = ep.getText(padID=p)['text']
            if 'Welcome to Etherpad!' in p_content:
                continue
            p_content = httpsre.sub(u'', p_content)
            p_content = srre.sub(u'', p_content)
            content.append(p_content)
        outfile = '{0}/{1}-{2}-en-{3}.usfm'.format(outdir, books[bk][1], bk,
                                                                         slug)
        if ver.lower() == 'draft':
            outfile = '{0}.txt'.format(outfile).lower()
        writeFile(outfile, u''.join(content))
        books_published.append(bk.lower())
    return books_published

def main(slug, ver):
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    try:
        pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                                         api_version='1.2.10')

    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    all_pads = ep.listAllPads()
    ver_pads = [x for x in all_pads['padIDs'] if slug.lower() in x]
    ver_pads.sort()

    if ver.lower() == 'draft':
        outdir = draftout.format(slug.lower(), 'en')
    else:
        outdir = baseout.format(slug.lower(), 'en')

    books_published = save(ver_pads, outdir, slug, ep, ver)
    status = { "slug": slug.lower(),
               "name": names[slug],
               "lang": "en",
               "date_modified": today,
               "books_published": books_published,
               "status": { "checking_entity": "Wycliffe Associates",
                           "checking_level": "3",
                           "comments": "Original source text",
                           "contributors": "Wycliffe Associates",
                           "publish_date": today,
                           "source_text": "en",
                           "source_text_version": ver,
                           "version": ver
                          }
             }
    writeJSON('{0}/status.json'.format(outdir), status)
    writeFile('{0}/LICENSE.usfm'.format(outdir), LICENSE.format(ver,
                                                                 names[slug]))
    print "Check {0} and do a git push".format(outdir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', dest="ver", default=False,
        required=True, help="Text Version")
    parser.add_argument('-r', '--resource', dest="slug", default=False,
        required=True, help="Resource (UDB|ULB)")

    args = parser.parse_args(sys.argv[1:])
    main(args.slug, args.ver)
