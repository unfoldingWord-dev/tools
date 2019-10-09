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
from __future__ import unicode_literals
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


def main(inpath, outpath, version, publisher, contributors, issued_date, book, title):
    tqRoot = inpath

    license = markdown2.markdown_path(tqRoot+'/'+'LICENSE.md')

    content = ''
    coverBookTitle = ''
    books = get_bible_book.book_order
    for b in books:
        bookTitle = get_bible_book.books[b][0]
        b = b.lower()
        if book == 'all' or b == book:
            if b == book:
              coverBookTitle = bookTitle
            content += '<div id="{0}" class="book">\n\n'.format(b)
            chapter_dirs = sorted(glob(os.path.join(tqRoot, b, '*')))
            for chapter_dir in chapter_dirs:
                if os.path.isdir(chapter_dir):
                    chapter = os.path.basename(chapter_dir).lstrip('0')
                    content += '<div id="{0}-chapter-{1}" class="chapter break">\n\n'.format(b, chapter)
                    if chapter == '1':
                       content += '<h1>{0}</h1>\n'.format(bookTitle)
                    content += '<h2>{0} {1}</h2>\n'.format(bookTitle, chapter)
                    verse_files = sorted(glob(os.path.join(chapter_dir, '*.md')))
                    for verse_idx, verse_file in enumerate(verse_files):
                        start_verse = os.path.splitext(os.path.basename(verse_file))[0].lstrip('0')
                        if verse_idx < len(verse_files)-1:
                            end_verse = str(int(os.path.splitext(os.path.basename(verse_files[verse_idx+1]))[0])-1)
                        else:
                            end_verse = bible_books.BOOK_CHAPTER_VERSES[b][chapter.lstrip('0')]
                        verses = '{0}-{1}'.format(start_verse, end_verse)
                        if start_verse == end_verse:
                           verses = start_verse
                        content += '<div id="{0}-chapter-{1}-verse-{2}" class="verse">\n'.format(b, chapter, start_verse)
                        content += '<h3>{0} {1}:{2}</h3>\n'.format(bookTitle, chapter, verses)
                        c = markdown2.markdown_path(verse_file)
                        c = c.replace('<h1>', '<div class="question no-break">\n<h4>')
                        c = c.replace('</h1>', '</h4>')
                        c = re.sub('<p><strong><a href="\./">Back to .*?</a></strong></p>', '', c)
                        c = c.replace('</p>', '</p>\n</div>\n\n')
                        content += c
                        content += '</div>\n\n';
                    content += '</div>\n\n'
            content += '</div>\n\n'
    content = fix_content(content)

    cover = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="translationquestions">
    <img src="https://cdn.door43.org/assets/uw-icons/logo-utq-256.png" width="120">
    <h1 class="h1">'''+title+'''</h1>
    <h2 class="h2">'''+coverBookTitle+'''</h2>
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
    <p>
      <strong>Date:</strong> '''+issued_date+'''<br/>
      <strong>Version:</strong> '''+version+'''<br/>
      <strong>Contributors:</strong> '''+contributors+'''<br/>
      <strong>Published by:</strong> '''+publisher+'''<br/>
    </p>
'''+license+'''
  </div>
</body>
</html>
'''

    body = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet">
  </style>
</head>
<body>
'''+content+'''
</body>
</html>
'''

    coverFile = outpath+'/{0}_cover.html'.format(book)
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
        required=True, help="Version of Translation Questions")
    parser.add_argument('-p', '--publisher', dest="publisher",
        required=True, help="Publisher of Translation Questions")
    parser.add_argument('-c', '--contributors', dest="contributors",
        required=True, help="Contributors of Translation Questions")
    parser.add_argument('-b', '--book', dest="book", default='all',
        required=False, help="Bible book")
    parser.add_argument('-d', '--issued-date', dest='issued_date', required=True, help='Issued date')
    parser.add_argument('-t', '--title', dest='title', required=True, help='Title')

    args = parser.parse_args(sys.argv[1:])

    main(args.inpath, args.outpath, args.version, args.publisher, args.contributors, args.issued_date, args.book, args.title)
