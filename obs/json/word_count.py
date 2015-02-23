#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

import os
import sys
import json
import codecs
import urllib2

api_url = u'https://api.unfoldingword.org/obs/txt/1/{0}/obs-{0}.json'

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return u''

def count(lang):
    content = getURL(api_url.format(lang))
    if not content:
        print '-> Error: nothing found at {0}'.format(api_url.format(lang))
    content_json = json.loads(content)

    text = []
    for chp in content_json['chapters']:
        for frame in chp['frames']:
            if 'text' not in frame:
                continue
            text.append(frame['text'])
    text_str = u'\n'.join(text)
    writeFile('/tmp/obs-{0}.txt'.format(lang), text_str)
    print 'Words in {0}: {1}'.format(lang, len(text_str.split()))

def writeFile(f, content):
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()


if __name__ == '__main__':
    lang = sys.argv[1]
    count(lang)
