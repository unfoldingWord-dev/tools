#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#
#  Converts a tA repo into a PDF
#
#  Usage: md_to_pdf.py -i <directory of all ta repos> -o <directory where html flies will be placed>
#

import os
import re
import sys
import codecs
import argparse
import markdown2
from glob import glob
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf8')

twRoot = ''
twOrder = ['kt', 'names', 'other']
category_titles = {
    'kt': 'Key Terms',
    'names': 'Names',
    'other': 'Other'
}
terms = {}

taUrl = u'https://unfoldingword.org/academy'
taManualUrls = {
    'en-ta-intro': u'ta-intro.html',
    'en-ta-process': u'ta-process.html',
    'en-ta-translate-vol1': u'ta-translation-1.html',
    'en-ta-translate-vol2': u'ta-translation-2.html',
    'en-ta-checking-vol1': u'ta-checking-1.html',
    'en-ta-checking-vol2': u'ta-checking-2.html',
    'en-ta-audio': u'ta-audio.html',
    'en-ta-gl': u'ta-gateway-language.html',
}


class TwTerm(object):
    def __init__(self, term, title, content):
        self.term = term
        self.title = title
        self.content = content


def populateWords():
    for category in twOrder:
        terms[category] = {}
        dir = os.path.join(twRoot, 'bible', category)
        files = glob(os.path.join(dir, '*.md'))
        ta_links = re.compile(
            '"https://git.door43.org/Door43/(en-ta-([^\/"]+?)-([^\/"]+?))/src/master/content/([^\/"]+?).md"')
        for f in files:
            term = os.path.splitext(os.path.basename(f))[0]
            content = markdown2.markdown_path(f)
            content = u'<div id="{0}-{1}" class="word">'.format(category, term) + content + u'</div>'
            parts = ta_links.split(content)
            if len(parts) == 6 and parts[1] in taManualUrls:
                content = parts[0] + '"{0}/{1}#{2}_{3}_{4}"'.format(taUrl, taManualUrls[parts[1]], parts[3], parts[2],
                                                                    parts[4]) + parts[5]

            # replace relative links
            content = re.sub(r'href="\.\.\/([^\/"]+)\/([^"]+)\.md"', r'href="#\1-\2"', content)

            #replace rc: links
            content = re.sub(r'href="rc\:\/\/([^\/"]+)\/([^\/"]+)\/([^\/"]+)\/([^\/"]+)\/([^\/"]+)\/([^\/"]+)"', r'href="https://git.door43.org/Door43/\1_\2/src/master/\4/\5/\6.md"', content)

            soup = BeautifulSoup(content, features="html.parser")
            if soup.h1:
                title = soup.h1.text
            else:
                title = term
                print title
            for i in reversed(range(1, 4)):
                for h in soup.select('h{0}'.format(i)):
                    h.name = 'h{0}'.format(i + 1)
            content = str(soup.div)
            word = TwTerm(term, title, content)
            terms[category][term] = word


def fix_content(content):
    for category in twOrder:
        for term in terms[category]:
            word = terms[category][term]
            content = re.sub(ur'#{0}-{1}">{1}<'.format(category, term),
                             ur'#{0}-{1}">{2}<'.format(category, term, word.title),
                             content)
    return content


def main(inpath, outpath, version, publisher, contributors, issued_date):
    global twRoot, taUrl, taManualUrls, twOrder, terms

    twRoot = inpath

    license = markdown2.markdown_path(twRoot + '/' + 'LICENSE.md')
    populateWords()

    cover = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="translationWords">
    <img src="https://unfoldingword.org/assets/img/icon-tw.png" width="120">
    <h1 class="h1">translationWords</h1>
    <h3 class="h3">v''' + version + '''</h3>
  </div>
</body>
</html>
'''

    license = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
''' + license + '''
    <p>
      <strong>Date:</strong> ''' + issued_date + '''<br/>
      <strong>Version:</strong> ''' + version + '''<br/>
      <strong>Contributors:</strong> ''' + contributors + '''<br/>
    </p>
    <p>
      <strong>Published by:</strong> ''' + publisher + '''<br/>
    </p>
  </div>
</body>
</html>
'''

    content = ''
    for category in twOrder:
        content += u'''
<div id="category-{0}" class="category">
    <h1>{1}</h1>
            '''.format(category, category_titles[category])
        for word in sorted(terms[category].values(), key=lambda w: w.title.lower()):
            content += word.content
        content += u'''
</div>
'''
    content = fix_content(content)

    body = u'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
  </style>
</head>
<body>
''' + content + u'''
</body>
</html>
'''

    coverFile = outpath + '/cover.html'
    f = codecs.open(coverFile, 'w', encoding='utf-8')
    f.write(cover)
    f.close()

    licenseFile = outpath + '/license.html'
    f = codecs.open(licenseFile, 'w', encoding='utf-8')
    f.write(license)
    f.close()

    bodyFile = outpath + '/body.html'
    f = codecs.open(bodyFile, 'w', encoding='utf-8')
    f.write(body)
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="inpath",
                        help="Directory of the tW repo to be compiled into html", required=True)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
                        required=False, help="Output path of the html file")
    parser.add_argument('-v', '--version', dest="version",
                        required=True, help="Version of translationWords")
    parser.add_argument('-p', '--publisher', dest="publisher",
                        required=True, help="Publisher of translationWords")
    parser.add_argument('-c', '--contributors', dest="contributors",
                        required=True, help="Contributors of translationWords")
    parser.add_argument('-d', '--issued_date', dest="issued_date",
                        required=True, help="Issued Date")

    args = parser.parse_args(sys.argv[1:])

    main(args.inpath, args.outpath, args.version, args.publisher, args.contributors, args.issued_date)
