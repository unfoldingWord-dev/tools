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

if os.path.exists('local_settings.py'):
    from local_settings import *
else:
    root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
    pages = root + '/pages'
    exportdir = root + '/media/exports'
digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')


def getChapter(chapterpath, jsonchapter):
    i = 0
    chapter = codecs.open(chapterpath, 'r', encoding='utf-8').readlines()
    for line in chapter:
        i += 1
        if line.startswith((u'\n', u'\ufeff')) or line == u'':
            continue
        if u'======' in line:
            jsonchapter['title'] = line.replace(u'======', u'').strip()
            continue
        elif line.startswith(u'//'):
            jsonchapter['ref'] = line.replace(u'//', u'').strip()
            continue
        elif line.startswith('{{'):
            if 'Program Files' in line:
                continue
            frame = { 'id': line.split('.jpg')[0].split('obs-')[1],
                      'img': line.strip()
                    }
        else:
            if 'No translation' in line:
                frame = { 'id': None,
                          'img': None,
                          'text': 'No translation'
                        }
                jsonchapter['frames'].append(frame)
                break
            try:
                frame['text'] = line.strip()
                jsonchapter['frames'].append(frame)
            except UnboundLocalError:
                error = 'Problem parsing line number: {0} in {1}'.format(
                                                               i, chapterpath)
                print error
                frame = { 'id': None,
                          'img': None,
                          'text': 'Invalid format.'
                        }
                jsonchapter['frames'].append(frame)
                break
    jsonchapter['frames'].sort(key=lambda frame: frame['id'])
    return jsonchapter

def writePage(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile.replace('txt', 'json'), 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getDump(j):
    return json.dumps(j, sort_keys=True, indent=2)

def loadJSON(f):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    return json.loads('{}')


if __name__ == '__main__':
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    catpath = '{0}/obs-catalog.json'.format(exportdir)
    catalog = loadJSON(catpath)
    for lang in os.listdir(pages):
        if ( os.path.isfile('{0}/{1}'.format(pages, lang)) or
             'obs' not in os.listdir('{0}/{1}'.format(pages, lang)) ):
            continue
        jsonlang = { 'language': '{0}'.format(lang),
                     'chapters': [],
                     'date_modified': today,
                   }
        for page in os.listdir('{0}/{1}/obs'.format(pages, lang)):
            if not page.startswith(digits): continue
            jsonchapter = { 'number': page.split('-')[0],
                            'frames': [],
                          }
            chapterpath = '{0}/{1}/obs/{2}'.format(pages, lang, page)
            jsonlang['chapters'].append(getChapter(chapterpath, jsonchapter))
        jsonlang['chapters'].sort(key=lambda frame: frame['number'])
        prevjsonlang = loadJSON('{0}/{1}/obs/obs-{1}.json'.format(exportdir, lang))
        curjson = getDump(jsonlang)
        prevjson = getDump(prevjsonlang)
        if not lang in catalog:
            catalog[lang] = today
        if len(str(curjson)) != len(str(prevjson)):
            catalog[lang] = today
            print '{0}/{1}/obs/obs-{1}.json'.format(exportdir, lang)
            writePage('{0}/{1}/obs/obs-{1}.json'.format(exportdir, lang),
                                                                      curjson)
    catjson = getDump(catalog)
    writePage(catpath, catjson)
