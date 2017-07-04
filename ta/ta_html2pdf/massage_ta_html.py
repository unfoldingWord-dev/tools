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
import re
import sys
import codecs
import argparse
from bs4 import BeautifulSoup


def read_file(file_name, encoding='utf-8-sig'):
    with codecs.open(file_name, 'r', encoding=encoding) as f:
        content = f.read()
    # convert Windows line endings to Linux line endings
    content = content.replace('\r\n', '\n')
    return content


def write_file(file_name, file_contents):
    with codecs.open(file_name, 'w', encoding='utf-8') as out_file:
        out_file.write(file_contents)


def main(infile, outfile, stylefile, version):
    soup = BeautifulSoup(read_file(infile), 'html.parser')

    # Removes first h1 tag which is English: translationAcademy
    soup.find('h1').extract()

    # Make all headers that have a header right before them non-break
    for h in soup.find_all(['h2','h3', 'h4', 'h5', 'h6']):
        prev = h.find_previous_sibling()
        if prev and re.match('^h[2-6]$', prev.name):
            h['class'] = h.get('class', []) + ['no-break'] 

    # Make all headers within the page content to just be span tags with h# classes
    for h in soup.find_all(['h3', 'h4', 'h5', 'h6']):
        if not h.get('class') or 'section-header' not in h['class']:
            h['class'] = h.get('class', []) + [h.name]
            h.name = 'span'

    # Make manual page
    for h in soup.find_all('h1'):
        container = soup.new_tag('div', style='text-align:center;padding-top:200px')
        container['class'] = ['break']
        h.insert_before(container)
        img = soup.new_tag('img', src="https://unfoldingword.org/assets/img/icon-ta.png", width="120")
        img['class'] = ['break']
        container.append(img)
        h1 = soup.new_tag('span')
        h1['class'] = ['h1']
        h1.string = 'translationAcademy'
        container.append(h1)
        h['class'] = ['h2', 'no-break']
        container.append(h)
        h3 = soup.new_tag('span')
        h3['class'] = ['h3']
        h3.string = 'Version {0}'.format(version)
        container.append(h3)

    for a in soup.find_all('a'):
        a['href'] = re.sub(r'^[A-Za-z0-9\.-]+#(.*)$', r'#\1', a['href'])

    soup.head.append(soup.new_tag('link', href="file://"+stylefile, rel="stylesheet"))

    write_file(outfile, unicode(soup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--infile', dest="infile",
        help="Filename of the ta.html file to read", required=True)
    parser.add_argument('-o', '--outfile', dest="outfile",
        help="Filename of the ta.html file to write out to", required=True)
    parser.add_argument('-s', '--styleile', dest="stylefile",
        help="Filename of the style sheet", required=True)
    parser.add_argument('-v', '--version', dest="version",
        help="Version of tA", required=True)

    args = parser.parse_args(sys.argv[1:])

    main(args.infile, args.outfile, args.stylefile, args.version)
