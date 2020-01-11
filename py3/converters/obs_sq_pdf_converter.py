#!/usr/bin/env python3
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF OBS SQ documents
"""
import os
import re
import markdown2
from glob import glob
from bs4 import BeautifulSoup
from .pdf_converter import run_converter
from .obs_sn_sq_pdf_converter import ObsSnSqPdfConverter


class ObsSqPdfConverter(ObsSnSqPdfConverter):

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
        obs_sq_html = f'''
<section id="{self.lang_code}-obs-sq">
    <div class="resource-title-page">
        <img src="images/{self.resources['obs'].logo_file}" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        files = sorted(glob(os.path.join(self.main_resource.repo_dir, 'content', '*.md')))
        for file in files:
            chapter_num = os.path.splitext(os.path.basename(file))[0]
            chapter_html = markdown2.markdown_path(file)
            chapter_html = self.increase_headers(chapter_html)
            soup = BeautifulSoup(chapter_html, 'html.parser')
            header = soup.find(re.compile(r'^h\d'))
            title = header.text
            header['class'] = 'section-header'
            # HANDLE OBS SQ RC CHAPTER LINKS
            obs_sq_rc_link = f'rc://{self.lang_code}/obs-sq/help/{chapter_num}'
            obs_sq_rc = self.add_rc(obs_sq_rc_link, title=title, article=chapter_html)
            chapter_data = self.get_obs_chapter_data(chapter_num)
            if len(chapter_data['frames']):
                frames_html = '<div class="obs-frames">\n'
                for idx, frame in enumerate(chapter_data['frames']):
                    frame_num = str(idx+1).zfill(2)
                    frame_title = f'{chapter_num}:{frame_num}'
                    # HANDLE FRAME RC LINKS FOR OBS
                    frame_rc_link = f'rc://{self.lang_code}/obs/book/obs/{chapter_num}/{frame_num}'
                    frame_rc = self.add_rc(frame_rc_link, title=frame_title)
                    frames_html += f'''
    <div id={frame_rc.article_id} class="obs-frame">
        <div class="obs-frame-title">
            {frame_title}
        </div>
        <div class="obs-frame-text">
            {frame}
        </div>
    </div>
'''
                frames_html += '</div>\n'
                header.insert_after(BeautifulSoup(frames_html, 'html.parser'))
            article_html = f'<article id="{obs_sq_rc.article_id}">{str(soup)}</article>\n\n'
            obs_sq_html += article_html
        return obs_sq_html


if __name__ == '__main__':
    run_converter(['obs-sq', 'obs'], ObsSqPdfConverter)
