#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#

'''
Exports tA for ru from json to html
'''

import os
import re
import sys
import json
import codecs
import urllib2
import argparse
import datetime

reload(sys)
sys.setdefaultencoding('utf8')

def main():
    filepath = u'/home/rmahn/ta-ru.json'

    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    with open(filepath) as data:
        js = json.load(data)

    titles = {}
    for manual in js['manuals']:
        for page in manual['pages']:
            titles[page['slug']] = page['title']

    output = ''
    for manual in js['manuals']:
        output += u'<div class="page break" id="'+manual['pages'][0]['manual']+u'">'
        output += u'<h1>'+manual['name']+u'</h1>'
        for page in manual['pages']:
            output += u'<h2 id="'+page['slug']+'">'+page['title']+'</h2>'

            if 'question' in page and page['question']:
                output += u'<p><b>This page answers the question:</b> <em>'+page['question']+'</em></p>'

            if 'dependencies' in page and page['dependencies']:
                output += u'<p><b>In order to understand this topic, it would be good to read: </b>'
                if isinstance(page['dependencies'], basestring):
                    page['dependencies'] = [page['dependencies']]
                for dep in page['dependencies']:
                    output += u'<a href="#'+dep+u'">'+(titles[dep] if dep in titles else dep)+u'</a> '
                output += u'</p>'

            for part in page['body']:
                output += u'<'+part['tag']+u'>'
                if 'text' in part:
                    output += part['text']
                if 'items' in part:
                    for item in part['items']:
                        output += u'<'+item['tag']+u'>'+item['text']+u'</'+item['tag']+u'>'
                output += u'</'+part['tag']+u'>'

            if 'recommended' in page and page['recommended']:
                output += u'<p><b>Next we recommend you learn about: </b>'
                if isinstance(page['recommended'], basestring):
                    page['recommended'] = [page['recommended']]
                for rec in page['recommended']:
                    output += u'<a href="#'+rec+u'">'+(titles[rec] if rec in titles else rec)+u'</a> '
                output += u'</p>'
        output += u'</div>'

    for slug in titles.keys():
        pattern = re.compile(r'\ben:ta:[^ ]*:' + slug + r'\b')
        output = pattern.sub('<a href="#'+slug+'">'+titles[slug]+"</a>", output)

#    license = getURL(u'https://door43.org/_export/xhtmlbody/{0}/legal/license/uw-trademark'.format(lang))
#    license += '<p><b>{0}</b></p>'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
#    output = license + output

    f = codecs.open('ta-ru.html', 'w', encoding='utf-8')
    f.write(output)
    f.close()

if __name__ == '__main__':
    main()
