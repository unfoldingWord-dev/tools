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
Converts translationWords from JSON to Markdown.
'''

import os
import re
import sys
import json
import codecs
import urllib2
linknamere = re.compile(ur'\|.*?(\]\])', re.UNICODE)
sugre = re.compile(ur'<h2>(Translation Suggestions)</h2>', re.UNICODE)
lire = re.compile(ur'<li>(.*?)</li>', re.UNICODE)

def getURL(url):
    try:
        request = urllib2.urlopen(url)
        content = request.read()
        #encoding = request.headers['content-type'].split('charset=')[-1]
        #ucontent = unicode(content, encoding)
    except:
        print "  => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    return content

def clean(text):
    text = linknamere.sub(ur'\1', text)
    text = sugre.sub(ur'\n\n## \1\n\n', text)
    text = text.replace(u'<ul>', u'\n\n').replace(u'</ul>', u'')
    text = lire.sub(ur'* \1\n', text)
    return text

## Need to add Bible/OBS References once that is in API

if __name__ == '__main__':
    terms_url = 'https://api.unfoldingword.org/ts/txt/2/bible/en/terms.json'
    terms_content = getURL(terms_url)
    terms_json = json.loads(terms_content)
    outdir = '/tmp/tw-en'
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    
    for x in terms_json:
        if 'id' not in x: continue
        chkf = codecs.open('{0}/{1}.md'.format(outdir, x['id']), 'w', encoding='utf-8')
        # Write tW
        chkf.write(u'# {0}\n\n'.format(x['term']))
        chkf.write(u'## {0}\n\n'.format(x['def_title']))
        chkf.write(clean(x['def']))
        chkf.write(u'\n\n## See Also\n\n')
        for cf in x['cf']:
            chkf.write(u'* {0}\n'.format(cf))
        if 'aliases' in x:
            chkf.write(u'\n## Aliases\n\n')
            for a in x['aliases']:
                chkf.write(u'* {0}\n'.format(a))
        chkf.close()
