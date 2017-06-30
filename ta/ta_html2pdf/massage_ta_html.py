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


def main(infile, outfile):
    soup = BeautifulSoup(read_file(infile), 'html.parser')

    for h in soup.find_all(['h3', 'h4', 'h5', 'h6']):
        if not h.get('class') or 'section-header' not in h['class']:
            h['class'] = h.get('class', []) + [h.name]
            h.name = 'span'

    soup.html.head.style.append('''
body {
    font-family: 'Noto Sans', sans-serif;
    font-size: 12pt;
}

h1, h2, h3, h4, h5, h6,
.h1, .h2, .h3, .h4, .h5, .h6 {
    page-break-before: auto !important;
    page-break-after: avoid !important;
    break-after: avoid-page !important;
}

.section-header {
    display: block;
    font-size: 1.5em;
    -webkit-margin-before: 0.83em;
    -webkit-margin-after: 0.83em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

h1 + *, h2 + *, h3 + *, h4 + *, h5 + *, h6 + *,
.h1 + *, .h2 + *, .h3 + *, .h4 + *, .h5 + *, .h6 + *,
.section-header > p:first-child {
    page-break-before: avoid;
    page-break-after: auto;
}

li {
    page-break-before: avoid;
    page-break-after: auto;
}

.break {
    page-break-before: always !important;
    clear: both;
}

.box {
    display: block;
    font-size: 10pt;
    border-style: solid;
    border-width: 1px;
    border-color: #999999;
    padding: 5px;
    margin: 5px;
    page-break-inside: avoid;
}

dl {
    padding: 0;
}

dl dt {
    padding: 0;
    margin-top: 16px;
    font-style: italic;
    font-weight: bold;
}

dl dd {
    padding: 0 16px;
    margin-bottom: 16px;
}

blockquote {
    padding: 0 15px;
    color: #444;
    border-left: 4px solid #ddd;
}
blockquote > :first-child {
    margin-top: 0;
}
blockquote > :last-child {
    margin-bottom: 0;
}

table {
    overflow: auto;
    margin-left:auto;
    margin-right:auto;
    margin-bottom: 10px;
    word-break: normal;
    word-break: keep-all;
    border-collapse: collapse;
    border-spacing: 0;
    page-break-inside: avoid;
}
thead {
    box-shadow: none;
}
table th {
    font-weight: bold;
}
table th,
table td {
    padding: 6px 13px !important;
    border: 1px solid #ddd !important;
}
table tr {
    background-color: #fff;
    border-top: 1px solid #ccc;
}
table tr:nth-child(2n) {
    background-color: #f8f8f8;
}
table td, table th {
    -webkit-transition: background .1s ease,color .1s ease;
    transition: background .1s ease,color .1s ease;
}

thead th {
    cursor: auto;
    background: #f9fafb;
    text-align: inherit;
    color: rgba(0,0,0,.87);
    padding: .92857143em .71428571em;
    vertical-align: inherit;
    font-style: none;
    font-weight: 700;
    text-transform: none;
    border-bottom: 1px solid rgba(34,36,38,.1);
    border-left: none;
}
thead tr>th:first-child {
    border-left: none;
}
thead tr:first-child>th:first-child {
    border-radius: .28571429rem 0 0;
}

a {
    display: inline-block;
    text-decoration: none;
    color: blue;
}
a:link {
    color: blue;
}
a:visited {
    color: blue;
}
a.internal {
    color: #15c !important;
}
a.external {
    color: #15F !important;
}

.docs-bubble-link, .docs-bubble a {
    color: #15c!important;
    cursor: pointer;
    text-decoration: none!important;
}

img {
    max-width: 600px;
    text-align: center;
}

ul li, ul li p {
    margin: 0;
}
div > ul > li:first-child, ol > li > ul > li:first-child {
    margin-top: 1em;
}
div > ul > li:last-child, ol > li > ul > li:last-child {
    margin-bottom: 1em;
}
ul li li:last-child {
    margin-bottom: .5em;
}

.h1 {
    display: block;
    font-size: 2em;
    -webkit-margin-before: 0.67em;
    -webkit-margin-after: 0.67em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

.h2 {
    display: block;
    font-size: 1.5em;
    -webkit-margin-before: 0.83em;
    -webkit-margin-after: 0.83em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

.h3 {
    display: block;
    font-size: 1.17em;
    -webkit-margin-before: 1em;
    -webkit-margin-after: 1em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

.h4 {
    display: block;
    -webkit-margin-before: 1.33em;
    -webkit-margin-after: 1.33em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

.h5 {
    display: block;
    font-size: 0.83em;
    -webkit-margin-before: 1.67em;
    -webkit-margin-after: 1.67em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

.h6 {
    display: block;
    font-size: 0.75em;
    -webkit-margin-before: 2em;
    -webkit-margin-after: 2em;
    -webkit-margin-start: 0px;
    -webkit-margin-end: 0px;
    font-weight: bold;
}

ol {
  list-style-type: decimal;
}
ol ol {
  list-style-type: upper-latin;
}
ol ol ol {
  list-style-type: lower-latin; 
}
ol ol ol {
  list-style-type: upper-roman;
}
ol ol ol ol {
  list-stype-type: lower-roman;
}
ul {
  list-style-type: disc;
}
ul ul {
  list-style-type: circle;
}
ul ul ul {
  list-style-type: square;
}
ul ul ul ul {
  list-style-type: circle;
}
ul ul ul ul ul {
  list-style-tyep: disc;
}
    ''')
    write_file(outfile, unicode(soup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--infile', dest="infile",
        help="Filename of the ta.html file to read", required=True)
    parser.add_argument('-o', '--outfile', dest="outfile",
        help="Filename of the ta.html file to write out to", required=True)

    args = parser.parse_args(sys.argv[1:])

    main(args.infile, args.outfile)
