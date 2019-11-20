#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

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
import dateutil.parser
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
                    output_dir=None, lang_code='en', books=None, tag='master'):
        """
        :param resource_id:
        :param working_dir:
        :param output_dir:
        :param lang_code:
        :param books:
        :param tag:
        """
        self.resource_id = resource_id
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.html_dir = os.path.join(self.output_dir, '{0}_{1}_html'.format(self.lang_code, self.resource_id))
        self.pdf_dir = os.path.join(self.output_dir, '{0}_{1}_pdf'.format(self.lang_code, self.resource_id))
        self.books = books
        self.tag = tag

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
        # self.uwc = UWCatalog()
        # self.resource = self.uwc.get_resource(self.lang_code, self.resource_id)
        self.download_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.bible_dir, 'manifest.yaml'))
        self.resource = self.manifest['dublin_core']
        self.title = self.resource['title']
        self.version = self.resource['version']
        self.contributors = '<br/>'.join(self.resource['contributor'])
        self.publisher = self.resource['publisher']
        self.issued =  dateutil.parser.parse(self.resource['issued']).strftime('%Y-%m-%d')
        projects = self.manifest['projects']
        if not self.books or 'nt' not in self.books:
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
                if True or not os.path.exists(os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))):
                    self.logger.info("Generating Body HTML...")
                    self.generate_bible_html()
                    self.logger.info("Generating Cover HTML...")
                    self.generate_cover_html()
                    self.logger.info("Generating License HTML...")
                    self.generate_license_html()
                if True or not os.path.exists(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))):
                    self.logger.info("Generating PDF {0}...".format(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))))
                    self.generate_bible_pdf()
        else:
                self.project = None
                self.book_number = '0'
                self.book_id = 'nt'
                self.book_title = 'New Testament'
                self.filename_base = '{0}_{1}_{2}_v{3}'.format(self.lang_code, self.resource_id, self.book_id.upper(), self.version)
                self.logger.info('Creating PDF for {0} {1} ({2})...'.format(self.resource_id.upper(), self.book_title, self.book_id))
                if not os.path.isdir(self.html_dir):
                    os.makedirs(self.html_dir)
                if True or not os.path.exists(os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))):
                    self.logger.info("Generating Body HTML...")
                    self.generate_bible_html()
                    self.logger.info("Generating Cover HTML...")
                    self.generate_cover_html()
                    self.logger.info("Generating License HTML...")
                    self.generate_license_html()
                if True or not os.path.exists(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))):
                    self.logger.info("Generating PDF {0}...".format(os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))))
                    self.generate_bible_pdf()

    def download_resource_files(self):
        if not os.path.isdir(os.path.join(self.bible_dir)):
            # zip_url = self.resource['formats'][0]['url']
            zip_url = 'https://git.door43.org/Door43-Catalog/{0}_{1}/archive/{2}.zip'.format(self.lang_code, self.resource_id, self.tag)
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

    def generate_bible_html(self):
        bible_html = self.get_bible_body_html()
        contributors_html = self.get_contributors_html()
        html = '\n'.join(['<html><head><title>{0} - {1}</title></head><body>'.format(self.book_title, self.title), bible_html, contributors_html, '</body></html>'])
        soup = BeautifulSoup(html, 'html.parser')
        soup.head.append(soup.new_tag('link', href="file://{0}/style.css".format(self.my_path), rel="stylesheet", type="text/css"))
        soup.head.append(soup.new_tag('script', src="file://{0}/jquery.min.js".format(self.my_path)))
        soup.head.append(soup.new_tag('script', src="file://{0}/script.js".format(self.my_path), type="text/javascript"))
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
  <link href="file://{4}/style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="https://unfoldingword.org/assets/img/icon-{0}.png" width="120">
    <h1>{1}</h1>
    <h2>{2}</h2>
    <h3>Version {3}</h3>
  </div>
