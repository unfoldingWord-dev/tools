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
This script generates the HTML and PDF documents for tA
"""
from __future__ import unicode_literals, print_function
import os
import sys
import re
import argparse
import logging
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
from bs4 import BeautifulSoup, Tag
from html import escape
from html.parser import HTMLParser
from weasyprint import HTML
from ...general_tools.file_utils import load_yaml_object, read_file, write_file

DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
DEFAULT_LANG = 'en'
OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']


def debug(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.__t = 0
        self.lines = []
        self.__current_line = ''
        self.__current_tag = ''
        self.__prev_is_text = False

    @staticmethod
    def __attr_str(attrs):
        return ' '.join('{}="{}"'.format(name, escape(value)) for (name, value) in attrs)

    def handle_starttag(self, tag, attrs):
        if tag != self.__current_tag and (tag != 'a' or not self.__prev_is_text):
            self.lines += [self.__current_line]
            self.__current_line = '\t' * self.__t
            self.__t += 1
        self.__current_line += '<{}>'.format(tag + (' ' + self.__attr_str(attrs) if attrs else ''))
        self.__current_tag = tag
        self.__prev_is_text = False

    def handle_endtag(self, tag):
        self.__t -= 1
        if tag != self.__current_tag:
            self.lines += [self.__current_line]
            self.lines += ['\t' * self.__t + '</{}>'.format(tag)]
            self.__current_line = ''
        elif tag == 'a':
            self.__current_line += '</{}>'.format(tag)
        else:
            self.lines += [self.__current_line + '</{}>'.format(tag)]
            self.__current_line = ''

    def handle_data(self, data):
        self.__prev_is_text = True
        self.__current_line += data

    def get_parsed_string(self):
        return '\n'.join(l for l in self.lines if l)


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
        self.ta_dir = None
        self.html_dir = ''
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
        self.soup = None
        self.section_count = 0
        self.titles = {}
        self.bad_links = {}
        self.config = None
        self.file_id = None

    def run(self):
        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='ta-')
        if not self.output_dir:
            self.output_dir = self.working_dir
        self.html_dir = os.path.join(self.output_dir, 'html')
        self.logger.info('WORKING DIR IS {0} FOR {1}'.format(self.working_dir, self.lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(self.lang_code))
        self.html_dir = os.path.join(self.output_dir, 'html')
        if not os.path.isdir(self.html_dir):
            os.makedirs(self.html_dir)
        self.setup_resource_files()
        self.file_id = '{0}_ta_{1}_{2}'.format(self.lang_code, self.ta_tag, self.generation_info['ta']['commit'])
        self.manifest = load_yaml_object(os.path.join(self.ta_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        self.title = self.manifest['dublin_core']['title']
        self.contributors = '<br/>'.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        with open(os.path.join(self.my_path, 'template.html')) as template_file:
            html_template = string.Template(template_file.read())
        html = html_template.safe_substitute(title=self.title)
        self.soup = BeautifulSoup(html, 'html.parser')
        self.soup.html.head.title.string = self.title
        self.get_cover()
        self.get_license()
        self.get_toc()
        self.get_articles()
        parser = MyHTMLParser()
        parser.feed(str(self.soup))
        output_html = parser.get_parsed_string()
        write_file(os.path.join(self.output_dir, '{0}_new.html'.format(self.file_id)), self.soup.prettify())
        write_file(os.path.join(self.output_dir, '{0}_bad_links.json'.format(self.file_id)), self.bad_links)
        write_file(os.path.join(self.output_dir, '{0}_titles.json'.format(self.file_id)), self.titles)
        for bad_link in sorted(self.bad_links.keys()):
            print('{0}: {1}'.format(bad_link, self.bad_links[bad_link]))
        weasy = HTML(string=output_html, base_url='file://{0}/'.format(self.output_dir))
        weasy.write_pdf(os.path.join(os.path.join(self.output_dir, '{0}_new.pdf'.format(self.file_id))))

    def get_cover(self):
        cover_html = '''
          <article id="cover">
            <img src="html/logo-uta.png" width="120"/>
            <h1 id="cover-title">{0}</h1>
            <h2>Version {1}</h2>
          </article>
        '''.format(self.title, self.version)
        cover = BeautifulSoup(cover_html, 'html.parser')
        self.soup.body.append(cover)

    def get_license(self):
        license_file = os.path.join(self.ta_dir, 'LICENSE.md')
        license_html = markdown2.markdown_path(license_file)
        license_html = '''
          <article id="license">
            <h1 id="license-title">Copyrights & Licensing</h1>
            <p>
              <div id="ta-date"><strong>Date:</strong> {0}</div>
              <div id="ta-version"><strong>Version:</strong> {1}</div>
              <div id="ta-published-by"><strong>Published by:</strong> {2}</div>
            </p>
            {3}
          </article>
        '''.format(self.issued, self.version, self.publisher, license_html)
        license = BeautifulSoup(license_html, 'html.parser')
        self.soup.body.append(license)

    def get_toc(self):
        toc_html = ''
        projects = self.manifest['projects']
        self.section_count = 0
        for idx, project in enumerate(projects):
            project_path = os.path.join(self.ta_dir, project['identifier'])
            toc = load_yaml_object(os.path.join(project_path, 'toc.yaml'))
            if not toc_html:
                toc_html = '''
                <article id="contents">
                  <h1>{0}</h1>
                  <ul id="contents-top-ul">
                '''.format(toc['title'])
            self.titles['{0}-cover'.format(project['identifier'])] = project['title']
            toc_html += '<li><a href="#{0}-manual-cover-title">{1}</a>'.format(project['identifier'], project['title'])
            toc_html += self.get_toc_html(toc)
            toc_html += '</li>'
        toc_html += '</ul></article>'
        self.soup.body.append(BeautifulSoup(toc_html, 'html.parser'))

    def get_toc_html(self, section):
        toc_html = ''
        if 'sections' not in section:
            return toc_html
        toc_html = '<ul>'
        for section in section['sections']:
            title = section['title']
            if 'link' in section:
                self.titles[section['link']] = title
            self.section_count += 1
            link = 'section-container-{0}'.format(self.section_count)
            toc_html += '<li><a href="#{0}">{1}</a>{2}</li>'.format(link, title, self.get_toc_html(section))
        toc_html += '</ul>'
        return toc_html

    def get_articles(self):
        articles_html = ''
        projects = self.manifest['projects']
        self.section_count = 0
        for idx, project in enumerate(projects):
            project_path = os.path.join(self.ta_dir, project['identifier'])
            toc = load_yaml_object(os.path.join(project_path, 'toc.yaml'))
            self.config = load_yaml_object(os.path.join(project_path, 'config.yaml'))
            articles_html += '''
                <article id="{0}-manual-cover">
                  <h1>{1}</h1>
                  <h2 id="{0}-manual-cover-title">{2}</h2>
                </article>
                '''.format(project['identifier'], self.title, project['title'])
            articles_html += self.get_articles_from_toc(project['identifier'], toc)
        self.soup.body.append(BeautifulSoup(articles_html, 'html.parser'))

    def get_articles_from_toc(self, project, section, level=2):
        articles_html = ''
        if 'sections' not in section:
            return articles_html
        for section in section['sections']:
            self.section_count += 1
            link = 'section-container-{0}'.format(self.section_count)
            title = section['title']
            articles_html += '<section id="{0}"><h{1} id="{0}-title">{2}</h{1}>'.\
                format(link, level, self.get_title(project, link, title))
            if 'link' in section:
                link = section['link']
                articles_html += self.get_article(project, link)
            if 'sections' in section:
                articles_html += self.get_articles_from_toc(project, section, level+1)
            articles_html += '</section>'
        return articles_html

    def get_title(self, project, link, alt_title):
        title_file = os.path.join(self.ta_dir, project, link, 'title.md')
        title = None
        if os.path.isfile(title_file):
            title = read_file(title_file).strip()
        if not title:
            title = alt_title.strip()
        return title

    def get_article(self, project, link):
        article_dir = os.path.join(self.ta_dir, project, link)
        question_file = os.path.join(article_dir, 'sub-title.md')
        question = None
        if os.path.isfile(question_file):
            question = read_file(question_file)
        article_file = os.path.join(article_dir, '01.md')
        article_file_html = markdown2.markdown_path(article_file, extras=['markdown-in-html', 'tables'])
        if not article_file_html:
            print("NO FILE AT {0}".format(article_file))
            bad_link = '{0}/{1}'.format(project.identifier, link)
            content_file = os.path.join(self.ta_dir, project.identifier, link, '01.md')
            if os.path.isdir(os.path.join(self.ta_dir, bad_link)):
                if not os.path.isfile(content_file):
                    self.bad_links[bad_link] = '[dir exists but no 01.md file]'
                else:
                    self.bad_links[bad_link] = '[01.md file exists but no content]'
            else:
                self.bad_links[bad_link] = '[no corresponding article found]'
        soup = BeautifulSoup(article_file_html, 'html.parser')
        # for h in soup.find_all(re.compile(r'^h\d$')):
        #     h['class'] = h.get('class', []) + [h.name]
        #     h.name = 'span'
        #     next = h.next_sibling
        top_box = ""
        bottom_box = ""
        if question:
            top_box += '''
            <div class="ta-question">
                This page answers the question: <em>{0}<em>
            </div>
            '''.format(question)
        if link in self.config:
            if 'dependencies' in self.config[link] and self.config[link]['dependencies']:
                top_box += '''
                <div class="ta-understand-topic">
                    In order to understand this topic, it would be good to read:
                    <ul>
                '''
                for dependency in self.config[link]['dependencies']:
                    if dependency in self.titles:
                        dep_title = self.titles[dependency]
                        top_box += '<li><a href="#{0}">{1}</a></li>\n'.format(dependency, dep_title)
                    else:
                        bad_links_key = '{0}/config.yaml:::{1}:::dependencies - {2}'.format(project, link, dependency)
                        self.bad_links[bad_links_key] = 'not found'
                        top_box += '<li>{0}</li>\n'.format(dependency)
                top_box += '''
                    </ul>
                </div>
                '''
            if 'recommended' in self.config[link] and self.config[link]['recommended']:
                bottom_box += '''
                <div class="ta-recommended">
                    Next we recommend you learn about:
                    <ul>
                '''
                for recommended in self.config[link]['recommended']:
                    if recommended in self.titles:
                        rec_title = self.titles[recommended]
                        bottom_box += '<li><a href="#{0}">{1}</a></li>\n'.format(recommended, rec_title)
                    else:
                        bad_link_key = '{0}/config.yaml:::{1}:::recommended - {2}'.format(project, link, recommended)
                        self.bad_links[bad_link_key] = 'not found'
                        bottom_box += '<li>{0}</li>\n'.format(recommended)
                bottom_box += '''
                    </ul>
                </div>
                '''
        article_html = '<article id="{0}">'.format(link)
        if top_box:
            article_html += '''
            <div class="top-box box">
                {0}
            </div>
            '''.format(top_box)
        article_html += str(soup)
        if bottom_box:
            article_html += '''
            <div class="bottom-box box">
                {0}
            </div>
            '''.format(bottom_box)
        article_html += '</article>'
        return article_html

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
                if self.owner not in owners:
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
        # if tag == DEFAULT_TAG:
        #     g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource('ta', self.ta_tag)
        if not os.path.isfile(os.path.join(self.html_dir, 'logo-uta.png')):
            command = 'curl -o {0}/logo-uta.png https://cdn.door43.org/assets/uw-icons/logo-uta-256.png'.format(
                self.html_dir)
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
