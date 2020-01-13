#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF OBS SN documents
"""
import os
import markdown2
from .pdf_converter import run_converter
from .obs_sn_sq_pdf_converter import ObsSnSqPdfConverter
from ..general_tools import obs_tools


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
<section id="{self.lang_code}-obs-sn">
    <div class="resource-title-page no-header">
        <img src="images/{self.resources['obs'].logo_file}" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        for chapter in range(1, 51):
            chapter_num = str(chapter).zfill(2)
            chapter_data = obs_tools.get_obs_chapter_data(self.resources['obs'].repo_dir, chapter_num)
            obs_sn_html += f'<article id="{self.lang_code}-obs-sn-{chapter_num}">\n\n'
            obs_sn_html += f'<h2 class="section-header">{chapter_data["title"]}</h2>\n'
            if 'bible_reference' in chapter_data and chapter_data['bible_reference']:
                obs_sn_html += f'''
                    <div class="bible_reference" class="no-break">{chapter_data['bible_reference']}</div>
            '''
            for frame_idx, obs_text in enumerate(chapter_data['frames']):
                frame_num = str(frame_idx+1).zfill(2)
                frame_title = f'{chapter_num}:{frame_num}'

                frame_notes_file = os.path.join(self.resources['obs-sn'].repo_dir, 'content', chapter_num,
                                                f'{frame_num}.md')
                if os.path.isfile(frame_notes_file):
                    notes_html = markdown2.markdown_path(frame_notes_file)
                    notes_html = self.increase_headers(notes_html, 3)
                else:
                    no_study_notes = self.translate('no_study_notes_for_this_frame')
                    notes_html = f'<div class="no-notes-message">({no_study_notes})</div>'

                # HANDLE RC LINKS FOR OBS SN FRAMES
                obs_sn_rc_link = f'rc://{self.lang_code}/obs-sn/help/obs/{chapter_num}/{frame_num}'
                obs_sn_rc = self.add_rc(obs_sn_rc_link, title=frame_title, article=notes_html)
                # HANDLE RC LINKS FOR OBS FRAMES
                obs_rc_link = f'rc://{self.lang_code}/obs/bible/obs/{chapter_num}/{frame_num}'
                self.add_rc(obs_rc_link, title=frame_title, article_id=obs_sn_rc.article_id)

                if obs_text and notes_html:
                    phrases = self.get_phrases_to_highlight(notes_html, 'h4')
                    if phrases:
                        obs_text = self.highlight_text_with_phrases(obs_text, phrases, obs_sn_rc)

                obs_sn_html += f'''
<div id="{obs_sn_rc.article_id}" class="frame">
    <h3>{frame_title}</h3>
    <div id="{obs_sn_rc.article_id}-text" class="frame-text">
        {obs_text}
    </div>
    <div id="{obs_sn_rc.article_id}-notes" class="frame-notes">
        {notes_html}
    </div>
</div>
'''
                if frame_idx < len(chapter_data['frames']) - 1:
                    obs_sn_html += '<hr class="frame-divider"/>'
            obs_sn_html += '</article>\n\n'
        obs_sn_html += '</section>'
        return obs_sn_html


if __name__ == '__main__':
    run_converter(['obs-sn', 'obs'], ObsSnPdfConverter)
