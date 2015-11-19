#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Exports tA for given language from json to html
'''

import os
import re
import sys
import json
import codecs
import urllib2
import argparse
from urllib2.request import urlopen

body_json = ''
refs = {}

api_url_txt = u'https://api.unfoldingword.org/ta/txt/1/en'
#api_url_txt = u'http://api.unfoldingword.org/test'

def getHtmlFromHash(hash, level):
    global refs
    output = ''
    if 'chapters' in hash:
        for chapter in hash['chapters']:
            output += u'<h{0}>{1}</h{0}>'.format(level, chapter['title'])
            output += getHtmlFromHash(chapter, level+1)
    if 'sections' in hash:
        for section in hash['sections']:
            output += u'<h{0}>{1}</h{0}>'.format(level, section['title'])
            output += getHtmlFromHash(section, level+1)
    if 'frames' in hash:
        for frame in hash['frames']:
            refs['"'+frame['ref']+'"'] = frame['id']
            text = frame['text']
            text = text.replace('<h5', '<h7');
            text = text.replace('</h5', '</h7'.format(level));
            text = text.replace('<h4', '<h6');
            text = text.replace('</h4', '</h6');
            text = text.replace('<h3', '<h5');
            text = text.replace('</h3', '</h5');
            text = text.replace('<h2', '<h4');
            text = text.replace('</h2', '</h4');
            text = text.replace('<h4', '<h{0}'.format(level), 1);
            text = text.replace('</h4', '</h{0}'.format(level), 1);
            output += text
            output += getHtmlFromHash(frame, level+1)
    return output

def renderHTMLFromJSON():
    global body_json
    global refs

    j = u'\n\n'
    output = ''
    output += getHtmlFromHash(body_json, 1)
    pattern = re.compile(r'(' + '|'.join(refs.keys()) + r')')
    output = pattern.sub(lambda x: '#'+refs[x.group()], output)
    # output = re.sub(' (href|src)="/', ' \g<1>="https://door43.org/', output)
    output = re.sub(' (src)="/', ' \g<1>="https://door43.org/', output)
    output = re.sub('href="/en/slack', 'href="https://door43.org/en/slack', output)
    output = re.sub('(?i)(help@door43.org)', '<a href="mailto:\g<1>">\g<1></a>', output)
    return output

def getJSON(jsonf,tmpf):
    anyJSONf = '/'.join([api_url_txt, jsonf])
    anytmpf = '/'.join(['/tmp', tmpf])
    getURL(anyJSONf, anytmpf)
    if not os.path.exists(anytmpf):
        print "Failed to get JSON {0} file into {1}.".format(jsonf,anytmpf)
        sys.exit(1)
    return anytmpf

def main(lang, outpath, checkinglevel):
    global body_json
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    json_file = 'ta-{0}.json'.format(lang)
    json_url = '/'.join([api_url_txt, json_file])
    body_json = json.load(urllib2.urlopen(json_url))
    output = renderHTMLFromJSON()

    try:
         with urlopen("https://door43.org/_export/xhtmlbody/en/legal/license/uw-trademark") as response:
            output = response.read(1) + output
    except OSError as e:
        print("error happened: {}".format(e))

    f = codecs.open(outpath, 'w', encoding='utf-8')
    f.write(output)
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default=False,
        required=True, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default=False,
        required=True, help="Language code")
    parser.add_argument('-c', '--checkinglevel', dest="checkinglevel", default="1",
        help="Quality Assurace level campleted: 1, 2, or 3")
    args = parser.parse_args(sys.argv[1:])
    main(args.lang, args.outpath, args.checkinglevel)
