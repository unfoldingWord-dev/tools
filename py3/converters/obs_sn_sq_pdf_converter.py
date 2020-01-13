#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF OBS SN & SQ documents
"""
import os
import re
import markdown2
from bs4 import BeautifulSoup
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import write_file


class ObsSnSqPdfConverter(PdfConverter):

    @property
    def name(self):
        return 'obs-sn-sq'

    @property
    def title(self):
        sn_title = self.resources['obs-sn'].title
        sq_title = self.resources['obs-sq'].title
        return f'{sn_title}\n<br/>\n&\n<br/>\n{sq_title}'

    @property
    def simple_title(self):
        sn_title = self.resources['obs-sn'].simple_title
        sq_title = self.resources['obs-sq'].simple_title
        return f'{sn_title} & {sq_title}'

    def get_body_html(self):
        self.logger.info('Generating OBS SN SQ html...')
        obs_sn_sq_html = f'''
<section id="{self.lang_code}-obs-sn">
    <div class="resource-title-page no-header">
        <img src="images/{self.resources['obs'].logo_file}" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        intro_file = os.path.join(self.resources['obs-sq'].repo_dir, 'content', '00.md')
        if os.path.isfile(intro_file):
            intro_id = 'obs-sq-intro'
            intro_content = markdown2.markdown_path(intro_file)
            intro_content = self.increase_headers(intro_content, 1)
            intro_content = intro_content.replace('<h2>', '<h2 class="section-header">', 1)
            obs_sn_sq_html += f'''
    <article id="{intro_id}">
        {intro_content}
    </article>
'''
        for chapter_num in range(1, 51):
            chapter_num = str(chapter_num).zfill(2)
            sn_chapter_dir = os.path.join(self.resources['obs-sn'].repo_dir, 'content', chapter_num)
            sq_chapter_file = os.path.join(self.resources['obs-sq'].repo_dir, 'content', f'{chapter_num}.md')
            obs_chapter_data = self.get_obs_chapter_data(chapter_num)
            chapter_title = obs_chapter_data['title']
            # HANDLE RC LINKS FOR OBS SN CHAPTER
            obs_sn_chapter_rc_link = f'rc://{self.lang_code}/obs-sn/help/obs/{chapter_num}'
            obs_sn_chapter_rc = self.add_rc(obs_sn_chapter_rc_link, title=chapter_title)
            obs_sn_sq_html += f'''
    <section id="{obs_sn_chapter_rc.article_id}">
        <h2 class="section-header reset-headers">{chapter_title}</h2>
        <section id="{obs_sn_chapter_rc.article_id}-notes" class="no-break">
            <h3 class="section-header no-break">{self.translate('study_notes')}</h3>
'''
            if 'bible_reference' in obs_chapter_data and obs_chapter_data['bible_reference']:
                obs_sn_sq_html += f'''
                    <div class="bible_reference" class="no-break">{obs_chapter_data['bible_reference']}</div>
            '''
            frames = obs_chapter_data['frames']
            for frame_idx, frame in enumerate(frames):
                image = obs_chapter_data['images'][frame_idx]
                frame_num = str(frame_idx + 1).zfill(2)
                frame_title = f'{chapter_num}:{frame_num}'
                obs_sn_file = os.path.join(sn_chapter_dir, f'{frame_num}.md')
                obs_text = re.sub(r'[\n\s]+', ' ', frame, flags=re.MULTILINE)

                if os.path.isfile(obs_sn_file):
                    notes_html = markdown2.markdown_path(obs_sn_file)
                    notes_html = self.increase_headers(notes_html, 3)
                else:
                    no_study_notes = self.translate('no_study_notes_for_this_frame')
                    notes_html = f'<div class="no-notes-message">({no_study_notes})</div>'

                # HANDLE RC LINKS FOR OBS SN FRAME
                obs_sn_rc_link = f'rc://{self.lang_code}/obs-sn/help/obs/{chapter_num}/{frame_num}'
                obs_sn_rc = self.add_rc(obs_sn_rc_link, title=frame_title, article=notes_html)
                # HANDLE RC LINKS FOR OBS FRAME
                obs_rc_link = f'rc://{self.lang_code}/obs/book/obs/{chapter_num}/{frame_num}'
                self.add_rc(obs_rc_link, title=frame_title, article_id=obs_sn_rc.article_id)

                if obs_text and notes_html:
                    phrases = self.get_phrases_to_highlight(notes_html, 'h4')
                    if phrases:
                        obs_text = self.highlight_text_with_phrases(obs_text, phrases, obs_sn_rc)

                obs_sn_sq_html += f'''
        <article id="{obs_sn_rc.article_id}">
          <h4>{frame_title}</h4>
          <div class="obs-img-and-text">
            <img src="{image}" class="obs-img"/>
            <div class="obs-text">
                {obs_text}
            </div>
          </div>
          <div class="obs-sn-notes">
            {notes_html}
          </div>
        </article>
'''
            obs_sn_sq_html += '''
    </section>
'''
            if os.path.isfile(sq_chapter_file):
                obs_sq_title = f'{chapter_title} - {self.translate("study_questions")}'
                obs_sq_html = markdown2.markdown_path(sq_chapter_file)
                obs_sq_html = self.increase_headers(obs_sq_html, 3)
                # HANDLE RC LINKS FOR OBS SQ
                obs_sq_rc_link = f'rc://{self.lang_code}/obs-sq/help/obs/{chapter_num}'
                obs_sq_rc = self.add_rc(obs_sq_rc_link, title=obs_sq_title, article=obs_sq_html)
                obs_sn_sq_html += f'''
        <article id="{obs_sq_rc.article_id}">
          <h3 class="section-header">{self.translate('study_questions')}</h3>
          {obs_sq_html}
        </article>
    </section>
'''
        obs_sn_sq_html += '''
</section>
'''
        return obs_sn_sq_html

    def get_obs_chapter_data(self, chapter_num):
        obs_chapter_data = {
            'title': None,
            'frames': [],
            'images': [],
            'bible_reference': None
        }
        obs_chapter_file = os.path.join(self.resources['obs'].repo_dir, 'content',  f'{chapter_num}.md')
        if os.path.isfile(obs_chapter_file):
            soup = BeautifulSoup(markdown2.markdown_path(os.path.join(self.resources['obs'].repo_dir,
                                                                      'content', f'{chapter_num}.md')), 'html.parser')
            obs_chapter_data['title'] = soup.h1.text
            paragraphs = soup.find_all('p')
            for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                if idx % 2 == 1:
                    obs_chapter_data['frames'].append(p.text)
                elif p.img:
                    src = p.img['src'].split('?')[0]
                    obs_chapter_data['images'].append(src)
                else:
                    obs_chapter_data['bible_reference'] = p.text
        return obs_chapter_data

    def fix_links(self, html):
        # Changes references to chapter/frame in links
        # <a href="1/10">Text</a> => <a href="rc://obs-sn/help/obs/01/10">Text</a>
        # <a href="10-1">Text</a> => <a href="rc://obs-sn/help/obs/10/01">Text</a>
        html = re.sub(r'href="(\d)/(\d+)"', r'href="0\1/\2"', html)  # prefix 0 on single-digit chapters
        html = re.sub(r'href="(\d+)/(\d)"', r'href="\1/0\2"', html)  # prefix 0 on single-digit frames
        html = re.sub(r'href="(\d\d)/(\d\d)"', fr'href="rc://{self.lang_code}/obs/book/obs/\1/\2"', html)

        # Changes references to chapter/frame that are just chapter/frame prefixed with a #
        # #1:10 => <a href="rc://en/obs/book/obs/01/10">01:10</a>
        # #10/1 => <a href="rc://en/obs/book/obs/10/01">10:01</a>
        # #10/12 => <a href="rc://en/obs/book/obs/10/12">10:12</a>
        html = re.sub(r'#(\d)[:/-](\d+)', r'#0\1-\2', html)  # prefix 0 on single-digit chapters
        html = re.sub(r'#(\d+)[:/-](\d)\b', r'#\1-0\2', html)  # prefix 0 on single-digit frames
        html = re.sub(r'#(\d\d)[:/-](\d\d)', rf'<a href="rc://{self.lang_code}/obs/book/obs/\1/\2">\1:\2</a>', html)

        return html

#     def save_bad_links_html(self):
#         bad_notes = '''
# <!DOCTYPE html>
#     <html lang="en-US">
#         <head>
#             <title>
#                 NON-MATCHING NOTES
#             </title>
#             <meta charset="utf-8">
#         </head>
# <body>
#     <h1>NON-MATCHING NOTES (i.e. not found in the frame text as written):</h1>
#     <ul>
# '''
#         for rc in sorted(self.bad_links.keys()):
#             rc_parts = rc[5:].split('/')
#             chapter = rc_parts[4]
#             frame = rc_parts[5]
#             bad_notes += f'''
#         <li>
#             <a href="html/{self.file_commit_id}.html#obs-sn-{chapter}" title="See in the OBS SN Docs (HTML)" target="obs-sn-html">{chapter}</a>
#             <a href="https://git.door43.org/{self.main_resource.owner}/{self.main_resource.repo_name}/src/branch/{self.main_resource.tag}/content/{chapter}/{frame}.md" style="text-decoration:none" target="obs-sn-git">
#                 <img src="http://www.myiconfinder.com/uploads/iconsets/16-16-65222a067a7152473c9cc51c05b85695-note.png" title="See OBS UTN note on DCS">
#             </a>
#             <a href="https://git.door43.org/{self.resources['obs'].owner}/{self.resources['obs'].repo_name}/src/branch/master/content/{chapter}.md" style="text-decoration:none" target="obs-git">
#                 <img src="https://cdn3.iconfinder.com/data/icons/linecons-free-vector-icons-pack/32/photo-16.png" title="See OBS story on DCS">
#             </a>:<br/>
#             <i>{self.bad_links[rc]['text']}</i><br/>
#             <ul>
# '''
#             for note in self.bad_links[rc]['notes']:
#                 for key in note.keys():
#                     if note[key]:
#                         bad_notes += f'<li><b><i>{key}</i></b><br/>{note[key]} (QUOTE ISSUE)</li>'
#                     else:
#                         bad_notes += f'<li><b><i>{key}</i></b></li>'
#             bad_notes += '''
#             </ul>
#         </li>
# '''
#         bad_notes += '''
#     </u>
# </body>
# </html>
# '''
#         save_file = os.path.join(self.output_dir, f'{self.file_commit_id}_bad_notes.html')
#         write_file(save_file, bad_notes)
#         self.logger.info(f'BAD NOTES file can be found at {save_file}')


if __name__ == '__main__':
    run_converter(['obs-sn', 'obs-sq', 'obs'], ObsSnSqPdfConverter)
