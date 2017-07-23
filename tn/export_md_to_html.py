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
from glob import glob
from ..catalog.v3.catalog import UWCatalog
from ..bible.bible_classes import Bible
from .. general_tools.file_utils import write_file, read_file, unzip, load_yaml_object
from ..general_tools.url_utils import download_file


class TnConverter(object):

    def __init__(self, output_dir=None, lang_code='en', books=None):
        """
        :param string output_dir:
        """
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.books = books
        if not self.output_dir:
            self.output_dir = '.'
        catalog = UWCatalog()
        self.tn = catalog.get_resource(lang_code, 'tn')
        self.tw = catalog.get_resource(lang_code, 'tw')
        self.tq = catalog.get_resource(lang_code, 'tq')
        self.ta = catalog.get_resource(lang_code, 'ta')

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.pp = pprint.PrettyPrinter(indent=4)

        # self.temp_dir = tempfile.mkdtemp(prefix='tn-')
        self.temp_dir = '/home/rich/tn'

        self.logger.debug('TEMP DIR IS {0}'.format(self.temp_dir))
        self.tn_dir = os.path.join(self.temp_dir, '{0}_tn'.format(lang_code))
        self.tw_dir = os.path.join(self.temp_dir, '{0}_tw'.format(lang_code))
        self.tq_dir = os.path.join(self.temp_dir, '{0}_tq'.format(lang_code))
        self.ta_dir = os.path.join(self.temp_dir, '{0}_ta'.format(lang_code))

        self.manifest = None

        self.book = None
        self.book_title = None
        self.project = None
        self.tn_text = ''
        self.tw_text = ''
        self.tq_text = ''
        self.ta_text = ''
        self.resource_rcs = {}
        self.resource_data = {}
        self.bad_links = {}

        self.bible = Bible.get_versification('ufw')

    def run(self):
        # self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book = p['identifier']
            self.book_title = p['title'].replace(' translationNotes', '')
            self.tn_text = ''
            self.tw_text = ''
            self.tq_text = ''
            self.ta_text = ''
            self.resource_data = {}
            self.resource_rcs = {}

            self.logger.info('Creating tN for {0}...'.format(self.book))
            self.preprocess_markdown()
            self.convert_md2html()
        self.pp.pprint(self.bad_links)

    def get_book_projects(self):
        projects = []
        if not self.manifest or 'projects' not in self.manifest or not self.manifest['projects']:
            return
        for p in self.manifest['projects']:
            if not self.books or p['identifier'] in self.books:
                projects.append(p)
        return projects

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
        tn_url = self.get_resource_url(self.tn)
        self.extract_files_from_url(tn_url)
        tw_url = self.get_resource_url(self.tw)
        self.extract_files_from_url(tw_url)
        tq_url = self.get_resource_url(self.tq)
        self.extract_files_from_url(tq_url)
        ta_url = self.get_resource_url(self.ta)
        self.extract_files_from_url(ta_url)

    def extract_files_from_url(self, url):
        zip_file = os.path.join(self.temp_dir, url.rpartition(os.path.sep)[2])
        try:
            self.logger.debug('Downloading {0}...'.format(url))
            download_file(url, zip_file)
        finally:
            self.logger.debug('finished.')
        try:
            self.logger.debug('Unzipping {0}...'.format(zip_file))
            unzip(zip_file, self.temp_dir)
        finally:
            self.logger.debug('finished.')

    def preprocess_markdown(self):
        tn_md = self.get_tn_markdown()
        tq_md = self.get_tq_markdown()
        tw_md = self.get_tw_markdown()
        ta_md = self.get_ta_markdown()
        md = '\n\n'.join([tn_md, tq_md, tw_md, ta_md])
        md = self.replace_rc_links(md)
        md = self.fix_links(md)
        write_file(os.path.join(self.temp_dir, self.book + '.md'), md)

    def get_tn_markdown(self):
        book_dir = os.path.join(self.tn_dir, self.book)

        if not os.path.isdir(book_dir):
            return

        self.resource_rcs['tn'] = {}
        tn_md = '<a id="tn-{0}"/>\n# {1}\n\n'.format(self.book, self.project['title'])

        intro_file = os.path.join(book_dir, 'front', 'intro.md')
        book_has_intro = os.path.isfile(intro_file)
        if book_has_intro:
            md = read_file(intro_file)
            md = self.fix_tn_links(md)
            md = self.increase_headers(md)
            md = '<a id="tn-{0}-front-intro"/>\n{1}\n\n'.format(self.book, md)
            rc = 'rc://{0}/tn/help/{1}/front/intro'.format(self.lang_code, self.book)
            anchor_id = 'tn-{1}-front-intro'.format(self.lang_code, self.book)
            title = self.get_first_header(md)
            self.resource_data[rc] = {
                'rc': rc,
                'id': anchor_id,
                'link': '#{0}'.format(anchor_id),
                'title': title,
                'text': md
            }
            self.resource_rcs['tn'][rc] = {
                'title': title,
                'rc': rc
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
                    md = self.fix_tn_links(md)
                    md = self.increase_headers(md)
                    title = self.get_first_header(md)
                    md = '<a id="tn-{0}-{1}-intro"/>\n{2}\n\n'.format(self.book, chapter, md)
                    rc = 'rc://{0}/tn/help/{0}/intro'.format(self.book, chapter)
                    anchor_id = 'tn-{0}-{1}-intro'.format(self.book, chapter)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                        'text': md
                    }
                    self.resource_rcs['tn'] = {
                        'title': title,
                        'rc': rc
                    }
                    self.get_resource_data_from_rc_links(md, rc)
                    tn_md += md
                chunk_files = sorted(glob(os.path.join(chapter_dir, '[0-9]*.md')))
                for idx, chunk_file in enumerate(chunk_files):
                    chunk = os.path.splitext(os.path.basename(chunk_file))[0]
                    if len(chunk_files) > idx + 1:
                        end_verse = int(os.path.splitext(os.path.basename(chunk_files[idx + 1]))[0])-1
                    else:
                        end_verse = self.bible[self.book].get_chapter(int(chapter.lstrip('0'))).num_verses
                    if self.book == 'psa':
                        end = str(end_verse).zfill(3)
                    else:
                        end = str(end_verse).zfill(2)
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter.lstrip('0'), chunk.lstrip('0'), end_verse)
                    md = self.increase_headers(read_file(chunk_file), 3)
                    md = self.fix_tn_links(md)
                    md = '<a id="tn-{0}-{1}-{2}"/>\n## {3}\n\n[[udb://{0}/{4}/{5}/{6}]]\n\n'\
                        '[[ulb://{0}/{4}/{5}/{6}]]\n\n### translationNotes\n\n{7}\n\n'. \
                        format(self.book, chapter, chunk, title, chapter.lstrip('0'), chunk.lstrip('0'),
                               end, md)
                    rc = 'rc://{0}/tn/help/{0}/{1}/{2}'.format(self.book, chapter, chunk)
                    anchor_id = 'tn-{0}-{1}-{2}'.format(self.book, chapter, chunk)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': anchor_id,
                        'link': '#{0}'.format(anchor_id),
                        'title': title,
                        'text': md
                    }
                    self.resource_rcs['tn'][rc] = {
                        'title': title,
                        'rc': rc
                    }
                    self.get_resource_data_from_rc_links(md, rc)
                    tn_md += md

                    links = '### Links:\n\n'
                    if book_has_intro:
                        links += '* [Introduction to {0}](#tn-{1}-front-intro)\n'.format(self.book_title, self.book)
                    if chapter_has_intro:
                        links += '* [{0} {1} General Notes](#tn-{2}-{3}-intro)\n'. \
                            format(self.book_title, chapter.lstrip('0'), self.book, chapter)
                    links += '* [{0} {1} translationQuestions](#tq-{1}-{2})\n'. \
                        format(self.book_title, chapter.lstrip('0'), self.book, chapter)
                    tn_md += links + '\n\n'
        return tn_md
    
    def get_tq_markdown(self):
        tq_md = '<a id="tq-{0}"/>\n# translationQuestions\n\n'.format(self.book)
        tq_book_dir = os.path.join(self.tq_dir, self.book)
        self.resource_rcs['tq'] = {}
        for chapter in sorted(os.listdir(tq_book_dir)):
            chapter_dir = os.path.join(tq_book_dir, chapter)
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                tq_md += '<a id="tq-{0}-{1}"/>\n## {2} {3}\n\n'.format(self.book, chapter, self.book_title,
                                                                         chapter.lstrip('0'))
                for chunk in sorted(os.listdir(chapter_dir)):
                    chunk_file = os.path.join(chapter_dir, chunk)
                    if os.path.isfile(chunk_file) and re.match(r'^\d+.md$', chunk):
                        md = read_file(chunk_file)
                        md = '{0}\n\n'.format(self.increase_headers(md, 2))
                        title = 'Question {0} {1}:{2}'.format(self.book_title, chapter.lstrip('0'), chunk.lstrip('0'))
                        rc = 'rc://{0}/tq/help/{0}/{1}/{2}'.format(self.book, chapter, chunk)
                        anchor_id = 'tn-{0}-{1}-{2}'.format(self.book, chapter, chunk)
                        self.resource_data[rc] = {
                            'rc': rc,
                            'id': anchor_id,
                            'link': '#{0}'.format(anchor_id),
                            'title': title,
                            'text': md
                        }
                        self.resource_rcs['tq'][rc] = {
                            'title': title,
                            'rc': rc
                        }
                        self.get_resource_data_from_rc_links(md, rc)
                        tq_md += md
        return tq_md

    def get_tw_markdown(self):
        tw_md = '<a id="tw-{0}"/>\n# translationWords\n\n'.format(self.book)
        items = sorted(self.resource_rcs['tw'].values(), key=lambda k: k['title'])
        for item in items:
            item = self.resource_data[item['rc']]
            tw_md += '<a id="{0}"/>\n{1}\n\n'.format(item['id'], self.increase_headers(item['text']))
        return tw_md
    
    def get_ta_markdown(self):
        ta_md = '<a id="ta-{0}"/>\n# translationAcademy\n\n'.format(self.book)
        items = sorted(self.resource_rcs['ta'].values(), key=lambda k: k['title'])
        for item in items:
            item = self.resource_data[item['rc']]
            ta_md += '<a id="{0}"/>\n{1}\n\n'.format(item['id'], item['text'])
        return ta_md

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            lang = parts[0]
            resource = parts[1]
            book = parts[3]
            path = '/'.join(parts[3:])

            # remove these text changes next version!
            if 'humanqualities' in path:
                path = path.replace('humanqualities', 'hq')
            if 'metaphore' in path:
                path = path.replace('metaphore', 'metaphor')
            if 'kt/dead' in path:
                path = path.replace('kt/dead', 'other/death')
            # text changes end

            if rc not in self.resource_data:
                title = None
                t = None
                if lang != self.lang_code or resource not in ['tw', 'tq', 'ta'] or \
                        (resource == 'tn' and self.book != book):
                    continue
                else:
                    anchor_id = '{0}-{1}'.format(resource, path.replace('/', '-'))
                    link = '#{0}'.format(anchor_id)
                    try:
                        file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                 '{0}.md'.format(path))
                        if not os.path.isfile(file_path):
                            file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                     '{0}/01.md'.format(path))
                        if not os.path.isfile(file_path):
                            if resource == 'tw':
                                if path.startswith('bible/other/'):
                                    path2 = re.sub(r'^bible/other/', r'bible/kt/', path)
                                else:
                                    path2 = re.sub(r'^bible/kt/', r'bible/other/', path)
                                anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                                link = '#{0}'.format(anchor_id)
                                file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
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
                            else:
                                title = self.get_first_header(t)
                            if resource == 'tw':
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
                    'referenced_by': [source_rc]
                }
                if t:
                    self.get_resource_data_from_rc_links(t, rc)
            else:
                self.resource_data[rc]['referenced_by'].append(source_rc)
            if resource not in self.resource_rcs:
                self.resource_rcs[resource] = {}
            self.resource_rcs[resource][rc] = {
                'title': self.resource_data[rc]['title'],
                'rc': rc
            }

    @staticmethod
    def increase_headers(text, increase_depth=1):
        if text:
            text = re.sub(r'^(#+) +(.+?) *#*$', r'\1{0} \2'.format('#'*increase_depth), text, flags=re.MULTILINE)
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

    def fix_tn_links(self, text):
        if 'kt/dead' in text:
            # Fix bad link in tN
            text = text.replace('kt/dead', 'other/death')
        text = re.sub(r'\]\(\.\./\.\./([^)]+?)(.md)*\)', r'](rc://{0}/tn/help/\1)'.format(self.lang_code), text)
        text = re.sub(r'\]\(\.\./([^)]+?)(.md)*\)', r'](rc://{0}/tn/help/{0}/\1)'.format(self.lang_code,
                                                                                         self.book), text)
        return text

    def fix_tw_links(self, text, dictionary):
        text = re.sub(r'\]\(\.\./([^/)]+?)(.md)*\)', r'](rc://{0}/tw/dict/bible/{1}/\1)'.format(self.lang_code, dictionary), text)
        text = re.sub(r'\]\(\.\./([^)]+?)(.md)*\)', r'](rc://{0}/tw/dict/bible/\1)'.format(self.lang_code), text)
        return text

    def fix_ta_links(self, text, manual):
        if 'bita-humanqualities' in text:
            # Fix bad link in tA
            text = text.replace('bita-humanqualities', 'bita-hq')
        text = re.sub(r'\]\(\.\./([^/)]+)/01.md\)', r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual), text)
        text = re.sub(r'\]\(\.\./\.\./([^/)]+)/([^/)]+)/01.md\)', r'](rc://{0}/ta/man/\1/\2)'.format(self.lang_code), text)
        text = re.sub(r'\]\(([^# :/)]+)\)', r'](rc://{0}/ta/man/{1}/\1)'.format(self.lang_code, manual), text)
        return text

    def replace_rc_links(self, text):
        rep = {}
        rep2 = {}
        for rc in self.resource_data:
            info = self.resource_data[rc]
            rep['[[{0}]]'.format(rc)] = '[{0}]({1})'.format(info['title'], info['link'])
            rep2[rc] = info['link']

        rep = dict((re.escape(k), v) for k, v in rep.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)

        rep2 = dict((re.escape(k), v) for k, v in rep2.iteritems())
        pattern = re.compile("|".join(rep2.keys()))
        text = pattern.sub(lambda m: rep2[re.escape(m.group(0))], text)

        return text

    def fix_links(self, text):
        # Fix metaphor misspelling
        if 'etaphore' in text:
            text = text.replace('etaphore', 'etaphor')
        # convert RC links, e.g. rc://en/tn/help/1sa/16/02 => https://git.door43.org/Door43/en_tn/1sa/16/02.md
        text = re.sub(r'rc://([^/]+)/([^/]+)/([^/]+)/([^\s\p\)\]\n$]+)',
                         r'https://git.door43.org/Door43/\1_\2/src/master/\4.md', text, flags=re.IGNORECASE)
        # convert URLs to links if not already
        text = re.sub(r'([^"\(])((http|https|ftp)://[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](\2)', text, flags=re.IGNORECASE)
        # URLS wth just www at the start, no http
        text = re.sub(r'([^A-Z0-9"\(\/])(www\.[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](http://\2.md)', text, flags=re.IGNORECASE)
        return text

    def convert_md2html(self):
        html = markdown.markdown(read_file(os.path.join(self.temp_dir, self.book + '.md')))
        write_file(os.path.join(self.output_dir, self.book + '.html'), html)


def main(lang_code, books, outfile):
    tn_converter = TnConverter(outfile, lang_code, books)
    tn_converter.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_code', default='en', required=False, help="Language Code")
    parser.add_argument('-b', '--book', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-o', '--outfile', dest='outfile', default=False, required=False, help="Output file")
    args = parser.parse_args(sys.argv[1:])
    main(args.lang_code, args.books, args.outfile)
