#!/usr/bin/env python3
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF TA documents
"""
import os
import yaml
import markdown2
from bs4 import BeautifulSoup
from .pdf_converter import PdfConverter, run_converter
from .rc_link import ResourceContainerLink
from ..general_tools.file_utils import read_file


class TaPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section_count = 0
        self.config = None
        self.toc_html = ''

    def get_toc_from_yaml(self):
        toc_html = ''
        projects = self.main_resource.projects
        self.section_count = 0
        for idx, project in enumerate(projects):
            project_path = os.path.join(self.main_resource.repo_dir, project['identifier'])
            toc = yaml.full_load(read_file(os.path.join(project_path, 'toc.yaml')))
            if not toc_html:
                toc_html = f'''
                <article id="contents">
                  <h1>{toc['title']}</h1>
                  <ul id="contents-top-ul">
'''
            toc_html += f'<li><a href="#{self.lang_code}-ta-man-{project["identifier"]}-cover"><span>{project["title"]}</span></a>'
            toc_html += self.get_toc_for_section(toc)
            toc_html += '</li>'
        toc_html += '</ul></article>'
        return toc_html

    def get_toc_for_section(self, section):
        toc_html = ''
        if 'sections' not in section:
            return toc_html
        toc_html = '<ul>'
        for section in section['sections']:
            title = section['title']
            self.section_count += 1
            link = f'section-container-{self.section_count}'
            toc_html += f'<li><a href="#{link}"><span>{title}</span></a>{self.get_toc_for_section(section)}</li>'
        toc_html += '</ul>'
        return toc_html

    def get_body_html(self):
        self.logger.info('Generating TA html...')
        self.toc_html = self.get_toc_from_yaml()
        ta_html = self.get_ta_html()
        return ta_html

    def get_ta_html(self):
        ta_html = f'''
<section id="{self.lang_code}-ta-man">
    {self.get_articles()}
</section>
'''
        return ta_html

    def get_articles(self):
        articles_html = ''
        projects = self.main_resource.projects
        self.section_count = 0
        for idx, project in enumerate(projects):
            project_id = project['identifier']
            project_path = os.path.join(self.main_resource.repo_dir, project_id)
            toc = yaml.full_load(read_file(os.path.join(project_path, 'toc.yaml')))
            self.config = yaml.full_load(read_file(os.path.join(project_path, 'config.yaml')))
            articles_html += f'''
                <article id="{self.lang_code}-ta-man-{project_id}-cover" class="manual-cover cover">
                  <img src="images/{self.main_resource.logo_file}" alt="{project_id}" />
                  <h1>{self.title}</h1>
                  <h2>{project['title']}</h2>
                </article>
'''
            articles_html += self.get_articles_from_toc(project_id, toc, project_id)
        return articles_html

    def get_articles_from_toc(self, project, section, project_id, level=2):
        articles_html = ''
        if 'sections' not in section:
            return articles_html
        for section in section['sections']:
            self.section_count += 1
            link = f'section-container-{self.section_count}'
            title = section['title']
            articles_html += f'<section id="{link}">'
            actual_title = self.get_title(project, link, title)
            section_header = f'''
    <h{level} id="{self.lang_code}-ta-man-{project}-{link}-title" class="section-header">{actual_title}</h{link}>
'''
            if 'link' in section:
                link = section['link']
                rc = ResourceContainerLink(f'rc://{self.lang_code}/ta/man/{project}/{link}', title=actual_title)
                if rc.rc_link in self.rcs:
                    rc = self.rcs[rc.rc_link]
                    rc.linking_level = 0
                self.get_article(rc, section_header, project_id)
                articles_html += rc.article
            else:
                articles_html += section_header
            if 'sections' in section:
                articles_html += self.get_articles_from_toc(project, section, project_id, level+1)
            articles_html += '</section>'
        return articles_html

    def get_title(self, project, link, alt_title):
        title_file = os.path.join(self.main_resource.repo_dir, project, link, 'title.md')
        title = None
        if os.path.isfile(title_file):
            title = read_file(title_file).strip()
        if not title:
            title = alt_title.strip()
        return title

    def get_article(self, rc, header, project_id):
        article_dir = os.path.join(self.main_resource.repo_dir, rc.project, rc.path)
        question_file = os.path.join(article_dir, 'sub-title.md')
        question = None
        if os.path.isfile(question_file):
            question = read_file(question_file)
        article_file = os.path.join(article_dir, '01.md')
        article_file_html = markdown2.markdown_path(article_file, extras=['markdown-in-html', 'tables'])
        if not article_file_html:
            print("NO FILE AT {0}".format(article_file))
            bad_link = '{0}/{1}'.format(rc.project, rc.path)
            content_file = os.path.join(self.main_resource.repo_dir, rc.project, rc.path, '01.md')
            if os.path.isdir(os.path.join(self.main_resource.repo_dir, bad_link)):
                if not os.path.isfile(content_file):
                    self.bad_links[bad_link] = '[dir exists but no 01.md file]'
                else:
                    self.bad_links[bad_link] = '[01.md file exists but no content]'
            else:
                self.bad_links[bad_link] = '[no corresponding article found]'
        top_box = ""
        bottom_box = ""
        if question:
            top_box += f'''
            <div class="ta-question">
                This page answers the question: <em>{question}<em>
            </div>
'''
        if rc.path in self.config:
            if 'dependencies' in self.config[rc.path] and self.config[rc.path]['dependencies']:
                top_box += f'''
                <div class="ta-understand-topic">
                    {self.translate('in_order_to_understand_this_topic')}:
                    <ul>
'''
                for dependency in self.config[rc.path]['dependencies']:
                    dep_project = project_id
                    for project in self.main_resource.projects:
                        dep_article_dir = os.path.join(self.main_resource.repo_dir, project['identifier'], dependency)
                        if os.path.isdir(dep_article_dir):
                            dep_project = project['identifier']
                    top_box += f'<li>[[rc://{self.lang_code}/ta/man/{dep_project}/{dependency}]]</li>'
                top_box += '''
                    </ul>
                </div>
'''
            if 'recommended' in self.config[rc.path] and self.config[rc.path]['recommended']:
                bottom_box += f'''
                <div class="ta-recommended">
                    {self.translate('next_we_recommend_you_learn_about')}:
                    <ul>
'''
                for recommended in self.config[rc.path]['recommended']:
                    rec_project = project_id
                    for project in self.main_resource.projects:
                        rec_article_dir = os.path.join(self.main_resource.repo_dir, project['identifier'], recommended)
                        if os.path.isdir(rec_article_dir):
                            rec_project = project['identifier']
                    bottom_box += f'<li>[[rc://{self.lang_code}/ta/man/{rec_project}/{recommended}]]</li>'
                bottom_box += '''
                    </ul>
                </div>
'''
        article_html = '<article id="{0}">{1}'.format(rc.article_id, header)
        if top_box:
            article_html += '''
            <div class="top-box box">
                {0}
            </div>
'''.format(top_box)
        article_html += article_file_html
        if bottom_box:
            article_html += '''
            <div class="bottom-box box">
                {0}
            </div>
'''.format(bottom_box)
        article_html += '</article>'
        rc.set_article(article_html)
        self.rcs[rc.rc_link] = rc

    def get_toc_html(self, body_html):
        return self.toc_html


if __name__ == '__main__':
    run_converter(['ta', 'tw'], TaPdfConverter)
