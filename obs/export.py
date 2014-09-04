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

'''
Exports OBS for given language to specified format.
'''

import os
import sys
import json
import codecs
import shutil
import urllib2
import argparse

api_url_txt = u'https://api.unfoldingword.org/obs/txt/1'
api_url_jpg = u'https://api.unfoldingword.org/obs/jpg/1'
api_abs = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1'


def writeFile(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getURL(url, outfile):
    try:
        request = urllib2.urlopen(url)
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def getImage(lang, fid, res, format='plain'):
    img_link = '/'.join([api_url_jpg, lang, res, 'obs-{0}-{1}.jpg'.format(
                                                                 lang, fid)])
    if format == 'html':
        return u'<img src="{0}" />'.format(img_link)
    return u''

def getTitle(text, format='plain'):
    if format == 'html':
        return u'<h1>{0}</h1>'.format(text)
    elif format == 'md':
        return u'{0}\n=========='.format(text)
    return text

def getFrame(text, format='plain'):
    if format == 'html':
        return u'<p>{0}</p>'.format(text)
    elif format == 'md':
        return u'\n{0}\n'.format(text)
    return text

def getRef(text, format='plain'):
    if format == 'html':
        return u'<em>{0}</em>'.format(text)
    elif format == 'md':
        return u'*{0}*'.format(text)
    return text

def export(lang_json, format, img_res, lang):
    '''
    Exports JSON to specificed format.
    '''
    output = []
    for chp in lang_json:
        output.append(getTitle(chp['title'], format))
        for fr in chp['frames']:
            output.append(getImage(lang, fr['id'], img_res, format))
            output.append(getFrame(fr['text'], format))
        output.append(getRef(chp['ref'], format))
    return '\n\n'.join(output)

def main(lang, outpath, format, img_res):
    jsonf = 'obs-{0}.json'.format(lang)
    lang_abs = os.path.join(api_abs, lang, jsonf)
    if os.path.exists(lang_abs):
        lang_json = loadJSON(lang_abs, 'd')
    else:
        lang_url = '/'.join([api_url_txt, lang, jsonf])
        tmpf = '/tmp/{0}'.format(jsonf)
        getURL(lang_url, tmpf)
        if not os.path.exists(tmpf):
            print "Failed to get JSON file."
            sys.exit(1)
        lang_json = loadJSON(tmpf, 'd')
    output = export(lang_json['chapters'], format, img_res,
                                                       lang_json['language'])
    writeFile(outpath, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default=False,
        required=True, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default=False,
        required=True, help="Language code")
    parser.add_argument('-f', '--format', dest="format", default=False,
        required=True, help="Desired format: html, md, or plain")
    parser.add_argument('-r', '--resolution', dest="img_res", default='360px',
        help="Image resolution: 360px, or 2160px")

    args = parser.parse_args(sys.argv[1:])
    main(args.lang, args.outpath, args.format, args.img_res)
