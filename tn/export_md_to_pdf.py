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
This script exports tN into HTML format from the API and generates a PDF from the HTML
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
        self.my_rcs = []
        self.rc_references = {}
        self.resource_data = {}
        self.bad_links = {}
        self.usfm_chunks = {}
        self.version = self.tn['version']
        self.issued = self.tn['issued']
        self.filename_base = None

    def run(self):
        self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book_id = p['identifier']
            self.book_title = p['title'].replace(' translationNotes', '')
            self.book_number = BOOK_NUMBERS[self.book_id]
            self.filename_base = '{0}_tn_{1}-{2}_v{3}'.format(self.lang_code, self.book_number.zfill(2),
                                                              self.book_id.upper(), self.version)
            self.rc_references = {}
            self.my_rcs = []
            self.logger.info('Creating tN for {0} ({1}-{2})...'.format(self.book_title, self.book_number,
                                                                       self.book_id.upper()))

            if not os.path.isfile(os.path.join(self.output_dir, '{0}.html'.format(self.filename_base))):
                print("Getting USFM chunks...")
                self.usfm_chunks = self.get_usfm_chunks()
                if not os.path.isfile(os.path.join(self.output_dir, '{0}.md'.format(self.filename_base))):
                    print("Processing Markdown...")
                    self.preprocess_markdown()
                print("Converting MD to HTML...")
                self.convert_md2html()
            if not os.path.isfile(os.path.join(self.output_dir, '{0}.pdf'.format(self.filename_base))):
                print("Generating PDF...")
                self.convert_html2pdf()
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
        if not os.path.isfile(os.path.join(self.working_dir, 'icon-tn.png')):
            command = 'curl -o {0}/icon-tn.png https://unfoldingword.org/assets/img/icon-tn.png'.format(self.working_dir)
            subprocess.call(command, shell=True)

        # QUICK FIX TO USE CHANGES TO V10 OF UDB AND ULB...REMOVE OR UPDATE NEXT tN VERSION
        if not os.path.isdir(os.path.join(self.working_dir, 'en_udb')):
            udb_url = 'https://git.door43.org/richmahn/en_udb/archive/changes-to-v10.zip'
            self.extract_files_from_url(udb_url)
        if not os.path.isdir(os.path.join(self.working_dir, 'en_ulb')):
            ulb_url = 'https://git.door43.org/richmahn/en_ulb/archive/changes-to-v10.zip'
            self.extract_files_from_url(ulb_url)
        # END QUICK FIX

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

            # url = self.catalog.get_format(self.lang_code, resource, self.book_id, 'text/usfm')['url']
            # usfm = get_url(url)

            # Quick fix for ULB Numbers having many marking errors. REMOVE IN NEXT VERSION OF tN and uncomment above
            usfm = read_file(os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource), '{0}-{1}.usfm'.format(self.book_number, self.book_id.upper())))
            # END QUICK FIX

            chunks = re.compile(r'\\s5\s*\n*').split(usfm)
            header = chunks[0]
            book_chunks[resource]['header'] = header
            for chunk in chunks[1:]:
                if not chunk.strip(): 
                    continue
                c_search = re.search(r'\\c[\u00A0\s](\d+)', chunk)
                if c_search:
                    chapter = c_search.group(1)
                verses = re.findall(r'\\v[\u00A0\s](\d+)', chunk)
                if not verses:
                    continue
                first_verse = verses[0]
                last_verse = verses[-1]
                if chapter not in book_chunks[resource]:
                    book_chunks[resource][chapter] = {'chunks': []}
                data = {
                    'usfm': chunk,
                    'first_verse': first_verse,
                    'last_verse': last_verse,
                    'verses': verses
                }
                # print('chunk: {0}-{1}-{2}-{3}-{4}'.format(resource, self.book_id, chapter, first_verse, last_verse))
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
        write_file(os.path.join(self.output_dir, '{0}.md'.format(self.filename_base)), md)

    def pad(self, num):
        if self.book_id == 'psa':
            return str(num).zfill(3)
        else:
            return str(num).zfill(2)

    def get_tn_markdown(self):
        book_dir = os.path.join(self.tn_dir, self.book_id)

        if not os.path.isdir(book_dir):
            return

        tn_md = '# translationNotes\n<a id="tn-{0}"/>\n\n'.format(self.book_id)

        intro_file = os.path.join(book_dir, 'front', 'intro.md')
        book_has_intro = os.path.isfile(intro_file)
        if book_has_intro:
            md = read_file(intro_file)
            title = self.get_first_header(md)
            md = self.fix_tn_links(md, 'intro')
            md = self.increase_headers(md)
            md = self.decrease_headers(md, 5)  # bring headers of 5 or more #'s down 1
            id_tag = '<a id="tn-{0}-front-intro"/>'.format(self.book_id)
            md = re.compile(r'# ([^\n]+)\n').sub(r'# \1\n{0}\n'.format(id_tag), md, 1)
            rc = 'rc://{0}/tn/help/{1}/front/intro'.format(self.lang_code, self.book_id)
            anchor_id = 'tn-{1}-front-intro'.format(self.lang_code, self.book_id)
            self.resource_data[rc] = {
                'rc': rc,
                'id': anchor_id,
                'link': '#{0}'.format(anchor_id),
                'title': title,
            }
            self.my_rcs.append(rc)
            self.get_resource_data_from_rc_links(md, rc)
            md += '\n\n'
            tn_md += md

        for chapter in sorted(os.listdir(book_dir)):
            chapter_dir = os.path.join(book_dir, chapter)
            chapter = chapter.lstrip('0')
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                intro_file = os.path.join(chapter_dir, 'intro.md')
                chapter_has_intro = os.path.isfile(intro_file)
                if chapter_has_intro:
                    md = read_file(intro_file)
                    title = self.get_first_header(md)
                    md = self.fix_tn_links(md, chapter)
                    md = self.increase_headers(md)
                    md = self.decrease_headers(md, 5, 2)  # bring headers of 5 or more #'s down 2
                    id_tag = '<a id="tn-{0}-{1}-intro"/>'.format(self.book_id, self.pad(chapter))
                    md = re.compile(r'# ([^\n]+)\n').sub(r'# \1\n{0}\n'.format(id_tag), md, 1)
                    rc = 'rc://{0}/tn/help/{1}/{2}/intro'.format(self.lang_code, self.book_id, self.pad(chapter))
                    anchor_id = 'tn-{0}-{1}-intro'.format(self.book_id, self.pad(chapter))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                    }
                    self.my_rcs.append(rc)
                    self.get_resource_data_from_rc_links(md, rc)
                    md += '\n\n'
                    tn_md += md
                chunk_files = sorted(glob(os.path.join(chapter_dir, '[0-9]*.md')))
                for idx, chunk_file in enumerate(chunk_files):
                    first_verse = os.path.splitext(os.path.basename(chunk_file))[0].lstrip('0')
                    last_verse = self.usfm_chunks['udb'][chapter][first_verse]['last_verse']
                    if first_verse != last_verse:
                        title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter, first_verse, last_verse)
                    else:
                        title = '{0} {1}:{2}'.format(self.book_title, chapter, first_verse)
                    md = self.increase_headers(read_file(chunk_file), 3)
                    md = self.decrease_headers(md, 5)  # bring headers of 5 or more #'s down 1
                    md = self.fix_tn_links(md, chapter)
                    md = md.replace('#### translationWords', '### translationWords')
                    anchors = ''
                    for verse in self.usfm_chunks['udb'][chapter][first_verse]['verses']:
                        anchors += '<a id="tn-{0}-{1}-{2}"/>'.format(self.book_id, self.pad(chapter), self.pad(verse))
                    pre_md = '\n## {0}\n{1}\n\n'.format(title, anchors)
                    pre_md += '### UDB:\n\n[[udb://{0}/{1}/{2}/{3}/{4}]]\n\n'\
                        .format(self.lang_code, self.book_id, self.pad(chapter), self.pad(first_verse),
                                self.pad(last_verse))
                    pre_md += '### ULB:\n\n[[ulb://{0}/{1}/{2}/{3}/{4}]]\n\n'\
                        .format(self.lang_code, self.book_id, self.pad(chapter), self.pad(first_verse),
                                self.pad(last_verse))
                    pre_md += '### translationNotes\n'
                    md = '{0}\n{1}'.format(pre_md, md)
                    rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                               self.pad(first_verse))
                    anchor_id = 'tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), self.pad(first_verse))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                    }
                    self.my_rcs.append(rc)
                    self.get_resource_data_from_rc_links(md, rc)
                    md += '\n\n'
                    tn_md += md

                    links = '### Links:\n\n'
                    if book_has_intro:
                        links += '* [[rc://{0}/tn/help/{1}/front/intro]]\n'.format(self.lang_code, self.book_id)
                    if chapter_has_intro:
                        links += '* [[rc://{0}/tn/help/{1}/{2}/intro]]\n'. \
                            format(self.lang_code, self.book_id, self.pad(chapter))
                    links += '* [[rc://{0}/tq/help/{1}/{2}]]\n'. \
                        format(self.lang_code, self.book_id, self.pad(chapter))
                    tn_md += links + '\n\n'
        return tn_md

    def get_tq_markdown(self):
        tq_md = '# translationQuestions\n<a id="tq-{0}"/>\n\n'.format(self.book_id)
        title = '{0} translationQuestions'.format(self.book_title)
        rc = 'rc://{0}/tq/help/{1}' \
            .format(self.lang_code, self.book_id)
        anchor_id = 'tq-{0}'.format(self.book_id)
        self.resource_data[rc] = {
            'rc': rc,
            'id': anchor_id,
            'link': '#{0}'.format(anchor_id),
            'title': title
        }
        self.my_rcs.append(rc)
        tq_book_dir = os.path.join(self.tq_dir, self.book_id)
        for chapter in sorted(os.listdir(tq_book_dir)):
            chapter_dir = os.path.join(tq_book_dir, chapter)
            chapter = chapter.lstrip('0')
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                id_tag = '<a id="tq-{0}-{1}"/>'.format(self.book_id, self.pad(chapter))
                tq_md += '## {0} {1}\n{2}\n\n'.format(self.book_title, chapter, id_tag)
                title = '{0} {1} translationQuestions'.format(self.book_title, chapter)
                rc = 'rc://{0}/tq/help/{1}/{2}' \
                    .format(self.lang_code, self.book_id, self.pad(chapter))
                anchor_id = 'tq-{0}-{1}'.format(self.book_id, self.pad(chapter))
                self.resource_data[rc] = {
                    'rc': rc,
                    'id': anchor_id,
                    'link': '#{0}'.format(anchor_id),
                    'title': title
                }
                self.my_rcs.append(rc)
                for chunk in sorted(os.listdir(chapter_dir)):
                    chunk_file = os.path.join(chapter_dir, chunk)
                    first_verse = os.path.splitext(chunk)[0].lstrip('0')
                    if os.path.isfile(chunk_file) and re.match(r'^\d+$', first_verse):
                        md = read_file(chunk_file)
                        md = self.increase_headers(md, 2)
                        md = re.compile('^([^#\n].+)$', flags=re.M).sub(r'\1 [<a href="#tn-{0}-{1}-{2}">{3}:{4}</a>]'.
                                                                        format(self.book_id, self.pad(chapter),
                                                                               self.pad(first_verse), chapter,
                                                                               first_verse),
                                                                        md)
                        title = '{0} {1}:{2} translationQuestions'.format(self.book_title, chapter, first_verse)
                        rc = 'rc://{0}/tq/help/{1}/{2}/{3}'\
                            .format(self.lang_code, self.book_id, self.pad(chapter), self.pad(first_verse))
                        anchor_id = 'tq-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), self.pad(first_verse))
                        self.resource_data[rc] = {
                            'rc': rc,
                            'id': anchor_id,
                            'link': '#{0}'.format(anchor_id),
                            'title': title
                        }
                        self.my_rcs.append(rc)
                        self.get_resource_data_from_rc_links(md, rc)
                        md += "\n\n"
                        tq_md += md
        return tq_md

    def get_tw_markdown(self):
        tw_md = '<a id="tw-{0}"/>\n# translationWords\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.my_rcs, key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/tw/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                md = self.resource_data[rc]['text']
            else:
                md = ''
            id_tag = '<a id="{0}"/>'.format(self.resource_data[rc]['id'])
            md = re.compile(r'# ([^\n]+)\n').sub(r'# \1\n{0}\n'.format(id_tag), md, 1)
            md = self.increase_headers(md)
            md += self.get_uses(rc)
            md += '\n\n'
            tw_md += md
        return tw_md

    def get_ta_markdown(self):
        ta_md = '<a id="ta-{0}"/>\n# translationAcademy\n\n'.format(self.book_id)
        sorted_rcs = sorted(self.my_rcs, key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/ta/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                md = self.resource_data[rc]['text']
            else:
                md = ''
            id_tag = '<a id="{0}"/>'.format(self.resource_data[rc]['id'])
            md = re.compile(r'# ([^\n]+)\n').sub(r'# \1\n{0}\n'.format(id_tag), md, 1)
            md = self.increase_headers(md)
            md += self.get_uses(rc)
            md += '\n\n'
            ta_md += md
        return ta_md

    def get_uses(self, rc):
        md = ''
        if len(self.rc_references[rc]):
            references = []
            for reference in self.rc_references[rc]:
                if '/tn/' in reference:
                    references.append('* [[{0}]]'.format(reference))
            if len(references):
                md += '### Uses:\n\n'
                md += '\n'.join(references)
                md += '\n'
        return md

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            resource = parts[1]
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

            if rc not in self.my_rcs:
                self.my_rcs.append(rc)
            if rc not in self.rc_references:
                self.rc_references[rc] = []
            self.rc_references[rc].append(source_rc)

            if rc not in self.resource_data:
                title = ''
                t = ''
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
                            question_file = os.path.join(os.path.dirname(file_path), 'sub-title.md')
                            if os.path.isfile(title_file):
                                title = read_file(title_file)
                            else:
                                title = self.get_first_header(t)
                            if os.path.isfile(question_file):
                                question = read_file(question_file)
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
        rep = {
            re.escape('**[2 Thessalonians intro](../front/intro.md)'): '**[2 Thessalonians intro](../front/intro.md)**',
            'kt/dead': 'other/death', # Fix bad link in tN, REMOVE NEXT VERSION!!!
            r'\]\(\.\./\.\./([^)]+?)(\.md)*\)': r'](rc://{0}/tn/help/\1)'.format(self.lang_code),
            r'\]\(\.\./([^)]+?)(\.md)*\)': r'](rc://{0}/tn/help/{1}/\1)'.format(self.lang_code, self.book_id),
            r'\]\(\./([^)]+?)(\.md)*\)': r'](rc://{0}/tn/help/{1}/{2}/\1)'.format(self.lang_code, self.book_id,
                                                                                  self.pad(chapter)),
            r'\n__.*\|.*': r''
        }
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_tw_links(self, text, dictionary):
        rep = {
            '../tax.md': '../other/tax.md',  # Fix for bad link in tW, REMOVE NEXT VERSION OF tN!
            r'\]\(\.\./([^/)]+?)(\.md)*\)': r'](rc://{0}/tw/dict/bible/{1}/\1)'.format(self.lang_code, dictionary),
            r'\]\(\.\./([^)]+?)(\.md)*\)': r'](rc://{0}/tw/dict/bible/\1)'.format(self.lang_code)
        }
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def fix_ta_links(self, text, manual):
        rep = {
            'bita-humanqualities': 'bita-hq', # Fix bad link in tA, REMOVE NEXT VERSION!!
            '<u>even when<u>': '<u>even when</u>',  # Fix bad underline in tA, REMOVE NEXT VERSION!
            r'\]\(\.\./([^/)]+)/01\.md\)': r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual),
            r'\]\(\.\./\.\./([^/)]+)/([^/)]+)/01\.md\)': r'](rc://{0}/ta/man/\1/\2)'.format(self.lang_code),
            r'\]\(([^# :/)]+)\)': r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual)
        }
        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def replace_rc_links(self, text):
        # Change [[rc://...]] rc links, e.g. [[rc://en/tw/help/bible/kt/word]] => [God's Word](#tw-kt-word)
        rep = dict((re.escape('[[{0}]]'.format(rc)), '[{0}]({1})'.
                    format(self.resource_data[rc]['title'], self.resource_data[rc]['link']))
                   for rc in self.my_rcs)
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

        def replace_with_door43_link(match):
            book = match.group(1)
            chapter = match.group(2)
            verse = match.group(3)
            book_num = BOOK_NUMBERS[book]
            if int(book_num) > 40:
                anchor_book_num = str(int(book_num) - 1)
            else:
                anchor_book_num = book_num
            url = 'https://live.door43.org/u/Door43/en_ulb/c0bd11bad0/{0}-{1}.html#{2}-ch-{3}-v-{4}'.format(
                book_num.zfill(2), book.upper(), anchor_book_num.zfill(3), chapter.zfill(3), verse.zfill(3))
            return url

        # convert tN links (NT books use USFM numbering in HTML file name, but standard book numbering in the anchor)
        # rc://en/tn/help/rev/15/07 => https://live.door43.org/u/Door43/en_ulb/c0bd11bad0/67-REV.html#066-ch-015-v-007
        rep[r'rc://en/tn/[^/]+/([^/]+)/([^/]+)/([^/]+)'] = replace_with_door43_link

        # convert RC links, e.g. rc://en/tn/help/1sa/16/02 => https://git.door43.org/Door43/en_tn/1sa/16/02.md
        rep[r'rc://([^/]+)/(?!tn)([^/]+)/([^/]+)/([^\s\)\]\n$]+)'] = r'https://git.door43.org/Door43/\1_\2/src/master/\4.md'

        # convert URLs to links if not already
        rep[r'([^"\(])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])'] = r'\1[\2](\2)'

        # URLS wth just www at the start, no http
        rep[r'([^A-Za-z0-9"\(\/])(www\.[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])'] = r'\1[\2](http://\2.md)'

        for pattern, repl in rep.iteritems():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text

    def convert_md2html(self):
        html = markdown.markdown(read_file(os.path.join(self.output_dir, '{0}.md'.format(self.filename_base))))
        html = self.replace_bible_links(html)
        write_file(os.path.join(self.output_dir, '{0}.html'.format(self.filename_base)), html)

    def replace_bible_links(self, text):
        bible_links = re.findall(r'(?:udb|ulb)://[A-Z0-9/]+', text,
                                 flags=re.IGNORECASE | re.MULTILINE)
        bible_links = list(set(bible_links))
        rep = {}
        for link in sorted(bible_links):
            parts = link.split('/')
            resource = parts[0][0:3]
            chapter = parts[4].lstrip('0')
            first_verse = parts[5].lstrip('0')
            rep[link] = '<div>{0}</div>'.format(self.get_chunk_html(resource, chapter, first_verse))
        rep = dict((re.escape('[[{0}]]'.format(link)), html) for link, html in rep.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        return text

    def get_chunk_html(self, resource, chapter, verse):
        # print("html: {0}-{3}-{1}-{2}".format(resource, chapter, verse, self.book_id))
        path = tempfile.mkdtemp(dir=self.working_dir, prefix='usfm-{0}-{1}-{2}-{3}-{4}_'.
                                format(self.lang_code, resource, self.book_id, chapter, verse))
        filename_base = '{0}-{1}-{2}-{3}'.format(resource, self.book_id, chapter, verse)
        chunk = self.usfm_chunks[resource][chapter][verse]['usfm']
        usfm = self.usfm_chunks[resource]['header']
        if '\\c' not in chunk:
            usfm += '\n\n\\c {0}\n'.format(chapter)
        usfm += chunk
        write_file(os.path.join(path, filename_base+'.usfm'), usfm)
        UsfmTransform.buildSingleHtml(path, path, filename_base)
        html = read_file(os.path.join(path, filename_base+'.html'))
        shutil.rmtree(path, ignore_errors=True)
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find('h1')
        if header:
            header.decompose()
        chapter = soup.find('h2')
        if chapter:
            chapter.decompose()
        html = ''.join(['%s' % x for x in soup.body.contents])
        return html

    def convert_html2pdf(self):
        command = """pandoc \
--latex-engine="xelatex" \
--template="tools/tn/tex/template.tex" \
--toc \
--toc-depth=2 \
-V documentclass="scrartcl" \
-V classoption="oneside" \
-V geometry='hmargin=2cm' \
-V geometry='vmargin=3cm' \
-V title="{2}" \
-V subtitle="translationNotes" \
-V logo="{6}/icon-tn.png" \
-V date="{3}" \
-V version="{4}" \
-V mainfont="Noto Serif" \
-V sansfont="Noto Sans" \
-V fontsize="13pt" \
-V urlcolor="Bittersweet" \
-V linkcolor="Bittersweet" \
-H "tools/tn/tex/format.tex" \
-o "{5}/{7}.pdf" \
"{5}/{7}.html"
""".format(BOOK_NUMBERS[self.book_id], self.book_id.upper(), self.book_title, self.issued, self.version, self.output_dir,
           self.working_dir, self.filename_base)
        print(command)
        subprocess.call(command, shell=True)


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
