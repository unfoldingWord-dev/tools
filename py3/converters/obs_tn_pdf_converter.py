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
from glob import glob
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import load_json_object
from ..general_tools import obs_tools

# Enter ignores in lowercase
TN_TITLES_TO_IGNORE = {
    'en': ['a bible story from',
           'connecting statement',
           'connecting statement:',
           'general information',
           'general note'
           ],
    'fr': ['information générale',
           'termes importants',
           'une histoire biblique tirée de',
           'une histoire de la bible tirée de',
           'une histoire de la bible à partir',
           'une histoire de la bible à partir de',
           'mots de traduction',
           'nota geral',
           'déclaration de connexion',
           'cette histoire biblique est tirée',
           'une histoire biblique tirée de:',
           'informations générales'
           ]
}


class ObsTnPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tw_cat = None
        self.bad_notes = {}

    @property
    def tw_cat(self):
        if not self._tw_cat:
            mapping = {
                'idol': 'falsegod',
                'witness': 'testimony',
                'newcovenant': 'covenant',
                'taxcollector': 'tax',
                'believer': 'believe'
            }
            tw_cat_file = os.path.join(self.converters_dir, 'tw_cat.json')
            self._tw_cat = load_json_object(tw_cat_file)
            for chapter in self._tw_cat['chapters']:
                self._tw_cat[chapter['id']] = {}
                for frame in chapter['frames']:
                    self._tw_cat[chapter['id']][frame['id']] = []
                    for item in frame['items']:
                        term = item['id']
                        category = None
                        for c in ['kt', 'names', 'other']:
                            if os.path.exists(os.path.join(self.resources['tw'].repo_dir, 'bible', c, f'{term}.md')):
                                category = c
                                break
                        if not category and term in mapping:
                            category = None
                            for c in ['kt', 'names', 'other']:
                                if os.path.exists(os.path.join(self.resources['tw'].repo_dir, 'bible', c,
                                                               f'{mapping[term]}.md')):
                                    category = c
                                    term = mapping[term]
                                    break
                        if category:
                            self._tw_cat[chapter['id']][frame['id']].append(
                                f'rc://{self.lang_code}/tw/dict/bible/{category}/{term}')
                        if not category or term != item['id']:
                            fix = None
                            if term != item['id']:
                                fix = f'change to: {term}'
                            source_rc_link = f'rc://{self.lang_code}/tw_cat/{chapter["id"]}/{frame["id"]}'
                            source_rc = self.create_rc(source_rc_link)
                            self.add_bad_link(source_rc, item['id'], fix)
        return self._tw_cat

    def get_body_html(self):
        self.logger.info('Generating OBS TN html...')
        return self.get_obs_tn_html()

    def get_obs_tn_html(self):
        obs_tn_html = f'''
<section id="obs-sn">
    <div class="resource-title-page no-header">
        <img src="images/{self.resources['obs'].logo_file}" class="logo" alt="UTN">
        <h1 class="section-header">{self.simple_title}</h1>
    </div>
'''
        obs_tn_chapter_dirs = sorted(glob(os.path.join(self.main_resource.repo_dir, 'content', '*')))
        for obs_tn_chapter_dir in obs_tn_chapter_dirs:
            if os.path.isdir(obs_tn_chapter_dir):
                chapter_num = os.path.basename(obs_tn_chapter_dir)
                chapter_data = obs_tools.get_obs_chapter_data(self.resources['obs'].repo_dir, chapter_num)
                obs_tn_html += f'''
    <article id="{self.lang_code}-obs-tn-{chapter_num}">
        <h2 class="section-header">{chapter_data['title']}</h2>
'''
                frames = [''] + chapter_data['frames']  # first item of '' if there are intro notes from the 00.md file
                for frame_idx, frame_html in enumerate(frames):
                    frame_num = str(frame_idx).zfill(2)
                    frame_title = f'{chapter_num}:{frame_num}'
                    notes_file = os.path.join(obs_tn_chapter_dir, f'{frame_num}.md')
                    notes_html = ''
                    if os.path.isfile(notes_file):
                        notes_html = markdown2.markdown_path(notes_file)
                        notes_html = self.increase_headers(notes_html, 3)
                    if not frame_html and not notes_html:
                        continue

                    # HANDLE RC LINKS FOR OBS FRAME
                    frame_rc_link = f'rc://{self.lang_code}/obs/book/obs/{chapter_num}/{frame_num}'
                    frame_rc = self.add_rc(frame_rc_link, title=frame_title)
                    # HANDLE RC LINKS FOR NOTES
                    notes_rc_link = f'rc://{self.lang_code}/obs-tn/help/{chapter_num}/{frame_num}'
                    notes_rc = self.add_rc(notes_rc_link, title=frame_title, article=notes_html)

                    if frame_html:
                        frame_html = re.sub(r'[\n\s]+', ' ', frame_html, flags=re.MULTILINE)
                        if notes_html:
                            phrases = self.get_phrases_to_highlight(notes_html, 'h4')
                            if phrases:
                                frame_html = self.highlight_text_with_phrases(frame_html, phrases, notes_rc,
                                                                              TN_TITLES_TO_IGNORE[self.lang_code])

                    if frame_idx == len(frames) - 1:
                        if 'bible_reference' in chapter_data and chapter_data['bible_reference']:
                            notes_html += f'''
                                <div class="bible-reference" class="no-break">{chapter_data['bible_reference']}</div>
                        '''
                    # Some OBS TN languages (e.g. English) do not have Translation Words in their TN article
                    # while some do (e.g. French). We need to add them ourselves from the tw_cat file
                    if notes_html and '/tw/' not in notes_html and chapter_num in self.tw_cat and \
                            frame_num in self.tw_cat[chapter_num] and len(self.tw_cat[chapter_num][frame_num]):
                        notes_html += f'''
           <h3>{self.resources['tw'].simple_title}</h3>
           <ul>
'''
                        for rc_link in self.tw_cat[chapter_num][frame_num]:
                            notes_html += f'''
                <li>[[{rc_link}]]</li>
'''
                        notes_html += '''
            </ul>
'''
                    notes_rc.set_article(notes_html)

                    if frame_html:
                        frame_html = f'''
            <div id="{frame_rc.article_id}" class="frame-text">
                {frame_html}
            </div>
'''
                    if notes_html:
                        notes_html = f'''
            <div id="{notes_rc.article_id}-notes" class="frame-notes">
                {notes_html}
            </div>
'''

                    obs_tn_html += f'''
        <div id="{notes_rc.article_id}">
            <h3>{frame_title}</h3>
            {frame_html}
            {notes_html}
        </div>
'''
                    if frame_idx < len(frames) - 1:
                        obs_tn_html += '<hr class="frame-divider"/>\n'
                obs_tn_html += '''
    </article>
'''
        obs_tn_html += '''
</section>
'''
        return obs_tn_html

    def fix_links(self, html):
        # Changes references to chapter/frame in links
        # <a href="1/10">Text</a> => <a href="rc://obs-sn/help/obs/01/10">Text</a>
        # <a href="10-1">Text</a> => <a href="rc://obs-sn/help/obs/10/01">Text</a>
        html = re.sub(r'href="(\d)/(\d+)"', r'href="0\1/\2"', html)  # prefix 0 on single-digit chapters
        html = re.sub(r'href="(\d+)/(\d)"', r'href="\1/0\2"', html)  # prefix 0 on single-digit frames
        html = re.sub(r'href="(\d\d)/(\d\d)"', fr'href="rc://{self.lang_code}/obs-tn/help/\1/\2"', html)

        # Changes references to chapter/frame that are just chapter/frame prefixed with a #
        # #1:10 => <a href="rc://en/obs/book/obs/01/10">01:10</a>
        # #10/1 => <a href="rc://en/obs/book/obs/10/01">10:01</a>
        # #10/12 => <a href="rc://en/obs/book/obs/10/12">10:12</a>
        html = re.sub(r'#(\d)[:/-](\d+)', r'#0\1-\2', html)  # prefix 0 on single-digit chapters
        html = re.sub(r'#(\d+)[:/-](\d)\b', r'#\1-0\2', html)  # prefix 0 on single-digit frames
        html = re.sub(r'#(\d\d)[:/-](\d\d)', rf'<a href="rc://{self.lang_code}/obs-tn/help/\1/\2">\1:\2</a>', html)

        return html


if __name__ == '__main__':
    run_converter(['obs-tn', 'obs', 'ta', 'tw'], ObsTnPdfConverter)
