#!/usr/bin/env python3
#
#  Copyright (c) 2019 unfoldingWord
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
from typing import List, Type
from bs4 import BeautifulSoup
from abc import abstractmethod
from weasyprint import HTML, LOGGER
from .resource import Resource, Resources
from ..general_tools.file_utils import write_file, load_json_object

DEFAULT_LANG_CODE = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
LANGUAGE_FILES = {
    'fr': 'French-fr_FR.json',
    'en': 'English-en_US.json'
}


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

        self.bad_links = {}
        self.resource_data = {}
        self.rc_references = {}

        self.images_dir = None
        self.save_dir = None
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
    def file_id(self):
        project_id_str = f'_{self.project_id}' if self.project_id else ''
        return f'{self.lang_code}_{self.name}{project_id_str}_{self.main_resource.tag}_{self.main_resource.commit}'

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

    def run(self):
        self.setup_dirs()
        self.setup_resource_files()

        self.html_file = os.path.join(self.output_dir, f'{self.file_id}.html')
        self.pdf_file = os.path.join(self.output_dir, f'{self.file_id}.pdf')

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

        self.images_dir = os.path.join(self.output_dir, 'images')
        if not os.path.isdir(self.images_dir):
            os.makedirs(self.images_dir)

        self.save_dir = os.path.join(self.output_dir, 'save')
        if not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir)

        css_path = os.path.join(self.converters_dir, 'templates/css')
        subprocess.call(f'ln -sf "{css_path}" "{self.output_dir}"', shell=True)

    def setup_logging_to_file(self):
        LOGGER.setLevel('INFO')  # Set to 'INFO' for debugging
        logger_handler = logging.FileHandler(os.path.join(self.output_dir, f'{self.file_id}_logger.log'))
        self.logger.addHandler(logger_handler)
        logger_handler = logging.FileHandler(os.path.join(self.output_dir, f'{self.file_id}_weasyprint.log'))
        LOGGER.addHandler(logger_handler)

    def generate_html(self):
        if self.regenerate or not os.path.exists(self.html_file):
            self.logger.info(f'Creating HTML file for {self.file_id}...')

            self.logger.info('Generating cover page HTML...')
            cover_html = self.get_cover_html()

            self.logger.info('Generating license page HTML...')
            license_html = self.get_license_html()

            self.logger.info('Generating body HTML...')
            body_html = self.get_body_html()
            self.logger.info('Fixing links in body HTML...')
            body_html = self.fix_links(body_html)
            body_html = self._fix_links(body_html)
            self.logger.info('Replacing RC links in body HTML...')
            body_html = self.replace_rc_links(body_html)
            self.logger.info('Generating Contributors HTML...')
            body_html += self.get_contributors_html()
            self.logger.info('Generating TOC HTML...')
            body_html = self.get_body_with_toc_html(body_html)
            body_html = self.download_all_images(body_html)

            with open(os.path.join(self.converters_dir, 'templates/template.html')) as template_file:
                html_template = string.Template(template_file.read())
            title = f'{self.title} - v{self.version}'
            link = ''
            personal_styles_file = os.path.join(self.output_dir, f'css/{self.name}_style.css')
            if os.path.isfile(personal_styles_file):
                link = f'<link href="css/{self.name}_style.css" rel="stylesheet">'
            body = '\n'.join([cover_html, license_html, body_html])
            html = html_template.safe_substitute(title=title, link=link, body=body)
            write_file(self.html_file, html)

            self.save_resource_data()
            self.save_bad_links_html()
            self.logger.info('Generated HTML file.')
        else:
            self.logger.info(f'HTML file {self.html_file} is already there. Not generating. Use -r to force regeneration.')

    def generate_pdf(self):
        if self.regenerate or not os.path.exists(self.pdf_file):
            self.logger.info(f'Generating PDF file {self.pdf_file}...')
            weasy = HTML(filename=self.html_file, base_url=f'file://{self.output_dir}/')
            weasy.write_pdf(self.pdf_file)
            self.logger.info('Generated PDF file.')
            self.logger.info(f'PDF file located at {self.pdf_file}')
            link_file_name = '_'.join(self.file_id.split('_')[0:-1]) + '.pdf'
            link_file_path = os.path.join(self.output_dir, link_file_name)
            subprocess.call(f'ln -sf "{self.pdf_file}" "{link_file_path}"', shell=True)
        else:
            self.logger.info(
                f'PDF file {self.pdf_file} is already there. Not generating. Use -r to force regeneration.')

    def save_bad_links_html(self):
        pass

    def setup_resource_files(self):
        for resource_name, resource in self.resources.items():
            resource.clone(self.working_dir)
            self.generation_info[resource.repo_name] = {'tag': resource.tag, 'commit': resource.commit}
            logo_path = os.path.join(self.images_dir, f'{resource.resource_name}.png')
            if not os.path.isfile(logo_path):
                command = f'curl -o "{logo_path}" {resource.get_logo_url()}'
                subprocess.call(command, shell=True)

    def determine_if_regeneration_needed(self):
        # check if any commit hashes have changed
        old_info = self.get_previous_generation_info()
        if not old_info:
            self.logger.info(f'Looks like this is a new commit of {self.file_id}. Generating PDF.')
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
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        save_file = os.path.join(self.save_dir, f'{self.file_id}_resource_data.json')
        write_file(save_file, self.resource_data)
        save_file = os.path.join(self.save_dir, f'{self.file_id}_references.json')
        write_file(save_file, self.rc_references)
        save_file = os.path.join(self.save_dir, f'{self.file_id}_bad_links.json')
        write_file(save_file, self.bad_links)
        save_file = os.path.join(self.save_dir, f'{self.file_id}_generation_info.json')
        write_file(save_file, self.generation_info)

    def get_previous_generation_info(self):
        save_file = os.path.join(self.save_dir, f'{self.file_id}_generation_info.json')
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

    def get_rc_info_by_link(self, link):
        for rc, rc_info in self.rc_references.items():
            if 'link' in rc_info and rc_info['link'] == link:
                return rc_info

    def get_body_with_toc_html(self, html):
        toc_html = f'''
<article id="contents">
    <h1>{self.translate('table_of_contents')}</h1>
'''
        current_level = 0
        count = 0
        soup = BeautifulSoup(html, 'html.parser')
        for header in soup.find_all(re.compile(r'^h\d'), {'class': 'section-header'}):
            level = int(header.name[1])
            # Handle closing of ul/li tags or handle the opening of new ul tags
            if level > current_level:
                for l in range(current_level, level):
                    toc_html += '\n<ul>\n'
            elif level < current_level:
                toc_html += '\n</li>\n'
                for l in range(current_level, level, -1):
                        toc_html += '</ul>\n</li>\n'
            elif current_level > 0:
                toc_html += '\n</li>\n'

            if header.get('id'):
                link = f'#{id}'
            else:
                parent = header.find_parent(['section', 'article'])
                if parent and parent.get('id'):
                    link = f'#{parent.get("id")}'
                else:
                    header_id = f'article-{count}'
                    count += 1
                    header['id'] = header_id
                    link = f'#{header_id}'
            title = header.text
            rc_info = self.get_rc_info_by_link(link)
            if rc_info and 'toc_title' in rc_info:
                title = rc_info['toc_title']
            toc_html += f'<li>\n<a href="{link}"><span>{title}</span></a>\n'
            current_level = level
        for l in range(current_level, 0, -1):
            toc_html += '</li>\n</ul>\n'
        toc_html += '</article>'
        return toc_html + str(soup)

    def get_cover_html(self):
        if self.project_id:
            project_title_html = f'<h2 id="cover-project">{self.project_title}</h2>'
            version_title_html = f'<h3 id="cover-version">{self.translate("license.version")} {self.version}</h3>'
        else:
            project_title_html = ''
            version_title_html = f'<h2 id="cover-version">{self.translate("license.version")} {self.version}</h2>'
        cover_html = f'''
<article id="main-cover" class="cover">
    <img src="images/{self.main_resource.logo}.png" alt="UTN"/>
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
            manifest = resource.manifest
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
                title = resource.title
                contributors_html += f'<h2>{title} {self.translate("contributors")}</h2>'
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
            if '<span' in text:
                split_pattern = '(' + re.sub(' +', r'(\\s+|(\\s*</*span[^>]*>\\s*)+)', part) + ')'
            else:
                split_pattern = '(' + part + ')'
            split_pattern += '(?![^<]*>)'  # don't match within HTML tags
            self.logger.info(f'SPLIT PATTER: {split_pattern}')
            splits = re.split(split_pattern, to_process_text, 1)
            processed_text += splits[0]
            if len(splits) > 1:
                highlight_classes = "highlight"
                if len(parts) > 1:
                    highlight_classes += ' split'
                processed_text += f'<span class="{highlight_classes}">{splits[1]}</span>'
                if len(splits) > 2:
                    to_process_text = splits[-1]
        if to_process_text:
            processed_text += to_process_text
        return processed_text

    def highlight_text_with_phrases(self, orig_text, phrases, rc, ignore=[]):
        highlighted_text = orig_text
        phrases.sort(key=len, reverse=True)
        for phrase in phrases:
            new_highlighted_text = self.highlight_text(highlighted_text, phrase)
            if new_highlighted_text != highlighted_text:
                highlighted_text = new_highlighted_text
            elif not ignore or phrase not in ignore:
                if rc not in self.bad_links:
                    self.bad_links[rc] = {
                        'text': orig_text,
                        'notes': []
                    }
                bad_note = {phrase: None}
                alt_phrase = [
                    phrase.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                    phrase.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                    phrase.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                    phrase.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                    phrase.replace('“', '"').replace('”', '"'),
                    phrase.replace('"', '”').replace('”', '“', 1),
                    phrase.replace("'", '’').replace('’', '‘', 1),
                    phrase.replace("'", '’'),
                    phrase.replace('’', "'"),
                    phrase.replace('‘', "'")]
                for alt_phrase in alt_phrase:
                    if orig_text != self.highlight_text(orig_text, alt_phrase):
                        bad_note[phrase] = alt_phrase
                        break
                self.bad_links[rc]['notes'].append(bad_note)
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

    @staticmethod
    def get_first_header(text):
        lines = text.split('\n')
        if len(lines):
            for line in lines:
                if re.match(r'<h1>', line):
                    return re.sub(r'<h1>(.*?)</h1>', r'\1', line)
            return lines[0]
        return "NO TITLE"

    def replace(self, m):
        before = m.group(1)
        rc = m.group(2)
        after = m.group(3)
        if rc not in self.resource_data:
            return m.group()
        info = self.resource_data[rc]
        if (before == '[[' and after == ']]') or (before == '(' and after == ')') or before == ' ' \
                or (before == '>' and after == '<'):
            return f'<a href="{info["link"]}">{info["title"]}</a>'
        if (before == '"' and after == '"') or (before == "'" and after == "'"):
            return info['link']
        self.logger.error(f'FOUND SOME MALFORMED RC LINKS: {m.group()}')
        return m.group()

    def replace_rc_links(self, html):
        # Change rc://... rc links to proper HTML links based on that links title and link to its article
        if self.lang_code != DEFAULT_LANG_CODE:
            html = re.sub('rc://en', f'rc://{self.lang_code}', html, flags=re.IGNORECASE)
        joined = '|'.join(map(re.escape, self.resource_data.keys()))
        pattern = r'(\[\[|\(|["\']| |>|)\b(' + joined + r')\b(\]\]|\)|["\']|<|)(?!\]\)")'

        html = re.sub(pattern, self.replace, html, flags=re.IGNORECASE)
        # Remove other scripture reference not in this SN
        html = re.sub(r'<a[^>]+rc://[^>]+>([^>]+)</a>', r'\1', html, flags=re.IGNORECASE | re.MULTILINE)
        return html

    @staticmethod
    def _fix_links(html):
        # Change [[http.*]] to <a href="http\1">http\1</a>
        html = re.sub(r'\[\[http([^\]]+)\]\]', r'<a href="http\1">http\1</a>', html, flags=re.IGNORECASE)

        # convert URLs to links if not already
        html = re.sub(r'([^">])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])',
                      r'\1<a href="\2">\2</a>', html, flags=re.IGNORECASE)

        # URLS wth just www at the start, no http
        html = re.sub(r'([^\/])(www\.[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])', r'\1<a href="http://\2">\2</a>',
                      html, flags=re.IGNORECASE)

        return html

    def fix_links(self, html):
        # could be implemented by child class
        return html


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
                resource = Resource(resource_name=resource_name, repo_name=repo_name, tag=tag, owner=owner, logo='obs')
                resources[resource_name] = resource
            converter = pdf_converter_class(resources=resources, project_id=project_id, working_dir=working_dir,
                                            output_dir=output_dir, lang_code=lang_code, regenerate=regenerate)
            project_id_str = f'_{project_id}' if project_id else ''
            converter.logger.info(f'Starting PDF Converter for {resources.main.repo_name}_{resources.main.tag}{project_id_str}...')
            converter.run()
