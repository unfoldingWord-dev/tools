#!/usr/bin/env python3
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF OBS SN documents
"""
import os
import re
import markdown2
from glob import glob
from bs4 import BeautifulSoup
from .pdf_converter import run_converter
from .obs_sn_sq_pdf_converter import ObsSnSqPdfConverter


class ObsSnPdfConverter(ObsSnSqPdfConverter):

    @property
    def name(self):
        return self.main_resource.resource_name

    @property
    def title(self):
        return self.main_resource.title

    @property
    def simple_title(self):
        return self.main_resource.simple_title

    def get_body_html(self):
        self.logger.info('Generating OBS SN html...')
        obs_sn_html = f'''
<section id="obs-sn">
    <div class="resource-title-page no-header">
        <img src="images/{self.resources['obs'].logo}.png" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        obs_chapter_files = sorted(glob(os.path.join(self.resources['obs'].repo_dir, 'content', '*.md')))
        for chapter_file in obs_chapter_files:
            if os.path.isfile(chapter_file):
                chapter_num = os.path.splitext(os.path.basename(chapter_file))[0]
                soup = BeautifulSoup(
                    markdown2.markdown_path(chapter_file), 'html.parser')
                title = soup.h1.text
                paragraphs = soup.find_all('p')
                frames = []
                for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                    if idx % 2:
                        obs_text = p.text
                        obs_text = re.sub(r'[\n\s]+', ' ', obs_text, flags=re.MULTILINE)
                        frames.append(obs_text)
                chapter_id = f'obs-sn-{chapter_num}'
                obs_sn_html += f'<article id="{chapter_id}">\n\n'
                obs_sn_html += f'<h2 class="section-header">{title}</h2>\n'
                # HANDLE RC LINKS FOR OBS SN CHAPTERS
                obs_sn_rc = f'rc://{self.lang_code}/obs-sn/help/{chapter_num}'
                self.rcs[obs_sn_rc] = {
                    'rc': obs_sn_rc,
                    'id': chapter_id,
                    'link': '#' + chapter_id,
                    'title': title
                }
                for frame_idx, obs_text in enumerate(frames):
                    frame_num = str(frame_idx+1).zfill(2)
                    frame_id = f'obs-sn-{chapter_num}-{frame_num}'
                    frame_title = f'{chapter_num}:{frame_num}'
                    obs_sn_html += f'<div id="{frame_id}" class="frame">\n'
                    obs_sn_html += f'<h3>{chapter_num}:{frame_num}</h3>\n'
                    # chapter_soup.ul.append(soup('<li><a href="#{0}">{1}</a></li>'))
                    notes_html = ''
                    frame_notes_file = os.path.join(self.resources['obs-sn'].repo_dir, 'content', chapter_num,
                                                    f'{frame_num}.md')
                    if os.path.isfile(frame_notes_file):
                        notes_html = markdown2.markdown_path(frame_notes_file)
                        notes_html = self.increase_headers(notes_html, 3)
                    if obs_text and notes_html:
                        phrases = self.get_phrases_to_highlight(notes_html, 'h4')
                        obs_text = self.highlight_text_with_phrases(obs_text, phrases, frame_title)
                    if not notes_html:
                        no_study_notes = self.translate('no_study_notes_for_this_frame')
                        notes_html = f'<div class="no-notes-message">({no_study_notes})</div>'
                    obs_sn_html += f'''
    <div id="{frame_id}-text" class="frame-text">
        {obs_text}
    </div>
    <div id="{frame_id}-notes" class="frame-notes">
        {notes_html}
    </div>
'''
                    obs_sn_html += '</div>\n\n'
                    if frame_idx < len(frames) - 1:
                        obs_sn_html += '<hr class="frame-divider"/>'
                    # HANDLE RC LINKS FOR OBS FRAMES
                    obs_rc = f'rc://{self.lang_code}/obs/bible/obs/{chapter_num}/{frame_num}'
                    self.rcs[obs_rc] = {
                        'rc': obs_rc,
                        'id': frame_id,
                        'link': '#' + frame_id,
                        'title': title
                    }
                    # HANDLE RC LINKS FOR OBS SN FRAMES
                    obs_sn_rc = f'rc://{self.lang_code}/obs-sn/help/obs/{chapter_num}/{frame_num}'
                    self.rcs[obs_sn_rc] = {
                        'rc': obs_sn_rc,
                        'id': frame_id,
                        'link': '#' + frame_id,
                        'title': title
                    }
                obs_sn_html += '</article>\n\n'
        obs_sn_html += '</section>'
        return obs_sn_html


if __name__ == '__main__':
    run_converter(['obs-sn', 'obs'], ObsSnPdfConverter)
