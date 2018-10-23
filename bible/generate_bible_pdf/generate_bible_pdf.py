#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

"""
This script generates the HTML tN documents for each book of the Bible
"""
from __future__ import unicode_literals, print_function
import os
import sys
import re
import pprint
import logging
import argparse
import tempfile
import markdown
import shutil
import subprocess
import csv
import codecs
import json
from glob import glob
from bs4 import BeautifulSoup
from usfm_tools.transform import UsfmTransform
from ...general_tools.file_utils import write_file, read_file, load_json_object, unzip, load_yaml_object
from ...general_tools.url_utils import download_file
from ...general_tools.bible_books import BOOK_NUMBERS, BOOK_CHAPTER_VERSES
from ...general_tools.usfm_utils import usfm3_to_usfm2
from ...catalog.v3.catalog import UWCatalog


_print = print

def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))

class BibleConverter(object):

    def __init__(self, resource_id=None, working_dir=None, 
                    output_dir=None, lang_code='en', books=None):
        """
        :param resource_id:
        :param working_dir:
        :param output_dir:
        :param lang_code:
        :param books:
        """
        self.resource_id = resource_id
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.html_dir = os.path.join(self.output_dir, '{0}_{1}_html'.format(self.lang_code, self.resource_id))
        self.pdf_dir = os.path.join(self.output_dir, '{0}_{1}_pdf'.format(self.lang_code, self.resource_id))
        self.books = books

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='bible-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.debug('TEMP DIR IS {0}'.format(self.working_dir))
        self.bible_dir = os.path.join(self.working_dir, '{0}_{1}'.format(lang_code, resource_id))

        self.title = None
        self.book_id = None
        self.book_title = None
        self.book_number = None
        self.project = None
        self.bible_text = ''
        self.version = None
        self.publisher = None
        self.issued = None
        self.filename_base = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.uwc = None
        self.resource = None

    def run(self):
        self.uwc = UWCatalog()
        self.resource = self.uwc.get_resource(self.lang_code, self.resource_id)
        self.title = self.resource['title']
        self.version = self.resource['version']
        self.contributors = '; '.join(self.resource['contributor'])
        self.publisher = self.resource['publisher']
        self.issued = self.resource['issued']
        self.download_resource_files()
        projects = self.resource['projects']
        for p in projects:
            self.project = p
            self.book_id = p['identifier']
            self.book_title = p['title']
            self.book_number = BOOK_NUMBERS[self.book_id]
            if int(self.book_number) < 41 or (self.books and p['identifier'] not in self.books):
                continue
            self.filename_base = '{0}_{1}_{2}-{3}_v{4}'.format(self.lang_code, self.resource_id, self.book_number.zfill(2), self.book_id.upper(), self.version)
            self.logger.info('Creating PDF for {0} {1} ({2}-{3})...'.format(self.resource_id.upper(), self.book_title, self.book_number, self.book_id))
            if not os.path.isdir(self.html_dir):
                os.makedirs(self.html_dir)
            if not os.path.exists(os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))):
                self.logger.info("Generating Body HTML...")
                self.generate_body_html()
                self.logger.info("Generating Cover HTML...")
                self.generate_cover_html()
                self.logger.info("Generating License HTML...")
                self.generate_license_html()
                self.logger.info("Copying header file...")
                header_file = os.path.join(self.my_path, 'header.html')
                shutil.copy2(header_file, self.html_dir)
                self.logger.info("Copying style sheet file...")
                style_file = os.path.join(self.my_path, 'style.css')
                shutil.copy2(style_file, self.html_dir)
            if not os.path.exists(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))):
                self.logger.info("Generating PDF {0}...".format(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))))
                self.generate_bible_pdf()

    def download_resource_files(self):
        if not os.path.isdir(os.path.join(self.bible_dir)):
            zip_url = self.resource['formats'][0]['url']
            self.extract_files_from_url(zip_url)

    def extract_files_from_url(self, url):
        zip_file = os.path.join(self.working_dir, url.rpartition('/')[2])
        try:
            self.logger.debug('Downloading {0}...'.format(url))
            download_file(url, zip_file)
        finally:
            self.logger.debug('finished.')
        try:
            self.logger.debug('Unzipping {0}...'.format(zip_file))
            unzip(zip_file, self.working_dir)
        finally:
            self.logger.debug('finished.')

    def get_contributors_html(self):
        if self.contributors and len(self.contributors):
            return '<div id="contributors" class="article">\n<h1 class="section-header">Contributors</h1>\n<p>{0}</p></div>'.format(self.contributors)
        else:
            return ''

    def generate_body_html(self):
        bible_html = self.get_bible_html()
        contributors_html = self.get_contributors_html()
        html = '\n'.join([bible_html, contributors_html])
        soup = BeautifulSoup(html, 'html.parser')
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
        soup.head.append(soup.new_tag('link', href="style.css", rel="stylesheet"))
        soup.head.append(soup.new_tag('link', href="http://fonts.googleapis.com/css?family=Noto+Serif", rel="stylesheet", type="text/css"))
        html_file = os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))
        write_file(html_file, unicode(soup))
        self.logger.info('Wrote HTML to {0}'.format(html_file))

    def generate_cover_html(self):
        cover_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="https://unfoldingword.org/assets/img/icon-{0}.png" width="120">
    <span class="h1">{1}</span>
    <span class="h2">{2}</span>
    <span class="h3">Version {3}</span>
  </div>
