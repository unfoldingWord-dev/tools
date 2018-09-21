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
#  Converts a tQ repo into a PDF
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
from ..general_tools import get_bible_book, bible_books

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
        title = get_bible_book.books[b][0]
        b = b.lower()
        if book == u'all' or b == book:
            content += u'<div id="{0}" class="book">\n\n'.format(b)
            chapter_dirs = sorted(glob(os.path.join(tqRoot, b, '*')))
            for chapter_dir in chapter_dirs:
                if os.path.isdir(chapter_dir):
                    chapter = os.path.basename(chapter_dir).lstrip('0')
                    content += u'<div id="{0}-chapter-{1}" class="chapter break">\n\n'.format(b, chapter)
                    if chapter == u'1':
                       content += u'<h1>{0}</h1>\n'.format(title)
                    content += u'<h2>{0} {1}</h2>\n'.format(title, chapter)
                    verse_files = sorted(glob(os.path.join(chapter_dir, u'*.md')))
                    for verse_idx, verse_file in enumerate(verse_files):
                        start_verse = os.path.splitext(os.path.basename(verse_file))[0].lstrip(u'0')
                        if verse_idx < len(verse_files)-1:
                            end_verse = str(int(os.path.splitext(os.path.basename(verse_files[verse_idx+1]))[0])-1)
                        else:
                            end_verse = bible_books.BOOK_CHAPTER_VERSES[b][chapter.lstrip(u'0')]
                        verses = u'{0}-{1}'.format(start_verse, end_verse)
                        if start_verse == end_verse:
                           verses = start_verse
                        content += u'<div id="{0}-chapter-{1}-verse-{2}" class="verse">\n'.format(b, chapter, start_verse)
                        content += u'<h3>{0} {1}:{2}</h3>\n'.format(title, chapter, verses)
                        c = markdown2.markdown_path(verse_file)
                        c = c.replace(u'<h1>', u'<div class="question no-break">\n<h4>')
                        c = c.replace(u'</h1>', u'</h4>')
                        c = re.sub(u'<p><strong><a href="\./">Back to .*?</a></strong></p>', u'', c)
                        c = c.replace(u'</p>', u'</p>\n</div>\n\n')
                        content += c
                        content += u'</div>\n\n';
                    content += u'</div>\n\n'
            content += u'</div>\n\n'
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
