#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
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
import datetime

body_json = ''
refs = {}

reload(sys)
sys.setdefaultencoding('utf8')

api_url = u'https://api.unfoldingword.org/ta/txt/1'

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return False

def getHtmlFromHash(hash, level):
    global refs
    output = ''
    if 'chapters' in hash:
        for chapter in hash['chapters']:
            output += u'<h{0}>{1}</h{0}>'.format(level, chapter['title'])+"\n"
            output += getHtmlFromHash(chapter, level+1)
    if 'frames' in hash:
        for frame in hash['frames']:
            refs[frame['ref']] = '#'+frame['id']

            text = frame['text']
#            text = re.sub(u'<h4([^>]*)>\s*(.*?)\s*</h4>', u'<h7\g<1>>\g<2></h7>', text, flags=re.MULTILINE)
#            text = re.sub(u'<h3([^>]*)>\s*(.*?)\s*</h3>', u'<h6\g<1>>\g<2></h6>', text, flags=re.MULTILINE)
#            text = re.sub(u'<h2([^>]*)>\s*(.*?)\s*</h2>', u'<h5\g<1>>\g<2></h5>', text, flags=re.MULTILINE)

            text = re.sub(u'<h5([^>]*)>\s*(.*?)\s*</h5>', u'<h5\g<1>><em>\g<2></em></h5>', text)
            text = re.sub(u'<h4([^>]*)>\s*(.*?)\s*</h4>', u'<h5\g<1>><b><em>\g<2></em></b></h5>', text)
            text = re.sub(u'<h3([^>]*)>\s*(.*?)\s*</h3>', u'<h5\g<1>>\g<2></h5>', text)

            text = re.sub(u'<h2([^>]*)>\s*(.*?)\s*</h2>', u'<h{0}\g<1>>\g<2></h{0}>'.format(level), text)

            output += text
            output += getHtmlFromHash(frame, level+1)
    if 'sections' in hash:
        for section in hash['sections']:
            output += u'<h{0}>{1}</h{0}>'.format(level, section['title'])+"\n"
            output += getHtmlFromHash(section, level+1)

    return output

def renderHTMLFromJSON():
    global body_json
    global refs

    j = u'\n\n'
    output = ''
    output += getHtmlFromHash(body_json, 1)

    for url in refs.keys():
        output = output.replace(u'href="{0}"'.format(url), u'href="{0}"'.format(refs[url]))

    output = re.sub(' src="assets/img/ta/audio_ocenaudio_properties.jpg"', '', output)
    output = re.sub(' src="/', ' src="https://unfoldingword.org/', output)
    output = re.sub(' src="assets/', ' src="https://unfoldingword.org/assets/', output)
    output = re.sub('href="/en/slack', 'href="https://door43.org/en/slack', output)
    output = re.sub('<img ([^>]*)>', '</p>\n<p><img \g<1>></p>\n<p>', output)
    output = re.sub('(?i)(help@door43.org)', '<a href="mailto:\g<1>">\g<1></a>', output)
    return output

def main(lang, inpath, outpath, checkinglevel):
    global body_json, refs

    refs['/{0}/ta/vol1/intro/toc_intro'.format(lang)] = u'#the-unfoldingword-project'
    refs['/{0}/ta/vol1/translate/toc_transvol1_2'.format(lang)] = u'#introduction-to-translation-manual'
    refs['/{0}/ta/vol1/checking/toc_checkvol1_2'.format(lang)] = u'#introduction-to-the-checking-manual'
    refs['/{0}/ta/vol1/tech/toc_techvol1_2'.format(lang)] = u'#welcome-to-the-technology-manual'
    refs['/{0}/ta/vol1/tech/toc_techvol1'.format(lang)] = u'#welcome-to-the-technology-manual'
    refs['/{0}/ta/vol1/process/toc_processvol1_2'.format(lang)] = u'#introduction-to-the-process-manual'
    refs['/{0}/ta/vol1/tech/uw_intro'.format(lang)] = u'#unfoldingword-mobile-app'
    refs['/{0}/obs'.format(lang)] = u'http://www.openbiblestories.com'
    refs['/{0}/bible/intro'.format(lang)] = u'https://unfoldingword.org/bible'
    refs['/{0}/obs/notes'.format(lang)] = u'https://unfoldingword.org/translationnotes/'
    refs['/{0}/bible/notes/home'.format(lang)] = u'https://unfoldingword.org/translationnotes/'
    refs['/{0}/obs/notes/questions/home'.format(lang)] = u'https://unfoldingword.org/translationquestions/'
    refs['/{0}/bible/questions/home'.format(lang)] = u'https://unfoldingword.org/translationquestions/'
    refs['/{0}/obe/home'.format(lang)] = u'https://unfoldingword.org/translationwords/'
    refs['/{0}/ta/vol1/tech/uw_app'.format(lang)] = u'https://unfoldingword.org/apps'
    refs['/{0}/ta'.format(lang)] = u'https://unfoldingword.org/academy'

    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    if inpath.startswith('http'):
        body_json = json.load(urllib2.urlopen(inpath))
    else:
        with open(inpath) as data:
             body_json = json.load(data)
    output = renderHTMLFromJSON()

#    license = getURL(u'https://door43.org/_export/xhtmlbody/{0}/legal/license/uw-trademark'.format(lang))
#    license += '<p><b>{0}</b></p>'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
#    output = license + output

    f = codecs.open(outpath, 'w', encoding='utf-8')
    f.write(output)
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default='en',
        required=False, help="Language code")
    parser.add_argument('-c', '--checkinglevel', dest="checkinglevel", default="1",
        help="Quality Assurace level campleted: 1, 2, or 3", required=False)
    parser.add_argument('-i', '--input', dest="inpath",
        help="Input file or url for the JSON file, will use api.unfoldingword.org if none specified.", required=False)

    args = parser.parse_args(sys.argv[1:])
    if not args.inpath:
         args.inpath = '/'.join([api_url, args.lang, 'ta-{0}.json'.format(args.lang)])

    main(args.lang, args.inpath, args.outpath, args.checkinglevel)
