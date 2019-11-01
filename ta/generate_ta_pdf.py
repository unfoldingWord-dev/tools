#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF documents for tA
"""
from __future__ import unicode_literals, print_function
import os
import sys
import re
import logging
import argparse
import tempfile
import shutil
import subprocess
import json
import git
import markdown2
import string
import codecs
from glob import glob
from shutil import copy
from bs4 import BeautifulSoup
from ..general_tools.file_utils import write_file, read_file, load_yaml_object, get_files
from ..general_tools.url_utils import get_url, download_file
from ResourceContainer import RC

_print = print
DEFAULT_LANG = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'

OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']


def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


class TaProcessor:
    manual_title_map = {
        'checking': 'Checking Manual',
        'intro': 'Introduction to unfoldingWord® Translation Academy',
        'process': 'Process Manual',
        'translate': 'Translation Manual'
    }
    ignoreDirectories = ['.git', '00']
    ignoreFiles = ['.DS_Store', 'reference.txt', 'title.txt', 'LICENSE.md', 'README.md']

    def __init__(self, rc, source_dir, output_dir):
        """
        :param RC rc:
        :param string source_dir:
        :param string output_dir:
        """
        self.rc = rc
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.section_container_id = 1
        self.titles = {}
        self.bad_links = {}

    def run(self):
        for idx, project in enumerate(self.rc.projects):
            project_path = os.path.join(self.source_dir, project.path)

            files = glob(os.path.join(project_path, '*.{0}'.format(self.rc.resource.file_ext)))
            if len(files):
                for file_path in files:
                    output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                    if os.path.isfile(file_path) and not os.path.exists(output_file_path) \
                            and os.path.basename(file_path) not in self.ignoreFiles:
                        copy(file_path, output_file_path)
        return True

    def get_title(self, project, link, alt_title=None):
        proj = None
        if link in project.config():
            proj = project
        else:
            for p in self.rc.projects:
                if link in p.config():
                    proj = p
        if proj:
            title_file = os.path.join(self.source_dir, proj.path, link, 'title.md')
            if os.path.isfile(title_file):
                return read_file(title_file)
        if alt_title:
            return alt_title
        else:
            return link.replace('-', ' ').title()

    def get_ref(self, project, link):
        if link in project.config():
            return '#{0}'.format(link)
        for p in self.rc.projects:
            if link in p.config():
                return '{0}.html#{1}'.format(p.identifier, link)
        return '#{0}'.format(link)

    def get_question(self, project, slug):
        subtitle_file = os.path.join(self.source_dir, project.path, slug, 'sub-title.md')
        if os.path.isfile(subtitle_file):
            return read_file(subtitle_file)

    def get_content(self, project, slug):
        content_file = os.path.join(self.source_dir, project.path, slug, '01.md')
        if os.path.isfile(content_file):
            return read_file(content_file)

    def compile_section(self, project, section, level):
        """
        Recursive section markdown creator

        :param project:
        :param dict section:
        :param int level:
        :return:
        """
        if 'link' in section:
            link = section['link']
        else:
            link = 'section-container-{0}'.format(self.section_container_id)
            self.section_container_id = self.section_container_id + 1
        title = self.get_title(project, link, section['title'])
        markdown = markdown = '{0} <a id="{1}"/>{2}\n\n'.format('#' * level, link, title)
        if 'link' in section:
            top_box = ""
            bottom_box = ""
            question = self.get_question(project, link)
            if question:
                top_box += 'This page answers the question: *{0}*\n\n'.format(question)
            config = project.config()
            if link in config:
                if 'dependencies' in config[link] and config[link]['dependencies']:
                    top_box += 'In order to understand this topic, it would be good to read:\n\n'
                    for dependency in config[link]['dependencies']:
                        top_box += '  * *[{0}]({1})*\n'.\
                            format(self.get_title(project, dependency), self.get_ref(project, dependency))
                if 'recommended' in config[link] and config[link]['recommended']:
                    bottom_box += 'Next we recommend you learn about:\n\n'
                    for recommended in config[link]['recommended']:
                        bottom_box += '  * *[{0}]({1})*\n'.\
                            format(self.get_title(project, recommended), self.get_ref(project, recommended))
            if top_box:
                markdown += '<div class="top-box box" markdown="1">\n{0}\n</div>\n\n'.format(top_box)
            content = self.get_content(project, link)
            if content:
                markdown += '{0}\n\n'.format(content)
            else:
                bad_link = '{0}/{1}'.format(project.identifier, link)
                content_file = os.path.join(self.source_dir, project.identifier, link, '01.md')
                if os.path.isdir(os.path.join(self.source_dir, bad_link)):
                    if not os.path.isfile(content_file):
                        self.bad_links[bad_link] = '[dir exists but no 01.md file]'
                    elif len(read_file(content_file)):
                        self.bad_links[bad_link] = '[01.md file exists but no content]'
                elif 'title' in section and section['title'] in self.titles:
                    self.bad_links[bad_link] = ' or '.join(self.titles[section['title']])
                else:
                    self.bad_links[bad_link] = '[no corresponding article found]'
            if bottom_box:
                markdown += '<div class="bottom-box box" markdown="1">\n{0}\n</div>\n\n'.format(bottom_box)
            markdown += '---\n\n'  # horizontal rule
        if 'sections' in section:
            for subsection in section['sections']:
                markdown += self.compile_section(project, subsection, level + 1)
        return markdown

    def get_titles(self, project):
        titles = {}
        project_path = os.path.join(self.source_dir, project)
        for dirname in sorted(glob(os.path.join(project_path, '*'))):
            if (os.path.isdir(dirname) and os.path.isfile(os.path.join(dirname, 'title.md'))):
                title = read_file(os.path.join(dirname, 'title.md'))
                if title not in titles:
                    titles[title] = []
                titles[title].append(os.path.basename(dirname))
        return titles

    def run(self):
        for idx, project in enumerate(self.rc.projects):
            self.titles = self.get_titles(project.identifier)
            self.section_container_id = 1
            toc = self.rc.toc(project.identifier)
            if project.identifier in self.manual_title_map:
                title = self.manual_title_map[project.identifier]
            else:
                title = '{0} Manual'.format(project.identifier.title())
            markdown = '# {0}\n\n'.format(title)
            for section in toc['sections']:
                markdown += self.compile_section(project, section, 2)
            markdown = self.fix_links(markdown)
            output_file = os.path.join(self.output_dir, '{0}-{1}.md'.format(str(idx+1).zfill(2), project.identifier))
            write_file(output_file, markdown)

            # Copy the toc and config.yaml file to the output dir so they can be used to
            # generate the ToC on live.door43.org
            toc_file = os.path.join(self.source_dir, project.path, 'toc.yaml')
            if os.path.isfile(toc_file):
                copy(toc_file, os.path.join(self.output_dir, '{0}-{1}-toc.yaml'.format(str(idx+1).zfill(2),
                                                                                       project.identifier)))
            config_file = os.path.join(self.source_dir, project.path, 'config.yaml')
            if os.path.isfile(config_file):
                copy(config_file, os.path.join(self.output_dir, '{0}-{1}-config.yaml'.format(str(idx+1).zfill(2), project.identifier)))
        self.print_bad_links()
        return True

    def print_bad_links(self):
        for link in sorted(self.bad_links.keys()):
            if self.bad_links[link]:
                _print("{0} => {1}".format(link, self.bad_links[link]))

    def fix_links(self, content):
        # convert RC links, e.g. rc://en/tn/help/1sa/16/02 => https://git.door43.org/Door43/en_tn/1sa/16/02.md
        content = re.sub(r'rc://([^/]+)/([^/]+)/([^/]+)/([^\s\p{P})\]\n$]+)',
                         r'https://git.door43.org/Door43/\1_\2/src/master/\4.md', content, flags=re.IGNORECASE)
        # fix links to other sections within the same manual (only one ../ and a section name)
        # e.g. [Section 2](../section2/01.md) => [Section 2](#section2)
        content = re.sub(r'\]\(\.\./([^/)]+)/01.md\)', r'](#\1)', content)
        # fix links to other manuals (two ../ and a manual name and a section name)
        # e.g. [how to translate](../../translate/accurate/01.md) => [how to translate](translate.html#accurate)
        for idx, project in enumerate(self.rc.projects):
            pattern = re.compile(r'\]\(\.\./\.\./{0}/([^/)]+)/01.md\)'.format(project.identifier))
            replace = r']({0}-{1}.html#\1)'.format(str(idx+1).zfill(2), project.identifier)
            content = re.sub(pattern, replace, content)
        # fix links to other sections that just have the section name but no 01.md page (preserve http:// links)
        # e.g. See [Verbs](figs-verb) => See [Verbs](#figs-verb)
        content = re.sub(r'\]\(([^# :/)]+)\)', r'](#\1)', content)
        # convert URLs to links if not already
        content = re.sub(r'([^"(])((http|https|ftp)://[A-Z0-9/?&_.:=#-]+[A-Z0-9/?&_:=#-])', r'\1[\2](\2)',
                         content, flags=re.IGNORECASE)
        # URLS wth just www at the start, no http
        content = re.sub(r'([^A-Z0-9"(/])(www\.[A-Z0-9/?&_.:=#-]+[A-Z0-9/?&_:=#-])', r'\1[\2](http://\2)',
                         content, flags=re.IGNORECASE)
        return content


class TaConverter(object):

    def __init__(self, ta_tag=None, working_dir=None, output_dir=None, lang_code=DEFAULT_LANG, owner=DEFAULT_OWNER,
                 regenerate=False, logger=None):
        self.ta_tag = ta_tag
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.owner = owner
        self.regenerate = regenerate
        self.logger = logger

        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='ta-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.info('WORKING DIR IS {0} FOR {1}'.format(self.working_dir, self.lang_code))

        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(lang_code))

        self.html_dir = os.path.join(self.output_dir, 'html')
        if not os.path.isdir(self.html_dir):
            os.makedirs(self.html_dir)

        self.manifest = None
        self.ta_html = ''
        self.version = None
        self.publisher = None
        self.contributors = None
        self.issued = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.generation_info = {}
        self.file_id = None
        self.title = 'unfoldingWord® Translation Academy'

    def run(self):
        self.setup_resource_files()
        self.file_id = '{0}_ta_{1}_{2}'.format(self.lang_code, self.ta_tag, self.generation_info['ta']['commit'])
        self.manifest = load_yaml_object(os.path.join(self.ta_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        self.title = self.manifest['dublin_core']['title']
        self.contributors = '<br/>'.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        self.file_id = self.file_id
        if self.regenerate or not os.path.exists(os.path.join(self.output_dir, '{0}.html'.format(self.file_id))):
            self.logger.info('Creating TA HTML files for {0}...'.format(self.file_id))
            self.generate_ta_html()
        self.logger.info('Generating Cover HTML for {0}...'.format(self.file_id))
        self.generate_cover_html()
        self.logger.info('Generating Licensbe HTML for {0}...'.format(self.file_id))
        self.generate_license_html()
        self.logger.info('Copying style sheet file for {0}...'.format(self.file_id))
        style_file = os.path.join(self.my_path, 'ta_style.css')
        shutil.copy2(style_file, self.html_dir)
        self.logger.info('Generating PDF {0}/{1}.pdf...'.format(self.output_dir, self.file_id))
        self.generate_ta_pdf()
        self.logger.info('PDF file can be found at {0}/{1}.pdf'.format(self.output_dir, self.file_id))

    def save_bad_links(self):
        bad_links = "BAD LINKS:\n"
        for source_rc in sorted(self.bad_links.keys()):
            for rc in sorted(self.bad_links[source_rc].keys()):
                source = source_rc[5:].split('/')
                parts = rc[5:].split('/')
                if source[1] == 'ult':
                    str = '  ULT {0} {1}:{2}: English ULT alignment not found for `{3}` (greek: `{4}`, occurrence: {5})'.format(
                        source[3].upper(), source[4], source[5], self.bad_links[source_rc][rc], parts[3], parts[4])
                else:
                    if source[1] == 'obn-tn':
                        if parts[1] == 'tw':
                            str = '  UGNT'
                        else:
                            str = '  tN'
                        str += ' {0} {1}:{2}'.format(source[3].upper(), source[4], source[5])
                    else:
                        str = '  {0}'.format(source_rc)
                    str += ': BAD RC - `{0}`'.format(rc)
                    if self.bad_links[source_rc][rc]:
                        str += ' - change to `{0}`'.format(self.bad_links[source_rc][rc])
                bad_links += "{0}\n".format(str)
        save_file = os.path.join(self.output_dir, '{0}_bad_links.txt'.format(self.file_id))
        write_file(save_file, bad_links)
        self.logger.info('BAD LINKS file can be found at {0}'.format(save_file))

    @staticmethod
    def get_resource_git_url(resource, lang, owner):
        return 'https://git.door43.org/{0}/{1}_{2}.git'.format(owner, lang, resource)

    def clone_resource(self, resource, tag=DEFAULT_TAG, url=None):
        if not url:
            url = self.get_resource_git_url(resource, self.lang_code, self.owner)
        repo_dir = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource))
        if not os.path.isdir(repo_dir):
            try:
                git.Repo.clone_from(url, repo_dir)
            except git.GitCommandError:
                owners = OWNERS
                owners.insert(0, self.owner)
                languages = [self.lang_code, DEFAULT_LANG]
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
        g.checkout(tag)
        if tag == DEFAULT_TAG:
            g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource('ta', self.ta_tag)
        if not os.path.isfile(os.path.join(self.html_dir, 'logo-uta.png')):
            command = 'curl -o {0}/logo-uta.png https://cdn.door43.org/assets/uw-icons/logo-uta-256.png'.format(
                self.html_dir)
            subprocess.call(command, shell=True)

    def merge_files(self, process_dir):
        files = ['01-']
        merged_html = """<!DOCTYPE html>
