#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF TQ documents
"""
import os
import yaml
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import read_file


class TqPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section_count = 0
        self.config = None
        self.toc_html = ''

#     def get_toc_from_yaml(self):
#         toc_html = ''
#         projects = self.main_resource.projects
#         self.section_count = 0
#         for idx, project in enumerate(projects):
#             project_path = os.path.join(self.main_resource.repo_dir, project['identifier'])
#             toc = yaml.full_load(read_file(os.path.join(project_path, 'toc.yaml')))
#             if not toc_html:
#                 toc_html = f'''
#                 <article id="contents">
#                   <h1>{toc['title']}</h1>
#                   <ul id="contents-top-ul">
# '''
#             toc_html += f'<li><a href="#{self.lang_code}-ta-man-{project["identifier"]}-cover"><span>{project["title"]}</span></a>'
#             toc_html += self.get_toc_for_section(toc)
#             toc_html += '</li>'
#         toc_html += '</ul></article>'
#         return toc_html
#
#     def get_toc_for_section(self, section):
#         toc_html = ''
#         if 'sections' not in section:
#             return toc_html
#         toc_html = '<ul>'
#         for section in section['sections']:
#             title = section['title']
#             self.section_count += 1
#             link = f'section-container-{self.section_count}'
#             toc_html += f'<li><a href="#{link}"><span>{title}</span></a>{self.get_toc_for_section(section)}</li>'
#         toc_html += '</ul>'
#         return toc_html

    def get_body_html(self):
        self.logger.info('Generating TA html...')
        # self.toc_html = self.get_toc_from_yaml()
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
<article id="{self.lang_code}-{project_id}-cover" class="manual-cover cover">
    <img src="images/{self.main_resource.logo_file}" alt="{project_id}" />
    <h1>{self.title}</h1>
    <h2 class="section-header" toc-level="1">{project['title']}</h2>
</article>
'''
            articles_html += self.get_articles_from_toc(project_id, toc)
        return articles_html

    def get_articles_from_toc(self, project_id, section, toc_level=2):
        if 'sections' not in section:
            return ''
        source_rc = self.create_rc(f'rc://{self.lang_code}/ta/man/{project_id}/toc.yaml')
        articles_html = ''
        for section in section['sections']:
            self.section_count += 1
            if 'link' in section:
                link = section['link']
                title = self.get_title(project_id, link, section['title'])
            else:
                link = f'section-container-{self.section_count}'
                title = section['title']
            rc_link = f'rc://{self.lang_code}/ta/man/{project_id}/{link}'
            rc = self.add_rc(rc_link, title=title)
            if 'link' in section:
                self.get_ta_article_html(rc, source_rc, self.config, toc_level)
            if 'sections' in section:
                sub_articles = self.get_articles_from_toc(project_id, section, toc_level + 1)
                section_header = ''
                if not rc.article:
                    section_header = f'''
    <h2 class="section-header" toc-level="{toc_level}">{title}</h2>
'''
                articles_html += f'''
<section id="{rc.article_id}-section">
    {section_header}
    {rc.article}
    {sub_articles}
</section>
'''
            else:
                articles_html += rc.article
        return articles_html

    def get_title(self, project, link, alt_title):
        title_file = os.path.join(self.main_resource.repo_dir, project, link, 'title.md')
        title = None
        if os.path.isfile(title_file):
            title = read_file(title_file).strip()
        if not title:
            title = alt_title.strip()
        return title

    # def get_toc_html(self, body_html):
    #     return self.toc_html


if __name__ == '__main__':
    run_converter(['tq'], TqPdfConverter)
