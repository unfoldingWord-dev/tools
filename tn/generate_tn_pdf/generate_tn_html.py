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

_print = print

def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))

class TnConverter(object):

    def __init__(self, ta_tag=None, tn_tag=None, tw_tag=None, ust_tag=None, ult_tag=None, ugnt_tag=None, working_dir=None, 
                    output_dir=None, lang_code='en', books=None):
        """
        :param ta_tag:
        :param tn_tag:
        :param tw_tag:
        :param ust_tag:
        :param ult_tag:
        :param ugnt_tag:
        :param working_dir:
        :param output_dir:
        :param lang_code:
        :param books:
        """
        self.ta_tag = ta_tag
        self.tn_tag = tn_tag
        self.tw_tag = tw_tag
        self.ust_tag = ust_tag
        self.ult_tag = ult_tag
        self.ugnt_tag = ugnt_tag
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
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
            self.working_dir = tempfile.mkdtemp(prefix='tn-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.debug('TEMP DIR IS {0}'.format(self.working_dir))
        self.tn_dir = os.path.join(self.working_dir, '{0}_tn'.format(lang_code))
        self.tw_dir = os.path.join(self.working_dir, '{0}_tw'.format(lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(lang_code))
        self.ust_dir = os.path.join(self.working_dir, '{0}_ust'.format(lang_code))
        self.ult_dir = os.path.join(self.working_dir, '{0}_ult'.format(lang_code))
        self.ugnt_dir = os.path.join(self.working_dir, 'UGNT')
        self.versification_dir = os.path.join(self.working_dir, 'versification', 'bible', 'ufw', 'chunks')

        self.manifest = None

        self.book_id = None
        self.book_title = None
        self.book_number = None
        self.project = None
        self.tn_text = ''
        self.tw_text = ''
        self.ta_text = ''
        self.rc_references = {}
        self.chapters_and_verses = {}
        self.verse_usfm = {}
        self.chunks_text = {}
        self.chunk_text = {}
        self.resource_data = {}
        self.tn_book_data = {}
        self.tw_words_data = {}
        self.bad_links = {}
        self.usfm_chunks = {}
        self.version = None
        self.publisher = None
        self.issued = None
        self.filename_base = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))

        self.lastEndedWithQuoteTag = False
        self.lastEndedWithParagraphTag = False
        self.openQuote = False
        self.nextFollowsQuote = False

    def run(self):
        self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        self.contributors = '; '.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book_id = p['identifier'].lower()
            self.book_title = p['title'].replace(' translationNotes', '')
            self.book_number = BOOK_NUMBERS[self.book_id]
            if int(self.book_number) < 41:
                continue
            self.resource_data = {}
            self.rc_references = {}
            self.populate_tn_book_data()
            self.populate_tw_words_data()
            self.populate_chapters_and_verses()
            self.populate_verse_usfm()
            self.populate_chunks_text()
            self.filename_base = '{0}_tn_{1}-{2}_v{3}'.format(self.lang_code, self.book_number.zfill(2), self.book_id.upper(), self.version)
            self.logger.info('Creating tN for {0} ({1}-{2})...'.format(self.book_title, self.book_number, self.book_id))
            if not os.path.isdir(os.path.join(self.output_dir, 'tn_html')):
                os.makedirs(os.path.join(self.output_dir, 'tn_html'))
            if not os.path.exists(os.path.join(self.output_dir, 'tn_html', '{0}.html'.format(self.filename_base))):
                self.logger.info("Generating Body HTML...")
                self.generate_body_html()
                self.logger.info("Generating Cover HTML...")
                self.generate_cover_html()
                self.logger.info("Generating License HTML...")
                self.generate_license_html()
                self.logger.info("Copying page header file...")
                header_file = os.path.join(self.my_path, 'header.html')
                shutil.copyfile(header_file, os.path.join(self.output_dir, 'tn_html', '{0}_header.html'.format(self.filename_base)))
                self.logger.info("Copying style sheet file...")
                style_file = os.path.join(self.my_path, 'style.css')
                shutil.copyfile(style_file, os.path.join(self.output_dir, 'tn_html', '{0}_style.css'.format(self.filename_base)))
            if not os.path.exists(os.path.join(self.output_dir, 'tn_pdf', '{0}.pdf'.format(self.filename_base))):
                self.logger.info("Generating PDF {0}...".format(os.path.join(self.output_dir, 'tn_pdf', '{0}.pdf'.format(self.filename_base))))
                #self.generate_tn_pdf()
        _print("BAD LINKS:")
        for source_rc in sorted(self.bad_links.keys()):
            for rc in sorted(self.bad_links[source_rc].keys()):
                source = source_rc[5:].split('/')
                parts = rc[5:].split('/')
                if source[1] == 'tn' and parts[1] == 'tw':
                    str = 'UGNT {0} {1}:{2}'.format(source[3].upper(), source[4], source[5])
                else:
                    str = 't{0} {1}'.format(source[1][1].upper(), '/'.join(source[3:]))
                str += ': BAD RC - {0}'.format(rc)
                if self.bad_links[source_rc][rc]:
                    str += ' - change to `{0}`'.format(self.bad_links[source_rc][rc])
                _print(str)

    def get_book_projects(self):
        projects = []
        if not self.manifest or 'projects' not in self.manifest or not self.manifest['projects']:
            return
        for p in self.manifest['projects']:
            if not self.books or p['identifier'] in self.books:
                if not p['sort']:
                    p['sort'] = BOOK_NUMBERS[p['identifier']]
                projects.append(p)
        return sorted(projects, key=lambda k: k['sort'])

    def get_resource_url(self, resource, tag):
        return 'https://git.door43.org/unfoldingWord/{0}_{1}/archive/{2}.zip'.format(self.lang_code, resource, tag)

    def setup_resource_files(self):
        if not os.path.isdir(os.path.join(self.working_dir, 'en_tn')):
            tn_url = self.get_resource_url('tn', self.tn_tag)
            self.extract_files_from_url(tn_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_tw')):
            tw_url = self.get_resource_url('tw', self.tw_tag)
            self.extract_files_from_url(tw_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_ta')):
            ta_url = self.get_resource_url('ta', self.ta_tag)
            self.extract_files_from_url(ta_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_ust')):
            ust_url = self.get_resource_url('ust', self.ust_tag)
            self.extract_files_from_url(ust_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_ult')):
            ult_url = self.get_resource_url('ult', self.ult_tag)
            self.extract_files_from_url(ult_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'ugnt')):
            ugnt_url = 'https://git.door43.org/unfoldingWord/UGNT/archive/{0}.zip'.format(self.ugnt_tag)
            self.extract_files_from_url(ugnt_url)
        if not os.path.isfile(os.path.join(self.working_dir, 'icon-tn.png')):
            command = 'curl -o {0}/icon-tn.png https://unfoldingword.bible/assets/img/icon-tn.png'.format(self.working_dir)
            subprocess.call(command, shell=True)
        if not os.path.isdir(os.path.join(self.working_dir, 'versification')):
            versification_url = 'https://git.door43.org/Door43-Catalog/versification/archive/master.zip'
            self.extract_files_from_url(versification_url)

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

    def populate_chunks_text(self):
        save_dir = os.path.join(self.working_dir, 'chunks_text')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}.json'.format(self.book_id))

        if os.path.isfile(save_file):
            self.chunks_text = load_json_object(save_file)
            return

        chunks_text = {}            
        for chapter_data in self.chapters_and_verses:
            chapter = chapter_data['chapter']
            chunks_text[str(chapter)] = {}
            for idx, first_verse in enumerate(chapter_data['first_verses']):
                if len(chapter_data['first_verses']) > idx+1:
                    last_verse = chapter_data['first_verses'][idx+1] - 1
                else:
                    last_verse = int(BOOK_CHAPTER_VERSES[self.book_id][str(chapter)])
                chunks_text[str(chapter)][str(first_verse)] = {
                    'first_verse': first_verse,
                    'last_verse': last_verse
                }
                for resource in ['ult', 'ust']:
                    versesInChunk = []
                    for verse in range(first_verse, last_verse+1):
                        if resource != 'ust' or verse in self.verse_usfm[resource][chapter]:
                            versesInChunk.append(self.verse_usfm[resource][chapter][verse])
                    chunk_usfm = '\n'.join(versesInChunk)
                    chunks_text[str(chapter)][str(first_verse)][resource] = {
                        'usfm': chunk_usfm,
                        'html': self.get_chunk_html(chunk_usfm, resource, chapter, first_verse)
                    }
            write_file(save_file, chunks_text)
        self.chunks_text = chunks_text

    def get_contributors_html(self):
        if self.contributors and len(self.contributors):
            return '<div id="contributors" class="article">\n<h1 class="section-header">Contributors</h1>\n<p>{0}</p></div>'.format(self.contributors)
        else:
            return ''

    def save_resource_data(self):
        save_dir = os.path.join(self.working_dir, 'resource_data')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}.json'.format(self.book_id))
        write_file(save_file, self.resource_data)
        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.book_id))
        write_file(save_file, self.rc_references)
        save_file = os.path.join(save_dir, 'bad_links.json'.format(self.book_id))
        write_file(save_file, self.bad_links)

    def load_resource_data(self):
        save_dir = os.path.join(self.working_dir, 'resource_data')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}.json'.format(self.book_id))
        if os.path.isfile(save_file):
            self.resource_data = load_json_object(save_file)
        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.book_id))
        if os.path.isfile(save_file):
            self.rc_references = load_json_object(save_file)
        save_file = os.path.join(save_dir, 'bad_links.json'.format(self.book_id))
        if os.path.isfile(save_file):
            self.bad_links = load_json_object(save_file)

    def generate_body_html(self):
        self.load_resource_data()
        tn_html = self.get_tn_html()
        self.save_resource_data()
        ta_html = self.get_ta_html()
        tw_html = self.get_tw_html()
        contributors_html = self.get_contributors_html()
        html = '\n'.join([tn_html, tw_html, ta_html, contributors_html])
        return html
        html = self.replace_rc_links(html)
        html = self.fix_links(html)
        html = '<head><title>tN</title></head>\n' + html
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

        soup.head.append(soup.new_tag('link', href="{0}_style.css".format(self.filename_base), rel="stylesheet"))
        soup.head.append(soup.new_tag('link', href="http://fonts.googleapis.com/css?family=Noto+Serif", rel="stylesheet", type="text/css"))

        html_file = os.path.join(self.output_dir, 'tn_html', '{0}.html'.format(self.filename_base))
        write_file(html_file, unicode(soup))
        self.logger.info('Wrote HTML to {0}'.format(html_file))

    def generate_cover_html(self):
        cover_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="{0}_style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="https://unfoldingword.org/assets/img/icon-tn.png" width="120">
    <span class="h1">translationNotes</span>
    <span class="h2">{1}</span>
    <span class="h3">Version {2}</span>
  </div>
