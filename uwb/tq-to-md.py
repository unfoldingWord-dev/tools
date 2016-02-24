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
Converts translationQuestions from JSON to Markdown.
'''

import os
import re
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
        return False
    return content

def clean(text):
    text = linknamere.sub(ur'\1', text)
    return text

def convert(tq_json, outdir):
    for x in tq_json:
        if 'id' not in x: continue
        outfile = os.path.join(outdir, '{0}.md'.format(x['id'])) 
        chkf = codecs.open(outfile, 'w', encoding='utf-8')
        # Write tQ
        chkf.write(u'# translationQuestions\n\n')
        for qa in x['cq']:
            chkf.write(u'Q? {0}\n\n'.format(qa['q']))
            refs = []
            for ref in qa['ref']:
                if u'&' in ref:
                    refp = ref.split(u'&')
                    c, v = refp[0].split(u'-')
                    refs.append(u'{0}:{1}'.format(int(c), int(v)))
                    refs.append(u'{0}:{1}'.format(int(c), int(refp[1])))
                    continue
                refp = ref.split(u'-')
                if len(refp) == 2:
                    refs.append(u'{0}:{1}'.format(int(refp[0]), int(refp[1])))
                elif len(refp) == 3:
                    refs.append(u'{0}:{1}-{2}'.format(int(refp[0]), int(refp[1]),
                                                                    int(refp[2])))
            chkf.write(u'A. {0} [{1}]\n\n\n'.format(qa['a'], '; '.join(refs)))
        chkf.close()


if __name__ == '__main__':
    api_v2 = 'https://api.unfoldingword.org/ts/txt/2/'
    for bk in [x.lower() for x in BOOKS]:
        tq = getURL('{0}/{1}/en/questions.json'.format(api_v2, bk))
        if not tq:
            print 'No questions for {0}'.format(bk)
            continue
        tq_json = json.loads(tq)
        outdir = os.path.join('/tmp/tq-en', bk)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        convert(tq_json, outdir)
