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
<section id="obs-sq">
    <div class="resource-title-page">
        <img src="images/{self.resources['obs'].logo}.png" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        files = sorted(glob(os.path.join(self.main_resource.repo_dir, 'content', '*.md')))
        for file in files:
            chapter_num = os.path.splitext(os.path.basename(file))[0]
            chapter_id = 'obs-sq-{0}'.format(chapter_num)
            chapter_html = markdown2.markdown_path(file)
            chapter_html = self.increase_headers(chapter_html)
            soup = BeautifulSoup(chapter_html, 'html.parser')
            header = soup.find(re.compile(r'^h\d'))
            title = header.text
            header['class'] = 'section-header'
            # HANDLE CHAPTER RC LINKS FOR SQ
            chapter_rc = f'rc://{self.lang_code}/obs-sq/help/{chapter_num}'
            self.rcs[chapter_rc] = {
                'rc': chapter_rc,
                'id': chapter_id,
                'link': f'#{chapter_id}',
                'title': title
            }
            obs_chapter_file = os.path.join(self.resources['obs'].repo_dir, 'content', f'{chapter_num}.md')
            if os.path.isfile(obs_chapter_file):
                obs_chapter_soup = BeautifulSoup(markdown2.markdown_path(obs_chapter_file), 'html.parser')
                paragraphs = obs_chapter_soup.find_all('p')
                frames = []
                for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                    if idx % 2:
                        obs_text = p.text
                        obs_text = re.sub(r'[\n\s]+', ' ', obs_text, flags=re.MULTILINE)
                        frames.append(obs_text)
                frames_html = '<div class="obs-frames">\n'
                for idx, frame in enumerate(frames):
                    frame_num = str(idx+1).zfill(2)
                    frame_id = f'obs-{chapter_num}-{frame_num}'
                    frame_title = f'{chapter_num}:{frame_num}'
                    frames_html += f'''
<div id={frame_id} class="obs-frame">
    <div class="obs-frame-title">
        {frame_title}
    </div>
    <div class="obs-frame-text">
        {frame}
    </div>
</div>
'''
                    # HANDLE FRAME RC LINKS FOR OBS
                    obs_rc = f'rc://{self.lang_code}/obs/bible/obs/{chapter_num}/{frame_num}'
                    self.rcs[obs_rc] = {
                        'rc': obs_rc,
                        'id': frame_id,
                        'link': f'#{frame_id}',
                        'title': frame_title
                    }
                frames_html += '</div>\n'
                header.insert_after(BeautifulSoup(frames_html, 'html.parser'))
            article_html = f'<article id="{chapter_id}" class="chapter break">{str(soup)}</article>\n\n'
            obs_sq_html += article_html
        return obs_sq_html


if __name__ == '__main__':
    run_converter(['obs-sq', 'obs'], ObsSqPdfConverter)
