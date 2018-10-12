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
        self.pp = pprint.PrettyPrinter(indent=4)

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
        self.ugnt_dir = os.path.join(self.working_dir, 'UGNT'.format(lang_code))
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
        self.resource_data = {}
        self.tn_book_data = {}
        self.tw_words_data = {}
        self.bad_links = {}
        self.usfm_chunks = {}
        self.version = None
        self.contributors = ''
        self.publisher = None
        self.issued = None
        self.filename_base = None

    def run(self):
        self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        #############self.contributors = '; '.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book_id = p['identifier'].upper()
            self.book_title = p['title'].replace(' translationNotes', '')
            self.book_number = BOOK_NUMBERS[self.book_id.lower()]
            if int(self.book_number) != 57:
                continue
            self.populate_tn_book_data()
            self.populate_tw_words_data()

            self.populate_chapters_and_verses()
            self.populate_usfm_chunks()
            self.filename_base = '{0}_tn_{1}-{2}_v{3}'.format(self.lang_code, self.book_number.zfill(2), self.book_id, self.version)
            self.rc_references = {}
            self.logger.info('Creating tN for {0} ({1}-{2})...'.format(self.book_title, self.book_number, self.book_id))
            if not os.path.isfile(os.path.join(self.output_dir, '{0}.hhhhtml'.format(self.filename_base))):
                print("Processing HTML...")
                self.generate_html()
        if len(self.bad_links.keys()):
            _print("BAD LINKS:")
            for bad in sorted(self.bad_links.keys()):
                for ref in self.bad_links[bad]:
                    parts = ref[5:].split('/')
                    _print("Bad reference: `{0}` in {1}'s {2}".format(bad, parts[1], '/'.join(parts[3:])))

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

    def populate_usfm_chunks(self):
        book_chunks = {}
        for resource in ['ult', 'ust']:
            save_dir = os.path.join(self.working_dir, 'chunk_data', resource)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_file = os.path.join(save_dir, '{0}.json'.format(self.book_id.lower()))

            if os.path.isfile(save_file):
                book_chunks[resource] = load_json_object(save_file)
                continue
            
            book_chunks[resource] = {}

            bible_dir = getattr(self, '{0}_dir'.format(resource))
            usfm = read_file(os.path.join(bible_dir, '{0}-{1}.usfm'.format(BOOK_NUMBERS[self.book_id.lower()], self.book_id)), encoding='utf-8')

            usfm = usfm3_to_usfm2(usfm)

            usfm = re.sub(r'\n*\s*\\s5\s*\n*', r'\n', usfm, flags=re.MULTILINE | re.IGNORECASE)
            chapters_usfm = re.compile(r'\n*\s*\\c[\u00A0\s]+').split(usfm)
            book_chunks[resource]['header'] = chapters_usfm[0]
            for chapter_data in self.chapters_and_verses:
                chapter = str(chapter_data['chapter'])
                book_chunks[resource][chapter] = {}
                book_chunks[resource][chapter]['chunks'] = []
                chapter_usfm = r'\\c ' + chapters_usfm[int(chapter)].strip()
                verses_usfm = re.compile(r'\n*\s*\\v[\u00A0\s]+').split(chapter_usfm)
                for idx, first_verse in enumerate(chapter_data['first_verses']):
                    if len(chapter_data['first_verses']) > idx+1:
                        last_verse = chapter_data['first_verses'][idx+1] - 1
                    else:
                        last_verse = int(BOOK_CHAPTER_VERSES[self.book_id.lower()][chapter])
                    chunk_usfm = ''
                    for verse in range(first_verse, last_verse+1):
                        chunk_usfm += r'\v '+verses_usfm[verse]+'\n'
                    data = {
                        'usfm': chunk_usfm,
                        'first_verse': first_verse,
                        'last_verse': last_verse,
                    }
                    # print('chunk: {0}-{1}-{2}-{3}-{4}'.format(resource, self.book_id, chapter, first_verse, last_verse))
                    book_chunks[resource][chapter][str(first_verse)] = data
                    book_chunks[resource][chapter]['chunks'].append(data)
            write_file(save_file, book_chunks[resource])
        self.usfm_chunks = book_chunks

    def generate_html(self):
        tn_html = self.get_tn_html()
        ta_html = self.get_ta_html()
        tw_html = self.get_tw_html()
        html = '\n<br>\n'.join([tn_html, tw_html, ta_html])
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

        soup.head.append(soup.new_tag('link', href="style.css", rel="stylesheet"))
        soup.head.append(soup.new_tag('link', href="http://fonts.googleapis.com/css?family=Noto+Serif", rel="stylesheet", type="text/css"))

        html_file = os.path.join(self.output_dir, '{0}.html'.format(self.filename_base))
        write_file(html_file, unicode(soup))
        print('Wrote HTML to {0}'.format(html_file))

    def pad(self, num):
        if self.book_id == 'PSA':
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
    
    def populate_chapters_and_verses(self):
        versification_file = os.path.join(self.versification_dir, '{0}.json'.format(self.book_id.lower()))
        self.chapter_and_verses = {}
        if os.path.isfile(versification_file):
            self.chapters_and_verses = load_json_object(versification_file)

    def populate_tn_book_data(self):
        book_file = os.path.join(self.tn_dir, 'en_tn_{0}-{1}.tsv'.format(self.book_number, self.book_id))
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
                    data[field] = row[idx]
                chapter = data['Chapter']
                verse = data['Verse']
                if not chapter in book_data:
                    book_data[chapter] = {}
                if not verse in book_data[chapter]:
                    book_data[chapter][verse] = []
                book_data[chapter][verse].append(data)
        self.tn_book_data = book_data

    def get_tn_html(self):
        tn_html = ''
        if 'front' in self.tn_book_data and 'intro' in self.tn_book_data['front']:
            intro = markdown.markdown(self.tn_book_data['front']['intro'][0]['OccurrenceNote'].decode('utf8').replace('<br>', '\n'))
            title = self.get_first_header(intro)
            intro = self.fix_tn_links(intro, 'intro')
            intro = self.increase_headers(intro)
            intro = self.decrease_headers(intro, 4)  # bring headers of 3 or more down 1
            id = 'tn-{0}-front-intro'.format(self.book_id)
            intro = re.sub(r'<h(\d)>', r'<h\1 id="{0}">'.format(id), intro, 1, flags=re.IGNORECASE | re.MULTILINE)
            intro += '<br><br>\n\n'
            tn_html += '\n<br>\n'+intro
            # HANDLE RC LINKS AND BACK REFERENCE
            rc = 'rc://*/tn/help/{0}/front/intro'.format(self.book_id.lower())
            self.resource_data[rc] = {
                'rc': rc,
                'id': id,
                'link': '#'+id,
                'title': title
            }
            self.get_resource_data_from_rc_links(intro, rc)

        for chapter_verses in self.chapters_and_verses:
            chapter = str(chapter_verses['chapter'])
            if 'intro' in self.tn_book_data[chapter]:
                intro = markdown.markdown(self.tn_book_data[chapter]['intro'][0]['OccurrenceNote'].replace('<br>',"\n"))
                intro = re.sub(r'<h(\d)>([^>]+) 0+([1-9])', r'<h\1>\2 \3', intro, 1, flags=re.MULTILINE | re.IGNORECASE)
                title = self.get_first_header(intro)
                intro = self.fix_tn_links(intro, chapter)
                intro = self.increase_headers(intro)
                intro = self.decrease_headers(intro, 5, 2)  # bring headers of 5 or more down 2
                id = 'tn-{0}-{1}-intro'.format(self.book_id, self.pad(chapter))
                header_class = 'section-header' if len(tn_html) else ''
                intro = re.sub(r'<h(\d+)>', r'<h\1 id="{0}" class="{1}">'.format(id, header_class), intro, 1, flags=re.IGNORECASE | re.MULTILINE)
                intro += '<br><br>\n\n'
                tn_html += '\n<br>\n'+intro
                # HANDLE RC LINKS
                rc = 'rc://*/tn/help/{0}/{1}/intro'.format(self.book_id.lower(), self.pad(chapter))
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
                    last_verse = int(BOOK_CHAPTER_VERSES[self.book_id.lower()][chapter])
                if first_verse != last_verse:
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter, first_verse, last_verse)
                else:
                    title = '{0} {1}:{2}'.format(self.book_title, chapter, first_verse)
                anchors = ''
                for verse in range(first_verse, last_verse+1):
                    id = 'tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), self.pad(verse))
                    anchors += '<a id="{0}"></a>'.format(id)
                    rc = 'rc://*/tn/help/{0}/{1}/{2}'.format(self.book_id.lower(), self.pad(chapter), self.pad(verse))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': id,
                        'link': '#'+id,
                        'title': title
                    }
                header_class = 'section-header' if len(tn_html) else ''
                header = '\n<br>\n<h2 class="{0}">{1}{2}</h2>\n\n'.format(header_class, anchors, title)
                col1 += '<sup style="color:light-gray">ULT</sup>' + self.get_bible_html('ult', int(chapter), first_verse, last_verse)
                col1 += '\n<br><br>\n'
                col1 += '<sup style="color:light-gray">UST</sup>' + self.get_bible_html('ust', int(chapter), first_verse, last_verse)

                col2 = ''
                for verse in range(first_verse, last_verse+1):
                    if str(verse) in self.tn_book_data[chapter]:
                        for data in self.tn_book_data[chapter][str(verse)]:
                            title = data['GLQuote'].decode('utf8')
                            col2 += '<b>' + title + (' -' if not title.endswith(':') else '') + ' </b>'
                            col2 += markdown.markdown(data['OccurrenceNote'].decode('utf8').replace('<br>',"\n")).replace('<p>', '').replace('</p>', '')
                            col2 += '\n<br><br>\n'
                if col2 != '':
                    col2 = self.decrease_headers(col2, 5)  # bring headers of 5 or more #'s down 1
                    col2 = self.fix_tn_links(col2, chapter)
                    chunk_page = '{0}\n<table style="width:100%">\n<tr>\n<td style="vertical-align:top;width:35%;padding-right:5px">\n\n<p>{1}</p>\n</td>\n<td style="vertical-align:top">\n\n<p>{2}</p>\n</td>\n</tr>\n</table>\n'.format(header, col1, col2)
