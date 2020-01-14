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
from ..general_tools import obs_tools


class ObsPdfConverter(PdfConverter):

    @property
    def toc_title(self):
        return f'<h1>{self.main_resource.simple_title}</h1>'

    def get_body_html(self):
        self.logger.info('Generating OBS html...')
        obs_html = ''
        for chapter_num in range(1, 51):
            chapter_num = str(chapter_num).zfill(2)
            obs_chapter_data = obs_tools.get_obs_chapter_data(self.main_resource.repo_dir, chapter_num)
            chapter_title = obs_chapter_data['title']
            obs_html += f'''
<div class="obs-chapter-title-page obs-page">
    <h1 id="{self.lang_code}-obs-{chapter_num}" class="section-header">{chapter_title}</h1>
</div>
'''
            frames = obs_chapter_data['frames']
            for frame_idx in range(0, len(frames), 2):
                obs_html += '''
<table class="obs-page">
'''
                for offset in range(0, 2 if len(frames) > frame_idx + 1 else 1):
                    image = obs_chapter_data['images'][frame_idx + offset]
                    frame_num = str(frame_idx + offset + 1).zfill(2)
                    obs_html += f'''
    <tr class="obs-frame no-break">
        <td>
            <img src="{image}" class="obs-img no-break"/>
            <div class="obs-text no-break">
                {frames[frame_idx + offset]}
            </div>
'''
                    if frame_idx + 2 >= len(frames):
                        obs_html += f'''
            <div class="bible-reference no-break">{obs_chapter_data['bible_reference']}</div>
'''
                    obs_html += '''
        </td>
    </tr>
'''
                obs_html += '''
</table>
'''
        return obs_html

    def get_contributors_html(self):
        return ''

    def get_cover_html(self):
        cover_html = f'''
<article id="main-cover" class="cover">
    <img src="images/{self.main_resource.logo_file}" alt="{self.name.upper()}"/>
</article>
'''
        return cover_html

    def get_license_html(self):
        front_path = os.path.join(self.main_resource.repo_dir, 'contents', 'front.md')
        front_html = markdown2
        license_html = f'''
<article id="license">
    <h1>{self.translate('license.copyrights_and_licensing')}</h1>
'''
        for resource_name, resource in self.resources.items():
            title = resource.title
            version = resource.version
            publisher = resource.publisher
            issued = resource.issued

            license_html += f'''
    <div class="resource-info">
      <div class="resource-title"><strong>{title}</strong></div>
      <div class="resource-date"><strong>{self.translate('license.date')}:</strong> {issued}</div>
      <div class="resource-version"><strong>{self.translate('license.version')}:</strong> {version}</div>
      <div class="resource-publisher"><strong>{self.translate('license.published_by')}:</strong> {publisher}</div>
    </div>
'''
        license_file = os.path.join(self.main_resource.repo_dir, 'LICENSE.md')
        license_html += markdown2.markdown_path(license_file)
        license_html += '</article>'
        return license_html



if __name__ == '__main__':
    logo_url = 'https://cdn.door43.org/obs/jpg/uWOBSverticallogo1200w.png'
    run_converter(['obs'], ObsPdfConverter, logo_url=logo_url)
