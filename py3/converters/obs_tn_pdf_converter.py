#!/usr/bin/env python3
#
#  Copyright (c) 2019 unfoldingWord
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
from bs4 import BeautifulSoup
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import write_file, load_json_object

TN_TITLES_TO_IGNORE = {
    'en': ['A Bible story from',
           'Connecting Statement',
           'Connecting Statement:',
           'General Information',
           'General Note'
           ],
    'fr': ['Information générale',
           'Termes Importants',
           'Une histoire biblique tirée de',
           'Une histoire de la Bible tirée de',
           'Une histoire de la Bible à partir',
           'Une histoire de la Bible à partir de',
           'Mots de Traduction',
           'Nota geral',
           'Déclaration de connexion',
           'Cette histoire biblique est tirée',
           'Une histoire biblique tirée de:',
           'Informations générales',
           'Information Générale'
           ]
}


class ObsTnPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tw_cat = None

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
                                fix = term
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
                chapter_id = f'obs-tn-{chapter_num}'
                soup = BeautifulSoup(
                    markdown2.markdown_path(os.path.join(self.resources['obs'].repo_dir, 'content',
                                                         f'{chapter_num}.md')), 'html.parser')
                chapter_title = soup.h1.text
                obs_tn_html += f'''
    <article id="{chapter_id}">
        <h2 class="section-header">{chapter_title}</h2>
'''
                paragraphs = soup.find_all('p')
                frames = ['']  # 0 is empty for the intro/title note
                for paragraph_idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                    if paragraph_idx % 2:
                        frames.append(p.text)
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
                    if frame_html:
                        frame_html = re.sub(r'[\n\s]+', ' ', frame_html, flags=re.MULTILINE)
                        if notes_html:
                            phrases = self.get_phrases_to_highlight(notes_html, 'h4')
                            frame_html = self.highlight_text_with_phrases(frame_html, phrases, frame_title,
                                                                          TN_TITLES_TO_IGNORE[self.lang_code])
                    # Some OBS TN languages (e.g. French) do not have Translation Words in their TN article.
                    # We need to add them ourselves from the tw_cat file
                    if notes_html and '/tw/' not in notes_html and chapter_num in self.tw_cat and \
                            frame_num in self.tw_cat[chapter_num] and len(self.tw_cat[chapter_num][frame_num]):
                        notes_html += f'''
           <h3>{self.resources['tw'].simple_title}</h3>
           <ul>
'''
                        for rc in self.tw_cat[chapter_num][frame_num]:
                            notes_html += f'''
                <li>[[{rc}]]</li>
'''
                        notes_html += '''
            </ul>
'''
                    # HANDLE RC LINKS FOR OBS FRAME
                    frame_rc_link = f'rc://{self.lang_code}/obs/book/obs/{chapter_num}/{frame_num}'
                    frame_rc = self.add_rc(frame_rc_link, title=frame_title)
                    if frame_html:
                        frame_html = f'''
            <div id="{frame_rc.article_id}" class="frame-text">
                {frame_html}
            </div>
'''
                    # HANDLE RC LINKS FOR NOTES
                    notes_rc_link = f'rc://{self.lang_code}/obs-tn/help/{chapter_num}/{frame_num}'
                    notes_rc = self.add_rc(notes_rc_link, title=frame_title, article=notes_html)
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

    def save_bad_notes(self):
        bad_notes = f'''
<!DOCTYPE html>
<html lang="{self.lang_code}">
    <head data-suburl="">
        <title>NON-MATCHING NOTES</title>
        <meta charset="utf-8">
    </head>
    <body>
        <p>NON-MATCHING NOTES (i.e. not found in the frame text as written):</p>
        <ul>
'''
        for cf in sorted(self.bad_links.keys()):
            bad_notes += f'''
<li>
    <a href="{self.html_file}#obs-tn-{cf}" title="See in the OBS tN Docs (HTML)" target="obs-tn-html">{cf}</a>
    <a href="https://git.door43.org/{self.main_resource.owner}/{self.lang_code}_obs-tn/src/branch/master/content/{cf.split('-')[0]}/{cf.split('-')[1]}.md" style="text-decoration:none" target="obs-tn-git">
        <img src="http://www.myiconfinder.com/uploads/iconsets/16-16-65222a067a7152473c9cc51c05b85695-note.png" title="See OBS UTN note on DCS">
    </a>
    <a href="https://git.door43.org/{self.resources['obs'].owner}/{self.lang_code}_obs/src/branch/master/content/{cf.split('-')[0]}.md" style="text-decoration:none" target="obs-git">
        <img src="https://cdn3.iconfinder.com/data/icons/linecons-free-vector-icons-pack/32/photo-16.png" title="See OBS story on DCS">
    </a>:
    <br/>
    <i>{self.bad_links[cf]['text']}</i>
    <br/>
    <ul>
'''
            for note in self.bad_links[cf]['notes']:
                for key in note.keys():
                    if note[key]:
                        bad_notes += f'''
        <li>
            <b><i>{key}</i></b>
            <br/>{note[key]} (QUOTE ISSUE)
        </li>
'''
                    else:
                        bad_notes += f'''
        <li>
            <b><i>{key}</i></b>
        </li>
'''
            bad_notes += '''
    </ul>
</li>'''
        bad_notes += '''
        </ul>
    </body>
</html>
'''
        save_file = os.path.join(self.output_dir, f'{self.file_id}_bad_notes.html')
        write_file(save_file, bad_notes)
        self.logger.info(f'BAD NOTES file can be found at {save_file}')

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