<html lang="en-US">
    <head data-suburl="">
        <meta charset="UTF-8"/>
        <link href="html/ta_style.css" rel="stylesheet"/>
        <style type="text/css">
            body > div {{
                page-break-after: always;
            }}
        </style>
    </head>
    <body>
""".format(self.lang_code)
        for fname in sorted(glob(os.path.join(process_dir, '*.html'))):
            with codecs.open(fname, 'r') as f:
                soup = BeautifulSoup(f, 'html.parser')
                # get the body of the raw html file
                content = soup.div
                content['id'] = os.path.basename(fname)
                merged_html += unicode(content)
        merged_html += """
    </body>
</html>
"""
        return merged_html

    def generate_orig_ta_html(self):
        process_dir = os.path.join(self.working_dir, self.file_id)
        rc = RC(self.ta_dir, '{0}_ta'.format(self.lang_code), self.manifest)
        processor = TaProcessor(rc, self.ta_dir, process_dir)
        test = processor.run()
        # find the first directory that has md files.
        files = get_files(process_dir, extensions=['.md'], exclude=["license.md", "package.json", "project.json", 'readme.md'])
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'template.html')) as template_file:
            html_template = string.Template(template_file.read())
        for filename in files:
            # Convert files that are markdown files
            with codecs.open(filename, 'r', 'utf-8-sig') as md_file:
                md = md_file.read()
                html = markdown2.markdown(md, extras=['markdown-in-html', 'tables'])
            html = html_template.safe_substitute(title='TA', content=html)
            # Change headers like <h1><a id="verbs"/>Verbs</h1> to <h1 id="verbs">Verbs</h1>
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all('a', {'id': True}):
                parent = tag.parent
                if parent and parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    parent['id'] = tag['id']
                    parent['class'] = parent.get('class', []) + ['section-header']
                    grandparent = parent.parent
                    if grandparent.name == 'p':
                        grandparent.insert_before(parent)
                        grandparent.insert_before(grandparent.span)
                        grandparent.extract()
                    tag.extract()
            # Any headers that don't have an id (i.e. they aren't in the TOC) need to be made a span tag
            for h in soup.find_all(re.compile('^h[2-6]$')):
                if not h.get('id'):
                    h['class'] = h.get('class', []) + [h.name]
                    h.name = 'span'
            html = unicode(soup)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            html_filename = base_name + ".html"
            output_file = os.path.join(process_dir, html_filename)
            write_file(output_file, html)
        ta_html_orig = self.merge_files(process_dir)

        ta_html_orig_file = os.path.join(self.output_dir, '{0}_orig.html'.format(self.file_id))
        write_file(ta_html_orig_file, ta_html_orig)

    def generate_ta_html(self):
        ta_html_orig_file = os.path.join(self.output_dir, '{0}_orig.html'.format(self.file_id))
        if self.regenerate or not os.path.isfile(ta_html_orig_file):
            self.generate_orig_ta_html()
        ta_html = read_file(ta_html_orig_file)

        soup = BeautifulSoup(ta_html, 'html.parser')

        # make all the links point to the anchors in this document
        for a in soup.find_all('a'):
            a['href'] = re.sub(r'^[A-Za-z0-9\.-]+#(.*)$', r'#\1', a['href'])

        # process headers
        for h in soup.find_all(re.compile('^h[1-5]$')):
            classes = []
            num = int(h.name[1])
            # make headers h1 and h2 be sections
            if num <= 2:
                classes.append('section-header')
            # Make all headers that have a header right before them non-break
            prev = h.find_previous_sibling()

            if prev and (re.match('^h[2-6]$', prev.name) or prev.name == 'span'):
                classes.append('no-break')
            h['class'] = h.get('class', []) + classes

        # Make manual page
        for h in soup.find_all('h1'):
            header_content = soup.new_tag('div', style='text-align:center;padding-top:200px')
            header_content['class'] = ['break']
            h.insert_before(header_content)
            img = soup.new_tag('img', src="html/logo-uta.png", width="120")
            header_content.append(img)
            h1 = soup.new_tag('span')
            h1['class'] = ['h1']
            h1.string = self.title
            header_content.append(h1)
            h['class'] = ['h2', 'no-break']
            header_content.append(h)
            h3 = soup.new_tag('span')
            h3['class'] = ['h3']
            h3.string = 'Version {0}'.format(self.version)
            header_content.append(h3)

        soup.html.body.append(BeautifulSoup(self.get_contributors_html(), 'html.parser'))
        self.ta_html = unicode(soup)

        ta_html_file = '{0}/{1}.html'.format(self.output_dir, self.file_id)
        write_file(ta_html_file, self.ta_html)

    def get_contributors_html(self):
        if self.contributors and len(self.contributors):
            return '<div id="contributors" class="article">\n<h1 class="section-header">Contributors</h1>\n<p>{0}</p></div>'.format(
                self.contributors)
        else:
            return ''

    def generate_cover_html(self):
        cover_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="ta_style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="logo-uta.png" width="120">
    <span class="h1">{0}</span>
    <span class="h3">Version {1}</span>
  </div>
</body>
</html>
'''.format(self.title, self.version)
        html_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.file_id))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        license_file = os.path.join(self.ta_dir, 'LICENSE.md')
        license = markdown2.markdown_path(license_file)
        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="ta_style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
    <p>
      <strong>Date:</strong> {0}<br/>
      <strong>Version:</strong> {1}<br/>
      <strong>Published by:</strong> {2}<br/>
    </p>
    {3}
  </div>
</body>
</html>'''.format(self.issued, self.version, self.publisher, license)
        html_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.file_id))
        write_file(html_file, license_html)

    def generate_ta_pdf(self):
        cover_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.file_id))
        license_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.file_id))
        header_file = os.path.join(self.my_path, 'ta_header.html')
        footer_file = os.path.join(self.my_path, 'ta_footer.html')
        body_file = os.path.join(self.output_dir, '{0}.html'.format(self.file_id))
        output_file = os.path.join(self.output_dir, '{0}.pdf'.format(self.file_id))
        template_file = os.path.join(self.my_path, 'toc_template.xsl')
        command = '''wkhtmltopdf 
                        --javascript-delay 2000
                        --debug-javascript
                        --cache-dir "{6}"
                        --run-script "setInterval(function(){{if(document.readyState=='complete') setTimeout(function() {{window.status='done';}}, 100);}},200)"
                        --window-status done
                        --encoding utf-8
                        --outline-depth 3
                        --orientation portrait -L 15 -R 15 -T 15 -B 15
                        --header-html "{0}"
                        --header-spacing 2
                        --footer-html '{7}'
                        cover "{1}"
                        cover "{2}"
                        toc
                        --disable-dotted-lines 
                        --enable-external-links 
                        --xsl-style-sheet "{3}"
                        "{4}" 
                        "{5}"
                    '''.format(header_file, cover_file, license_file, template_file, body_file, output_file,
                               os.path.join(self.working_dir, 'wkhtmltopdf'), footer_file)
        command = re.sub(r'\s+', ' ', command, flags=re.MULTILINE)
        self.logger.info(command)
        subprocess.call(command, shell=True)


def main(ta_tag, lang_codes, working_dir, output_dir, owner, regenerate):
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
        print('Using env var WORKING_DIR: {0}'.format(working_dir))
    if not output_dir and 'OUTPUT_DIR' in os.environ:
        output_dir = os.environ['OUTPUT_DIR']
        print('Using env var OUTPUT_DIR: {0}'.format(output_dir))

    for lang_code in lang_codes:
        print('Starting TA Converter for {0}...'.format(lang_code))
        ta_converter = TaConverter(ta_tag, working_dir, output_dir, lang_code, owner, regenerate, logger)
        ta_converter.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_codes', required=False, help='Language Code(s)', action='append')
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('--ta-tag', dest='ta', default=DEFAULT_TAG, required=False, help='tA Tag')
    parser.add_argument('-r', '--regenerate', dest='regenerate', action='store_true',
                        help='Regenerate PDF even if exists')
    args = parser.parse_args(sys.argv[1:])
    main(args.ta, args.lang_codes, args.working_dir, args.output_dir, args.owner, args.regenerate)
