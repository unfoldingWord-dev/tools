#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF tN documents for each book of the Bible
"""
from __future__ import unicode_literals, print_function
import os
import sys
import re
import logging
import argparse
import tempfile
import markdown2
import shutil
import subprocess
import csv
import json
import git
import requests
import string
import prettierfier
from glob import glob
from bs4 import BeautifulSoup
from weasyprint import HTML, LOGGER
from datetime import datetime
from ..usfm_tools.transform import UsfmTransform
from ..general_tools.file_utils import write_file, read_file, load_json_object, unzip, load_yaml_object
from ..general_tools.url_utils import download_file
from ..general_tools.bible_books import BOOK_NUMBERS, BOOK_CHAPTER_VERSES
from ..general_tools.usfm_utils import usfm3_to_usfm2


_print = print
DEFAULT_LANG = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
DEFAULT_UST_ID = 'ust'
DEFAULT_ULT_ID = 'ult'
DEFAULT_TN_ID = 'tn'
OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']


def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


def tryint(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    return [tryint(c) for c in re.split('([0-9]+)', s)]


def sort_alphanumeric(l):
    l.sort(key=alphanum_key)


def get_latest_version(path_to_versions):
    versions = [d for d in os.listdir(path_to_versions) if re.match(r'^v\d+', d) and
                os.path.isdir(os.path.join(path_to_versions, d))]
    if versions and len(versions):
        sort_alphanumeric(versions)
        return os.path.join(path_to_versions, versions[-1])
    else:
        return path_to_versions


class TnConverter(object):

    def __init__(self, ta_tag=None, tn_tag=None, tw_tag=None, ust_tag=None, ult_tag=None, ugnt_tag=None,
                 working_dir=None, output_dir=None, lang_code=DEFAULT_LANG, books=None, owner=DEFAULT_OWNER,
                 regenerate=False, logger=None, ust_id=DEFAULT_UST_ID, ult_id=DEFAULT_ULT_ID, tn_id=DEFAULT_TN_ID,
                 regenerate_all=False):
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
        self.hash = tn_tag
        self.owner = owner
        self.regenerate = regenerate_all or regenerate
        self.regenerate_all = regenerate_all
        self.logger = logger
        self.ust_id = ust_id
        self.ult_id = ult_id
        self.tn_id = tn_id

        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='tn-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.info('WORKING DIR IS {0}'.format(self.working_dir))

        self.tn_dir = os.path.join(self.working_dir, '{0}_{1}'.format(lang_code, tn_id))
        self.tw_dir = os.path.join(self.working_dir, '{0}_tw'.format(lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(lang_code))
        self.ust_dir = os.path.join(self.working_dir, '{0}_{1}'.format(lang_code, self.ust_id))
        self.ult_dir = os.path.join(self.working_dir, '{0}_{1}'.format(lang_code, self.ult_id))
        self.ugnt_dir = os.path.join(self.working_dir, 'el-x-koine_ugnt')
        self.versification_dir = os.path.join(self.working_dir, 'versification', 'bible', 'ufw', 'chunks')
        self.html_dir = os.path.join(self.output_dir, 'html')
        if not os.path.isdir(self.html_dir):
            os.makedirs(self.html_dir)

        self.title = 'unfoldingWord® Translation Notes'
        self.file_id = None
        self.book_file_id = None
        self.book_id = None
        self.tn_manifest = None
        self.tw_manifest = None
        self.ta_manifest = None
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
        self.resource_data = {}
        self.rc_lookup = {}
        self.tn_book_data = {}
        self.tw_words_data = {}
        self.bad_links = {}
        self.bad_notes = {}
        self.usfm_chunks = {}
        self.version = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.tn_resources_dir = '/tmp/tn_resources'

        self.lastEndedWithQuoteTag = False
        self.lastEndedWithParagraphTag = False
        self.openQuote = False
        self.nextFollowsQuote = False
        self.generation_info = {}
        self.soup = None
        self.date = datetime.now().strftime('%Y-%m-%d')

    def run(self):
        self.setup_resource_files()
        self.file_id = '{0}_{1}_tn_{2}_{3}'.format(self.date, self.lang_code, self.tn_tag,
                                                   self.generation_info[self.tn_id]['commit'])
        self.determine_if_regeneration_needed()
        self.tn_manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        self.tw_manifest = load_yaml_object(os.path.join(self.tw_dir, 'manifest.yaml'))
        self.ta_manifest = load_yaml_object(os.path.join(self.ta_dir, 'manifest.yaml'))
        self.version = self.tn_manifest['dublin_core']['version']
        self.title = self.tn_manifest['dublin_core']['title']
        projects = self.get_book_projects()
        for p in projects:
            self.project = p
            self.book_id = p['identifier'].lower()
            self.book_title = p['title']
            self.book_number = BOOK_NUMBERS[self.book_id]
            self.book_file_id = '{0}_{1}_tn_{2}_{3}_{4}-{5}'.format(self.date, self.lang_code, self.tn_tag,
                                                                self.generation_info[self.tn_id]['commit'],
                                                                self.book_number.zfill(2), self.book_id.upper())
            self.logger.info('Creating tN for {0}...'.format(self.book_file_id))
            self.load_resource_data()
            html_file = os.path.join(self.output_dir, '{0}.html'.format(self.book_file_id))
            pdf_file = os.path.join(self.output_dir, '{0}.pdf'.format(self.book_file_id))
            if self.regenerate or not os.path.exists(html_file):
                self.logger.info('Generating HTML file {0}...'.format(html_file))
                self.resource_data = {}
                self.rc_references = {}
                self.populate_tn_book_data()
                self.populate_tw_words_data()
                self.populate_chapters_and_verses()
                self.populate_verse_usfm()
                self.populate_chunks_text()
                with open(os.path.join(self.my_path, '..', 'common_files', 'template.html')) as template_file:
                    html_template = string.Template(template_file.read())
                html = html_template.safe_substitute(title='{0} - {1} - v{2}'.format(self.title, self.book_title,
                                                                                     self.version))
                self.soup = BeautifulSoup(html, 'html.parser')
                self.soup.html.head.title.string = self.title
                self.soup.html.head.append(
                    BeautifulSoup('<link href="html/tn_style.css" rel="stylesheet"/>', 'html.parser'))
                self.get_cover()
                self.get_license()
                self.get_body_html()
                self.download_all_images()

                write_file(os.path.join(self.output_dir, 'tn_not_prettified.html'), str(self.soup))
                write_file(os.path.join(self.output_dir, 'tn_soup_prettified.html'), self.soup.prettify())
                prettierfied_html = prettierfier.prettify_html(self.soup.prettify())
                write_file(os.path.join(self.output_dir, 'tn_prettierfier_prettified.html'), prettierfied_html)

                write_file(html_file, str(self.soup))

                self.logger.info("Copying style sheet files...")
                style_file = os.path.join(self.my_path, '..', 'common_files', 'style.css')
                shutil.copy2(style_file, self.html_dir)
                style_file = os.path.join(self.my_path, 'tn_style.css')
                shutil.copy2(style_file, self.html_dir)
                if not os.path.exists(os.path.join(self.html_dir, 'fonts')):
                    fonts_dir = os.path.join(self.my_path, '..', 'common_files', 'fonts')
                    shutil.copytree(fonts_dir, os.path.join(self.html_dir, 'fonts'))

                self.save_resource_data()
                self.save_bad_links()
                self.logger.info('Generated HTML file.')
            else:
                self.logger.info(
                    'HTML file {0} already there. Not generating. Use -r to force regeneration.'.format(html_file))

            if self.regenerate or not os.path.exists(pdf_file):
                self.logger.info('Generating PDF file {0}...'.format(pdf_file))
                LOGGER.setLevel('INFO')  # Set to 'INFO' for debugging
                LOGGER.addHandler(
                    logging.FileHandler(os.path.join(self.output_dir, '{0}_errors.log'.format(self.book_file_id))))
                weasy = HTML(filename=html_file, base_url='file://{0}/'.format(self.output_dir))
                weasy.write_pdf(pdf_file)
                self.logger.info('Generated PDF file.')
                link_file = os.path.join(self.output_dir, '{0}_tn_{1}_{2}-{3}.pdf'.
                                         format(self.lang_code, self.tn_tag, self.book_number.zfill(2),
                                                self.book_id.upper()))
                subprocess.call('ln -sf "{0}" "{1}"'.format(pdf_file, link_file), shell=True)
            else:
                self.logger.info(
                    'PDF file {0} already there. Not generating. Use -r to force regeneration.'.format(pdf_file))

    def get_cover(self):
        cover_html = '''
<article id="main-cover" class="cover">
    <img src="html/logo-utn-256.png" alt="UTN"/>
    <h1 id="cover-title">{0}</h1>
    <h2 id="cover-book-title">{1}</h2>
    <h3 id="cover-version">Version {2}</h3>
</article>
        '''.format(self.title, self.book_title, self.version)
        self.soup.body.append(BeautifulSoup(cover_html, 'html.parser'))

    def get_license(self):
        tn_license_file = os.path.join(self.tn_dir, 'LICENSE.md')
        tn_license = markdown2.markdown_path(tn_license_file)

        tn_title = self.tn_manifest['dublin_core']['title']
        tn_version = self.tn_manifest['dublin_core']['version']
        tn_publisher = self.tn_manifest['dublin_core']['publisher']
        tn_issued = self.tn_manifest['dublin_core']['issued']

        ta_title = self.ta_manifest['dublin_core']['title']
        ta_version = self.ta_manifest['dublin_core']['version']
        ta_publisher = self.ta_manifest['dublin_core']['publisher']
        ta_issued = self.ta_manifest['dublin_core']['issued']

        tw_title = self.tw_manifest['dublin_core']['title']
        tw_version = self.tw_manifest['dublin_core']['version']
        tw_publisher = self.tw_manifest['dublin_core']['publisher']
        tw_issued = self.tw_manifest['dublin_core']['issued']

        license_html = '''
<article id="license">
    <h1>Copyrights & Licensing</h1>
    <div class="resource-info">
      <div class="resource-title"><strong>{0}</strong></div>
      <div class="resource-date"><strong>Date:</strong> {1}</div>
      <div class="resource-version"><strong>Version:</strong> {2}</div>
      <div class="resource-publisher"><strong>Published by:</strong> {3}</div>
    </div>
    <div class="resource-info">
      <div class="resource-title"><strong>{4}</strong></div>
      <div class="resource-date"><strong>Date:</strong> {5}</div>
      <div class="resource-version"><strong>Version:</strong> {6}</div>
      <div class="resource-publisher"><strong>Published by:</strong> {7}</div>
    </div>
    <div class="resource-info">
      <div class="resource-title"><strong>{8}</strong></div>
      <div class="resource-date"><strong>Date:</strong> {9}</div>
      <div class="resource-version"><strong>Version:</strong> {10}</div>
      <div class="resource-publisher"><strong>Published by:</strong> {11}</div>
    </div>
    {12}
</article>
'''.format(tn_title, tn_issued, tn_version, tn_publisher,
           ta_title, ta_issued, ta_version, ta_publisher,
           tw_title, tw_issued, tw_version, tw_publisher,
           tn_license)
        self.soup.body.append(BeautifulSoup(license_html, 'html.parser'))

    def save_bad_links(self):
        bad_links = "BAD LINKS:\n"
        for source_rc in sorted(self.bad_links.keys()):
            for rc in sorted(self.bad_links[source_rc].keys()):
                source = source_rc[5:].split('/')
                parts = rc[5:].split('/')
                if source[1] == self.ult_id:
                    str = '  ULT {0} {1}:{2}: English ULT alignment not found for `{3}` (greek: `{4}`, occurrence: {5})'.format(source[3].upper(), source[4], source[5], self.bad_links[source_rc][rc], parts[3], parts[4])
                else:
                    if source[1] == 'tn':
                        if parts[1] == 'tw':
                            str = '  UGNT'
                        else:
                            str = '  tN'
                        str += ' {0} {1}:{2}'.format(source[3].upper(), source[4], source[5])
                    else:
                        str = '  {0} {1}'.format(source[1], '/'.join(source[3:]))
                    str += ': BAD RC - `{0}`'.format(rc)
                    if self.bad_links[source_rc][rc]:
                        str += ' - change to `{0}`'.format(self.bad_links[source_rc][rc])
                bad_links += "{0}\n".format(str)
        save_file = os.path.join(self.output_dir, '{0}_bad_links.txt'.format(self.book_file_id))
        write_file(save_file, bad_links)
        self.logger.info('BAD LINKS file can be found at {0}'.format(save_file))

    def get_book_projects(self):
        projects = []
        if not self.tn_manifest or 'projects' not in self.tn_manifest or not self.tn_manifest['projects']:
            return
        for p in self.tn_manifest['projects']:
            if not self.books or p['identifier'] in self.books:
                if not p['sort']:
                    p['sort'] = BOOK_NUMBERS[p['identifier']]
                projects.append(p)
        return sorted(projects, key=lambda k: k['sort'])

    @staticmethod
    def get_resource_git_url(resource, lang, owner):
        return 'https://git.door43.org/{0}/{1}_{2}.git'.format(owner, lang, resource)

    def clone_resource(self, resource, tag=DEFAULT_TAG, lang=None):
        if not lang:
            lang = self.lang_code
        url = self.get_resource_git_url(resource, lang, self.owner)
        repo_dir = os.path.join(self.working_dir, '{0}_{1}'.format(lang, resource))
        if not os.path.isdir(repo_dir):
            try:
                git.Repo.clone_from(url, repo_dir)
            except git.GitCommandError:
                owners = OWNERS
                owners.insert(0, self.owner)
                languages = [lang, self.lang_code, DEFAULT_LANG]
                if not os.path.isdir(repo_dir):
                    for lang in languages:
                        for owner in owners:
                            url = self.get_resource_git_url(resource, lang, owner)
                            try:
                                git.Repo.clone_from(url, repo_dir)
                            except git.GitCommandError:
                                continue
                            break
                        if os.path.isdir(repo_dir):
                            break
        g = git.Git(repo_dir)
        g.fetch()
        g.checkout(tag)
        if tag == DEFAULT_TAG:
            # self.logger.info("not pulling")
            g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource(self.tn_id, self.tn_tag)
        self.clone_resource('tw', self.tw_tag)
        self.clone_resource('ta', self.ta_tag)
        self.clone_resource(self.ult_id, self.ult_tag)
        self.clone_resource(self.ust_id, self.ust_tag)
        self.clone_resource('ugnt', self.ugnt_tag, 'el-x-koine')
        if not os.path.isdir(self.versification_dir):
            git.Repo.clone_from('https://git.door43.org/Door43-Catalog/versification.git',
                                os.path.join(self.working_dir, 'versification'))
        logos = ['utn', 'utw', 'uta']
        for logo in logos:
            logo_path = os.path.join(self.html_dir, 'logo-{0}-256.png'.format(logo))
            if not os.path.isfile(logo_path):
                command = 'curl -o "{0}" https://cdn.door43.org/assets/uw-icons/logo-{1}-256.png'.\
                    format(logo_path, logo)
                subprocess.call(command, shell=True)

    def extract_files_from_url(self, url):
        zip_file = os.path.join(self.working_dir, url.rpartition('/')[2])
        try:
            self.logger.info('Downloading {0}...'.format(url))
            download_file(url, zip_file)
        finally:
            self.logger.info('finished.')
        try:
            self.logger.info('Unzipping {0}...'.format(zip_file))
            unzip(zip_file, self.working_dir)
        finally:
            self.logger.info('finished.')

    def populate_chunks_text(self):
        save_dir = os.path.join(self.output_dir, 'chunks_text')
        save_file = os.path.join(save_dir, '{0}.json'.format(self.book_file_id))
        if not self.regenerate_all and os.path.isfile(save_file):
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
                for resource in [self.ult_id, self.ust_id]:
                    verses_in_chunk = []
                    for verse in range(first_verse, last_verse+1):
                        if resource not in self.verse_usfm:
                            self.logger.error('{0} not in verse_usfm!!!'.format(resource))
                            self.logger.error(self.verse_usfm)
                            exit(1)
                        if chapter not in self.verse_usfm[resource]:
                            self.logger.error('Chapter {0} not in {1}!!!'.format(chapter, resource))
                            exit(1)
                        if verse not in self.verse_usfm[resource][chapter]:
                            self.logger.error('{0}:{1} not in {2}!!!'.format(chapter, verse, resource))
                            if len(verses_in_chunk):
                                self.verse_usfm[resource][chapter][verse] = ''
                            else:
                                exit(1)
                        verses_in_chunk.append(self.verse_usfm[resource][chapter][verse])
                    chunk_usfm = '\n'.join(verses_in_chunk)
                    if resource not in chunks_text[str(chapter)][str(first_verse)]:
                        chunks_text[str(chapter)][str(first_verse)][resource] = {}
                    chunks_text[str(chapter)][str(first_verse)][resource] = {
                        'usfm': chunk_usfm,
                        'html': self.get_chunk_html(chunk_usfm, resource, chapter, first_verse)
                    }
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            write_file(save_file, chunks_text)
        self.chunks_text = chunks_text

    def determine_if_regeneration_needed(self):
        # check if any commit hashes have changed
        old_info = self.get_previous_generation_info()
        if not old_info:
            self.logger.info('Looks like this is a new commit of {0}. Generating PDF.'.format(self.book_file_id))
            self.regenerate = True
        else:
            for resource in self.generation_info:
                if resource in old_info and resource in self.generation_info \
                        and (old_info[resource]['tag'] != self.generation_info[resource]['tag']
                             or old_info[resource]['commit'] != self.generation_info[resource]['commit']):
                    self.logger.info('Resource {0} has changed: {1} => {2}, {3} => {4}. REGENERATING PDF.'.format(
                        resource, old_info[resource]['tag'], self.generation_info[resource]['tag'],
                        old_info[resource]['commit'], self.generation_info[resource]['commit']
                    ))
                    self.regenerate = True

    def get_contributors(self):
        tn_title = self.tn_manifest['dublin_core']['title']
        tw_title = self.tw_manifest['dublin_core']['title']
        ta_title = self.ta_manifest['dublin_core']['title']

        tn_contributors = '<div class="contributor">'+'</div><div class="contributor">'.join(self.tn_manifest['dublin_core']['contributor'])+'</div>'
        tw_contributors = '<div class="contributor">'+'</div><div class="contributor">'.join(self.tw_manifest['dublin_core']['contributor'])+'</div>'
        ta_contributors = '<div class="contributor">'+'</div><div class="contributor">'.join(self.ta_manifest['dublin_core']['contributor'])+'</div>'

        contributors_html = '''
<section id="contributors">
    <div class="contributors-list">
        <h1 class="section-header">Contributors</h1>
        <span class="h2">{0} - Contributors</span>
        {1}
    </div>
    <div class="contributors-list">
        <span class="h2">{2} - Contributors</span>
        {3}
    </div>
    <div class="contributors-list">
        <span class="h2">{4} - Contributors</span>
        {5}
    </div>
</section>
'''.format(tn_title, tn_contributors, ta_title, ta_contributors, tw_title, tw_contributors)
        return contributors_html

    def save_resource_data(self):
        save_dir = os.path.join(self.output_dir, 'save')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}_resource_data.json'.format(self.book_file_id))
        write_file(save_file, self.resource_data)
        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.book_file_id))
        write_file(save_file, self.rc_references)
        save_file = os.path.join(save_dir, '{0}_bad_links.json'.format(self.book_file_id))
        write_file(save_file, self.bad_links)
        save_file = os.path.join(save_dir, '{0}_bad_notes.json'.format(self.book_file_id))
        write_file(save_file, self.bad_notes)
        save_file = os.path.join(save_dir, '{0}_generation_info.json'.format(self.file_id))
        write_file(save_file, self.generation_info)

    def get_previous_generation_info(self):
        save_dir = os.path.join(self.output_dir, 'save')
        save_file = os.path.join(save_dir, '{0}_generation_info.json'.format(self.file_id))
        if os.path.isfile(save_file):
            return load_json_object(save_file)
        else:
            return {}

    def load_resource_data(self):
        save_dir = os.path.join(self.output_dir, 'save')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        save_file = os.path.join(save_dir, '{0}_resource_data.json'.format(self.book_file_id))
        if not self.regenerate and os.path.isfile(save_file):
            self.resource_data = load_json_object(save_file)
        else:
            self.regenerate = True
            self.resource_data = {}

        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.book_file_id))
        if not self.regenerate and os.path.isfile(save_file):
            self.rc_references = load_json_object(save_file)
        else:
            self.regenerate = True
            self.rc_references = {}

        save_file = os.path.join(save_dir, '{0}_bad_links.json'.format(self.book_file_id))
        if not self.regenerate and os.path.isfile(save_file):
            self.bad_links = load_json_object(save_file)
        else:
            self.regenerate = True
            self.bad_links = {}

    def download_all_images(self):
        img_dir = os.path.join(self.html_dir, 'images')
        os.makedirs(img_dir, exist_ok=True)
        for img in self.soup.find_all('img'):
            if img['src'].startswith('http'):
                url = img['src']
                filename = re.search(r'/([\w_-]+[.](jpg|gif|png))$', url).group(1)
                img['src'] = 'html/images/{0}'.format(filename)
                filepath = os.path.join(img_dir, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'wb') as f:
                        response = requests.get(url)
                        f.write(response.content)

    def get_body_html(self):
        self.logger.info('Generating TN html...')
        html = self.get_tn_html()
        self.logger.info('Generating TA html...')
        html += self.get_ta_html()
        self.logger.info('Generating TW html...')
        html += self.get_tw_html()
        self.logger.info('Generating Contributors html...')
        html += self.get_contributors()
        self.logger.info('Replacing RC links...')
        html = self.replace_rc_links(html)
        self.logger.info('Fixing links...')
        html = self.fix_links(html)
        self.logger.info('Generating TOC html...')
        toc_html = self.get_toc_html(html)
        write_file(os.path.join(self.output_dir, 'tn_raw_body.html'), html)
        write_file(os.path.join(self.output_dir, 'tn_toc.html'), toc_html)
        self.soup.body.append(BeautifulSoup(toc_html, 'html.parser'))
        self.soup.body.append(BeautifulSoup(html, 'html.parser'))

    def get_toc_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        toc_html = '''
<article id="contents">
    <h1>{0}</h1>
    <ul id="contents-top-ul">
'''.format('Table of Contents')  # TODO: Replace with a localized string
        for section in soup.find_all('section'):
            header = section.find(re.compile(r'^h\d'), {'class': 'section-header'})
            toc_html += '''
<li><a href="#{0}"><span>{1}</span></a>
'''.format(section.get('id'), header.text)
            articles = section.find_all('article')
            if len(articles):
                toc_html += '<ul>'
                for article in articles:
                    rc = self.resource_data[self.rc_lookup[article.get('id')]]
                    title = rc['alt_title'] if 'alt_title' in rc and rc['alt_title'] else rc['title']
                    toc_html += '''
<li><a href="{0}"><span>{1}</span></a></li>
'''.format(rc['link'], title)
                toc_html += '</ul>'
            toc_html += '</li>'
        toc_html += '''
    </ul>
</article>
'''
        return toc_html

    def pad(self, num):
        if self.book_id == 'psa':
            return str(num).zfill(3)
        else:
            return str(num).zfill(2)

    def get_usfm_from_verse_objects(self, verse_objects, depth=0):
        usfm = ''
        for idx, obj in enumerate(verse_objects):
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
                if idx == len(verse_objects) -1 and obj['tag'] == 'q' and len(obj['text']) == 0:
                    self.lastEndedWithQuoteTag = True
                else:
                    usfm += '\n\\{0} {1}'.format(obj['tag'], obj['text'] if len(obj['text']) > 0 else '')
                if obj['text'].count('"') == 1:
                    self.openQuote = not self.openQuote
                if self.openQuote and '"' in obj['text']:
                    self.nextFollowsQuote = True
            elif obj['type'] == 'section':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
            elif obj['type'] == 'paragraph':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if idx == len(verse_objects) - 1 and not obj['text']:
                    self.lastEndedWithParagraphTag = True
                else:
                    usfm += '\n\\{0}{1}\n'.format(obj['tag'], obj['text'])
            elif obj['type'] == 'footnote':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                usfm += r' \{0} {1} \{0}*'.format(obj['tag'], obj['content'])
            else:
                self.logger.error("ERROR! Not sure what to do with this:")
                self.logger.error(obj)
                exit(1)
        return usfm

    def populate_verse_usfm(self):
        self.populate_verse_usfm_ult()
        self.populate_verse_usfm_ust()

    def populate_verse_usfm_ust(self):
        book_data = {}
        book_file = os.path.join(self.ust_dir, '{0}-{1}.usfm'.format(self.book_number, self.book_id.upper()))
        usfm3 = read_file(book_file)
        usfm2 = usfm3_to_usfm2(usfm3)
        chapters = usfm2.split(r'\c ')
        for chapter_usfm in chapters[1:]:
            chapter = int(re.findall('(\d+)', chapter_usfm)[0])
            book_data[chapter] = {}
            chapter_usfm = r'\c '+chapter_usfm
            verses = chapter_usfm.split(r'\v ')
            for verseUsfm in verses[1:]:
                verse = int(re.findall('(\d+)', verseUsfm)[0])
                verseUsfm = r'\v '+verseUsfm
                if re.match(r'^\\v \d+\s*$', verseUsfm, flags=re.MULTILINE):
                    verseUsfm = ''
                book_data[chapter][verse] = verseUsfm
        self.verse_usfm[self.ust_id] = book_data

    def populate_verse_usfm_ult(self):
        bookData = {}
        book_file = os.path.join(self.ult_dir, '{0}-{1}.usfm'.format(self.book_number, self.book_id.upper()))
        usfm3 = read_file(book_file)
        usfm2 = usfm3_to_usfm2(usfm3)
        chapters = usfm2.split(r'\c ')
        for chapterUsfm in chapters[1:]:
            chapter = int(re.findall('(\d+)', chapterUsfm)[0])
            bookData[chapter] = {}
            chapterUsfm = r'\c '+chapterUsfm
            verses = chapterUsfm.split(r'\v ')
            for verseUsfm in verses[1:]:
                verse = int(re.findall('(\d+)', verseUsfm)[0])
                verseUsfm = r'\v '+verseUsfm
                if re.match(r'^\\v \d+\s*$', verseUsfm, flags=re.MULTILINE):
                    verseUsfm = ''
                bookData[chapter][verse] = verseUsfm
        self.verse_usfm[self.ult_id] = bookData

    def populate_chapters_and_verses(self):
        versification_file = os.path.join(self.versification_dir, '{0}.json'.format(self.book_id))
        self.chapter_and_verses = {}
        if os.path.isfile(versification_file):
            self.chapters_and_verses = load_json_object(versification_file)

    @staticmethod
    def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
        csv_reader = csv.reader(utf8_data, dialect=dialect, delimiter=str("\t"), quotechar=str('"'), **kwargs)
        for row in csv_reader:
            yield [cell for cell in row]

    def populate_tn_book_data(self):
        book_file = os.path.join(self.tn_dir, '{0}_tn_{1}-{2}.tsv'.format(self.lang_code, self.book_number, self.book_id.upper()))
        self.tn_book_data = {}
        if not os.path.isfile(book_file):
            return
        book_data = {}
        reader = self.unicode_csv_reader(open(book_file))
        header = next(reader)
        for row in reader:
            data = {}
            found = False
            for idx, field in enumerate(header):
                field = field.strip()
                if idx >= len(row):
                    self.logger.error('ERROR: {0} is malformed'.format(book_file))
                    found = False
                    break
                else:
                    found = True
                    data[field] = row[idx]
            if not found:
                break
            self.logger.info('{0} {1}:{2}:{3}'.format(data['Book'], data['Chapter'], data['Verse'], data['ID']))
            chapter = data['Chapter'].lstrip('0')
            verse = data['Verse'].lstrip('0')
            if not chapter in book_data:
                book_data[chapter] = {}
            if not verse in book_data[chapter]:
                book_data[chapter][verse] = []
            book_data[str(chapter)][str(verse)].append(data)
        self.tn_book_data = book_data

    def get_tn_html(self):
        tn_html = '''
<section id="tn-{0}">
<div class="resource-title-page">
    <img src="html/logo-utn-256.png" class="logo" alt="UTN">
    <h1 class="section-header">{1} - {2}</h1>
</div>
'''.format(self.book_id, self.tn_manifest['dublin_core']['title'], self.book_title)
        if 'front' in self.tn_book_data and 'intro' in self.tn_book_data['front']:
            intro = markdown2.markdown(self.tn_book_data['front']['intro'][0]['OccurrenceNote'].replace('<br>', '\n'))
            title = self.get_first_header(intro)
            intro = self.fix_tn_links(intro, 'intro')
            intro = self.increase_headers(intro)
            intro = self.decrease_headers(intro, 4)  # bring headers of 3 or more down 1
            intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
            intro_id = 'tn-{0}-front-intro'.format(self.book_id)
            tn_html += '<article id="{0}">\n{1}\n</article>\n\n'.format(intro_id, intro)
            # HANDLE RC LINKS AND BACK REFERENCE
            rc = 'rc://{0}/tn/help/{1}/front/intro'.format(self.lang_code, self.book_id)
            self.resource_data[rc] = {
                'rc': rc,
                'id': intro_id,
                'link': '#'+intro_id,
                'title': title
            }
            self.rc_lookup[intro_id] = rc
            self.get_resource_data_from_rc_links(intro, rc)

        for chapter_verses in self.chapters_and_verses:
            chapter = str(chapter_verses['chapter'])
            self.logger.info('Chapter {0}...'.format(chapter))
            if 'intro' in self.tn_book_data[chapter]:
                intro = markdown2.markdown(self.tn_book_data[chapter]['intro'][0]['OccurrenceNote'].replace('<br>',"\n"))
                intro = re.sub(r'<h(\d)>([^>]+) 0+([1-9])', r'<h\1>\2 \3', intro, 1, flags=re.MULTILINE | re.IGNORECASE)
                title = self.get_first_header(intro)
                intro = self.fix_tn_links(intro, chapter)
                intro = self.increase_headers(intro)
                intro = self.decrease_headers(intro, 5, 2)  # bring headers of 5 or more down 2
                intro_id = 'tn-{0}-{1}-intro'.format(self.book_id, self.pad(chapter))
                intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
                tn_html += '<article id="{0}">\n{1}\n</article>\n\n'.format(intro_id, intro)
                # HANDLE RC LINKS
                rc = 'rc://{0}/tn/help/{1}/{2}/intro'.format(self.lang_code, self.book_id, self.pad(chapter))
                self.resource_data[rc] = {
                    'rc': rc,
                    'id': intro_id,
                    'link': '#'+intro_id,
                    'title': title
                }
                self.rc_lookup[intro_id] = rc
                self.get_resource_data_from_rc_links(intro, rc)

            for idx, first_verse in enumerate(chapter_verses['first_verses']):
                if idx < len(chapter_verses['first_verses'])-1:
                    last_verse = chapter_verses['first_verses'][idx+1] - 1
                else:
                    last_verse = int(BOOK_CHAPTER_VERSES[self.book_id][chapter])

                chunk_notes = ''
                for verse in range(first_verse, last_verse + 1):
                    if str(verse) in self.tn_book_data[chapter]:
                        verse_notes = ''
                        for data in self.tn_book_data[chapter][str(verse)]:
                            note_quote = data['GLQuote']
                            note = markdown2.markdown(data['OccurrenceNote'].replace('<br>', "\n"))
                            note = re.sub(r'</*p[^>]*>', '', note, flags=re.IGNORECASE | re.MULTILINE)
                            verse_notes += '''
                <div class="verse-note">
                    <h3 class="verse-note-title">{0}</h3>
                    <div class="verse-note-text">
                        {1}
                    </div>
                </div>
            '''.format(note_quote, note)
                        rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                                   self.pad(verse))
                        self.get_resource_data_from_rc_links(verse_notes, rc)
                        chunk_notes += verse_notes

                if not chunk_notes:
                    continue

                chunk_notes = self.decrease_headers(chunk_notes, 5)  # bring headers of 5 or more #'s down 1
                chunk_notes = self.fix_tn_links(chunk_notes, chapter)

                if first_verse != last_verse:
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter, first_verse, last_verse)
                else:
                    title = '{0} {1}:{2}'.format(self.book_title, chapter, first_verse)

                verse_ids = []
                for verse in range(first_verse, last_verse+1):
                    verse_id = 'tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), self.pad(verse))
                    verse_ids.append(verse_id)
                    rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                               self.pad(verse))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': verse_id,
                        'link': '#'+verse_id,
                        'title': title
                    }
                    self.rc_lookup[verse_id] = rc
                    self.rc_lookup[verse_id + '-top'] = rc

                scripture = '''
    <h3 class="bible-resource-title">{0}</h3>
    <div class="bible-text">{1}</div>
    <h3 class="bible-resource-title">{2}</h3>
    <div class="bible-text">{3}</div>
'''.format(self.ult_id.upper(), self.get_highlighted_html(self.ult_id, int(chapter), first_verse, last_verse),
           self.ust_id.upper(), self.get_plain_html(self.ust_id, int(chapter), first_verse))

                chunk_article = '''
    <h2 class="section-header">{0}</h2>
    <table class="tn-notes-table" style="width:100%">
        <tr>
            <td class="col1" style="vertical-align:top;width:35%;padding-right:5px">
                {1}
            </td>
            <td class="col2" style="vertical-align:top">
                {2}
            </td>
        </tr>
    </table>
'''.format(title, scripture, chunk_notes)
                tn_html += '''
<article id="{0}-top">
  {1}
  {2}
</article>
'''.format(verse_ids[0], "\n".join(map(lambda x: '<a id="{0}"></a>'.format(x), verse_ids)), chunk_article)
        tn_html += "\n</section>\n\n"
        return tn_html

    def populate_tw_words_data(self):
        groups = ['kt', 'names', 'other']
        grc_path = get_latest_version(os.path.join(self.tn_resources_dir, 'grc/translationHelps/translationWords'))
        if not os.path.isdir(grc_path):
            self.logger.error('{0} not found! Please make sure you ran `node getResources ./` in the generate_tn_pdf dir and that the version in the script is correct'.format(grc_path))
            exit(1)
        words = {}
        for group in groups:
            files_path = '{0}/{1}/groups/{2}/*.json'.format(grc_path, group, self.book_id)
            files = glob(files_path)
            for file in files:
                base = os.path.splitext(os.path.basename(file))[0]
                rc = 'rc://{0}/tw/dict/bible/{1}/{2}'.format(self.lang_code, group, base)
                occurrences = load_json_object(file)
                for occurrence in occurrences:
                    context_id = occurrence['contextId']
                    chapter = context_id['reference']['chapter']
                    verse = context_id['reference']['verse']
                    context_id['rc'] = rc
                    if chapter not in words:
                        words[chapter] = {}
                    if verse not in words[chapter]:
                        words[chapter][verse] = []
                    words[chapter][verse].append(context_id)
        self.tw_words_data = words

    def get_plain_html(self, resource, chapter, first_verse):
        html = self.chunks_text[str(chapter)][str(first_verse)][resource]['html']
        html = re.sub(r'\s*\n\s*', '', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub(r'\s*</*p[^>]*>\s*', '', html, flags=re.IGNORECASE | re.MULTILINE)
        html = html.strip()
        html = re.sub(r'\s*<span class="v-num"', '</div><div class="verse"><span class="v-num"', html, flags=re.IGNORECASE | re.MULTILINE)
        html = re.sub(r'^</div>', '', html)
        html = re.sub(r'id="(ref-)*fn-', r'id="{0}-\1fn-'.format(resource), html, flags=re.IGNORECASE | re.MULTILINE)
        html += '</div>'
        return html

    def get_highlighted_html(self, resource, chapter, first_verse, last_verse):
        html = self.get_plain_html(resource, chapter, first_verse)
        regex = re.compile(' <div')
        verses_and_footer = regex.split(html)
        verses_html = verses_and_footer[0]
        footer_html = ''
        if len(verses_and_footer) > 1:
            footer_html = ' <div {0}'.format(verses_and_footer[1])
        regex = re.compile(r'<div class="verse"><span class="v-num" id="{0}-\d+-ch-\d+-v-\d+"><sup><strong>(\d+)</strong></sup></span>'.
                           format(resource))
        verses_split = regex.split(verses_html)
        verses = {}
        for i in range(1, len(verses_split), 2):
            verses[int(verses_split[i])] = verses_split[i+1]
        new_html = verses_split[0]
        for verse_num in range(first_verse, last_verse+1):
            words = self.get_all_words_to_match(resource, chapter, verse_num)
            for word in words:
                parts = word['text'].split(' ... ')
                pattern = ''
                replace = ''
                new_parts = []
                for idx, part in enumerate(parts):
                    words_to_ignore = ['a', 'am', 'an', 'and', 'as', 'are', 'at', 'be', 'by', 'did', 'do', 'does', 'done', 'for', 'from', 'had', 'has', 'have', 'he', 'her', 'his', 'i', 'in', 'into', 'less', 'let', 'may', 'might', 'more', 'my', 'not', 'is', 'of', 'on', 'one', 'onto', 'our', 'she', 'the', 'their', 'they', 'this', 'that', 'those', 'these', 'to', 'was', 'we', 'who', 'whom', 'with', 'will', 'were', 'your', 'you', 'would', 'could', 'should', 'shall', 'can']
                    part = re.sub(r'^(({0})\s+)+'.format('|'.join(words_to_ignore)), '', part, flags=re.MULTILINE | re.IGNORECASE)
                    if not part or (idx < len(parts)-1 and part.lower().split(' ')[-1] in words_to_ignore):
                        continue
                    new_parts.append(part)
                for idx, part in enumerate(new_parts):
                    pattern += r'(?<![></\\_-])\b{0}\b(?![></\\_-])'.format(part)
                    replace += r'<a href="{0}">{1}</a>'.format(word['contextId']['rc'], part)
                    if idx + 1 < len(new_parts):
                        pattern += r'(.*?)'
                        replace += r'\{0}'.format(idx + 1)
                verses[verse_num] = re.sub(pattern, replace, verses[verse_num], 1, flags=re.MULTILINE | re.IGNORECASE)
            rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                       self.pad(str(verse_num)))
            verse_text = ''
            if verse_num in verses:
                verse_text = verses[verse_num]
                self.get_resource_data_from_rc_links(verses[verse_num], rc)
            new_html += '<div class="verse"><span class="v-num" id="{0}-{1}-ch-{2}-v-{3}"><sup><strong>{4}</strong></sup></span>{5}'.\
                format(resource, str(self.book_number).zfill(3), str(chapter).zfill(3), str(verse_num).zfill(3),
                       verse_num, verse_text)
        new_html += footer_html
        return new_html

    def get_all_words_to_match(self, resource, chapter, verse):
        path = '{0}/{1}/{2}.json'.format(
            get_latest_version(os.path.join(self.tn_resources_dir, '{0}/bibles/{1}'.format(self.lang_code, resource))),
            self.book_id, chapter)
        words = []
        data = load_json_object(path)
        chapter = int(chapter)
        if chapter in self.tw_words_data and verse in self.tw_words_data[chapter]:
            context_ids = self.tw_words_data[int(chapter)][int(verse)]
            verse_objects = data[str(verse)]['verseObjects']
            for context_id in context_ids:
                aligned_text = self.get_aligned_text(verse_objects, context_id, False)
                if aligned_text:
                    words.append({'text': aligned_text, 'contextId': context_id})
        return words

    def find_english_from_combination(self, verse_objects, quote, occurrence):
        greekWords = []
        wordList = []
        for verse_object in verse_objects:
            greek = None
            if 'content' in verse_object and verse_object['type'] == 'milestone':
                greekWords.append(verse_object['content'])
                englishWords = []
                for child in verse_object['children']:
                    if child['type'] == 'word':
                        englishWords.append(child['text'])
                english = ' '.join(englishWords)
                found = False
                for idx, word in enumerate(wordList):
                    if word['greek'] == verse_object['content'] and word['occurrence'] == verse_object['occurrence']:
                        wordList[idx]['english'] += ' ... ' + english
                        found = True
                if not found:
                    wordList.append({'greek': verse_object['content'], 'english': english, 'occurrence': verse_object['occurrence']})
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

    def find_english_from_split(self, verse_objects, quote, occurrence, isMatch=False):
        words_to_match = quote.split(' ')
        separator = ' '
        needs_ellipsis = False
        text = ''
        for index, verse_object in enumerate(verse_objects):
            last_match = False
            if verse_object['type'] == 'milestone' or verse_object['type'] == 'word':
                if ((('content' in verse_object and verse_object['content'] in words_to_match) or ('lemma' in verse_object and verse_object['lemma'] in words_to_match)) and verse_object['occurrence'] == occurrence) or isMatch:
                    last_match = True
                    if needs_ellipsis:
                        separator += '... '
                        needs_ellipsis = False
                    if text:
                        text += separator
                    separator = ' '
                    if 'text' in verse_object and verse_object['text']:
                        text += verse_object['text']
                    if 'children' in verse_object and verse_object['children']:
                        text += self.find_english_from_split(verse_object['children'], quote, occurrence, True)
                elif 'children' in verse_object and verse_object['children']:
                    childText = self.find_english_from_split(verse_object['children'], quote, occurrence, isMatch)
                    if childText:
                        last_match = True
                        if needs_ellipsis:
                            separator += '... '
                            needs_ellipsis = False
                        text += (separator if text else '') + childText
                        separator = ' '
                    elif text:
                        needs_ellipsis = True
            if last_match and (index+1) in verse_objects and verse_objects[index + 1]['type'] == "text" and text:
                if separator == ' ':
                    separator = ''
                separator += verse_objects[index + 1]['text']
        return text

    def get_aligned_text(self, verse_objects, context_id, isMatch=False):
        if not verse_objects or not context_id or not 'quote' in context_id or not context_id['quote']:
            return ''
        text = self.find_english_from_combination(verse_objects, context_id['quote'], context_id['occurrence'])
        if text:
            return text
        text = self.find_english_from_split(verse_objects, context_id['quote'], context_id['occurrence'])
        if text:
            return text
        rc = 'rc://{0}/{1}/bible/{2}/{3}/{4}'.format(self.lang_code, self.ult_id, self.book_id,
                                                     context_id['reference']['chapter'],
                                                     context_id['reference']['verse'])
        bad_rc = 'rc://*/grc/word/{0}/{1}'.format(context_id['quote'], context_id['occurrence'])
        if rc not in self.bad_links:
            self.bad_links[rc] = {}
        self.bad_links[rc][bad_rc] = context_id['rc']
        self.logger.error('{0} word not found for Greek word `{1}` (occurrence: {2}) in `ULT {3} {4}:{5}`'.
                          format(self.lang_code.upper(), context_id['quote'], context_id['occurrence'],
                                 self.book_id.upper(), context_id['reference']['chapter'],
                                 context_id['reference']['verse']))

    def get_tw_html(self):
        tw_html = '''
<section id="tw-{0}">
<div class="resource-title-page">
    <img src="html/logo-utw-256.png" class="logo" alt="UTW">
    <h1 class="section-header">{1}</h1>
</div>
'''.format(self.book_id, self.tw_manifest['dublin_core']['title'])
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/tw/' not in rc:
                continue
            html = self.resource_data[rc]['text']
            html = self.increase_headers(html)
            title = self.resource_data[rc]['title']
            alt_title = self.resource_data[rc]['alt_title']
            if alt_title:
                html = '<h2 class="section-header">{0}</h2>\n{2}{3}'.format(alt_title, title, self.get_reference_text(rc), html)
            else:
                html = '<h2 class="section-header">{0}</h2>\n{1}{2}'.format(title, self.get_reference_text(rc), html)
            tw_html += '<article id="{0}">\n{1}\n</article>\n\n'.format(self.resource_data[rc]['id'], html)
        tw_html += "\n</section>\n\n"
        return tw_html

    def get_ta_html(self):
        ta_html = '''
<section id="ta-{0}">
<div class="resource-title-page">
    <img src="html/logo-uta-256.png" class="logo" alt="UTA">
    <h1 class="section-header">{1}</h1>
</div>
'''.format(self.book_id, self.ta_manifest['dublin_core']['title'])
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/ta/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                html = self.resource_data[rc]['text']
                html = self.increase_headers(html)
                html = '''
    <h2 class="section-header">{0}</h2>
    {1}
    <div class="alt-title"><strong>{2}</strong></div>
    {3}
'''.format(self.resource_data[rc]['title'], self.get_reference_text(rc), self.resource_data[rc]['alt_title'], html)
                ta_html += '''
<article id="{0}">
    {1}
</article>
'''.format(self.resource_data[rc]['id'], html)
        ta_html += "\n</section>\n\n"
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
            uses = '<div class="go-back">\n(<strong>Go back to:</strong> {0})\n</div>\n'.format('; '.join(references))
        return uses

    def get_resource_data_from_rc_links(self, text, source_rc):
        for rc in re.findall(r'rc://[A-Z0-9/_\*-]+', text, flags=re.IGNORECASE | re.MULTILINE):
            parts = rc[5:].split('/')
            rc = 'rc://{0}/{1}'.format(self.lang_code, '/'.join(parts[1:]))
            resource = parts[1]
            path = '/'.join(parts[3:])

            if resource not in ['ta', 'tw']:
                continue

            if rc not in self.rc_references:
                self.rc_references[rc] = []
            if source_rc not in self.rc_references[rc]:
                self.rc_references[rc].append(source_rc)
            title = ''
            t = ''
            anchor_id = '{0}-{1}'.format(resource, path.replace('/', '-'))
            link = '#{0}'.format(anchor_id)
            file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource), path)
            if resource == 'ta':
                file_path = os.path.join(file_path, '01.md')
            else:
                file_path += '.md'
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
                    fix = 'rc://{0}/tw/dict/{1}'.format(self.lang_code, path2)
                    anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                    link = '#{0}'.format(anchor_id)
                    file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                '{0}.md'.format(path2))
                elif resource == 'ta':
                    bad_names = {
                        'figs-abstractnoun': 'translate/figs-abstractnouns'
                    }
                    if parts[3] in bad_names:
                        path2 = bad_names[parts[3]]
                    else:
                        path2 = path
                    fix = 'rc://{0}/ta/man/{1}'.format(self.lang_code, path2)
                    anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                    link = '#{0}'.format(anchor_id)
                    file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                '{0}/01.md'.format(path2))

            if os.path.isfile(file_path):
                if fix:
                    if source_rc not in self.bad_links:
                        self.bad_links[source_rc] = {}
                    self.bad_links[source_rc][rc] = fix
                if not rc in self.resource_data:
                    t = markdown2.markdown_path(file_path)
                    alt_title = ''
                    if resource == 'ta':
                        title_file = os.path.join(os.path.dirname(file_path), 'title.md')
                        question_file = os.path.join(os.path.dirname(file_path), 'sub-title.md')
                        if os.path.isfile(title_file):
                            title = read_file(title_file)
                        else:
                            title = self.get_first_header(t)
                            t = re.sub(r'\s*\n*\s*<h\d>[^<]+</h\d>\s*\n*', r'', t, 1,
                                       flags=re.IGNORECASE | re.MULTILINE)  # removes the header
                        if os.path.isfile(question_file):
                            question = read_file(question_file)
                            if question:
                                t = '''
<div class="top-box box">
    <div class="ta-question">
        This page answers the question: <em>{0}<em>
    </div>
</div>
{1}
'''.format(question, t)
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
                    self.rc_lookup[anchor_id] = rc
                    self.get_resource_data_from_rc_links(t, rc)
                else:
                    if source_rc not in self.resource_data[rc]['references']:
                        self.resource_data[rc]['references'].append(source_rc)
            else:
                if source_rc not in self.bad_links:
                    self.bad_links[source_rc] = {}
                if rc not in self.bad_links[source_rc]:
                    self.bad_links[source_rc][rc] = None

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
        def replace_link(match):
            before_href = match.group(1)
            link = match.group(2)
            after_href = match.group(3)
            linked_text = match.group(4)
            new_link = link
            if link.startswith('../../'):
                # link to another book, which we don't link to so link removed
                return linked_text
            elif link.startswith('../'):
                # links to another chunk in another chapter
                link = os.path.splitext(link)[0]
                parts = link.split('/')
                if len(parts) == 3:
                    # should have two numbers, the chapter and the verse
                    c = parts[1]
                    v = parts[2]
                    new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, c, v)
                if len(parts) == 2:
                    # shouldn't be here, but just in case, assume link to the first chunk of the given chapter
                    c = parts[1]
                    new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, c, '01')
            elif link.startswith('./'):
                # link to another verse in the same chapter
                link = os.path.splitext(link)[0]
                parts = link.split('/')
                v = parts[1]
                new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), v)
            return '<a{0}href="{1}"{2}>{3}</a>'.format(before_href, new_link, after_href, linked_text)
        regex = re.compile(r'<a([^>]+)href="(\.[^"]+)"([^>]*)>(.*?)</a>')
        text = regex.sub(replace_link, text)
        return text

    def fix_tw_links(self, text, group):
        text = re.sub(r'href="\.\./([^/)]+?)(\.md)*"', r'href="rc://{0}/tw/dict/bible/{1}/\1"'.
                      format(self.lang_code, group), text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_ta_links(self, text, manual):
        text = re.sub(r'href="\.\./([^/"]+)/01\.md"', r'href="rc://{0}/ta/man/{1}/\1"'.format(self.lang_code, manual),
                      text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./\.\./([^/"]+)/([^/"]+)/01\.md"', r'href="rc://{0}/ta/man/\1/\2"'.
                      format(self.lang_code), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="([^# :/"]+)"', r'href="rc://{0}/ta/man/{1}/\1"'.format(self.lang_code, manual),
                      text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def replace_rc_links(self, text):
        # Change rc://... rc links,
        # Case 1: [[rc://en/tw/help/bible/kt/word]] => <a href="#tw-kt-word">God's Word</a>
        # Case 2: rc://en/tw/help/bible/kt/word => #tw-kt-word (used in links that are already formed)
        # Case 3: Remove other scripture reference not in this tN
        def replace_rc(match):
            left = match.group(1)
            rc = match.group(2)
            right = match.group(3)
            title = match.group(4)
            if rc in self.resource_data:
                info = self.resource_data[rc]
                if left and right and left == '[[':
                    # Case 1
                    return '<a href="{0}">{1}</a>'.format(info['link'], info['title'])
                else:
                    # Case 2
                    return left + info['link'] + right
            else:
                # Case 3
                return title if title else rc
        regex = re.compile(r'(\[\[|<a[^>]+href=")*(rc://[/A-Za-z0-9\*_-]+)(\]\]|"[^>]*>(.*?)</a>)*')
        text = regex.sub(replace_rc, text)
        return text

    def fix_links(self, text):
        # convert URLs to links if not already
        text = re.sub(r'(?<![">])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])', r'<a href="\1">\1</a>', text, flags=re.IGNORECASE)

        # # Removes leading 0s from verse references
        # text = re.sub(r' 0*(\d+):0*(\d+)(-*)0*(\d*)', r' \1:\2\3\4', text, flags=re.IGNORECASE | re.MULTILINE)

        return text

    def get_chunk_html(self, usfm, resource, chapter, verse):
        usfm_chunks_path = os.path.join(self.working_dir, 'usfm_chunks', 'usfm-{0}-{1}-{2}-{3}-{4}'.
                                        format(self.lang_code, resource, self.book_id, chapter, verse))
        filename_base = '{0}-{1}-{2}-{3}'.format(resource, self.book_id, chapter, verse)
        html_file = os.path.join(usfm_chunks_path, '{0}.html'.format(filename_base))
        usfm_file = os.path.join(usfm_chunks_path, '{0}.usfm'.format(filename_base))
        if not os.path.exists(usfm_chunks_path):
            os.makedirs(usfm_chunks_path)
        usfm = '''\id {0}
\ide UTF-8
\h {1}
\mt {1}

\c {2}
{3}'''.format(self.book_id.upper(), self.book_title, chapter, usfm)
        write_file(usfm_file, usfm)
        UsfmTransform.buildSingleHtml(usfm_chunks_path, usfm_chunks_path, filename_base)
        html = read_file(os.path.join(usfm_chunks_path, filename_base+'.html'))
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find('h1')
        if header:
            header.decompose()
        chapter = soup.find('h2')
        if chapter:
            chapter.decompose()
        for span in soup.find_all('span', {'class': 'v-num'}):
            span['id'] = '{0}-{1}'.format(resource, span['id'])
        html = ''.join(['%s' % x for x in soup.body.contents])
        write_file(html_file, html)
        return html


def main(ta_tag, tn_tag, tw_tag, ust_tag, ult_tag, ugnt_tag, lang_codes, books, working_dir, output_dir, owner,
         regenerate, ust_id, ult_id, tn_id, regenerate_all):
    lang_codes = lang_codes
    if not lang_codes:
        lang_codes = [DEFAULT_LANG]

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if not working_dir and 'WORKING_DIR' in os.environ:
        working_dir = os.environ['WORKING_DIR']
        logger.info('Using env var WORKING_DIR: {0}'.format(working_dir))
    if not output_dir and 'OUTPUT_DIR' in os.environ:
        output_dir = os.environ['OUTPUT_DIR']
        logger.info('Using env var OUTPUT_DIR: {0}'.format(output_dir))

    for lang_code in lang_codes:
        logger.info('Starting TN Converter for {0}...'.format(lang_code))
        tn_converter = TnConverter(ta_tag, tn_tag, tw_tag, ust_tag, ult_tag, ugnt_tag, working_dir, output_dir,
                                   lang_code, books, owner, regenerate, logger, ust_id, ult_id, tn_id, regenerate_all)
        tn_converter.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_codes', required=False, help='Language Code(s)', action='append')
    parser.add_argument('-b', '--book_id', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help="Working Directory")
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help="Output Directory")
    parser.add_argument('--tn-tag', dest='tn', default=DEFAULT_TAG, required=False, help='tN Tag')
    parser.add_argument('--tn-id', dest='tn_id', default=DEFAULT_TN_ID, required=False, help="TN ID")
    parser.add_argument('--ta-tag', dest='ta', default=DEFAULT_TAG, required=False, help='tA Tag')
    parser.add_argument('--tw-tag', dest='tw', default=DEFAULT_TAG, required=False, help='tW Tag')
    parser.add_argument('--ust-id', dest='ust_id', default=DEFAULT_UST_ID, required=False, help="UST ID")
    parser.add_argument('--ult-id', dest='ult_id', default=DEFAULT_ULT_ID, required=False, help="ULT ID")
    parser.add_argument('--ust-tag', dest='ust', default=DEFAULT_TAG, required=False, help="UST Tag")
    parser.add_argument('--ult-tag', dest='ult', default=DEFAULT_TAG, required=False, help="ULT Tag")
    parser.add_argument('--ugnt-tag', dest='ugnt', default=DEFAULT_TAG, required=False, help="UGNT Tag")
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('-r', '--regenerate', dest='regenerate', default=False, action='store_true',
                        help='Regenerate even if exists')
    parser.add_argument('--regenerate-all', dest='regenerate_all', default=False, action='store_true',
                        help='Regenerate all things even scripture html even if exists')
    args = parser.parse_args(sys.argv[1:])
    main(args.ta, args.tn, args.tw, args.ust, args.ult, args.ugnt, args.lang_codes, args.books, args.working_dir,
         args.output_dir, args.owner, args.regenerate, args.ust_id, args.ult_id, args.tn_id, args.regenerate_all)
