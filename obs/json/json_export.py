#!/usr/bin/env python
# -*- coding: utf8 -*-
#  Copyright (c) 2013 Jesse Griffin
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import os
import json
import codecs
import datetime
from urllib import urlencode

if os.path.exists('local_settings.py'):
    from local_settings import *
else:
    root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
    pages = root + '/pages'
    exportdir = root + '/media/exports'
digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')


def getChapter(chapter, jsonchapter):
    for line in chapter.readlines():
        if line.startswith('\n'): continue
        if '======' in line:
            jsonchapter['title'] = line.replace('======', '').strip()
            continue
        elif line.startswith('//'):
            jsonchapter['ref'] = line.replace('//', '').strip()
            continue
        elif line.startswith('{{'):
            frame = { 'id': line.split('.jpg')[0].split('obs-')[1],
                      'img': line.strip()
                    }
        else:
            frame['text'] = line.strip()
            jsonchapter['frames'].append(frame)
    return jsonchapter

def writePage(outfile, p):
    f = codecs.open(outfile.replace('txt', 'json'), 'w', encoding='utf-8')
    f.write(p)
    f.close()


if __name__ == '__main__':
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    for lang in os.listdir(pages):
        if lang != 'en': continue
        if 'obs' not in os.listdir('{0}/{1}'.format(pages, lang)): continue
        jsonlang = { 'language': '{0}'.format(lang),
                     'chapters': [],
                     'date_modified': today,
                   }
        for page in os.listdir('{0}/{1}/obs'.format(pages, lang)):
            if not page.startswith(digits): continue
            jsonchapter = { 'number': page.split('-')[0],
                            'frames': [],
                          }
            chapter = codecs.open('{0}/{1}/obs/{2}'.format(pages, lang, page),
                                                        'r', encoding='utf-8')
            jsonlang['chapters'].append(getChapter(chapter, jsonchapter))
            chapter.close()
        jsonpage = json.dumps(jsonlang, sort_keys=True, indent=2)
        writePage('{0}/{1}/obs-{1}.json'.format(pages, lang), jsonpage)
        break
