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
from glob import glob
from ..catalog.v3.catalog import UWCatalog
from ..general_tools.bible_books import BOOK_NUMBERS
from ..general_tools.file_utils import write_file, read_file, unzip, load_yaml_object
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

        self.current_book = None
        self.project = None
        self.tn_text = ''
        self.tw_text = ''
        self.tq_text = ''
        self.ta_text = ''
        self.rc_links = {}
        self.bad_links = {}
    
    def run(self):
        # self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.current_book = p['identifier']
            self.tn_text = ''
            self.tw_text = ''
            self.tq_text = ''
            self.ta_text = ''
            self.rc_links = {}
            self.create_md_files()
#        self.pp.pprint(self.bad_links)

    def get_book_projects(self):
        projects = []
        if not self.manifest or 'projects' not in self.manifest or not self.manifest['projects']:
            return
        for p in self.manifest['projects']:
            if not self.books or p['identifier'] in self.books:
                projects.append(p)
        return projects

    @staticmethod
    def extract_files_from_url_url(resource):
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
        tn_url = self.extract_files_from_url_url(self.tn)
        self.extract_files_from_url(tn_url)
        tw_url = self.extract_files_from_url_url(self.tw)
        self.extract_files_from_url(tw_url)
        tq_url = self.extract_files_from_url_url(self.tq)
        self.extract_files_from_url(tq_url)
        ta_url = self.extract_files_from_url_url(self.ta)
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

    @staticmethod
    def increase_headers(text, increase_depth=1):
        return re.sub(r'^(#+) +(.+?) *#*$', r'\1{0} \2'.format('#'*increase_depth), text, flags=re.MULTILINE)

    def create_md_files(self):
        book_dir = os.path.join(self.tn_dir, self.current_book)

        if not os.path.isdir(book_dir):
            return

        title = self.project['title']
        book_name = title.replace(' translationNotes', '')
        tn_text = '<a id="tn-{0}"/>\n# {1}\n\n'.format(self.current_book, title)

        intro_file = os.path.join(book_dir, 'front', 'intro.md')
        book_has_intro = os.path.isfile(intro_file)
        if book_has_intro:
            text = read_file(intro_file)
            text = '<a id="tn-{0}-intro"/>\n{1}\n\n'.format(self.current_book, self.increase_headers(text))
            tn_text += text

        for chapter in sorted(os.listdir(book_dir)):
            chapter_dir = os.path.join(book_dir, chapter)
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                intro_file = os.path.join(chapter_dir, 'intro.md')
                chapter_has_intro = os.path.isfile(intro_file)
                if chapter_has_intro:
                    text = read_file(intro_file)
                    text = '<a id="tn-{0}-{1}-intro"/>\n{2}\n\n'.format(self.current_book, chapter,
                                                                          self.increase_headers(text))
                    self.get_rc_links(text)
                    tn_text += text
                chunk_files = sorted(glob(os.path.join(chapter_dir, '[0-9]*.md')))
                for idx, chunk_file in enumerate(chunk_files):
                    chunk = os.path.splitext(os.path.basename(chunk_file))[0]
                    if len(chunk_files) > idx + 1:
                        next_chunk = int(os.path.splitext(os.path.basename(chunk_files[idx + 1]))[0])
                    else:
                        next_chunk = 10000
                    text = self.increase_headers(read_file(chunk_file), 2)
                    text = text.replace('### translationWords', '## translationWords')
                    text = '<a id="tn-{0}-{1}-{2}"/>\n# {3} {4}:{5}-{6}\n\n[[UDB:{0}:{4}:{5}-{6}]]\n\n'\
                           '[[ULB:{0}:{4}:{5}-{6}]]\n\n## translationNotes\n\n{7}\n\n'. \
                        format(self.current_book, chapter, chunk, book_name, chapter.lstrip('0'), chunk.lstrip('0'),
                               next_chunk - 1, text)
                    self.get_rc_links(text)
                    tn_text += text

                    links = '## Links:\n\n'
                    if book_has_intro:
                        links += '* [Introduction to {0}](#tn-{1}-intro)\n'.format(book_name, self.current_book)
                    if chapter_has_intro:
                        links += '* [{0} {1} General Notes](#tn-{2}-{3}-intro)\n'. \
                            format(book_name, chapter.lstrip('0'), self.current_book, chapter)
                    links += '* [{0} {1} translationQuestions](#tq-{1}-{2})\n'. \
                        format(book_name, chapter.lstrip('0'), self.current_book, chapter)
                    tn_text += links + '\n\n'

        tq_text = '<a id="tq-{0}"/>\n# {1}\n\n'.format(self.current_book, 'translationQuestions')
        tq_book_dir = os.path.join(self.tq_dir, self.current_book)
        for chapter in sorted(os.listdir(tq_book_dir)):
            chapter_dir = os.path.join(tq_book_dir, chapter)
            if os.path.isdir(chapter_dir) and re.match(r'^\d+$', chapter):
                tq_text += '<a id="tq-{0}-{1}"/>\n## {2} {3}\n\n'.format(self.current_book, chapter, book_name,
                                                                           chapter.lstrip('0'))
                for chunk in sorted(os.listdir(chapter_dir)):
                    chunk_file = os.path.join(chapter_dir, chunk)
                    if os.path.isfile(chunk_file) and re.match(r'^\d+.md$', chunk):
                        chunk = os.path.splitext(chunk)[0]
                        text = read_file(chunk_file)
                        text = '{0}\n\n'.format(self.increase_headers(text, 2))
                        self.get_rc_links(text)
                        tq_text += text
        write_file(os.path.join(self.temp_dir, self.current_book + '.md'), tn_text+'\n\n'+tq_text)

    def get_rc_links(self, text):
        for rc in re.findall(r'rc://[A-Z0-9/_-]+', text, flags=re.IGNORECASE):
            parts = rc[5:].split('/')
            lang = parts[0]
            resource = parts[1]
            book = parts[3]
            path = '/'.join(parts[3:])
            if resource not in self.rc_links:
                self.rc_links[resource] = {}
            if path not in self.rc_links[resource]:
                link = None
                id = None
                title = None
                t = None
                if lang != self.lang_code or resource not in ['tw', 'tq', 'ta'] or \
                        (resource == 'tn' and self.current_book != book):
                    link = 'https://git.door43.org/Door43/{0}_{1}/src/master/{2}'.format(lang, resource, path)
                else:
                    id = '{0}-{1}'.format(resource, path.replace('/', '-'))
                    link = '#{0}'.format(id)
                    try:
                        file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                 '{0}.md'.format(path))
                        if not os.path.isfile(file_path):
                            file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                     '{0}/01.md'.format(path))
                        if not os.path.isfile(file_path):
                            if rc not in self.bad_links:
                                self.bad_links[rc] = []
                            self.bad_links[rc].append(text.split('\n', 1)[0])
                            if resource == 'tw':
                                if path.startswith('bible/other/'):
                                    path2 = re.sub(r'^bible/other/', r'bible/kt/', path)
                                else:
                                    path2 = re.sub(r'^bible/kt/', r'bible/other/', path)
                                file_path = os.path.join(self.temp_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                         '{0}.md'.format(path2))
                        if os.path.isfile(file_path):
                            t = read_file(file_path)
                            title = re.sub(r'^# (.*?) *#*$', r'\1', t.split('\n', 1)[0])
                    except:
                        pass
                self.rc_links[resource][path] = {
                    'rc': rc,
                    'link': link,
                    'id': id,
                    'title': title,
                    'text': t,
                }
                if text:
                    self.get_rc_links(text)

    def fix_links(self, content):
        # fix links to other sections within the same manual (only one ../ and a section name)
        # e.g. [Section 2](../section2/01.md) => [Section 2](#section2)
        content = re.sub(r'\]\(\.\./([^/\)]+)/01.md\)', r'](#\1)', content)
        # fix links to other manuals (two ../ and a manual name and a section name)
        # e.g. [how to translate](../../translate/accurate/01.md) => [how to translate](translate.html#accurate)
        for idx, project in enumerate(self.rc.projects):
            pattern = re.compile(r'\]\(\.\./\.\./{0}/([^/\)]+)/01.md\)'.format(project.identifier))
            replace = r']({0}-{1}.html#\1)'.format(str(idx+1).zfill(2), project.identifier)
            content = re.sub(pattern, replace, content)
        # fix links to other sections that just have the section name but no 01.md page (preserve http:// links)
        # e.g. See [Verbs](figs-verb) => See [Verbs](#figs-verb)
        content = re.sub(r'\]\(([^# :/\)]+)\)', r'](#\1)', content)
        # convert URLs to links if not already
        content = re.sub(r'([^"\(])((http|https|ftp)://[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](\2)', content, flags=re.IGNORECASE)
        # URLS wth just www at the start, no http
        content = re.sub(r'([^A-Z0-9"\(\/])(www\.[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](http://\2)', content, flags=re.IGNORECASE)
        return content


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
    # main(args.lang_code, args.books, args.outfile)
    main(args.lang_code, None, args.outfile)