</body>
</html>
'''.format(self.filename_base, self.book_title, self.version)
        html_file = os.path.join(self.output_dir, 'tn_html', '{0}_cover.html'.format(self.filename_base))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        license_file = os.path.join(self.tn_dir, 'LICENSE.md')
        license = markdown.markdown(read_file(license_file))
        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="{0}_style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
    <p>
      <strong>Date:</strong> {1}<br/>
      <strong>Version:</strong> {2}<br/>
      <strong>Published by:</strong> {3}<br/>
    </p>
    {4}
  </div>
</body>
</html>'''.format(self.filename_base, self.issued, self.version, self.publisher, license)
        html_file = os.path.join(self.output_dir, 'tn_html', '{0}_license.html'.format(self.filename_base))
        write_file(html_file, license_html)

    def generate_tn_pdf(self):
        header_file = os.path.join(self.output_dir, 'tn_html', '{0}_header.html'.format(self.filename_base))
        cover_file = os.path.join(self.output_dir, 'tn_html', '{0}_cover.html'.format(self.filename_base))
        license_file = os.path.join(self.output_dir, 'tn_html', '{0}_license.html'.format(self.filename_base))
        body_file = os.path.join(self.output_dir, 'tn_html', '{0}.html'.format(self.filename_base))
        output_file = os.path.join(self.output_dir, 'tn_pdf', '{0}.pdf'.format(self.filename_base))
        template_file = os.path.join(self.my_path, 'toc_template.xsl')
        if not os.path.isdir(os.path.join(self.output_dir, 'tn_pdf')):
            os.makedirs(os.path.join(self.output_dir, 'tn_pdf'))
        command = '''wkhtmltopdf --javascript-delay 2000 --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "{0}" --header-spacing 2 --footer-center '[page]' cover "{1}" cover "{2}" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "{3}" "{4}" "{5}"'''.format(
            header_file, cover_file, license_file, template_file, body_file, output_file)
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

    def get_usfm_from_verse_objects(self, verseObjects, depth=0):
        usfm = ''
        for idx, obj in enumerate(verseObjects):
            if obj['type'] == 'milestone':
                usfm += self.get_usfm_from_verse_objects(obj['children'])
            elif obj['type'] == 'word':
                if not self.nextFollowsQuote and obj['text'] != 's':
                    usfm += ' '
                usfm += obj['text']
                self.nextFollowsQuote = False
            elif obj['type'] == 'text':
                obj['text'] = obj['text'].replace('\n', '').strip()
                if not self.openQuote and len(obj['text']) > 2 and obj['text'][-1] == '"':
                    obj['text' ] = '{0} {1}'.format(obj['text'][:-1], obj['text'][-1])
                if not self.openQuote and obj['text'] == '."':
                    obj['text' ] = '. "'
                if len(obj['text']) and obj['text'][0] == '"' and not self.openQuote and obj['text'] not in ['-', '—']:
                    usfm += ' '
                usfm += obj['text']
                if obj['text'].count('"') == 1:
                    self.openQuote = not self.openQuote
                if self.openQuote and '"' in obj['text'] or obj['text'] in ['-', '—', '(', '[']:
                    self.nextFollowsQuote = True
            elif obj['type'] == 'quote':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if idx == len(verseObjects) -1 and obj['tag'] == 'q' and len(obj['text']) == 0:
                    self.lastEndedWithQuoteTag = True
                else:
                    usfm += '\n\\{0} {1}'.format(obj['tag'], obj['text'] if len(obj['text']) > 0 else '')
                if obj['text'].count('"') == 1:
                    self.openQuote = not self.openQuote
                if self.openQuote and '"' in obj['text']:
                    self.nextFollowsQuote = True 
            elif obj['type'] == 'section':  
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if len(obj['text']):
                    print("Seciton with text: {0}:{1}:".format(chapter, verse))
                    print(obj)
                    exit(1)
                    continue
            elif obj['type'] == 'paragraph':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if idx == len(verseObjects) - 1 and not obj['text']:
                    self.lastEndedWithParagraphTag = True
                else:
                    usfm += '\n\\{0}{1}\n'.format(obj['tag'], obj['text'])
            elif obj['type'] == 'footnote':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if len(obj['text']):
                    print("Footnote with text: {0}:{1}:".format(chapter, verse))
                    print(obj)
                    exit(1)
                usfm += ' \{0} {1} \{0}*'.format(obj['tag'], obj['content'])
            else:
                print("ERROR! Not sure what to do with this in {0}:{1} in {2}: ".format(chapter, verse, chapter_file))
                print(obj)
                exit(1)
        return usfm

    def populate_verse_usfm(self):
        resources = ['ult', 'ust']
        bible_path = 'tools/tn/generate_tn_pdf/en/bibles'
        bookData = {}
        for resource in resources:
            bookData[resource] = {}
            chapters_path = '{0}/{1}/v1/{2}'.format(bible_path, resource, self.book_id)
            chapter_files_path = '{0}/*.json'.format(chapters_path)
            chapter_files = sorted(glob(chapter_files_path))
            for chapter_file in chapter_files:
                try:
                    chapter = int(os.path.splitext(os.path.basename(chapter_file))[0])
                except ValueError:
                    continue
                bookData[resource][chapter] = {}
                chapterData = load_json_object(chapter_file)
                self.lastEndedWithQuoteTag = False
                self.lastEndedWithParagraphTag = False
                for verse, verseData in chapterData.iteritems():
                    try:
                        verse = int(verse)
                    except ValueError:
                        continue
                    verseObjects = verseData['verseObjects']
                    self.openQuote = False
                    self.nextFollowsQuote = False
                    usfm = ''
                    if self.lastEndedWithParagraphTag:
                        usfm += '\p '
                        self.lastEndedWithParagraphTag = False
                    usfm += '\\v {0} '.format(verse)
                    if self.lastEndedWithQuoteTag:
                        usfm += '\q '
                        self.lastEndedWithQuoteTag = False
                    usfm += self.get_usfm_from_verse_objects(verseObjects)
                    bookData[resource][chapter][verse] = usfm
        self.verse_usfm = bookData
    
    def populate_chapters_and_verses(self):
        versification_file = os.path.join(self.versification_dir, '{0}.json'.format(self.book_id))
        self.chapter_and_verses = {}
        if os.path.isfile(versification_file):
            self.chapters_and_verses = load_json_object(versification_file)

    def populate_tn_book_data(self):
        book_file = os.path.join(self.tn_dir, 'en_tn_{0}-{1}.tsv'.format(self.book_number, self.book_id.upper()))
        self.tn_book_data = {}
        if not os.path.isfile(book_file):
            return
        book_data = {}
        with open(book_file) as fd:
            rd = csv.reader(fd, delimiter=str("\t"), quotechar=str('"'))
            header = next(rd)
            for row in rd:
                data = {}
                for idx, field in enumerate(header):
                    if idx >= len(row):
                        print('ERROR: {0} is maformed'.format(book_file))
                        exit(1)
                    data[field] = row[idx]
                print('{0} {1}:{2}:{3}'.format(data['Book'], data['Chapter'], data['Verse'], data['ID']))
                chapter = data['Chapter'].lstrip('0')
                verse = data['Verse'].lstrip('0')
                if not chapter in book_data:
                    book_data[chapter] = {}
                if not verse in book_data[chapter]:
                    book_data[chapter][verse] = []
                book_data[str(chapter)][str(verse)].append(data)
        self.tn_book_data = book_data

    def get_tn_html(self):
        tn_html = '<div id="tn-{0}" class="resource-title-page">\n<h1 class="section-header">translationNotes</h1>\n</div>'.format(self.book_id)
        if 'front' in self.tn_book_data and 'intro' in self.tn_book_data['front']:
            intro = markdown.markdown(self.tn_book_data['front']['intro'][0]['OccurrenceNote'].decode('utf8').replace('<br>', '\n'))
            title = self.get_first_header(intro)
            intro = self.fix_tn_links(intro, 'intro')
            intro = self.increase_headers(intro)
            intro = self.decrease_headers(intro, 4)  # bring headers of 3 or more down 1
            intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
            id = 'tn-{0}-front-intro'.format(self.book_id)
            tn_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(id, intro)
            # HANDLE RC LINKS AND BACK REFERENCE
            rc = 'rc://*/tn/help/{0}/front/intro'.format(self.book_id)
            self.resource_data[rc] = {
                'rc': rc,
                'id': id,
                'link': '#'+id,
                'title': title
            }
            self.get_resource_data_from_rc_links(intro, rc)

        for chapter_verses in self.chapters_and_verses:
            chapter = str(chapter_verses['chapter'])
            print('Chapter {0}...'.format(chapter))
            if 'intro' in self.tn_book_data[chapter]:
                intro = markdown.markdown(self.tn_book_data[chapter]['intro'][0]['OccurrenceNote'].replace('<br>',"\n"))
                intro = re.sub(r'<h(\d)>([^>]+) 0+([1-9])', r'<h\1>\2 \3', intro, 1, flags=re.MULTILINE | re.IGNORECASE)
                title = self.get_first_header(intro)
                intro = self.fix_tn_links(intro, chapter)
                intro = self.increase_headers(intro)
                intro = self.decrease_headers(intro, 5, 2)  # bring headers of 5 or more down 2
                id = 'tn-{0}-{1}-intro'.format(self.book_id, self.pad(chapter))
                intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
                tn_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(id, intro)
                # HANDLE RC LINKS
                rc = 'rc://*/tn/help/{0}/{1}/intro'.format(self.book_id, self.pad(chapter))
                self.resource_data[rc] = {
                    'rc': rc,
                    'id': id,
                    'link': '#'+id,
                    'title': title
                }
                self.get_resource_data_from_rc_links(intro, rc)

            for idx, first_verse in enumerate(chapter_verses['first_verses']):
                col1 = ''
                if idx < len(chapter_verses['first_verses'])-1:
                    last_verse = chapter_verses['first_verses'][idx+1] - 1
                else:
                    last_verse = int(BOOK_CHAPTER_VERSES[self.book_id][chapter])
                if first_verse != last_verse:
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter, first_verse, last_verse)
                else:
                    title = '{0} {1}:{2}'.format(self.book_title, chapter, first_verse)
                ids = []
                for verse in range(first_verse, last_verse+1):
                    id = 'tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), self.pad(verse))
                    ids.append(id)
                    rc = 'rc://*/tn/help/{0}/{1}/{2}'.format(self.book_id, self.pad(chapter), self.pad(verse))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': id,
                        'link': '#'+id,
                        'title': title
                    }
                header = '<h2 class="section-header">{0}</h2>'.format(title)
                col1 += '<sup style="color:light-gray">ULT</sup>' + self.get_highlighted_html('ult', int(chapter), first_verse, last_verse)
                col1 += '\n<br><br>\n'
                col1 += '<sup style="color:light-gray">UST</sup>' + self.get_plain_html('ust', int(chapter), first_verse)

                col2 = ''
                for verse in range(first_verse, last_verse+1):
                    if str(verse) in self.tn_book_data[chapter]:
                        verseNotes = ''
                        for data in self.tn_book_data[chapter][str(verse)]:
                            title = data['GLQuote'].decode('utf8')
                            verseNotes += '<b>' + title + (' -' if not title.endswith(':') else '') + ' </b>'
                            verseNotes += markdown.markdown(data['OccurrenceNote'].decode('utf8').replace('<br>',"\n")).replace('<p>', '').replace('</p>', '')
                            verseNotes += '\n<br><br>\n'
                        rc = 'rc://*/tn/help/{0}/{1}/{2}'.format(self.book_id, self.pad(chapter), self.pad(verse))
                        self.get_resource_data_from_rc_links(verseNotes, rc)
                        col2 += verseNotes
                if col2 != '':
                    col2 = self.decrease_headers(col2, 5)  # bring headers of 5 or more #'s down 1
                    col2 = self.fix_tn_links(col2, chapter)
                    chunk_article = '{0}\n<table class="tn-notes-table" style="width:100%">\n<tr>\n<td class="col1" style="vertical-align:top;width:35%;padding-right:5px">\n\n<p>{1}</p>\n</td>\n<td class="col2" style="vertical-align:top">\n\n<p>{2}</p>\n</td>\n</tr>\n</table>\n'.format(header, col1, col2)
                    tn_html += '<div id="{0}" class="article">\n{1}\n{2}\n</div>\n\n'.format(ids[0], ''.join(map(lambda x: '<a id="{0}"></a>'.format(x), ids)) if len(ids) > 1 else '', chunk_article)
        return tn_html

    def populate_tw_words_data(self):
        groups = ['kt', 'names', 'other']
        grc_path = 'tools/tn/generate_tn_pdf/grc/translationHelps/translationWords/v0.4'
        if not os.path.isdir(grc_path):
            self.logger.error('{0} not found! Please make sure you ran `node getResources ./` in the generate_tn_pdf dir and that the version in the script is correct'.format(grc_path))
            exit(1)
        words = {}
        for group in groups:
            files_path = '{0}/{1}/groups/{2}/*.json'.format(grc_path, group, self.book_id)
            files = glob(files_path)
            for file in files:
                base = os.path.splitext(os.path.basename(file))[0]
                rc = 'rc://*/tw/dict/bible/{0}/{1}'.format(group, base)
                occurrences = load_json_object(file)
                for occurrence in occurrences:
                    contextId = occurrence['contextId']
                    chapter = contextId['reference']['chapter']
                    verse = contextId['reference']['verse']
                    contextId['rc'] = rc
                    if chapter not in words:
                        words[chapter] = {}
                    if verse not in words[chapter]:
                        words[chapter][verse] = []
                    words[chapter][verse].append(contextId)
        self.tw_words_data = words

    def get_plain_html(self, resource, chapter, first_verse):
        html = self.chunks_text[str(chapter)][str(first_verse)][resource]['html']
        html = html.replace('\n', '').replace('<p>', '').replace('</p>', '').strip()
        html = re.sub(r'<span class="v-num"', '<br><span class="v-num"', html, flags=re.IGNORECASE | re.MULTILINE)
        return html;

    def get_highlighted_html(self, resource, chapter, first_verse, last_verse):
        html = self.get_plain_html(resource, chapter, first_verse)
        regex = re.compile(' <div')
        versesAndFooter = regex.split(html)
        versesHtml = versesAndFooter[0]
        footerHtml = ''
        if len(versesAndFooter) > 1:
            footerHtml = ' <div {0}'.format(versesAndFooter[1])
        regex = re.compile(r'<span class="v-num" id="\d+-ch-\d+-v-\d+"><sup><b>(\d+)</b></sup></span>')
        versesSplit = regex.split(versesHtml)
        verses = {}
        for i in range(1, len(versesSplit), 2):
            verses[int(versesSplit[i])] = versesSplit[i+1]
        newHtml = versesSplit[0]
        for verseNum in range(first_verse, last_verse +1):
            words = self.get_all_words_to_match(resource, chapter, verseNum)
            for word in words:
                parts = word['text'].split(' ... ')
                pattern = ''
                replace = ''
                newParts = []
                for idx, part in enumerate(parts):
                    prepositions = ['a', 'an', 'and', 'as', 'at', 'by', 'for', 'from', 'in', 'into', 'may', 'of', 'on', 'onto', 'the', 'with']
                    part = re.sub(r'^(({0})\s+)+'.format('|'.join(prepositions)), '', part, flags=re.MULTILINE | re.IGNORECASE)
                    if not part or (idx < len(parts)-1 and part.lower().split(' ')[-1] in prepositions):
                        continue
                    newParts.append(part)
                for idx, part in enumerate(newParts):
                    pattern += r'(?<![></\\_-])\b{0}\b(?![></\\_-])'.format(part)
                    replace += r'<a href="{0}">{1}</a>'.format(word['contextId']['rc'], part)
                    if idx + 1 < len(newParts):
                        pattern += r'(.*?)'
                        replace += r'\{0}'.format(idx + 1)
                verses[verseNum] = re.sub(pattern, replace, verses[verseNum], 1, flags=re.MULTILINE | re.IGNORECASE)
            rc = 'rc://*/tn/help/{0}/{1}/{2}'.format(self.book_id, self.pad(chapter), self.pad(str(verseNum)))
            self.get_resource_data_from_rc_links(verses[verseNum], rc)
            newHtml += '<span class="v-num" id="{0}-ch-{1}-v-{2}"><sup><b>{3}</b></sup></span>{4}'.format(str(self.book_number).zfill(3), str(chapter).zfill(3), str(verseNum).zfill(3), verseNum, verses[verseNum])
        newHtml += footerHtml
        return newHtml

    def get_all_words_to_match(self, resource, chapter, verse):
        path = 'tools/tn/generate_tn_pdf/en/bibles/{0}/v1/{1}/{2}.json'.format(resource, self.book_id, chapter)
        words = []
        data = load_json_object(path)
        chapter = int(chapter)
        if chapter in self.tw_words_data and verse in self.tw_words_data[chapter]:
            contextIds = self.tw_words_data[int(chapter)][int(verse)]
            verseObjects = data[str(verse)]['verseObjects']
            for contextId in contextIds:
                aligned_text = self.get_aligned_text(verseObjects, contextId, False)
                if aligned_text:
                    words.append({'text': aligned_text, 'contextId': contextId})
        return words

    def find_english_from_combination(self, verseObjects, quote, occurrence):
        greekWords = []
        wordList = []
        for verseObject in verseObjects:
            greek = None
            if 'content' in verseObject and verseObject['type'] == 'milestone':
                greekWords.append(verseObject['content'])
                englishWords = []
                for child in verseObject['children']:
                    if child['type'] == 'word':
                        englishWords.append(child['text'])
                english = ' '.join(englishWords)
                found = False
                for idx, word in enumerate(wordList):
                    if word['greek'] == verseObject['content'] and word['occurrence'] == verseObject['occurrence']:
                        wordList[idx]['english'] += ' ... ' + english
                        found = True
                if not found:
                    wordList.append({'greek': verseObject['content'], 'english': english, 'occurrence': verseObject['occurrence']})
        combinations = []
        occurrences = {}
        for i in range(0, len(wordList)):
            greek = wordList[i]['greek']
            english = wordList[i]['english']
            for j in range(i, len(wordList)):
                if i != j:
                    greek += ' '+wordList[j]['greek']
                    english += ' '+wordList[j]['english']
                if greek not in occurrences:
                    occurrences[greek] = 0
                occurrences[greek] += 1
                combinations.append({'greek': greek, 'english': english, 'occurrence': occurrences[greek]})
        for combination in combinations:
            if combination['greek'] == quote and combination['occurrence'] == occurrence:
                return combination['english']
        return None

    def find_english_from_split(self, verseObjects, quote, occurrence, isMatch=False):
        wordsToMatch = quote.split(' ')
        separator = ' '
        needsEllipsis = False
        text = ''
        for index, verseObject in enumerate(verseObjects):
            lastMatch = False
            if verseObject['type'] == 'milestone' or verseObject['type'] == 'word':
                if ((('content' in verseObject and verseObject['content'] in wordsToMatch) or ('lemma' in verseObject and verseObject['lemma'] in wordsToMatch)) and verseObject['occurrence'] == occurrence) or isMatch:
                    lastMatch = True
                    if needsEllipsis:
                        separator += '... '
                        needsEllipsis = False
                    if text:
                        text += separator
                    separator = ' '
                    if 'text' in verseObject and verseObject['text']:
                        text += verseObject['text']
                    if 'children' in verseObject and verseObject['children']:
                        text += self.find_english_from_split(verseObject['children'], quote, occurrence, True)
                elif 'children' in verseObject and verseObject['children']:
                    childText = self.find_english_from_split(verseObject['children'], quote, occurrence, isMatch)
                    if childText:
                        lastMatch = True
                        if needsEllipsis:
                            separator += '... '
                            needsEllipsis = False
                        text += (separator if text else '') + childText
                        separator = ' '
                    elif text:
                        needsEllipsis = True
            if lastMatch and (index+1) in verseObjects and verseObjects[index + 1]['type'] == "text" and text:
                if separator == ' ':
                    separator = ''
                separator += verseObjects[index + 1]['text']
        return text

    def get_aligned_text(self, verseObjects, contextId, isMatch=False):
        if not verseObjects or not contextId or not 'quote' in contextId or not contextId['quote']:
            return ''
        text = self.find_english_from_combination(verseObjects, contextId['quote'], contextId['occurrence'])
        if text:
            return text
        text = self.find_english_from_split(verseObjects, contextId['quote'], contextId['occurrence'])
        if text:
            return text
        # self.logger.error('English not found!')
        # print(contextId)

    def get_tw_html(self):
        tw_html = '<div id="tw-{0}" class="resource-title-page">\n<h1 class="section-header">translationWords</h1>\n</div>\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/tw/' not in rc:
                continue
            html = self.resource_data[rc]['text']
            html = self.increase_headers(html)
            title = self.resource_data[rc]['title']
            alt_title = self.resource_data[rc]['alt_title']
            if alt_title:
                html = '<h2 class="hidden">{0}</h2><span class="h2 section-header">{1}</span>\n{2}{3}'.format(alt_title, title, self.get_reference_text(rc), html)
            else:
                html = '<h2 class="section-header">{0}</h2>\n{1}{2}'.format(title, self.get_reference_text(rc), html)
            tw_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(self.resource_data[rc]['id'], html)
        return tw_html

    def get_ta_html(self):
        ta_html = '<div id="ta-{0}" class="resource-title-page">\n<h1 class="section-header">translationAcademy</h1>\n</div>\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/ta/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                html = self.resource_data[rc]['text']
                html = self.increase_headers(html)
                html = '<h2 class="section-header">{0}</h2>\n{1}<b>{2}</b>\n<br>{3}\n'.format(self.resource_data[rc]['title'], self.get_reference_text(rc), self.resource_data[rc]['alt_title'], html)
                ta_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(self.resource_data[rc]['id'], html)
        return ta_html

    def get_reference_text(self, rc):
        uses = ''
        references = []
        book_title = '{0} '.format(self.book_title)
        done = {}
        for reference in self.rc_references[rc]:
            if '/tn/' in reference and reference not in done:
                parts = reference[5:].split('/')
                id = 'tn-{0}-{1}-{2}'.format(self.book_id, parts[4], parts[5])
                if parts[4] == 'front':
                    text = 'Intro to {0}'.format(self.book_title)
                elif parts[5] == 'intro':
                    text = '{0} {1} Notes'.format(self.book_title, parts[4].lstrip('0'))
                else:
                    text = '{0}{1}:{2}'.format(book_title, parts[4].lstrip('0'), parts[5].lstrip('0'))
                    book_title = ''
                references.append('<a href="#{0}">{1}</a>'.format(id, text))
                done[reference] = True
        if len(references):
            uses = '<p>\n(<b>Go back to:</b> {0})\n</p>\n'.format('; '.join(references))
        return uses

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_\*-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            rc = 'rc://*/{0}'.format('/'.join(parts[1:]))
            resource = parts[1]
            path = '/'.join(parts[3:])

            if resource not in ['ta', 'tw']:
                continue

            if rc not in self.rc_references:
                self.rc_references[rc] = []
            if source_rc not in self.rc_references[rc]:
                self.rc_references[rc].append(source_rc)

            if rc not in self.resource_data:
                title = ''
                t = ''
                anchor_id = '{0}-{1}'.format(resource, path.replace('/', '-'))
                link = '#{0}'.format(anchor_id)
                file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                            '{0}.md'.format(path))
                if not os.path.isfile(file_path):
                    file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                '{0}/01.md'.format(path))
                fix = None
                if not os.path.isfile(file_path):
                    if resource == 'tw':
                        bad_names = {
                            'fishermen': 'bible/other/fisherman',
                            'chiefpriests': 'bible/kt/highpriest',
                            'capitive': 'bible/other/captive',
                            'olive': 'bible/other/olive',
                            'forsake': 'bible/kt/forsaken',
                            'destroy': 'bible/other/destroyer',
                            'jusdasiscariot': 'bible/names/judasiscariot',
                            'jusdassonofjames': 'bible/names/judassonofjames',
                            'jusdasonofjames': 'bible/names/judassonofjames',
                            'curcumcise': 'bible/kt/circumcise',
                            'noble': 'bible/other/noble',
                            'thessalonia': 'bible/names/thessalonica',
                            'deliver': 'bible/other/deliverer',
                            'strnegth': 'bible/other/strength',
                            'destiny': 'bible/kt/predestine',
                            'zeal': 'bible/kt/zealous',
                            'pure': 'bible/kt/purify',
                            'boey': 'bible/kt/body',
                            'prefect': 'bible/other/perfect',
                            'glorify': 'bible/kt/glory',
                            'partiarchs': 'bible/other/patriarchs',
                            'joseph': 'bible/names/josephot',
                            'soldier': 'bible/other/warrior',
                            'live': 'bible/kt/life'
                        }
                        if parts[5] in bad_names:
                            path2 = bad_names[parts[5]]
                        elif path.startswith('bible/other/'):
                            path2 = re.sub(r'^bible/other/', r'bible/kt/', path)
                        else:
                            path2 = re.sub(r'^bible/kt/', r'bible/other/', path)
                        fix = 'rc://*/tw/dict/{0}'.format(path2)
                        anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                        link = '#{0}'.format(anchor_id)
                        file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                    '{0}.md'.format(path2))
                    if resource == 'ta':
                        bad_names = {
                            'figs-abstractnoun': 'translate/figs-abstractnouns'
                        }
                        if parts[3] in bad_names:
                            path2 = bad_names[parts[3]]
                        fix = 'rc://*/ta/man/{0}'.format(path2)
                        anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                        link = '#{0}'.format(anchor_id)
                        file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                    '{0}/01.md'.format(path2))

                if os.path.isfile(file_path):
                    if fix:
                        if source_rc not in self.bad_links:
                            self.bad_links[source_rc] = {} 
                        self.bad_links[source_rc][rc] = fix
                    t = markdown.markdown(read_file(file_path))
                    alt_title = ''
                    if resource == 'ta':
                        title_file = os.path.join(os.path.dirname(file_path), 'title.md')
                        question_file = os.path.join(os.path.dirname(file_path), 'sub-title.md')
                        if os.path.isfile(title_file):
                            title = read_file(title_file)
                        else:
                            title = self.get_first_header(t)
                            t = re.sub(r'\s*\n*\s*<h\d>[^<]+</h\d>\s*\n*', r'', t, 1, flags=re.IGNORECASE | re.MULTILINE) # removes the header
                        if os.path.isfile(question_file):
                            question = read_file(question_file)
                            alt_title = 'This page answers the question: <i>{0}</i>'.format(question)
                        t = self.fix_ta_links(t, path.split('/')[0])
                    elif resource == 'tw':
                        title = self.get_first_header(t)
                        t = re.sub(r'\s*\n*\s*<h\d>[^<]+</h\d>\s*\n*', r'', t, 1, flags=re.IGNORECASE | re.MULTILINE) # removes the header
                        if len(title) > 70:
                            alt_title = ','.join(title[:70].split(',')[:-1]) + ', ...'
                        t = re.sub(r'\n*\s*\(See [^\n]*\)\s*\n*', '\n\n', t, flags=re.IGNORECASE | re.MULTILINE) # removes the See also line
                        t = self.fix_tw_links(t, path.split('/')[1])
                    self.resource_data[rc] = {
                        'rc': rc,
                        'link': link,
                        'id': anchor_id,
                        'title': title,
                        'alt_title': alt_title,
                        'text': t,
                        'references': [source_rc]
                    }
                    self.get_resource_data_from_rc_links(t, rc)
                else:
                    if source_rc not in self.bad_links:
                        self.bad_links[source_rc] = {}
                    if rc not in self.bad_links[source_rc]:
                        self.bad_links[source_rc][rc] = None
            else:
                if source_rc not in self.resource_data[rc]['references']:
                    self.resource_data[rc]['references'].append(source_rc)
                if '*'+rc in self.bad_links:
                    if source_rc not in self.bad_links['*'+rc]:
                        self.bad_links['*'+rc].append(source_rc)

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

    @staticmethod
    def get_first_header(text):
        lines = text.split('\n')
        if len(lines):
            for line in lines:
                if re.match(r'<h1>', line):
                    return re.sub(r'<h1>(.*?)</h1>', r'\1', line)
            return lines[0]
        return "NO TITLE"

    def fix_tn_links(self, text, chapter):
        text = re.sub(r'<a href="\.\./\.\./([^"]+)">([^<]+)</a>', r'\2', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)/([^"]+?)(\.md)*"', r'href="#tn-{0}-\1-\2"'.format(self.book_id), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)(\.md)*"', r'href="#tn-{0}-\1"'.format(self.book_id), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\./([^"]+?)(\.md)*"', r'href="#tn-{0}-{1}-\1"'.format(self.book_id, self.pad(chapter)), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\n__.*\|.*', r'', text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_tw_links(self, text, group):
        text = re.sub(r'href="\.\./([^/)]+?)(\.md)*"', r'href="rc://*/tw/dict/bible/{0}/\1"'.format(group), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'hrefp="\.\./([^)]+?)(\.md)*"', r'href="rc://*/tw/dict/bible/\1"', text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_ta_links(self, text, manual):
        text = re.sub(r'href="\.\./([^/"]+)/01\.md"', r'href="rc://*/ta/man/{0}/\1"'.format(manual), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./\.\./([^/"]+)/([^/"]+)/01\.md"', r'href="rc://*/ta/man/\1/\2"', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="([^# :/"]+)"', r'href="rc://*/ta/man/{0}/\1"'.format(manual), text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def replace_rc_links(self, text):
        # Change rc://... rc links, 
        # 1st: [[rc://en/tw/help/bible/kt/word]] => <a href="#tw-kt-word">God's Word</a>
        # 2nd: rc://en/tw/help/bible/kt/word => #tw-kt-word (used in links that are already formed)
        for rc, info in self.resource_data.iteritems():
            parts = rc[5:].split('/')
            tail = '/'.join(parts[1:])

            pattern = r'\[\[rc://[^/]+/{0}\]\]'.format(re.escape(tail))
            replace = r'<a href="{0}">{1}</a>'.format(info['link'], info['title'])
            text = re.sub(pattern, replace, text, flags=re.IGNORECASE | re.MULTILINE)

            pattern = r'rc://[^/]+/{0}'.format(re.escape(tail))
            replace = info['link']
            text = re.sub(pattern, replace, text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove other scripture reference not in this tN
        text = re.sub(r'<a[^>]+rc://[^>]+>([^>]+)</a>', r'\1', text, flags=re.IGNORECASE | re.MULTILINE)

        return text

    def fix_links(self, text):
        # Change [[http.*]] to <a href="http\1">http\1</a>
        text = re.sub(r'\[\[http([^\]]+)\]\]', r'<a href="http\1">http\1</a>', text, flags=re.IGNORECASE)

        # convert URLs to links if not already
        text = re.sub(r'([^">])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])', r'\1<a href="\2">\2</a>', text, flags=re.IGNORECASE)

        # URLS wth just www at the start, no http
        text = re.sub(r'([^\/])(www\.[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])', r'\1<a href="http://\2">\2</a>', text, flags=re.IGNORECASE)

        # Removes leading 0s from verse references
        text = re.sub(r' 0*(\d+):0*(\d+)(-*)0*(\d*)', r' \1:\2\3\4', text, flags=re.IGNORECASE | re.MULTILINE)

        return text

    def get_chunk_html(self, usfm, resource, chapter, verse):
        # print("html: {0}-{3}-{1}-{2}".format(resource, chapter, verse, self.book_id))
        path = os.path.join(self.working_dir, 'usfm_chunks', 'usfm-{0}-{1}-{2}-{3}-{4}'.
                                format(self.lang_code, resource, self.book_id, chapter, verse))
        filename_base = '{0}-{1}-{2}-{3}'.format(resource, self.book_id, chapter, verse)
        html_file = os.path.join(path, '{0}.html'.format(filename_base))
        usfm_file = os.path.join(path, '{0}.usfm'.format(filename_base))
        if not os.path.exists(path):
            os.makedirs(path)
        usfm = '''\id {0}
\ide UTF-8
\h {1}
\mt {1}

{2}'''.format(self.book_id.upper(), self.book_title, usfm)
        write_file(usfm_file, usfm)
        UsfmTransform.buildSingleHtml(path, path, filename_base)
        html = read_file(os.path.join(path, filename_base+'.html'))
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find('h1')
        if header:
            header.decompose()
        chapter = soup.find('h2')
        if chapter:
            chapter.decompose()
        html = ''.join(['%s' % x for x in soup.body.contents])
        write_file(html_file, html)
        return html

def main(ta_tag, tn_tag, tw_tag, ust_tag, ult_tag, ugnt_tag, lang_code, books, working_dir, output_dir):
    """
    :param ta_tag:
    :param tn_tag:
    :param tw_tag:
    :param ust_tag:
    :param ult_tag:
    :param ugnt_tag:
    :param lang_code:
    :param books:
    :param working_dir:
    :param output_dir:
    :return:
    """
    tn_converter = TnConverter(ta_tag, tn_tag, tw_tag, ust_tag, ult_tag, ugnt_tag, working_dir, output_dir, 
                                lang_code, books)
    tn_converter.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_code', default='en', required=False, help="Language Code")
    parser.add_argument('-b', '--book_id', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help="Working Directory")
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help="Output Directory")
    parser.add_argument('--ta-tag', dest='ta', default='v10', required=False, help="tA Tag")
    parser.add_argument('--tn-tag', dest='tn', default='v13', required=False, help="tN Tag")
    parser.add_argument('--tw-tag', dest='tw', default='v9', required=False, help="tW Tag")
    parser.add_argument('--ust-tag', dest='ust', default='master', required=False, help="UST Tag")
    parser.add_argument('--ult-tag', dest='ult', default='master', required=False, help="ULT Tag")
    parser.add_argument('--ugnt-tag', dest='ugnt', default='v0.4', required=False, help="UGNT Tag")

    args = parser.parse_args(sys.argv[1:])
    main(args.ta, args.tn, args.tw, args.ust, args.ult, args.ugnt, args.lang_code, args.books, args.working_dir, args.output_dir)