</body>
</html>
'''.format(self.resource_id, self.title, self.book_title, self.version)
        html_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.filename_base))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        license_file = os.path.join(self.bible_dir, 'LICENSE.md')
        license = markdown.markdown(read_file(license_file))
        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
    <p>
      <strong>Date:</strong> {0}<br/>
      <strong>Version:</strong> {1}<br/>
      <strong>Published by:</strong> {2}<br/>
    </p>
    {3}
  </div>
</body>
</html>'''.format(self.issued, self.version, self.publisher, license)
        html_file = os.path.join(self.html_dir, 'license.html')
        write_file(html_file, license_html)

    def generate_bible_pdf(self):
        cover_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.filename_base))
        license_file = os.path.join(self.html_dir, 'license.html')
        header_file = os.path.join(self.html_dir, 'header.html')
        body_file = os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))
        output_file = os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))
        template_file = os.path.join(self.my_path, 'toc_template.xsl')
        if not os.path.isdir(self.pdf_dir):
            os.makedirs(self.pdf_dir)
        command = '''wkhtmltopdf 
                        --javascript-delay 2000 
                        --encoding utf-8 
                        --outline-depth 3 
                        -O portrait 
                        -L 15 -R 15 -T 15 -B 15 
                        --header-html "{0}" --header-spacing 2 
                        --footer-center '[page]' 
                        cover "{1}" 
                        cover "{2}" 
                        toc 
                        --disable-dotted-lines 
                        --enable-external-links 
                        --xsl-style-sheet "{3}" 
                        "{4}" 
                        "{5}"
                    '''.format(header_file, cover_file, license_file, template_file, body_file, output_file)
        command = re.sub(r'\s+', ' ', command, flags=re.MULTILINE)
        self.logger.info(command)
        subprocess.call(command, shell=True)

    def pad(self, num):
        if self.book_id == 'psa':
            return str(num).zfill(3)
        else:
            return str(num).zfill(2)

    @staticmethod
    def isInt(str):
        try: 
            int(str)
            return True
        except ValueError:
            return False

    def get_bible_html(self):
        path = os.path.join(self.working_dir, '{0}_{1}_usfm_conversion'.format(self.lang_code, self.resource_id), '{0}'.
                                format(self.book_id))
        filename_base = '{0}-{1}'.format(self.book_number, self.book_id.upper())
        usfm_file = os.path.join(path, '{0}.usfm'.format(filename_base))
        html_file = os.path.join(path, '{0}.html'.format(filename_base))
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(html_file):
            repo_usfm_file = os.path.join(self.bible_dir, '{0}.usfm'.format(filename_base))
            usfm3 = read_file(repo_usfm_file)
            usfm2 = usfm3_to_usfm2(usfm3)
            write_file(usfm_file, usfm2)
            UsfmTransform.buildSingleHtml(path, path, filename_base)
        html = read_file(html_file)
        return html

    @staticmethod
    def increase_headers(text, increase_depth=1):
        if text:
            for num in range(5,0,-1):
                text = re.sub(r'<h{0}>\s*(.+?)\s*</h{0}>'.format(num), r'<h{0}>\1</h{0}>'.format(num+increase_depth), text, flags=re.MULTILINE)
        return text

    @staticmethod
    def decrease_headers(text, minimum_header=1, decrease=1):
        if text:
            for num in range(minimum_header, minimum_header+10):
                text = re.sub(r'<h{0}>\s*(.+?)\s*</h{0}>'.format(num), r'<h{0}>\1</h{0}>'.format(num-decrease if (num-decrease) <= 5 else 5), text, flags=re.MULTILINE)
        return text

def main(resource_id, lang_code, books, working_dir, output_dir):
    """
    :param resource_id:
    :param lang_code:
    :param books:
    :param working_dir:
    :param output_dir:
    :return:
    """
    converter = BibleConverter(resource_id, working_dir, output_dir, lang_code, books)
    converter.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_code', default='en', required=False, help="Language Code")
    parser.add_argument('-b', '--book_id', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help="Working Directory")
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help="Output Directory")
    parser.add_argument('-r', '--resource', dest='resource_id', default='ult', required=False, help="Bible resource")

    args = parser.parse_args(sys.argv[1:])
    main(args.resource_id, args.lang_code, args.books, args.working_dir, args.output_dir)
