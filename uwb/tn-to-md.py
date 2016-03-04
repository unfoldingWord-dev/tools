#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>
#
#  Requires PyGithub for unfoldingWord export.

'''
Converts translationNotes from JSON to Markdown.
'''

import os
import re
import sys
import json
import codecs
import urllib2
linknamere = re.compile(ur'\|.*?(\]\])', re.UNICODE)
BOOKS = [ 'GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA',
          '2SA', '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB',
          'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN',
          'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP',
          'HAG', 'ZEC', 'MAL',
          'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL',
          'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM',
          'HEB', 'JAS', '1PE', '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV'
        ]

def getURL(url):
    try:
        request = urllib2.urlopen(url)
        content = request.read()
    except:
        print "  => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    return content

def clean(text):
    text = linknamere.sub(ur'\1', text)
    return text

def convert(notes_json, tw_json, outdir):
    for x in notes_json:
        if 'id' not in x: continue
        chp, chk = x['id'].split(u'-')
        chp_path = os.path.join(outdir, chp)
        if not os.path.exists(chp_path):
            os.mkdir(chp_path)
        chkf = codecs.open('{0}/{1}.md'.format(chp_path, chk), 'w', encoding='utf-8')
        # Find tW and write
        chkf.write(u'## translationWords\n\n')
        for chps in tw_json['chapters']:
            if not chp == chps['id']: continue
            for frm in chps['frames']:
                if not chk == frm['id']: continue
                for item in frm['items']:
                    chkf.write(u'* [[en:tw:{0}]]\n'.format(item['id']))
        # Write tN
        chkf.write(u'\n## translationNotes\n\n')
        for tn in x['tn']:
            clean_text = clean(tn['text'])
            if not tn['ref']:
                chkf.write(u'* {0}\n'.format(clean_text))
            else:
                chkf.write(u'* **{0}** - {1}\n'.format(tn['ref'], clean_text))
        chkf.close()


if __name__ == '__main__':
    api_v2 = 'https://api.unfoldingword.org/ts/txt/2/'
    for bk in [x.lower() for x in BOOKS]:
        outdir = os.path.join('/tmp/tn-en', bk)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        notes = getURL('{0}/{1}/en/notes.json'.format(api_v2, bk))
        notes_json = json.loads(notes)
        tw_cat = getURL('{0}/{1}/en/tw_cat.json'.format(api_v2, bk))
        tw_json = json.loads(tw_cat)
        convert(notes_json, tw_json, outdir)