</body>
</html>
'''.format(self.resource_id, self.title, self.book_title, self.version, self.my_path)
        html_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.filename_base))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        license_file = os.path.join(self.bible_dir, 'LICENSE.md')
        license = markdown.markdown(read_file(license_file))
        license = license.replace('<h1', '<span class="h2"').\
            replace('<h2', '<span class="h3"').\
            replace('<h3', '<span class="h4"').\
            replace('</h1>', '</span>').\
            replace('</h2>', '</span>').\
            replace('</h3>', '</span>')
        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="file://{4}/style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <h1>Copyrights & Licensing</h1>
    <p>
      <strong>Date:</strong> {0}<br/>
      <strong>Version:</strong> {1}<br/>
      <strong>Published by:</strong> {2}<br/>
    </p>
    {3}
  </div>
</body>
</html>'''.format(self.issued, self.version, self.publisher, license, self.my_path)
        html_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.filename_base))
        write_file(html_file, license_html)

    def generate_bible_pdf(self):
        header_file = os.path.join(self.my_path, 'header.html')
        template_file = os.path.join(self.my_path, 'toc_template.xsl')
        cover_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.filename_base))
        license_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.filename_base))
        body_file = os.path.join(self.html_dir, '{0}.html'.format(self.filename_base))
        output_file = os.path.join(self.pdf_dir, '{0}.pdf'.format(self.filename_base))
        
        if not os.path.isdir(self.pdf_dir):
            os.makedirs(self.pdf_dir)

        command = '''wkhtmltopdf 
                        --print-media-type
                        --dpi 96
                        --page-size letter
                        --enable-javascript
                        --javascript-delay 5000
                        --no-stop-slow-scripts
                        --debug-javascript
                        --encoding utf-8 
                        --outline-depth 3 
                        -O portrait
                        -L 15 -R 15 -T 15 -B 15 
                        --header-html "{0}"
                        --header-spacing 2 
                        --footer-center '[page]' 
                        cover "{1}" 
                        page "{2}" 
                        toc 
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

    def get_bible_body_html(self):
        usfm_conversion_path = os.path.join(self.working_dir, '{0}_{1}_usfm_conversion'.format(self.lang_code, self.resource_id), '{0}'.
                                format(self.book_id))
        filename_base = '{0}-{1}'.format(self.book_number, self.book_id.upper())
        html_file = os.path.join(usfm_conversion_path, '{0}.html'.format(filename_base))
        if not os.path.exists(usfm_conversion_path):
            os.makedirs(usfm_conversion_path)
        if True or not os.path.exists(html_file):
            usfm_files = glob(os.path.join(self.bible_dir, '*.usfm'))
            for usfm_file in usfm_files:
                usfm_file_base = os.path.basename(usfm_file)
                if filename_base in usfm_file_base or (self.book_id == 'nt' and int(usfm_file_base.split('-')[0]) > 40):
                    usfm3 = read_file(usfm_file)
                    usfm2 = usfm3_to_usfm2(usfm3)
                    write_file(os.path.join(usfm_conversion_path, usfm_file_base), usfm2)
            UsfmTransform.buildSingleHtml(usfm_conversion_path, usfm_conversion_path, filename_base)
        html = read_file(html_file)
        soup = BeautifulSoup(html, 'html.parser')
        html = unicode(soup.find('body'))
        html = re.sub(r' +(<span id="ref-fn-)', r'\1', html, flags=re.MULTILINE)
        html = re.sub(r'(</b></sup></span>) +', r'\1', html, flags=re.MULTILINE)
        html = re.sub(r' +(</i>)', r'\1', html, flags=re.MULTILINE)
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

def main(resource_id, lang_code, books, working_dir, output_dir, tag):
    """
    :param resource_id:
    :param lang_code:
    :param books:
    :param working_dir:
    :param output_dir:
    :param tag:
    :return:
    """
    converter = BibleConverter(resource_id, working_dir, output_dir, lang_code, books, tag)
    converter.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_code', default='en', required=False, help="Language Code")
    parser.add_argument('-b', '--book_id', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help="Working Directory")
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help="Output Directory")
    parser.add_argument('-r', '--resource', dest='resource_id', default='ult', required=False, help="Bible resource")
    parser.add_argument('-t', '--tag', dest='tag', default='master', required=False, help="repo tag of the version, master also allowed")

    args = parser.parse_args(sys.argv[1:])
    main(args.resource_id, args.lang_code, args.books, args.working_dir, args.output_dir, args.tag)
