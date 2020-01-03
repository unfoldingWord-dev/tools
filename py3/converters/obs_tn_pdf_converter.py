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
from .rc_link import ResourceContainerLink
from .pdf_converter import PdfConverter, run_converter
from ..general_tools.file_utils import write_file, load_json_object, read_file

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
                            source_rc = f'tw_cat.json {chapter["id"]}/{frame["id"]}'
                            self.add_bad_link(source_rc, item['id'], fix)
        return self._tw_cat

    def get_body_html(self):
        self.logger.info('Generating OBS TN html...')
        tn_html = self.get_obs_tn_html()
        ta_html = self.get_ta_html()
        tw_html = self.get_tw_html()
        body_html = '\n'.join([tn_html, tw_html, ta_html])
        return body_html

    def get_obs_tn_html(self):
        obs_tn_html = f'''
<section id="obs-sn">
    <div class="resource-title-page no-header">
        <img src="images/{self.resources['obs'].logo}.png" class="logo" alt="UTN">
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
                    frame_id = f'obs-tn-{chapter_num}-{frame_num}'
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
                    if frame_html:
                        frame_html = f'''
            <div id="{frame_id}-text" class="frame-text">
                {frame_html}
            </div>
'''
                    if notes_html:
                        notes_html = f'''
            <div id="{frame_id}-notes" class="frame-notes">
                {notes_html}
            </div>
'''
                    obs_tn_html += f'''
        <div id="{frame_id}">
            <h3>{frame_title}</h3>
            {frame_html}
            {notes_html}
        </div>
'''
                    if frame_idx < len(frames) - 1:
                        obs_tn_html += '<hr class="frame-divider"/>\n'
                    # HANDLE RC LINKS FOR FRAME
                    frame_rc = f'rc://{self.lang_code}/obs-tn/help/{chapter_num}/{frame_num}'
                    self.rcs[frame_rc] = {
                        'rc': frame_rc,
                        'id': frame_id,
                        'link': f'#{frame_id}',
                        'title': frame_title
                    }
                    self.crawl_ta_tw_deep_linking(notes_html, frame_rc)
                obs_tn_html += '''
    </article>
'''
        obs_tn_html += '''
</section>
'''
        return obs_tn_html

    def has_tn_references(self, source_rc):
        if source_rc.rc_link not in self.rc_references:
            return False
        for rc in self.rc_references[source_rc.rc_link]:
            if rc.resource == 'obs-tn':
                return True
        return False

    def get_go_back_to_html(self, rc):
        if not self.has_tn_references(rc):
            return ''
        references = []
        done = {}
        for reference in self.rc_references[rc]:
            if '/obs-tn/' in reference and reference not in done:
                parts = reference[5:].split('/')
                frame_id = f'obs-tn-{parts[3]}-{parts[4]}'
                frame_title = f'{parts[3]}:{parts[4]}'
                references.append(f'<a href="#{frame_id}">{frame_title}</a>')
                done[reference] = True
        go_back_to_html = ''
        if len(references):
            references_str = '; '.join(references)
            go_back_to_html = f'''
    <p class="go-back">
        (<b>{self.translate('go_back_to')}:</b> {references_str})
    </p>
'''
        return go_back_to_html

    def fix_tw_links(self, text, group):
        text = re.sub(r'href="\.\./([^/)]+?)(\.md)*"', rf'href="rc://{self.lang_code}/tw/dict/bible/{group}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^)]+?)(\.md)*"', rf'href="rc://{self.lang_code}/tw/dict/bible/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'(\(|\[\[)(\.\./)*(kt|names|other)/([^)]+?)(\.md)*(\)|\]\])(?!\[)',
                      rf'[[rc://{self.lang_code}/tw/dict/bible/\3/\4]]', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_ta_links(self, text, manual):
        text = re.sub(r'href="\.\./([^/"]+)/01\.md"', rf'href="rc://{self.lang_code}/ta/man/{manual}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./\.\./([^/"]+)/([^/"]+)/01\.md"', rf'href="rc://{self.lang_code}/ta/man/\1/\2"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="([^# :/"]+)"', rf'href="rc://{self.lang_code}/ta/man/{manual}/\1"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text

    def save_bad_notes(self):
        bad_notes = '<!DOCTYPE html><html lang="en-US"><head data-suburl=""><title>NON-MATCHING NOTES</title><meta charset="utf-8"></head><body><p>NON-MATCHING NOTES (i.e. not found in the frame text as written):</p><ul>'
        for cf in sorted(self.bad_notes.keys()):
            bad_notes += '<li><a href="{0}_html/{0}.html#obs-tn-{1}" title="See in the OBS tN Docs (HTML)" target="obs-tn-html">{1}</a><a href="https://git.door43.org/{6}/{2}_obs-tn/src/branch/{7}/content/{3}/{4}.md" style="text-decoration:none" target="obs-tn-git"><img src="http://www.myiconfinder.com/uploads/iconsets/16-16-65222a067a7152473c9cc51c05b85695-note.png" title="See OBS UTN note on DCS"></a><a href="https://git.door43.org/{6}/{2}_obs/src/branch/master/content/{3}.md" style="text-decoration:none" target="obs-git"><img src="https://cdn3.iconfinder.com/data/icons/linecons-free-vector-icons-pack/32/photo-16.png" title="See OBS story on DCS"></a>:<br/><i>{5}</i><br/><ul>'.format(
                self.file_id, cf, self.lang_code, cf.split('-')[0], cf.split('-')[1], self.bad_notes[cf]['text'],
                self.owner, DEFAULT_TAG)
            for note in self.bad_notes[cf]['notes']:
                for key in note.keys():
                    if note[key]:
                        bad_notes += f'<li><b><i>{key}</i></b><br/>{note[key]} (QUOTE ISSUE)</li>'
                    else:
                        bad_notes += f'<li><b><i>{key}</i></b></li>'
            bad_notes += '</ul></li>'
        bad_notes += "</u></body></html>"
        save_file = os.path.join(self.output_dir, f'{self.file_id}_bad_notes.html')
        write_file(save_file, bad_notes)
        self.logger.info(f'BAD NOTES file can be found at {save_file}')


if __name__ == '__main__':
    run_converter(['obs-tn', 'obs', 'ta', 'tw'], ObsTnPdfConverter)
