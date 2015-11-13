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

body_json = ''
refs = {}

#api_url_txt = u'http://td-demo.unfoldingword.org/publishing'
api_url_txt = u'http://api.unfoldingword.org/test'

def renderHTMLFromJSON():
    global body_json
    global refs

    j = u'\n\n'
    output = []
    for chp in body_json['chapters']:
        output.append(u'<h1>{0}</h1>'.format(chp['title']))
        for fr in chp['frames']:
            refs['"'+fr['ref']+'"'] = fr['id']
            output.append(fr['text'])
#            output.append('<h2>frame title</h2>\n<p>\nframe text\n</p>\n')
    output = j.join(output)
    pattern = re.compile(r'(' + '|'.join(refs.keys()) + r')')
    output = pattern.sub(lambda x: '#'+refs[x.group()], output)
    # output = re.sub(' (href|src)="/', ' \g<1>="https://door43.org/', output)
    output = re.sub(' (src)="/', ' \g<1>="https://door43.org/', output)
    return output

def getJSON(jsonf,tmpf):
    anyJSONf = '/'.join([api_url_txt, jsonf])
    anytmpf = '/'.join(['/tmp', tmpf])
    getURL(anyJSONf, anytmpf)
    if not os.path.exists(anytmpf):
        print "Failed to get JSON {0} file into {1}.".format(jsonf,anytmpf)
        sys.exit(1)
    return anytmpf

def main(lang, outpath, format, checkinglevel):
    global body_json
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    json_file = 'ta-{0}.json'.format(lang)
    json_url = '/'.join([api_url_txt, json_file])
    body_json = json.load(urllib2.urlopen(json_url))
    output = renderHTMLFromJSON()
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
    parser.add_argument('-f', '--format', dest="format", default=False,
        required=True, help="Desired format: html, md, tex, or plain")
    parser.add_argument('-c', '--checkinglevel', dest="checkinglevel", default="1",
        help="Quality Assurace level campleted: 1, 2, or 3")
    args = parser.parse_args(sys.argv[1:])
    main(args.lang, args.outpath, args.format, args.checkinglevel)
