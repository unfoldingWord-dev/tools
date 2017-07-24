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
This script exports tN into HTML format from the API.
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
from glob import glob
from bs4 import BeautifulSoup
from ..catalog.v3.catalog import UWCatalog
from usfm_tools.transform import UsfmTransform
from .. general_tools.file_utils import write_file, read_file, unzip, load_yaml_object
from ..general_tools.url_utils import download_file, get_url
from ..general_tools.bible_books import BOOK_NUMBERS


class TnConverter(object):

    def __init__(self, working_dir=None, output_dir=None, lang_code='en', books=None):
        """
        :param string output_dir:
        """
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.books = books

        self.catalog = UWCatalog()
        self.tn = self.catalog.get_resource(lang_code, 'tn')
        self.tw = self.catalog.get_resource(lang_code, 'tw')
        self.tq = self.catalog.get_resource(lang_code, 'tq')
        self.ta = self.catalog.get_resource(lang_code, 'ta')

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
        self.tq_dir = os.path.join(self.working_dir, '{0}_tq'.format(lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(lang_code))

        self.manifest = None

        self.book_id = None
        self.book_title = None
        self.book_number = None
        self.project = None
        self.tn_text = ''
        self.tw_text = ''
        self.tq_text = ''
        self.ta_text = ''
        self.resource_rcs = {}
        self.resource_data = {}
        self.bad_links = {}
        self.usfm_chunks = {}

    def run(self):
        self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book_id = p['identifier']
            self.book_title = p['title'].replace(' translationNotes', '')
            self.book_number = BOOK_NUMBERS[self.book_id]
            self.resource_rcs = {}
            self.logger.info('Creating tN for {0} ({1}-{2})...'.format(self.book_title, self.book_number,
                                                                       self.book_id.upper()))

            if not os.path.isfile(os.path.join(self.output_dir, '{0}-{1}.html'.format(self.book_number, self.book_id.upper()))):
                self.usfm_chunks = self.get_usfm_chunks()
                self.preprocess_markdown()
                self.convert_md2html()
            if not os.path.isfile(os.path.join(self.output_dir, '{0}-{1}.pdf'.format(self.book_number, self.book_id.upper()))):
                print("Generating PDF...")
                #self.convert_html2pdf()
        self.pp.pprint(self.bad_links)

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

    @staticmethod
    def get_resource_url(resource):
        formats = None
        if 'formats' in resource:
            formats = resource['formats']
        else:
            if 'projects' in resource:
                if 'formats' in resource['projects'][0]:
                    formats = resource['projects'][0]['formats']
        if formats:
            for f in formats:
                if f['url'].endswith('.zip'):
                    return f['url']

    def setup_resource_files(self):
        if not os.path.isdir(os.path.join(self.working_dir, 'en_tn')):
            tn_url = self.get_resource_url(self.tn)
            self.extract_files_from_url(tn_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_tw')):
            tw_url = self.get_resource_url(self.tw)
            self.extract_files_from_url(tw_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_tq')):
            tq_url = self.get_resource_url(self.tq)
            self.extract_files_from_url(tq_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_ta')):
            ta_url = self.get_resource_url(self.ta)
            self.extract_files_from_url(ta_url)

    def extract_files_from_url(self, url):
        zip_file = os.path.join(self.working_dir, url.rpartition(os.path.sep)[2])
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

    def get_usfm_chunks(self):
        book_chunks = {}
        for resource in ['udb', 'ulb']:
            book_chunks[resource] = {}
            url = self.catalog.get_format(self.lang_code, resource, self.book_id, 'text/usfm')['url']

            # Quick fix for ULB Numbers having many marking errors. REMOVE IN NEXT VERSION OF tN
            if resource == 'ulb' and self.book_id == 'num':
                url = 'https://git.door43.org/Door43/en_ulb/raw/master/04-NUM.usfm'
            # END QUICK FIX

            usfm = get_url(url)
            chunks = re.compile(r'\\s5\s*\n*').split(usfm)
            header = chunks[0]
            book_chunks[resource]['header'] = header
            for chunk in chunks[1:]:
                if not chunk.strip(): 
                    continue
                c_search = re.search(r'\\c[\u00A0\s](\d+)', chunk)
                if c_search:
                    chapter = int(c_search.group(1))
                verses = re.findall(r'\\v[\u00A0\s](\d+)', chunk)
                if not verses:
                    continue
                first_verse = int(verses[0])
                last_verse = int(verses[-1])
                if chapter not in book_chunks[resource]:
                    book_chunks[resource][chapter] = {'chunks': []}
                data = {
                    'usfm': chunk,
                    'first_verse': first_verse,
                    'last_verse': last_verse,
                }
                print('chunk: {0}-{4}-{1}-{2}-{3}'.format(resource, chapter, first_verse, last_verse, self.book_id))
                book_chunks[resource][chapter][first_verse] = data
                book_chunks[resource][chapter]['chunks'].append(data)
        return book_chunks

    def preprocess_markdown(self):
        tn_md = self.get_tn_markdown()
        tq_md = self.get_tq_markdown()
        tw_md = self.get_tw_markdown()
        ta_md = self.get_ta_markdown()
        md = '\n\n'.join([tn_md, tq_md, tw_md, ta_md])
        md = self.replace_rc_links(md)
        md = self.fix_links(md)
        write_file(os.path.join(self.working_dir, '{0}-{1}.md'.format(str(self.book_number).zfill(2),
                                                                   self.book_id.upper())), md)

    def get_tn_markdown(self):
        book_dir = os.path.join(self.tn_dir, self.book_id)

        if not os.path.isdir(book_dir):
            return

        tn_md = '<a id="tn-{0}"/>\n# {1}\n\n'.format(self.book_id, self.project['title'])

        intro_file = os.path.join(book_dir, 'front', 'intro.md')
        book_has_intro = os.path.isfile(intro_file)
        if book_has_intro:
            md = read_file(intro_file)
            md = self.fix_tn_links(md, 'intro')
            md = self.increase_headers(md)
            md = self.decrease_headers(md, 5)  # bring headers of 5 or more #'s down 1
            md = '<a id="tn-{0}-front-intro"/>\n{1}\n\n'.format(self.book_id, md)
            rc = 'rc://{0}/tn/help/{1}/front/intro'.format(self.lang_code, self.book_id)
            anchor_id = 'tn-{1}-front-intro'.format(self.lang_code, self.book_id)
            title = self.get_first_header(md)
            self.resource_data[rc] = {
                'rc': rc,
                'id': anchor_id,
                'link': '#{0}'.format(anchor_id),
                'title': title,
            }
            self.get_resource_data_from_rc_links(md, rc)
            tn_md += md

        for chapter in sorted(os.listdir(book_dir)):
            chapter_dir = os.path.join(book_dir, chapter)
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                intro_file = os.path.join(chapter_dir, 'intro.md')
                chapter_has_intro = os.path.isfile(intro_file)
                if chapter_has_intro:
                    md = read_file(intro_file)
                    md = self.fix_tn_links(md, chapter)
                    md = self.increase_headers(md)
                    md = self.decrease_headers(md, 5, 2)  # bring headers of 5 or more #'s down 2
                    title = self.get_first_header(md)
                    md = '<a id="tn-{0}-{1}-intro"/>\n{2}\n\n'.format(self.book_id, chapter, md)
                    rc = 'rc://{0}/tn/help/{1}/{2}/intro'.format(self.lang_code, self.book_id, chapter)
                    anchor_id = 'tn-{0}-{1}-intro'.format(self.book_id, chapter)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                    }
                    self.get_resource_data_from_rc_links(md, rc)
                    tn_md += md
                chunk_files = sorted(glob(os.path.join(chapter_dir, '[0-9]*.md')))
                for idx, chunk_file in enumerate(chunk_files):
                    chunk = os.path.splitext(os.path.basename(chunk_file))[0]
                    if len(chunk_files) > idx + 1:
                        end_verse = int(os.path.splitext(os.path.basename(chunk_files[idx + 1]))[0])-1
                    else:
                        end_verse = self.usfm_chunks['udb'][int(chapter)]['chunks'][-1]['last_verse']
                    if self.book_id == 'psa':
                        end = str(end_verse).zfill(3)
                    else:
                        end = str(end_verse).zfill(2)
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, int(chapter), int(chunk), end_verse)
                    md = self.increase_headers(read_file(chunk_file), 3)
                    md = self.decrease_headers(md, 5)  # bring headers of 5 or more #'s down 1
                    md = self.fix_tn_links(md, chapter)
                    md = md.replace('#### translationWords', '### trnaslationWords')
                    md = '<a id="tn-{0}-{1}-{2}"/>\n## {3}\n\n[[udb://{0}/{4}/{5}/{6}]]\n\n'\
                        '[[ulb://{0}/{4}/{5}/{6}]]\n\n### translationNotes\n\n{7}\n\n'. \
                        format(self.book_id, chapter, chunk, title, int(chapter), int(chunk),
                               end, md)
                    rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, chapter, chunk)
                    anchor_id = 'tn-{0}-{1}-{2}'.format(self.book_id, chapter, chunk)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                    }
                    self.get_resource_data_from_rc_links(md, rc)
                    tn_md += md

                    links = '### Links:\n\n'
                    if book_has_intro:
                        links += '* [Introduction to {0}](#tn-{1}-front-intro)\n'.format(self.book_title, self.book_id)
                    if chapter_has_intro:
                        links += '* [{0} {1} General Notes](#tn-{2}-{3}-intro)\n'. \
                            format(self.book_title, int(chapter), self.book_id, chapter)
                    links += '* [{0} {1} translationQuestions](#tq-{2}-{3})\n'. \
                        format(self.book_title, int(chapter), self.book_id, chapter)
                    tn_md += links + '\n\n'
        return tn_md

    def get_tq_markdown(self):
        tq_md = '<a id="tq-{0}"/>\n# translationQuestions\n\n'.format(self.book_id)
        tq_book_dir = os.path.join(self.tq_dir, self.book_id)
        for chapter in sorted(os.listdir(tq_book_dir)):
            chapter_dir = os.path.join(tq_book_dir, chapter)
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                tq_md += '<a id="tq-{0}-{1}"/>\n## {2} {3}\n\n'.format(self.book_id, chapter, self.book_title,
                                                                       int(chapter))
                for chunk in sorted(os.listdir(chapter_dir)):
                    chunk_file = os.path.join(chapter_dir, chunk)
                    chunk = os.path.splitext(chunk)[0]
                    if os.path.isfile(chunk_file) and re.match(r'^\d+.md$', chunk):
                        md = read_file(chunk_file)
                        md = '{0}\n\n'.format(self.increase_headers(md, 2))
                        title = 'Question {0} {1}:{2}'.format(self.book_title, int(chapter), int(chunk))
                        rc = 'rc://{0}/tq/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, chapter, chunk)
                        anchor_id = 'tn-{0}-{1}-{2}'.format(self.book_id, chapter, chunk)
                        self.resource_data[rc] = {
                            'rc': rc,
                            'id': anchor_id,
                            'link': '#{0}'.format(anchor_id),
                            'title': title,
                        }
                        self.get_resource_data_from_rc_links(md, rc)
                        tq_md += md
        return tq_md

    def get_tw_markdown(self):
        tw_md = '<a id="tw-{0}"/>\n# translationWords\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.resource_rcs['tw'], key=lambda k: self.resource_data[k]['title'])
        for rc in sorted_rcs:
            data = self.resource_data[rc]
            tw_md += '<a id="{0}"/>\n{1}\n\n'.format(data['id'], self.increase_headers(data['text']))
        return tw_md

    def get_ta_markdown(self):
        ta_md = '<a id="ta-{0}"/>\n# translationAcademy\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.resource_rcs['ta'], key=lambda k: self.resource_data[k]['title'])
        for rc in sorted_rcs:
            data = self.resource_data[rc]
            text = self.increase_headers(data['text'])
            ta_md += '<a id="{0}"/>\n{1}\n\n'.format(data['id'], text)
        return ta_md

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            lang = parts[0]
            resource = parts[1]
            book = parts[3]
            path = '/'.join(parts[3:])

            if resource not in ['ta', 'tw']:
                continue

            # REMOVE THESE FIXES IN NEXT VERSION OF tN!
            if 'humanqualities' in path:
                path = path.replace('humanqualities', 'hq')
            if 'metaphore' in path:
                path = path.replace('metaphore', 'metaphor')
            if 'kt/dead' in path:
                path = path.replace('kt/dead', 'other/death')
            # TEXT FIXES END

            if resource not in self.resource_rcs:
                self.resource_rcs[resource] = []
            if rc not in self.resource_rcs[resource]:
                self.resource_rcs[resource].append(rc)

            if rc not in self.resource_data:
                title = None
                t = None
                anchor_id = '{0}-{1}'.format(resource, path.replace('/', '-'))
                link = '#{0}'.format(anchor_id)
                try:
                    file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                             '{0}.md'.format(path))
                    if not os.path.isfile(file_path):
                        file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                 '{0}/01.md'.format(path))
                    if not os.path.isfile(file_path):
                        if resource == 'tw':
                            if path.startswith('bible/other/'):
                                path2 = re.sub(r'^bible/other/', r'bible/kt/', path)
                            else:
                                path2 = re.sub(r'^bible/kt/', r'bible/other/', path)
                            anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                            link = '#{0}'.format(anchor_id)
                            file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                     '{0}.md'.format(path2))
                    if os.path.isfile(file_path):
                        t = read_file(file_path)
                        if resource == 'ta':
                            title_file = os.path.join(os.path.dirname(file_path), 'title.md')
                            question_file = os.path.join(os.path.dirname(file_path), 'subtitle.md')
                            if os.path.isfile(title_file):
                                title = read_file(title_file)
                            else:
                                title = self.get_first_header(t)
                            if os.path.isfile(question_file):
                                question = read_file(os.path.join(os.path.dirname(file_path), 'subtitle.md'))
                                question = 'This page answers the question: *{0}*\n\n'.format(question)
                            else:
                                question = ''
                            t = '# {0}\n\n{1}{2}'.format(title, question, t)
                            t = self.fix_ta_links(t, path.split('/')[0])
                        elif resource == 'tw':
                            title = self.get_first_header(t)
                            t = self.fix_tw_links(t, path.split('/')[1])
                    else:
                        if rc not in self.bad_links:
                            self.bad_links[rc] = []
                        self.bad_links[rc].append(source_rc)
                except:
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
            text = re.sub(r'^(#+) +(.+?) *#*$', r'\1{0} \2'.format('#'*increase_depth), text, flags=re.MULTILINE)
        return text

    @staticmethod
    def decrease_headers(text, minimum_header=1, decrease=1):
        if text:
            text = re.sub(r'^({0}#*){1} +(.+?) *#*$'.format('#'*(minimum_header-decrease), '#'*decrease),
                          r'\1 \2', text, flags=re.MULTILINE)
        return text

    @staticmethod
    def get_first_header(text):
        lines = text.split('\n')
        if len(lines):
            for line in lines:
                if re.match(r'^ *#+ ', line):
                    return re.sub(r'^ *#+ (.*?) *#*$', r'\1', line)
            return lines[0]
        return "NO TITLE"

    def fix_tn_links(self, text, chapter):
        rep = {}
        rep['kt/dead'] = 'other/death' # Fix bad link in tN, REMOVE NEXT VERSION!!!
        rep[r'\]\(\.\./\.\./([^)]+?)(\.md)*\)'] = r'](rc://{0}/tn/help/\1)'.format(self.lang_code)
        rep[r'\]\(\.\./([^)]+?)(\.md)*\)'] = r'](rc://{0}/tn/help/{1}/\1)'.format(self.lang_code, self.book_id)
        rep[r'\]\(\./([^)]+?)(\.md)*\)'] = r'](rc://{0}/tn/help/{1}/{2}/\1)'.format(self.lang_code, self.book_id, chapter)
        rep[r'\n__.*\|.*'] = r''
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_tw_links(self, text, dictionary):
        rep = {}
        rep[r'\]\(\.\./([^/)]+?)(\.md)*\)'] = r'](rc://{0}/tw/dict/bible/{1}/\1)'.format(self.lang_code, dictionary)
        rep[r'\]\(\.\./([^)]+?)(\.md)*\)'] = r'](rc://{0}/tw/dict/bible/\1)'.format(self.lang_code)
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def fix_ta_links(self, text, manual):
        rep = {}
        rep['bita-humanqualities'] = 'bita-hq' # Fix bad link in tA, REMOVE NEXT VERSION!!
        rep[r'\]\(\.\./([^/)]+)/01\.md\)'] = r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual)
        rep[r'\]\(\.\./\.\./([^/)]+)/([^/)]+)/01\.md\)'] = r'](rc://{0}/ta/man/\1/\2)'.format(self.lang_code)
        rep[r'\]\(([^# :/)]+)\)'] = r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual)
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def replace_rc_links(self, text):
        # Change [[rc://...]] rc links, e.g. [[rc://en/tw/help/bible/kt/word]] => [God's Word](#tw-kt-word)
        rep = dict((re.escape('[[{0}]]'.format(rc)), '[{0}]({1})'.format(info['title'], info['link']))
                   for rc, info in self.resource_data.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

        # Change ].(rc://...) rc links, e.g. [Click here](rc://en/tw/help/bible/kt/word) => [Click here](#tw-kt-word)
        rep = dict((re.escape(']({0})'.format(rc)), ']({0})'.format(info['link']))
                   for rc, info in self.resource_data.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

        # Change rc://... rc links, e.g. rc://en/tw/help/bible/kt/word => [God's](#tw-kt-word)
        rep = dict((re.escape(rc), '[{0}]({1})'.format(info['title'], info['link']))
                   for rc, info in self.resource_data.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

        return text

    def fix_links(self, text):
        rep = {}
        # Fix metaphor misspelling, REMOVE NEXT VERSION!!
        rep['etaphore'] = 'etaphor'
        # convert RC links, e.g. rc://en/tn/help/1sa/16/02 => https://git.door43.org/Door43/en_tn/1sa/16/02.md
        rep[r'rc://([^/]+)/([^/]+)/([^/]+)/([^\s\)\]\n$]+)'] = r'https://git.door43.org/Door43/\1_\2/src/master/\4.md'
        # convert URLs to links if not already
        rep[r'([^"\(])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])'] = r'\1[\2](\2)'
        # URLS wth just www at the start, no http
        rep[r'([^A-Za-z0-9"\(\/])(www\.[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])'] = r'\1[\2](http://\2.md)'
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def convert_md2html(self):
        html = markdown.markdown(read_file(os.path.join(self.working_dir, '{0}-{1}.md'.format(
            str(self.book_number).zfill(2), self.book_id.upper()))))
        html = self.replace_bible_links(html)
        write_file(os.path.join(self.output_dir, '{0}-{1}.html'.format(str(self.book_number).zfill(2),
                                                                       self.book_id.upper())), html)

    def replace_bible_links(self, text):
        bible_links = re.findall(r'(?:udb|ulb)://{0}/[A-Z0-9/]+'.format(self.book_id), text,
                                 flags=re.IGNORECASE | re.MULTILINE)
        bible_links = list(set(bible_links))
        rep = {}
        for link in sorted(bible_links):
            parts = link.split('/')
            resource = parts[0][0:3]
            chapter = int(parts[3])
            chunk = int(parts[4])
            rep[link] = '<div>{0}</div>'.format(self.get_chunk_html(resource, chapter, chunk))
        rep = dict((re.escape('[[{0}]]'.format(link)), html) for link, html in rep.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        return text

    def get_chunk_html(self, resource, chapter, verse):
        path = tempfile.mkdtemp(dir=self.working_dir, prefix='usfm-{0}-{1}-{2}-{3}-{4}_'.
                                format(self.lang_code, resource, self.book_id, chapter, verse))
        filename_base = '{0}-{1}-{2}-{3}'.format(resource, self.book_id, chapter, verse)
        usfm = self.usfm_chunks[resource]['header']
        usfm += '\n\n'
        print("html: {0}-{3}-{1}-{2}".format(resource,chapter,verse,self.book_id))
        usfm += self.usfm_chunks[resource][chapter][verse]['usfm']
        write_file(os.path.join(path, filename_base+'.usfm'), usfm)
        UsfmTransform.buildSingleHtml(path, path, filename_base)
        html = read_file(os.path.join(path, filename_base+'.html'))
        shutil.rmtree(path, ignore_errors=True)
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find('h1')
        if header:
            header.name = 'h3'
            header.string = '{0}:'.format(resource.upper())
        chapter = soup.find('h2')
        if chapter:
            chapter.decompose()
        html = ''.join(['%s' % x for x in soup.body.contents])
        return html

    def convert_html2pdf(self):
        subprocess.check_call(['pwd', 'ls'])
        command = '/usr/local/bin/pandoc --latex-engine="xelatex" --template="tools/tn/tex/template.tex" -V logo="{5}icon-tn.png" --toc --toc-depth=2 -V documentclass="scrartcl" -V classoption="oneside" -V geometry="hmargin=2cm" -V geometry="vmargin=3cm" -V title="translationWords" -V subtitle="{2}" -V date="{3}" -V version="{4}" -V mainfont="Noto Serif" -V sansfont="Noto Sans" -o "{5}{0}-{1}.pdf" "{5}{0}-{1}.html"'.format(BOOK_NUMBERS[self.book_id], self.book_id.upper(), self.book_title, '2017-07-24', '2', self.output_dir)
        print(command)
        subprocess.check_call([command])



def main(lang_code, books, working_dir, output_dir):
    tn_converter = TnConverter(working_dir, output_dir, lang_code, books)
    tn_converter.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_code', default='en', required=False, help="Language Code")
    parser.add_argument('-b', '--book_id', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help="Working Directory")
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help="Output Directory")
    args = parser.parse_args(sys.argv[1:])
    main(args.lang_code, args.books, args.working_dir, args.output_dir)
