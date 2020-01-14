#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF for OBS
"""
import os
import markdown2
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import read_file
from ..general_tools import obs_tools


class ObsPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = None

    @property
    def title(self):
        if not self._title:
            front_title_path = os.path.join(self.main_resource.repo_dir, 'content', 'front', 'title.md')
            self._title = read_file(front_title_path).strip()
        return self._title

    @property
    def toc_title(self):
        return f'<h1>{self.main_resource.simple_title}</h1>'

    def get_body_html(self):
        self.logger.info('Generating OBS html...')
        obs_html = '''
<article class="blank-page">
</article>        
'''
        for chapter_num in range(1, 51):
            chapter_num = str(chapter_num).zfill(2)
            obs_chapter_data = obs_tools.get_obs_chapter_data(self.main_resource.repo_dir, chapter_num)
            chapter_title = obs_chapter_data['title']
            obs_html += f'''
<article class="obs-chapter-title-page no-header-footer">
    <h1 id="{self.lang_code}-obs-{chapter_num}" class="section-header">{chapter_title}</h1>
</article>
'''
            frames = obs_chapter_data['frames']
            for frame_idx in range(0, len(frames), 2):
                obs_html += '''
<article class="obs-page">
'''
                for offset in range(0, 2 if len(frames) > frame_idx + 1 else 1):
                    image = obs_chapter_data['images'][frame_idx + offset]
                    frame_num = str(frame_idx + offset + 1).zfill(2)
                    obs_html += f'''
    <div class="obs-frame no-break obs-frame-{'odd' if offset == 0 else 'even'}">
        <img src="{image}" class="obs-img no-break"/>
        <div class="obs-text no-break">
            {frames[frame_idx + offset]}
        </div>
'''
                    if frame_idx + offset + 1 == len(frames):
                        obs_html += f'''
        <div class="bible-reference no-break">{obs_chapter_data['bible_reference']}</div>
'''
                    obs_html += '''
    </div>
'''
                obs_html += '''
</article>
'''
        obs_html += self.get_back_html()
        return obs_html

    def get_contributors_html(self):
        return ''

    def get_cover_html(self):
        cover_html = f'''
<article id="main-cover" class="cover no-header-footer">
    <img src="css/uw-obs-logo.png" alt="{self.name.upper()}"/>
</article>
<article class="blank-page no-footer">
</article>
'''
        return cover_html

    def get_license_html(self):
        front_path = os.path.join(self.main_resource.repo_dir, 'content', 'front', 'intro.md')
        front_html = markdown2.markdown_path(front_path)
        license_html = f'''
<article id="license" class="no-footer">
  {front_html}
</article>
'''
        return license_html

    def get_back_html(self):
        back_path = os.path.join(self.main_resource.repo_dir, 'content', 'back', 'intro.md')
        back_html = markdown2.markdown_path(back_path)
        back_html = f'''
<article id="back" class="no-footer">
  {back_html}
</article>
'''
        return back_html


if __name__ == '__main__':
    run_converter(['obs'], ObsPdfConverter)