#                    chunk_page = '{0}\n<table style="width:100%;border:none"><tr><td style="width:50%">{1}</td><td>{2}</td></tr></table>'.format(header, col1, col2) # REMOVE
                    tn_html += chunk_page
                    self.get_resource_data_from_rc_links(chunk_page, rc)
        tn_html = '<h1 id="tn-{0}" class="section-header">translationNotes</h1>\n\n'.format(self.book_id) + tn_html
        return tn_html

    def populate_tw_words_data(self):
        groups = ['kt', 'names', 'other']
        grc_path = 'tools/tn/generate_tn_pdf/grc/translationHelps/translationWords/v0.4'
        if not os.path.isdir(grc_path):
            _print('{0} not found! Please make sure you ran `node getResources ./` in the generate_tn_pdf dir and that the version in the script is correct'.format(grc_path))
            exit(1)
        words = {}
        for group in groups:
            files_path = '{0}/{1}/groups/{2}/*.json'.format(grc_path, group, self.book_id.lower())
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

    def get_bible_html(self, resource, chapter, first_verse, last_verse):
        html = self.get_chunk_html(resource, chapter, first_verse)
        html = html.replace('\n', '').replace('<p>', '').replace('</p>', '').strip()
        html = re.sub(r'<span class="v-num"', '<br><span class="v-num"', html, flags=re.IGNORECASE | re.MULTILINE)
        if resource != 'ult':
            return html
        words = self.get_all_words_to_match(resource, chapter, first_verse, last_verse)
        verses = html.split('<sup>')
        for word in words:
            parts = word['text'].split(' ... ')
            highlights = {}
            idx = word['contextId']['reference']['verse']-first_verse+1
            for part in parts:
                highlights[part] = r'<a href="{0}">{1}</a>'.format(word['contextId']['rc'], part)
            regex = re.compile(r'(?<![></\\_-])\b(%s)\b(?![></\\_-])' % "|".join(highlights.keys()))
            verses[idx] = regex.sub(lambda m: highlights[m.group(0)], verses[idx])
        html = '<sup>'.join(verses)
        return html

    def get_all_words_to_match(self, resource, chapter, first_verse, last_verse):
        path = 'tools/tn/generate_tn_pdf/en/bibles/{0}/v1/{1}/{2}.json'.format(resource, self.book_id.lower(), chapter)
        words = []
        data = load_json_object(path)
        chapter = int(chapter)
        for verse in range(first_verse, last_verse + 1):
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
        _print('English not found!')
        print(contextId)

    def get_tw_html(self):
        tw_html = '<h1 id="tw-{0}" class="section-header">translationWords</h1>\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for idx, rc in enumerate(sorted_rcs):
            if '/tw/' not in rc:
                continue
            html = self.resource_data[rc]['text']
            html = self.increase_headers(html)
            header_class = 'section-header' if idx > 0 else ''
            html = re.sub(r'<h(\d)>(.*?)</h(\d)>', r'<h\1 id="{0}" class="{1}">\2</h\3>\n{2}'.format(self.resource_data[rc]['id'], header_class, self.get_reference_text(rc)), html, 1, flags=re.IGNORECASE | re.MULTILINE)
            html += '\n\n'
            tw_html += html
        return tw_html

    def get_ta_html(self):
        ta_html = '<h1 id="{0}-ta-{1}" class="section-header">translationAcademy</h1>\n\n'.format(self.lang_code, self.book_id)
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for idx, rc in enumerate(sorted_rcs):
            if '/ta/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                html = self.resource_data[rc]['text']
                html = self.increase_headers(html)
                header_class = 'section-header' if idx > 0 else ''
                html = re.sub(r'<h(\d)>(.*?)</h(\d)>', r'<h\1 id="{0}" class="{1}">\2</h\3>{2}\n'.format(self.resource_data[rc]['id'], header_class, self.get_reference_text(rc)), html, 1, flags=re.IGNORECASE | re.MULTILINE)
                html += "\n\n"
                ta_html += html
        return ta_html

    def get_reference_text(self, rc):
        uses = ''
        if len(self.rc_references[rc]):
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
                uses = '(<b>Go back to:</b> {0})\n<br><br>\n'.format('; '.join(references))
        return uses

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_\*-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            resource = parts[1]
            path = '/'.join(parts[3:])

            if resource not in ['ta', 'tw']:
                continue

            if rc not in self.rc_references:
                self.rc_references[rc] = []
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
                # if not os.path.isfile(file_path):
                #     if resource == 'tw':
                #         if path.startswith('bible/other/'):
                #             path2 = re.sub(r'^bible/other/', r'bible/kt/', path)
                #         else:
                #             path2 = re.sub(r'^bible/kt/', r'bible/other/', path)
                #         anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                #         link = '#{0}'.format(anchor_id)
                #         file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                #                                     '{0}.md'.format(path2))
                if os.path.isfile(file_path):
                    t = markdown.markdown(read_file(file_path))
                    if resource == 'ta':
                        title_file = os.path.join(os.path.dirname(file_path), 'title.md')
                        question_file = os.path.join(os.path.dirname(file_path), 'sub-title.md')
                        if os.path.isfile(title_file):
                            title = read_file(title_file)
                        else:
                            title = self.get_first_header(t)
                        if os.path.isfile(question_file):
                            question = read_file(question_file)
                            question = 'This page answers the question: <i>{0}</i>\n<br><br>\n'.format(question)
                        else:
                            question = ''
                        t = '<h1>{0}</h1>\n\n{1}{2}'.format(title, question, t)
                        t = self.fix_ta_links(t, path.split('/')[0])
                    elif resource == 'tw':
                        title = self.get_first_header(t)
                        t = re.sub(r'\n*\s*\(See [^\n]*\)\s*\n*', '\n\n', t, flags=re.IGNORECASE | re.MULTILINE) # removes the See also line
                        t = self.fix_tw_links(t, path.split('/')[1])
                else:
                    if rc not in self.bad_links:
                        self.bad_links[rc] = []
                    self.bad_links[rc].append(source_rc)
                self.resource_data[rc] = {
                    'rc': rc,
                    'link': link,
                    'id': anchor_id,
                    'title': title,
                    'text': t,
                }
                if t:
                    self.get_resource_data_from_rc_links(t, rc)

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
        text = re.sub(r'<a href="\.\./\.\./([^"]+)">([^<]+)</a>', r'\2'.format(self.lang_code), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)/([^"]+?)(\.md)*"', r'href="#{0}-tn-{1}-\1-\2"'.format(self.lang_code, self.book_id), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)(\.md)*"', r'href="#{0}-tn-{1}-\1"'.format(self.lang_code, self.book_id), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\./([^"]+?)(\.md)*"', r'href="#{0}-tn-{1}-{2}-\1"'.format(self.lang_code, self.book_id, self.pad(chapter)), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\n__.*\|.*', r'', text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_tw_links(self, text, dictionary):
        text = re.sub(r'\]\(\.\./([^/)]+?)(\.md)*\)', r'](rc://{0}/tw/dict/bible/{1}/\1)'.format(self.lang_code, dictionary), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\]\(\.\./([^)]+?)(\.md)*\)', r'](rc://{0}/tw/dict/bible/\1)'.format(self.lang_code), text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_ta_links(self, text, manual):
        text = re.sub(r'\]\(\.\./([^/)]+)/01\.md\)', r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\]\(\.\./\.\./([^/)]+)/([^/)]+)/01\.md\)', r'](rc://{0}/ta/man/\1/\2)'.format(self.lang_code), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\]\(([^# :/)]+)\)', r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual), text, flags=re.IGNORECASE | re.MULTILINE)
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

    def get_chunk_html(self, resource, chapter, verse):
        # print("html: {0}-{3}-{1}-{2}".format(resource, chapter, verse, self.book_id))
        path = os.path.join(self.working_dir, 'usfm_chunks', 'usfm-{0}-{1}-{2}-{3}-{4}'.
                                format(self.lang_code, resource, self.book_id, chapter, verse))
        filename_base = '{0}-{1}-{2}-{3}'.format(resource, self.book_id, chapter, verse)
        html_file = os.path.join(path, '{0}.html'.format(filename_base))
        usfm_file = os.path.join(path, '{0}.usfm'.format(filename_base))
        if os.path.isfile(html_file):
            return read_file(html_file)
        if not os.path.exists(path):
            os.makedirs(path)
        chunk = self.usfm_chunks[resource][str(chapter)][str(verse)]['usfm']
        usfm = self.usfm_chunks[resource]['header']
        if '\\c' not in chunk:
            usfm += '\n\n\\c {0}\n'.format(chapter)
        usfm += chunk
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
