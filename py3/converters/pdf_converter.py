#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
Class for any resource PDF converter
"""
import os
import re
import logging
import tempfile
import markdown2
import shutil
import subprocess
import string
import requests
import sys
import argparse
import jsonpickle
import yaml
from collections import OrderedDict
from typing import List, Type
from bs4 import BeautifulSoup
from abc import abstractmethod
from weasyprint import HTML, LOGGER
from .resource import Resource, Resources
from .rc_link import ResourceContainerLink
from ..general_tools.file_utils import write_file, read_file, load_json_object

DEFAULT_LANG_CODE = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
LANGUAGE_FILES = {
    'fr': 'French-fr_FR.json',
    'en': 'English-en_US.json'
}
APPENDIX_LINKING_LEVEL = 1
APPENDIX_RESOURCES = ['ta', 'tw']


class PdfConverter:

    def __init__(self, resources: Resources, project_id=None, working_dir=None, output_dir=None,
                 lang_code=DEFAULT_LANG_CODE, regenerate=False, logger=None):
        self.resources = resources
        self.main_resource = self.resources.main
        self.project_id = project_id
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.regenerate = regenerate
        self.logger = logger

        self.save_dir = None
        self.log_dir = None
        self.images_dir = None
        self.output_res_dir = None

        self.bad_links = {}
        self.bad_highlights = {}
        self.rcs = {}
        self.appendix_rcs = {}
        self.all_rcs = {}

        self.html_file = None
        self.pdf_file = None
        self.generation_info = {}
        self.translations = {}
        self.remove_working_dir = False
        self.converters_dir = os.path.dirname(os.path.realpath(__file__))

        if not self.logger:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def __del__(self):
        if self.remove_working_dir:
            shutil.rmtree(self.working_dir)

    @property
    def name(self):
        return self.main_resource.resource_name

    @property
    def title(self):
        return self.main_resource.title

    @property
    def simple_title(self):
        return self.main_resource.simple_title

    @property
    def version(self):
        return self.main_resource.version

    @property
    def file_commit_id(self):
        return f'{self.file_base_id}_{self.main_resource.commit}'

    @property
    def file_base_id(self):
        project_id_str = f'_{self.project_id}' if self.project_id else ''
        return f'{self.lang_code}_{self.name}{project_id_str}_{self.main_resource.tag}'

    @property
    def project(self):
        if self.project_id:
            project = self.main_resource.find_project(self.project_id)
            if project:
                self.logger.info(f'Project ID: {self.project_id}; Project Title: {self.project_title}')
                return project
            else:
                self.logger.error(f'Project not found: {self.project_id}')
                exit(1)

    @property
    def project_title(self):
        project = self.project
        if project:
            return project.title

    def translate(self, key):
        if not self.translations:
            if self.lang_code not in LANGUAGE_FILES:
                self.logger.error(f'No locale file for {self.lang_code}.')
                exit(1)
            locale_file = os.path.join(self.converters_dir, '..', 'locale', LANGUAGE_FILES[self.lang_code])
            if not os.path.isfile(locale_file):
                self.logger.error(f'No locale file found at {locale_file} for {self.lang_code}.')
                exit(1)
            self.translations = load_json_object(locale_file)
        keys = key.split('.')
        t = self.translations
        for key in keys:
            t = t.get(key, None)
            if t is None:
                # handle the case where the self.translations doesn't have that (sub)key
                self.logger.error(f"No translation for `{key}`")
                exit(1)
                break
        return t

    @staticmethod
    def create_rc(rc_link, article=None, title=None, linking_level=0, article_id=None):
        rc = ResourceContainerLink(rc_link, article=article, title=title, linking_level=linking_level,
                                   article_id=article_id)
        return rc

    def add_rc(self, rc_link, article=None, title=None, linking_level=0, article_id=None):
        rc = self.create_rc(rc_link, article=article, title=title, linking_level=linking_level, article_id=article_id)
        self.rcs[rc.rc_link] = rc
        return rc

    def add_appendix_rc(self, rc_link, article=None, title=None, linking_level=0):
        rc = self.create_rc(rc_link, article=article, title=title, linking_level=linking_level)
        self.appendix_rcs[rc.rc_link] = rc
        return rc

    def add_bad_link(self, source_rc, bad_rc_link, fix=None):
        if source_rc:
            if source_rc.rc_link not in self.bad_links:
                self.bad_links[source_rc.rc_link] = {}
            if bad_rc_link not in self.bad_links[source_rc.rc_link] or fix:
                self.bad_links[source_rc.rc_link][bad_rc_link] = fix

    def add_bad_highlight(self, rc, text, bad_highlights):
        if rc:
            if rc.rc_link not in self.bad_highlights:
                self.bad_highlights[rc.rc_link] = {
                    'rc': rc,
                    'text': text,
                    'bad_highlights': []
                }
            self.bad_highlights[rc.rc_link]['bad_highlights'].append(bad_highlights)

    def run(self):
        self.setup_dirs()
        self.setup_resources()

        self.html_file = os.path.join(self.output_res_dir, f'{self.file_commit_id}.html')
        self.pdf_file = os.path.join(self.output_res_dir, f'{self.file_commit_id}.pdf')

        self.setup_logging_to_file()
        self.determine_if_regeneration_needed()
        self.generate_html()
        self.generate_pdf()

    def setup_dirs(self):
        if not self.working_dir:
            if 'WORKING_DIR' in os.environ:
                self.working_dir = os.environ['WORKING_DIR']
                self.logger.info(f'Using env var WORKING_DIR: {self.working_dir}')
            else:
                self.working_dir = tempfile.mkdtemp(prefix=f'{self.main_resource.repo_name}-')
                self.remove_working_dir = True

        if not self.output_dir:
            if 'OUTPUT_DIR' in os.environ:
                self.output_dir = os.environ['OUTPUT_DIR']
                self.logger.info(f'Using env var OUTPUT_DIR: {self.output_dir}')
            if not self.output_dir:
                self.output_dir = self.working_dir
                self.remove_working_dir = False

        self.output_res_dir = os.path.join(self.output_dir, self.main_resource.resource_name)
        if not os.path.isdir(self.output_res_dir):
            os.makedirs(self.output_res_dir)

        self.images_dir = os.path.join(self.output_res_dir, 'images')
        if not os.path.isdir(self.images_dir):
            os.makedirs(self.images_dir)

        self.save_dir = os.path.join(self.output_res_dir, 'save')
        if not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir)

        self.log_dir = os.path.join(self.output_res_dir, 'log')
        if not os.path.isdir(self.log_dir):
            os.makedirs(self.log_dir)

        css_path = os.path.join(self.converters_dir, 'templates/css')
        subprocess.call(f'ln -sf "{css_path}" "{self.output_res_dir}"', shell=True)

        index_path = os.path.join(self.converters_dir, 'index.php')
        subprocess.call(f'ln -sf "{index_path}" "{self.output_dir}"', shell=True)

    def setup_logging_to_file(self):
        LOGGER.setLevel('INFO')  # Set to 'INFO' for debugging
        log_file = os.path.join(self.log_dir, f'{self.file_commit_id}_logger.log')
        logger_handler = logging.FileHandler(log_file)
        link_file_path = os.path.join(self.log_dir, f'{self.file_base_id}_logger.log')
        subprocess.call(f'ln -sf "{log_file}" "{link_file_path}"', shell=True)

        self.logger.addHandler(logger_handler)
        log_file = os.path.join(self.log_dir, f'{self.file_commit_id}_weasyprint.log')
        logger_handler = logging.FileHandler(log_file)
        LOGGER.addHandler(logger_handler)
        link_file_path = os.path.join(self.log_dir, f'{self.file_base_id}_weasyprint.log')
        subprocess.call(f'ln -sf "{log_file}" "{link_file_path}"', shell=True)

    def generate_html(self):
        if self.regenerate or not os.path.exists(self.html_file):
            self.logger.info(f'Creating HTML file for {self.file_commit_id}...')

            self.logger.info('Generating cover page HTML...')
            cover_html = self.get_cover_html()

            self.logger.info('Generating license page HTML...')
            license_html = self.get_license_html()

            self.logger.info('Generating body HTML...')
            body_html = self.get_body_html()
            self.get_appendix_rcs()
            self.all_rcs = {**self.rcs, **self.appendix_rcs}
            if 'ta' in self.resources:
                body_html += self.get_appendix_html(self.resources['ta'])
            if 'tw' in self.resources:
                body_html += self.get_appendix_html(self.resources['tw'])
            self.logger.info('Fixing links in body HTML...')
            body_html = self.fix_links(body_html)
            body_html = self._fix_links(body_html)
            self.logger.info('Replacing RC links in body HTML...')
            body_html = self.replace_rc_links(body_html)
            self.logger.info('Generating Contributors HTML...')
            body_html += self.get_contributors_html()
            body_html = self.download_all_images(body_html)
            self.logger.info('Generating TOC HTML...')
            body_html, toc_html = self.get_toc_html(body_html)

            with open(os.path.join(self.converters_dir, 'templates/template.html')) as template_file:
                html_template = string.Template(template_file.read())
            title = f'{self.title} - v{self.version}'
            link = ''
            personal_styles_file = os.path.join(self.output_dir, f'css/{self.name}_style.css')
            if os.path.isfile(personal_styles_file):
                link = f'<link href="css/{self.name}_style.css" rel="stylesheet">'
            body = '\n'.join([cover_html, license_html, toc_html, body_html])
            html = html_template.safe_substitute(title=title, link=link, body=body)
            write_file(self.html_file, html)

            link_file_path = os.path.join(self.output_res_dir, f'{self.file_base_id}.html')
            subprocess.call(f'ln -sf "{self.html_file}" "{link_file_path}"', shell=True)

            self.save_resource_data()
            self.save_bad_links_html()
            self.save_bad_highlights_html()
            self.logger.info('Generated HTML file.')
        else:
            self.logger.info(f'HTML file {self.html_file} is already there. Not generating. Use -r to force regeneration.')

    def generate_pdf(self):
        if self.regenerate or not os.path.exists(self.pdf_file):
            self.logger.info(f'Generating PDF file {self.pdf_file}...')
            weasy = HTML(filename=self.html_file, base_url=f'file://{self.output_res_dir}/')
            weasy.write_pdf(self.pdf_file)
            self.logger.info('Generated PDF file.')
            self.logger.info(f'PDF file located at {self.pdf_file}')

            link_file_path = os.path.join(self.output_res_dir, f'{self.file_base_id}.pdf')
            subprocess.call(f'ln -sf "{self.pdf_file}" "{link_file_path}"', shell=True)
        else:
            self.logger.info(
                f'PDF file {self.pdf_file} is already there. Not generating. Use -r to force regeneration.')

    def save_bad_links_html(self):
        link_file_path = os.path.join(self.output_res_dir, f'{self.file_base_id}_bad_links.html')

        if not self.bad_links:
            self.logger.info('No bad links for this version!')
            subprocess.call(f'rm -f "{link_file_path}"', shell=True)
            return

        bad_links_html = '''
<h1>BAD LINKS</h1>
<ul>
'''
        for source_rc_links in sorted(self.bad_links.keys()):
            for rc_links in sorted(self.bad_links[source_rc_links].keys()):
                line = f'<li>{source_rc_links}: BAD RC - `{rc_links}`'
                if self.bad_links[source_rc_links][rc_links]:
                    line += f' - change to `{self.bad_links[source_rc_links][rc_links]}`'
                bad_links_html += f'{line}</li>\n'
        bad_links_html += '''
</ul>
'''
        with open(os.path.join(self.converters_dir, 'templates/template.html')) as template_file:
            html_template = string.Template(template_file.read())
        html = html_template.safe_substitute(title=f'BAD LINKS FOR {self.file_commit_id}', link='', body=bad_links_html)
        save_file = os.path.join(self.output_res_dir, f'{self.file_commit_id}_bad_links.html')
        write_file(save_file, html)
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        self.logger.info(f'BAD LINKS HTML file can be found at {save_file}')

    def save_bad_highlights_html(self):
        link_file_path = os.path.join(self.output_res_dir, f'{self.file_base_id}_bad_highlights.html')

        if not self.bad_highlights:
            self.logger.info('No bad highlights for this version!')
            subprocess.call(f'rm -f "{link_file_path}"', shell=True)
            return

        bad_highlights_html = f'''
<h1>BAD HIGHLIGHTS:</h1>
<h2>(i.e. phrases not found in text as written)</h2>
<ul>
'''
        for rc_link in sorted(self.bad_highlights.keys()):
            rc = self.bad_highlights[rc_link]['rc']
            bad_highlights_html += f'''
    <li>
        <a href="{self.html_file}#{rc.article_id}" title="See in the HTML" target="obs-tn-html">{rc.rc_link}</a>:
        <br/>
        <i>{self.bad_highlights[rc_link]['text']}</i>
        <br/>
        <ul>
'''
            for bad_highlights in self.bad_highlights[rc_link]['bad_highlights']:
                for key in bad_highlights.keys():
                    if bad_highlights[key]:
                        bad_highlights_html += f'''
            <li>
                <b><i>{key}</i></b>
                <br/>{bad_highlights[key]} (QUOTE ISSUE)
            </li>
'''
                    else:
                        bad_highlights_html += f'''
            <li>
                <b><i>{key}</i></b>
            </li>
'''
            bad_highlights_html += '''
        </ul>
    </li>'''
        bad_highlights_html += '''
</ul>
'''
        with open(os.path.join(self.converters_dir, 'templates/template.html')) as template_file:
            html_template = string.Template(template_file.read())
        html = html_template.safe_substitute(title=f'BAD HIGHLIGHTS FOR {self.file_commit_id}', link='',
                                             body=bad_highlights_html)

        save_file = os.path.join(self.output_res_dir, f'{self.file_commit_id}_bad_highlights.html')
        write_file(save_file, html)
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        self.logger.info(f'BAD HIGHLIGHTS file can be found at {save_file}')

    def setup_resource(self, resource):
        resource.clone(self.working_dir)
        self.generation_info[resource.repo_name] = {'tag': resource.tag, 'commit': resource.commit}
        logo_path = os.path.join(self.images_dir, resource.logo_file)
        if not os.path.isfile(logo_path):
            command = f'cd "{self.images_dir}" && curl -O "{resource.logo_url}"'
            subprocess.call(command, shell=True)

    def setup_resources(self):
        for resource_name, resource in self.resources.items():
            self.setup_resource(resource)

    def determine_if_regeneration_needed(self):
        # check if any commit hashes have changed
        old_info = self.get_previous_generation_info()
        if not old_info:
            self.logger.info(f'Looks like this is a new commit of {self.file_commit_id}. Generating PDF.')
            self.regenerate = True
        else:
            for resource in self.generation_info:
                if resource in old_info and resource in self.generation_info:
                    old_tag = old_info[resource]['tag']
                    new_tag = self.generation_info[resource]['tag']
                    old_commit = old_info[resource]['commit']
                    new_commit = self.generation_info[resource]['commit']
                    if old_tag != new_tag or old_commit != new_commit:
                        self.logger.info(f'Resource {resource} has changed: {old_tag} => {new_tag}, {old_commit} => {new_commit}. REGENERATING PDF.')
                        self.regenerate = True
                else:
                    self.regenerate = True

    def save_resource_data(self):
        save_file = os.path.join(self.save_dir, f'{self.file_commit_id}_rcs.json')
        write_file(save_file, jsonpickle.dumps(self.rcs))
        link_file_path = os.path.join(self.save_dir, f'{self.file_base_id}_rcs.json')
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        save_file = os.path.join(self.save_dir, f'{self.file_commit_id}_appendix_rcs.json')
        write_file(save_file, jsonpickle.dumps(self.appendix_rcs))
        link_file_path = os.path.join(self.save_dir, f'{self.file_base_id}_appendix_rcs.json')
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        save_file = os.path.join(self.save_dir, f'{self.file_commit_id}_bad_links.json')
        write_file(save_file, jsonpickle.dumps(self.bad_links))
        link_file_path = os.path.join(self.save_dir, f'{self.file_base_id}_bad_links.json')
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        save_file = os.path.join(self.save_dir, f'{self.file_commit_id}_bad_highlights.json')
        write_file(save_file, jsonpickle.dumps(self.bad_highlights))
        link_file_path = os.path.join(self.save_dir, f'{self.file_base_id}_bad_highlights.json')
        subprocess.call(f'ln -sf "{save_file}" "{link_file_path}"', shell=True)

        save_file = os.path.join(self.save_dir, f'{self.file_base_id}_generation_info.json')
        write_file(save_file, jsonpickle.dumps(self.generation_info))

    def get_previous_generation_info(self):
        save_file = os.path.join(self.save_dir, f'{self.file_base_id}_generation_info.json')
        if os.path.isfile(save_file):
            return load_json_object(save_file)
        else:
            return {}

    def download_all_images(self, html):
        img_dir = os.path.join(self.images_dir, f'{self.main_resource.repo_name}_images')
        os.makedirs(img_dir, exist_ok=True)
        soup = BeautifulSoup(html, 'html.parser')
        for img in soup.find_all('img'):
            if img['src'].startswith('http'):
                url = img['src']
                filename = re.search(r'/([\w_-]+[.](jpg|gif|png))$', url).group(1)
                img['src'] = f'images/{self.main_resource.repo_name}_images/{filename}'
                filepath = os.path.join(img_dir, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'wb') as f:
                        response = requests.get(url)
                        f.write(response.content)
        return str(soup)

    @abstractmethod
    def get_body_html(self):
        pass

    def get_rc_by_article_id(self, article_id):
        for rc_link, rc in self.all_rcs.items():
            if rc.article_id == article_id:
                return rc

    def get_toc_html(self, body_html):
        toc_html = f'''
<article id="contents">
    <h1>{self.translate('table_of_contents')}</h1>
'''
        prev_toc_level = 0
        soup = BeautifulSoup(body_html, 'html.parser')
        done = {}
        heading_titles = [None, None, None, None, None, None]
        for header in soup.find_all(re.compile(r'^h\d'), {'class': 'section-header'}):
            toc_level = int(header.get('toc-level', header.name[1]))
            # Handle closing of ul/li tags or handle the opening of new ul tags
            if toc_level > prev_toc_level:
                for level in range(prev_toc_level, toc_level):
                    toc_html += '\n<ul>\n'
                    heading_titles[level] = None
            elif toc_level < prev_toc_level:
                toc_html += '\n</li>\n'
                for level in range(prev_toc_level, toc_level, -1):
                    toc_html += '</ul>\n</li>\n'
                    heading_titles[level-1] = None
            elif prev_toc_level > 0:
                toc_html += '\n</li>\n'
            if header.get('id'):
                article_id = header.get('id')
            else:
                parent = header.find_parent(['article', 'section'])
                article_id = parent.get('id')
            heading_titles[toc_level-1] = header.text
            if article_id and article_id not in done:
                rc = self.get_rc_by_article_id(article_id)
                if rc:
                    toc_title = rc.toc_title
                else:
                    toc_title = header.text
                toc_html += f'<li><a href="#{article_id}"><span>{toc_title}</span></a>\n'
                prev_toc_level = toc_level
                done[article_id] = True
                header_tag = soup.new_tag('span', **{'class': 'hidden heading-right'})
                header_tag.string = ' :: '.join(filter(None, heading_titles[1:toc_level]))
                # if len(header_tag.string) > 80:
                #     if toc_level >= 5:
                #         header_tag.string = ' :: '.join(filter(None, [heading_titles[1], '…'] +
                #                                                heading_titles[toc_level-2:toc_level]))
                #     elif toc_level == 4:
                #         header_tag.string = ' :: '.join([heading_titles[1], '…', heading_titles[toc_level - 1]])
                header.insert_before(header_tag)
        for level in range(prev_toc_level, 0, -1):
            toc_html += '</li>\n</ul>\n'
        toc_html += '</article>'
        return [str(soup), toc_html]

    def get_cover_html(self):
        if self.project_id:
            project_title_html = f'<h2 id="cover-project">{self.project_title}</h2>'
            version_title_html = f'<h3 id="cover-version">{self.translate("license.version")} {self.version}</h3>'
        else:
            project_title_html = ''
            version_title_html = f'<h2 id="cover-version">{self.translate("license.version")} {self.version}</h2>'
        cover_html = f'''
<article id="main-cover" class="cover">
    <img src="images/{self.main_resource.logo_file}" alt="UTN"/>
    <h1 id="cover-title">{self.title}</h1>
    {project_title_html}
    {version_title_html}
</article>
'''
        return cover_html

    def get_license_html(self):
        license_html = f'''
<article id="license">
    <h1>{self.translate('license.copyrights_and_licensing')}</h1>
'''
        for resource_name, resource in self.resources.items():
            title = resource.title
            version = resource.version
            publisher = resource.publisher
            issued = resource.issued

            license_html += f'''
    <div class="resource-info">
      <div class="resource-title"><strong>{title}</strong></div>
      <div class="resource-date"><strong>{self.translate('license.date')}:</strong> {issued}</div>
      <div class="resource-version"><strong>{self.translate('license.version')}:</strong> {version}</div>
      <div class="resource-publisher"><strong>{self.translate('license.published_by')}:</strong> {publisher}</div>
    </div>
'''
        license_file = os.path.join(self.main_resource.repo_dir, 'LICENSE.md')
        license_html += markdown2.markdown_path(license_file)
        license_html += '</article>'
        return license_html

    def get_contributors_html(self):
        contributors_html = '<section id="contributors" class="no-header">'
        for idx, resource_name in enumerate(self.resources.keys()):
            resource = self.resources[resource_name]
            contributors = resource.contributors
            contributors_list_classes = 'contributors-list'
            if len(contributors) > 10:
                contributors_list_classes += ' more-than-ten'
            elif len(contributors) > 4:
                contributors_list_classes += ' more-than-four'
            contributors_html += f'<div class="{contributors_list_classes}">'
            if idx == 0:
                contributors_html += f'<h1 class="section-header">{self.translate("contributors")}</h1>'
            if len(self.resources) > 1:
                contributors_html += f'<h2 id="{self.lang_code}-{resource_name}-contributors" class="section-header">{resource.title} {self.translate("contributors")}</h2>'
            for contributor in contributors:
                contributors_html += f'<div class="contributor">{contributor}</div>'
            contributors_html += '</div>'
        contributors_html += '</section>'
        return contributors_html

    @staticmethod
    def get_title_from_html(html):
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find(re.compile(r'^h\d'))
        if header:
            return header.text
        else:
            return "NO TITLE"

    @staticmethod
    def get_phrases_to_highlight(html, header_tag=None):
        phrases = []
        soup = BeautifulSoup(html, 'html.parser')
        if header_tag:
            headers = soup.find_all(header_tag)
        else:
            headers = soup.find_all(re.compile(r'^h[3-6]'))
        for header in headers:
            phrases.append(header.text)
        return phrases

    @staticmethod
    def highlight_text(text, phrase):
        parts = re.split(r'\s*…\s*|\s*\.\.\.\s*', phrase)
        processed_text = ''
        to_process_text = text
        for idx, part in enumerate(parts):
            if not part.strip():
                continue
            escaped_part = re.escape(part)
            if '<span' in text:
                split_pattern = '(' + re.sub('(\\\\ +)', r'(\\s+|(\\s*</*span[^>]*>\\s*)+)', escaped_part) + ')'
            else:
                split_pattern = '(' + escaped_part + ')'
            split_pattern += '(?![^<]*>)'  # don't match within HTML tags
            splits = re.split(split_pattern, to_process_text, 1)
            processed_text += splits[0]
            if len(splits) > 1:
                highlight_classes = "highlight"
                if len(parts) > 1:
                    highlight_classes += ' split'
                processed_text += f'<span class="{highlight_classes}">{splits[1]}</span>'
                if len(splits) > 2:
                    to_process_text = splits[-1]
                else:
                    to_process_text = ''
            else:
                to_process_text = ''
        if to_process_text:
            processed_text += to_process_text
        return processed_text

    def highlight_text_with_phrases(self, orig_text, phrases, rc, ignore=None):
        highlighted_text = orig_text
        phrases.sort(key=len, reverse=True)
        for phrase in phrases:
            new_highlighted_text = self.highlight_text(highlighted_text, phrase)
            if new_highlighted_text != highlighted_text:
                highlighted_text = new_highlighted_text
            elif not ignore or phrase.lower() not in ignore:
                # This is just to determine the fix for any terms that differ in curly/straight quotes
                bad_highlights = OrderedDict({phrase: None})
                alt_phrase = [
                    # All curly quotes made straight
                    phrase.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                    # All straight quotes made curly, first single and double pointing right
                    phrase.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                    # All curly double quotes made straight
                    phrase.replace('“', '"').replace('”', '"'),
                    # All straight double quotes made curly with first pointing right
                    phrase.replace('"', '”').replace('”', '“', 1),
                    # All straight single quotes made curly with first pointing right
                    phrase.replace("'", '’').replace('’', '‘', 1),
                    # All straight single quotes made straight (all point left)
                    phrase.replace("'", '’'),
                    # All left pointing curly single quotes made straight
                    phrase.replace('’', "'"),
                    # All right pointing curly single quotes made straight
                    phrase.replace('‘', "'")]
                for alt_phrase in alt_phrase:
                    if orig_text != self.highlight_text(orig_text, alt_phrase):
                        bad_highlights[phrase] = alt_phrase
                        break
                self.add_bad_highlight(rc, orig_text, bad_highlights)
        return highlighted_text

    @staticmethod
    def increase_headers(html, increase_depth=1):
        if html:
            for level in range(5, 0, -1):
                new_level = level + increase_depth
                if new_level > 6:
                    new_level = 6
                html = re.sub(rf'<h{level}([^>]*)>\s*(.+?)\s*</h{level}>', rf'<h{new_level}\1>\2</h{new_level}>',
                              html, flags=re.MULTILINE)
        return html

    @staticmethod
    def make_first_header_section_header(html):
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find(re.compile(r'^h\d'))
        if header:
            header['class'] = header.get('class', []) + ['section-header']
        return str(soup)

    @staticmethod
    def decrease_headers(html, minimum_header=2, decrease=1):
        if html:
            if minimum_header < 2:
                minimum_header = 2
            for level in range(minimum_header, 6):
                new_level = level - decrease
                if new_level < 1:
                    new_level = 1
                html = re.sub(rf'<h{level}([^>]*)>\s*(.+?)\s*</h{level}>', rf'<h{new_level}\1>\2</h{new_level}>', html,
                              flags=re.MULTILINE)
        return html

    def replace(self, m):
        before = m.group(1)
        rc_link = m.group(2)
        after = m.group(3)
        if rc_link not in self.all_rcs:
            return m.group()
        rc = self.all_rcs[rc_link]
        if (before == '[[' and after == ']]') or (before == '(' and after == ')') or before == ' ' \
                or (before == '>' and after == '<'):
            return f'<a href="#{rc.article_id}">{rc.title}</a>'
        if (before == '"' and after == '"') or (before == "'" and after == "'"):
            return f'#{rc.article_id}'
        self.logger.error(f'FOUND SOME MALFORMED RC LINKS: {m.group()}')
        return m.group()

    def replace_rc(self, match):
        # Replace rc://... rc links according to self.resource_data:
        # Case 1: RC links in double square brackets that need to be converted to <a> elements with articles title:
        #   e.g. [[rc://en/tw/help/bible/kt/word]] => <a href="#tw-kt-word">God's Word</a>
        # Case 2: RC link already in an <a> tag's href, thus preserve its text
        #   e.g. <a href="rc://en/tw/help/bible/kt/word">text</a> => <a href="#tw-kt-word>Text</a>
        # Case 3: RC link without square brackets not in <a> tag's href:
        #   e.g. rc://en/tw/help/bible/kt/word => <a href="#tw-kt-word">God's Word</a>
        # Case 4: RC link for was not referenced by the main content (exists due to a secondary resource referencing it)
        #   e.g. <a href="rc://en/tw/help/bible/names/horeb">Horeb Mountain</a> => Horeb Mountain
        #   e.g. [[rc://en/tw/help/bible/names/horeb]] => Horeb
        # Case 5: Remove other links to resources without text (they weren't directly reference by main content)
        left = match.group(1)
        rc_link = match.group(2)
        right = match.group(3)
        title = match.group(4)
        if rc_link in self.all_rcs:
            rc = self.all_rcs[rc_link]
            if (left == '[[' and right == ']]') or (not left and not right):
                # Only if it is a main article or is in the appendix
                if rc.linking_level <= APPENDIX_LINKING_LEVEL:
                    # Case 1 and Case 3
                    return f'<a href="#{rc.article_id}">{rc.title}</a>'
                else:
                    # Case 4:
                    return rc.title
            else:
                if rc.linking_level <= APPENDIX_LINKING_LEVEL:
                    # Case 3, left = `<a href="` and right = `">[text]</a>`
                    return left + '#' + rc.article_id + right
                else:
                    # Case 4
                    return title if title else rc.title
        # Case 5
        return title if title else rc_link

    def replace_rc_links(self, text):
        regex = re.compile(r'(\[\[|<a[^>]+href=")*(rc://[/A-Za-z0-9*_-]+)(\]\]|"[^>]*>(.*?)</a>)*')
        text = regex.sub(self.replace_rc, text)
        return text

    @staticmethod
    def _fix_links(html):
        # Change [[http.*]] to <a href="http\1">http\1</a>
        html = re.sub(r'\[\[http([^\]]+)\]\]', r'<a href="http\1">http\1</a>', html, flags=re.IGNORECASE)

        # convert URLs to links if not already
        html = re.sub(r'([^">])((http|https|ftp)://[A-Za-z0-9/?&_.:=#-]+[A-Za-z0-9/?&_:=#-])',
                      r'\1<a href="\2">\2</a>', html, flags=re.IGNORECASE)

        # URLS wth just www at the start, no http
        html = re.sub(r'([^/])(www\.[A-Za-z0-9/?&_.:=#-]+[A-Za-z0-9/?&_:=#-])', r'\1<a href="http://\2">\2</a>',
                      html, flags=re.IGNORECASE)

        return html

    def fix_links(self, html):
        # can be implemented by child class
        return html

    def get_appendix_rcs(self):
        for rc_link, rc in self.rcs.items():
            self.crawl_ta_tw_deep_linking(rc)

    def crawl_ta_tw_deep_linking(self, source_rc: ResourceContainerLink):
        if not source_rc.article or source_rc.linking_level > APPENDIX_LINKING_LEVEL + 1:
            return
        # get all rc links. the "?:" in the regex means to not leave the (ta|tw) match in the result
        rc_links = re.findall(r'rc://[A-Z0-9_*-]+/(?:ta|tw)/[A-Z0-9/_*-]+', source_rc.article, flags=re.IGNORECASE | re.MULTILINE)
        for rc_link in rc_links:
            if rc_link in self.rcs or rc_link in self.appendix_rcs:
                rc = self.rcs[rc_link] if rc_link in self.rcs else self.appendix_rcs[rc_link]
                if rc.linking_level > source_rc.linking_level + 1:
                    rc.linking_level = source_rc.linking_level + 1
                rc.add_reference(source_rc)
                continue
            rc = self.add_appendix_rc(rc_link, linking_level=source_rc.linking_level+1)
            if rc.resource not in self.resources:
                # We don't have this resource in our list of resources, so adding
                resource = Resource(resource_name=rc.resource, repo_name=f'{self.lang_code}_{rc.resource}',
                                    owner=self.main_resource.owner)
                self.setup_resource(resource)
            rc.add_reference(source_rc)
            if not rc.article:
                if rc.resource == 'ta':
                    self.get_ta_article_html(rc, source_rc)
                elif rc.resource == 'tw':
                    self.get_tw_article_html(rc, source_rc)
                if rc.article:
                    self.crawl_ta_tw_deep_linking(rc)
                else:
                    self.add_bad_link(source_rc, rc.rc_link)
                    del self.appendix_rcs[rc.rc_link]

    def get_appendix_html(self, resource):
        self.logger.info(f'Generating {resource.resource_name} appendix html...')
        html = ''
        filtered_rcs = dict(filter(lambda x: x[1].resource == resource.resource_name and
                                   x[1].linking_level == APPENDIX_LINKING_LEVEL,
                            self.appendix_rcs.items()))
        sorted_rcs = sorted(filtered_rcs.items(), key=lambda x: x[1].title.lower())
        for item in sorted_rcs:
            rc = item[1]
            if rc.article:
                html += rc.article.replace('</article>', self.get_go_back_to_html(rc) + '</article>')
        if html:
            html = f'''
<section id="{self.lang_code}-{resource.resource_name}-appendix-cover">
    <div class="resource-title-page">
        <h1 class="section-header">{resource.title}</h1>
    </div>
    {html}
</section>
'''
        return html

    def get_ta_article_html(self, rc, source_rc, config=None, toc_level=2):
        if not config:
            config_file = os.path.join(self.resources[rc.resource].repo_dir, rc.project, 'config.yaml')
            config = yaml.full_load(read_file(config_file))
        article_dir = os.path.join(self.resources[rc.resource].repo_dir, rc.project, rc.path)
        article_file = os.path.join(article_dir, '01.md')
        if os.path.isfile(article_file):
            article_file_html = markdown2.markdown_path(article_file, extras=['markdown-in-html', 'tables'])
        else:
            self.logger.error("NO FILE AT {0}".format(article_file))
            if os.path.isdir(article_dir):
                if not os.path.isfile(article_file):
                    self.add_bad_link(source_rc, rc.rc_link, '[dir exists but no 01.md file]')
                else:
                    self.add_bad_link(source_rc, rc.rc_link, '[01.md file exists but no content]')
            else:
                self.add_bad_link(source_rc, rc.rc_link, '[no corresponding article found]')
            return
        top_box = ''
        bottom_box = ''
        question = ''
        dependencies = ''
        recommendations = ''

        title = rc.title
        if not title:
            title_file = os.path.join(article_dir, 'title.md')
            title = read_file(title_file)
            rc.set_title(title)

        question_file = os.path.join(article_dir, 'sub-title.md')
        if os.path.isfile(question_file):
            question = f'''
        <div class="ta-question">
            {self.translate('this_page_answers_the_question')}: <em>{read_file(question_file)}<em>
        </div>
'''
        if rc.path in config:
            if 'dependencies' in config[rc.path] and config[rc.path]['dependencies']:
                lis = ''
                for dependency in config[rc.path]['dependencies']:
                    dep_project = rc.project
                    for project in self.resources['ta'].projects:
                        dep_article_dir = os.path.join(self.resources['ta'].repo_dir, project['identifier'], dependency)
                        if os.path.isdir(dep_article_dir):
                            dep_project = project['identifier']
                    lis += f'''
                    <li>[[rc://{self.lang_code}/ta/man/{dep_project}/{dependency}]]</li>
'''
                dependencies += f'''
        <div class="ta-dependencies">
            {self.translate('in_order_to_understand_this_topic')}:
            <ul>
                {lis}
            </ul>
        </div>
'''
            if 'recommended' in config[rc.path] and config[rc.path]['recommended']:
                lis = ''
                for recommended in config[rc.path]['recommended']:
                    rec_project = rc.project
                    rec_article_dir = os.path.join(self.resources['ta'].repo_dir, rec_project, recommended)
                    if not os.path.exists(rec_article_dir):
                        for project in self.resources['ta'].projects:
                            rec_article_dir = os.path.join(self.resources['ta'].repo_dir, project['identifier'], recommended)
                            if os.path.isdir(rec_article_dir):
                                rec_project = project['identifier']
                                break
                    if not os.path.exists(rec_article_dir):
                        self.add_bad_link(rc, f'{rc.project}/config.yaml:::{rc.path}:::recommended:::{recommended}')
                        continue
                    lis += f'''
                    <li>[[rc://{self.lang_code}/ta/man/{rec_project}/{recommended}]]</li>
'''
                recommendations = f'''
            <div class="ta-recommendations">
                {self.translate('next_we_recommend_you_learn_about')}:
                <ul>
                    {lis}
                </ul>
            </div>
'''

        if question or dependencies:
            top_box = f'''
    <div class="top-box box">
        {question}
        {dependencies}
    </div>
'''
        if recommendations:
            bottom_box = f'''
    <div class="bottom-box box">
        {recommendations}
    </div>
'''
        article_html = f'''
<article id="{rc.article_id}">
    <h{toc_level} class="section-header" toc-level="{toc_level}">{rc.title}</h{toc_level}>
    {top_box}
    {article_file_html}
    {bottom_box}
</article>'''
        article_html = self.fix_ta_links(article_html, rc.project)
        rc.set_article(article_html)

    def get_go_back_to_html(self, source_rc):
        if source_rc.linking_level == 0:
            return ''
        references = []
        for rc_link in source_rc.references:
            if rc_link in self.rcs:
                rc = self.rcs[rc_link]
                references.append(f'<a href="#{rc.article_id}">{rc.title}</a>')
        go_back_to_html = ''
        if len(references):
            references_str = '; '.join(references)
            go_back_to_html = f'''
    <div class="go-back-to">
        (<strong>{self.translate('go_back_to')}:</strong> {references_str})
    </div>
'''
        return go_back_to_html

    def fix_ta_links(self, text, project):
        text = re.sub(r'href="\.\./([^/"]+)/01\.md"', rf'href="rc://{self.lang_code}/ta/man/{project}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./\.\./([^/"]+)/([^/"]+)/01\.md"', rf'href="rc://{self.lang_code}/ta/man/\1/\2"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="([^# :/"]+)"', rf'href="rc://{self.lang_code}/ta/man/{project}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text

    def get_tw_article_html(self, rc, source_rc=None):
        file_path = os.path.join(self.resources[rc.resource].repo_dir, rc.project, f'{rc.path}.md')
        fix = None
        if not os.path.exists(file_path):
            bad_names = {
                'live': 'bible/kt/life'
            }
            if rc.extra_info[-1] in bad_names:
                path2 = bad_names[rc.extra_info[-1]]
            elif rc.path.startswith('bible/other/'):
                path2 = re.sub(r'^bible/other/', r'bible/kt/', rc.path)
            else:
                path2 = re.sub(r'^bible/kt/', r'bible/other/', rc.path)
            fix = 'rc://{0}/tw/dict/{1}'.format(self.lang_code, path2)
            file_path = os.path.join(self.resources[rc.resource].repo_dir, rc.project, f'{path2}.md')
        if os.path.isfile(file_path):
            if fix:
                self.add_bad_link(source_rc, rc.rc_link, fix)
            tw_article_html = markdown2.markdown_path(file_path)
            tw_article_html = self.make_first_header_section_header(tw_article_html)
            tw_article_html = self.increase_headers(tw_article_html)
            tw_article_html = self.fix_tw_links(tw_article_html, rc.extra_info[0])
            tw_article_html = f'''                
<article id="{rc.article_id}">
    {tw_article_html}
</article>
'''
            rc.set_title(self.get_title_from_html(tw_article_html))
            rc.set_article(tw_article_html)
        else:
            if source_rc.rc_link not in self.bad_links:
                self.bad_links[source_rc.rc_link] = {}
            if rc.rc_link not in self.bad_links[source_rc.rc_link]:
                self.bad_links[source_rc.rc_link][rc.rc_link] = None

    def fix_tw_links(self, text, group):
        text = re.sub(r'href="\.\./([^/)]+?)(\.md)*"', rf'href="rc://{self.lang_code}/tw/dict/bible/{group}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^)]+?)(\.md)*"', rf'href="rc://{self.lang_code}/tw/dict/bible/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'(\(|\[\[)(\.\./)*(kt|names|other)/([^)]+?)(\.md)*(\)|\]\])(?!\[)',
                      rf'[[rc://{self.lang_code}/tw/dict/bible/\3/\4]]', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text


def run_converter(resource_names: List[str], pdf_converter_class: Type[PdfConverter]):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang_code', dest='lang_codes', required=False, help='Language Code(s)',
                        action='append')
    parser.add_argument('-p', '--project_id', dest='project_ids', required=False, help='Project ID(s)', action='append')
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('-r', '--regenerate', dest='regenerate', action='store_true',
                        help='Regenerate PDF even if exists')
    for resource_name in resource_names:
        parser.add_argument(f'--{resource_name}-tag', dest=resource_name, default=DEFAULT_TAG, required=False)

    args = parser.parse_args(sys.argv[1:])
    lang_codes = args.lang_codes
    project_ids = args.project_ids
    working_dir = args.working_dir
    output_dir = args.output_dir
    owner = args.owner
    regenerate = args.regenerate
    if not lang_codes:
        lang_codes = [DEFAULT_LANG_CODE]
    if not project_ids:
        project_ids = [None]

    resources = Resources()
    for lang_code in lang_codes:
        for project_id in project_ids:
            for resource_name in resource_names:
                repo_name = f'{lang_code}_{resource_name}'
                tag = getattr(args, resource_name)
                resource = Resource(resource_name=resource_name, repo_name=repo_name, tag=tag, owner=owner)
                resources[resource_name] = resource
            converter = pdf_converter_class(resources=resources, project_id=project_id, working_dir=working_dir,
                                            output_dir=output_dir, lang_code=lang_code, regenerate=regenerate)
            project_id_str = f'_{project_id}' if project_id else ''
            converter.logger.info(f'Starting PDF Converter for {resources.main.repo_name}_{resources.main.tag}{project_id_str}...')
            converter.run()
