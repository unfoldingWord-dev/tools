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
import time
from glob import glob
from ..general_tools import get_bible_book

reload(sys)
sys.setdefaultencoding('utf8')

tqRoot = ''


def fix_content(content):
    content = re.sub(ur'A\. (.*)', ur'A. \1\n</p>\n\n<p>\n<hr/>', content)
    content = re.sub(ur'(Q\?|A\.) ', ur'<b>\1</b> ', content)
    content = re.sub(ur'>([^>]+) 0*([0-9]+) Translation Questions', ur'>\1 \2', content)
    return content


def main(inpath, outpath, version, issued_date, book):
    tqRoot = inpath

    license = markdown2.markdown_path(tqRoot+'/'+'LICENSE.md')

    content = ''
    books = get_bible_book.book_order
    for b in books:
        b = b.lower()
        if book == 'all' or b == book:
            content += u'<div id="{0}" class="book">'.format(b)
            file_spec = os.path.join(tqRoot, b, '*/*.md')
            files = sorted(glob(file_spec))
            for f in files:
                root = os.path.splitext(f)[0]
                parts = root.split('/')
                chapter = parts[-2]
                verse = parts[-1]
                c = markdown2.markdown_path(f)
                c = u'<div id="{0}-chapter-{1}-{2}" class="chapter">'.format(b, chapter, verse) + c + u'</div>'
                c = re.sub('<p><strong><a href="\./">Back to .*?</a></strong></p>', '', c)
                content += c
            content += u'</div>'
    content = fix_content(content)

    cover = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="translationQuestions">
    <img src="https://unfoldingword.org/assets/img/icon-tq.png" width="120">
    <h1 class="h1">translationQuestions</h1>
    <h3 class="h3">v'''+version+'''</h3>
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
'''+license+'''
    <p>
      <strong>Date:</strong> '''+issued_date+'''<br/>
      <strong>Version:</strong> '''+version+'''
    </p>
  </div>
</body>
</html>
'''

    body = u'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
  </style>
</head>
<body>
'''+content+u'''
</body>
</html>
'''

    coverFile = outpath+'/cover.html'
    f = codecs.open(coverFile, 'w', encoding='utf-8')
    f.write(cover)
    f.close()

    licenseFile = outpath+'/license.html'
    f = codecs.open(licenseFile, 'w', encoding='utf-8')
    f.write(license)
    f.close()

    bodyFile = outpath+'/{0}.html'.format(book)
    f = codecs.open(bodyFile, 'w', encoding='utf-8')
    f.write(body)
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tQ repo to be compiled into html", required=True)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path of the html file")
    parser.add_argument('-v', '--version', dest="version",
        required=True, help="Version of translationQuestions")
    parser.add_argument('-b', '--book', dest="book", default='all',
        required=False, help="Bible book")
    parser.add_argument('-d', '--issued-date', dest='issued_date', required=True, help='Issued date')

    args = parser.parse_args(sys.argv[1:])

    main(args.inpath, args.outpath, args.version, args.issued_date, args.book)
