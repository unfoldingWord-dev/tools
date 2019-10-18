#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF OBS tN document
"""
from __future__ import unicode_literals, print_function
import os
import sys
import re
import logging
import argparse
import tempfile
import markdown2
import shutil
import subprocess
import json
import git
from glob import glob
from bs4 import BeautifulSoup
from ..general_tools.file_utils import write_file, read_file, load_json_object, unzip, load_yaml_object

_print = print
DEFAULT_LANG = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'

OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']


def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


class TnConverter(object):
    def __init__(self, tn_tag=None, obs_tag=None, tw_tag=None, ta_tag=None, working_dir=None, output_dir=None,
                 lang_code=DEFAULT_LANG, owner=DEFAULT_OWNER, regenerate=False, logger=None):
        self.tn_tag = tn_tag
        self.obs_tag = obs_tag
        self.tw_tag = tw_tag
        self.ta_tag = ta_tag
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.owner = owner
        self.regenerate = regenerate
        self.logger = logger

        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='obs-tn-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.info('WORKING DIR IS {0} FOR {1}'.format(self.working_dir, self.lang_code))

        self.tn_dir = os.path.join(self.working_dir, '{0}_obs-tn'.format(lang_code))
        self.obs_dir = os.path.join(self.working_dir, '{0}_obs'.format(lang_code))
        self.tw_dir = os.path.join(self.working_dir, '{0}_tw'.format(lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(lang_code))

        self.html_dir = None
        self.manifest = None
        self.tn_text = ''
        self.tw_text = ''
        self.ta_text = ''
        self.bad_links = {}
        self.resource_data = {}
        self.rc_references = {}
        self.tn_content = ''
        self.version = None
        self.publisher = None
        self.contributors = None
        self.issued = None
        self.id = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.generation_info = {}
        self.id = '{0}_obs-tn_{1}'.format(lang_code, tn_tag)
        self.title = 'unfoldingWord® Open Bible Stories Translation Notes'

    def run(self):
        self.load_resource_data()
        self.setup_resource_files()
        self.id = '{0}_obs-tn_{1}_{2}'.format(self.lang_code, self.tn_tag, self.generation_info['obs-tn']['commit'])
        self.determine_if_regeneration_needed()
        self.html_dir = os.path.join(self.output_dir, '{0}_html'.format(self.id))
        self.manifest = load_yaml_object(os.path.join(self.tn_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        self.title = self.manifest['dublin_core']['title']
        self.contributors = '; '.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        self.id = self.id
        if self.regenerate or not os.path.exists(os.path.join(self.html_dir, '{0}.html'.format(self.id))):
            self.logger.info('Creating OBS tN HTML files for {0}...'.format(self.id))
            if not os.path.isdir(self.html_dir):
                os.makedirs(self.html_dir)
            self.bad_links = {}
            self.bad_notes = {}
            self.resource_data = {}
            self.rc_references = {}
            self.generate_tn_content()
            self.logger.info('Generating Body HTML for {0}...'.format(self.id))
            self.generate_body_html()
            self.logger.info('Generating Cover HTML for {0}...'.format(self.id))
            self.generate_cover_html()
            self.logger.info('Generating License HTML for {0}...'.format(self.id))
            self.generate_license_html()
            self.logger.info('Copying header file... for {0}...'.format(self.id))
            header_file = os.path.join(self.my_path, 'header.html')
            shutil.copy2(header_file, self.html_dir)
            self.logger.info('Copying style sheet file for {0}...'.format(self.id))
            style_file = os.path.join(self.my_path, 'style.css')
            shutil.copy2(style_file, self.html_dir)
            self.save_resource_data()
            self.save_bad_links()
            self.save_bad_notes()
        if self.regenerate or not os.path.exists(os.path.join(self.output_dir, '{0}.pdf'.format(self.id))):
            self.logger.info('Generating PDF {0}/{1}.pdf...'.format(self.output_dir, self.id))
            self.generate_tn_pdf()
        else:
            self.logger.info('No PDF generation needed for {0}.'.format(self.id))
        self.logger.info('PDF file can be found at {0}/{1}.pdf'.format(self.output_dir, self.id))

    def save_bad_links(self):
        bad_links = "BAD LINKS:\n"
        for source_rc in sorted(self.bad_links.keys()):
            for rc in sorted(self.bad_links[source_rc].keys()):
                source = source_rc[5:].split('/')
                parts = rc[5:].split('/')
                if source[1] == 'ult':
                    str = '  ULT {0} {1}:{2}: English ULT alignment not found for `{3}` (greek: `{4}`, occurrence: {5})'.format(
                        source[3].upper(), source[4], source[5], self.bad_links[source_rc][rc], parts[3], parts[4])
                else:
                    if source[1] == 'obn-tn':
                        if parts[1] == 'tw':
                            str = '  UGNT'
                        else:
                            str = '  tN'
                        str += ' {0} {1}:{2}'.format(source[3].upper(), source[4], source[5])
                    else:
                        str = '  {0} {1}'.format(source[1], '/'.join(source[3:]))
                    str += ': BAD RC - `{0}`'.format(rc)
                    if self.bad_links[source_rc][rc]:
                        str += ' - change to `{0}`'.format(self.bad_links[source_rc][rc])
                bad_links += "{0}\n".format(str)
        save_file = os.path.join(self.output_dir, '{0}_bad_links.txt'.format(self.id))
        write_file(save_file, bad_links)
        self.logger.info('BAD LINKS file can be found at {0}'.format(save_file))

    def save_bad_notes(self):
        bad_notes = '<!DOCTYPE html><html lang="en-US"><head data-suburl=""><title>NON-MATCHING NOTES</title><meta charset="utf-8"></head><body><p>NON-MATCHING NOTES (i.e. not found in the frame text as written):</p><ul>'
        for cf in sorted(self.bad_notes.keys()):
            bad_notes += '<li><a href="{0}_html/{0}.html#obs-tn-{1}" title="See in the OBS tN Docs (HTML)" target="obs-tn-html">{1}</a><a href="https://git.door43.org/{6}/{2}_obs-tn/src/branch/{7}/content/{3}/{4}.md" style="text-decoration:none" target="obs-tn-git"><img src="http://www.myiconfinder.com/uploads/iconsets/16-16-65222a067a7152473c9cc51c05b85695-note.png" title="See OBS UTN note on DCS"></a><a href="https://git.door43.org/{6}/{2}_obs/src/branch/master/content/{3}.md" style="text-decoration:none" target="obs-git"><img src="https://cdn3.iconfinder.com/data/icons/linecons-free-vector-icons-pack/32/photo-16.png" title="See OBS story on DCS"></a>:<br/><i>{5}</i><br/><ul>'.format(
                self.id, cf, self.lang_code, cf.split('-')[0], cf.split('-')[1], self.bad_notes[cf]['text'], self.owner, DEFAULT_TAG)
            for note in self.bad_notes[cf]['notes']:
                for key in note.keys():
                    if note[key]:
                        bad_notes += '<li><b><i>{0}</i></b><br/>{1} (QUOTE ISSUE)</li>'.format(key, note[key])
                    else:
                        bad_notes += '<li><b><i>{0}</i></b></li>'.format(key)
            bad_notes += '</ul></li>'
        bad_notes += "</u></body></html>"
        save_file = os.path.join(self.output_dir, '{0}_bad_notes.html'.format(self.id))
        write_file(save_file, bad_notes)
        self.logger.info('BAD NOTES file can be found at {0}'.format(save_file))

    @staticmethod
    def get_resource_git_url(resource, lang, owner):
        return 'https://git.door43.org/{0}/{1}_{2}.git'.format(owner, lang, resource)

    def clone_resource(self, resource, tag=DEFAULT_TAG, url=None):
        if not url:
            url = self.get_resource_git_url(resource, self.lang_code, self.owner)
        repo_dir = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource))
        try:
            git.Repo.clone_from(url, repo_dir)
        except git.GitCommandError:
            owners = OWNERS
            owners.insert(0, self.owner)
            languages = [self.lang_code, DEFAULT_LANG]
            if not os.path.isdir(repo_dir):
                for lang in languages:
                    for owner in owners:
                        url = self.get_resource_git_url(resource, lang, owner)
                        try:
                            git.Repo.clone_from(url, repo_dir)
                        except git.GitCommandError:
                            continue
                        break
                    if os.path.isdir(repo_dir):
                        break
        g = git.Git(repo_dir)
        g.checkout(tag)
        if tag == DEFAULT_TAG:
            g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource('obs-tn', self.tn_tag)
        self.clone_resource('obs', self.obs_tag)
        self.clone_resource('tw', self.tw_tag)
        self.clone_resource('ta', self.ta_tag)
        if not os.path.isfile(os.path.join(self.working_dir, 'icon-obs-tn.png')):
            command = 'curl -o {0}/icon-obs-tn.png https://cdn.door43.org/assets/uw-icons/logo-obs-256.png'.format(
                self.working_dir)
            subprocess.call(command, shell=True)

    def determine_if_regeneration_needed(self):
        # check if any commit hashes have changed
        old_info = self.get_previous_generation_info()
        if not old_info:
            self.logger.info('Looks like this is a new commit of {0}. Generating PDF.'.format(self.id))
            self.regenerate = True
        else:
            for resource in self.generation_info:
                if resource in old_info and resource in self.generation_info \
                        and (old_info[resource]['tag'] != self.generation_info[resource]['tag']
                             or old_info[resource]['commit'] != self.generation_info[resource]['commit']):
                    self.logger.info('Resource {0} has changed: {1} => {2}, {3} => {4}. REGENERATING PDF.'.format(
                        resource, old_info[resource]['tag'], self.generation_info[resource]['tag'],
                        old_info[resource]['commit'], self.generation_info[resource]['commit']
                    ))
                    self.regenerate = True

    def get_contributors_html(self):
        if self.contributors and len(self.contributors):
            return '<div id="contributors" class="article">\n<h1 class="section-header">Contributors</h1>\n<p>{0}</p></div>'.format(
                self.contributors)
        else:
            return ''

    def save_resource_data(self):
        save_dir = os.path.join(self.output_dir, '{0}_resource_data'.format(self.id))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}.json'.format(self.id))
        write_file(save_file, self.resource_data)
        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.id))
        write_file(save_file, self.rc_references)
        save_file = os.path.join(save_dir, '{0}_bad_links.json'.format(self.id))
        write_file(save_file, self.bad_links)
        save_file = os.path.join(save_dir, '{0}_bad_notes.json'.format(self.id))
        write_file(save_file, self.bad_notes)
        save_file = os.path.join(save_dir, '{0}_info.json'.format(self.id))
        write_file(save_file, self.generation_info)

    def get_previous_generation_info(self):
        save_dir = os.path.join(self.output_dir, '{0}_resource_data'.format(self.id))
        save_file = os.path.join(save_dir, '{0}_info.json'.format(self.id))
        if os.path.isfile(save_file):
            return load_json_object(save_file)
        else:
            return {}

    def load_resource_data(self):
        save_dir = os.path.join(self.output_dir, '{0}_resource_data'.format(self.id))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        save_file = os.path.join(save_dir, '{0}.json'.format(self.id))
        if os.path.isfile(save_file):
            self.resource_data = load_json_object(save_file)

        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.id))
        if os.path.isfile(save_file):
            self.rc_references = load_json_object(save_file)

        save_file = os.path.join(save_dir, '{0}_bad_links.json'.format(self.id))
        if os.path.isfile(save_file):
            self.bad_links = load_json_object(save_file)

    def generate_body_html(self):
        tn_html = self.tn_content
        ta_html = self.get_ta_html()
        tw_html = self.get_tw_html()
        contributors_html = self.get_contributors_html()
        html = '\n'.join([tn_html, tw_html, ta_html, contributors_html])
        html = self.replace_rc_links(html)
        html = self.fix_links(html)
        html = '<!DOCTYPE html><html lang="en-US"><head data-suburl=""><meta charset="utf-8"><title>{0} - v{1}</title></head><body>{2}</body></html>\n'.format(
            self.title, self.version, html)
        soup = BeautifulSoup(html, 'html.parser')

        # Make all headers that have a header right before them non-break
        for h in soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6']):
            prev = h.find_previous_sibling()
            if prev and re.match('^h[2-6]$', prev.name):
                h['class'] = h.get('class', []) + ['no-break']

                # Make all headers within the page content to just be span tags with h# classes
        for h in soup.find_all(['h3', 'h4', 'h5', 'h6']):
            if not h.get('class') or 'section-header' not in h['class']:
                h['class'] = h.get('class', []) + [h.name]
                h.name = 'span'

        soup.head.append(soup.new_tag('link', href="style.css", rel="stylesheet"))

        html_file = os.path.join(self.html_dir, '{0}.html'.format(self.id))
        write_file(html_file, unicode(soup))
        self.logger.info('Wrote HTML to {0}'.format(html_file))

    def generate_cover_html(self):
        cover_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="cover">
    <img src="https://cdn.door43.org/assets/uw-icons/logo-obs-256.png" width="120">
    <span class="h1">{0}</span>
    <span class="h3">Version {1}</span>
  </div>
</body>
</html>
'''.format(self.title, self.version)
        html_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.id))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        license_file = os.path.join(self.tn_dir, 'LICENSE.md')
        license = markdown2.markdown_path(license_file)
        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
    <p>
      <strong>Date:</strong> {0}<br/>
      <strong>Version:</strong> {1}<br/>
      <strong>Published by:</strong> {2}<br/>
    </p>
    {3}
  </div>
</body>
</html>'''.format(self.issued, self.version, self.publisher, license)
        html_file = os.path.join(self.html_dir, 'license.html')
        write_file(html_file, license_html)

    def generate_tn_pdf(self):
        cover_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.id))
        license_file = os.path.join(self.html_dir, 'license.html')
        header_file = os.path.join(self.html_dir, 'header.html')
        body_file = os.path.join(self.html_dir, '{0}.html'.format(self.id))
        output_file = os.path.join(self.output_dir, '{0}.pdf'.format(self.id))
        template_file = os.path.join(self.my_path, 'toc_template.xsl')
        command = '''wkhtmltopdf 
                        --javascript-delay 2000 
                        --encoding utf-8 
                        --outline-depth 3 
                        -O portrait 
                        -L 15 -R 15 -T 15 -B 15 
                        --header-html "{0}" --header-spacing 2 
                        --footer-center '[page]' 
                        cover "{1}" 
                        cover "{2}" 
                        toc 
                        --disable-dotted-lines 
                        --enable-external-links 
                        --xsl-style-sheet "{3}" 
                        "{4}" 
                        "{5}"
                    '''.format(header_file, cover_file, license_file, template_file, body_file, output_file)
        command = re.sub(r'\s+', ' ', command, flags=re.MULTILINE)
        self.logger.info(command)
        subprocess.call(command, shell=True)

    @staticmethod
    def highlight_text(text, note):
        parts = re.split(r"\s*…\s*|\s*\.\.\.\s*", note)
        pattern = ''
        replace = ''
        for idx, part in enumerate(parts):
            if idx > 0:
                pattern += '(.*?)'
                replace += r'\{0}'.format(idx)
            pattern += re.escape(part)
            replace += r'<b>{0}</b>'.format(part)
        new_text = re.sub(pattern, replace, text)
        return new_text

    def generate_tn_content(self):
        ignore = ['A Bible story from', 'Connecting Statement', 'Connecting Statement:',
                  'General Information', 'General Note', 'Information générale',
                  'Termes Importants', 'Une histoire biblique tirée de', 'Une histoire de la Bible tirée de',
                  'Une histoire de la Bible à partir', 'Une histoire de la Bible à partir de',
                  'Mots de Traduction', 'Nota geral', 'Déclaration de connexion', 'Cette histoire biblique est tirée',
                  'Une histoire biblique tirée de:', 'Informations générales', 'Information Générale']
        content = ''
        chapter_dirs = sorted(glob(os.path.join(self.tn_dir, 'content', '*')))
        for chapter_dir in chapter_dirs:
            if os.path.isdir(chapter_dir):
                chapter = os.path.basename(chapter_dir)
                soup = BeautifulSoup(
                    markdown2.markdown_path(os.path.join(self.obs_dir, 'content', '{0}.md'.format(chapter))),
                    'html.parser')
                title = soup.h1.text
                paragraphs = soup.find_all('p')
                frames = []
                for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                    if idx % 2:
                        frames.append(p.text)
                content += '<div id="chapter-{0}" class="chapter break">\n\n'.format(chapter)
                content += '<h1>{0}</h1>\n'.format(title)
                frame_files = sorted(glob(os.path.join(chapter_dir, '*.md')))
                for frame_file in frame_files:
                    frame = os.path.splitext(os.path.basename(frame_file))[0]
                    frame_idx = int(frame)
                    id = 'obs-tn-{0}-{1}'.format(chapter, frame)
                    content += '<div id="{0}" class="frame">\n'.format(id)
                    content += '<h2>{0}-{1}</h2>\n'.format(chapter, frame)
                    text = ''
                    orig_text = ''
                    if frame_idx > 0:
                        text = re.sub(r'[\n\s]+', ' ', frames[frame_idx - 1], flags=re.MULTILINE)
                        orig_text = text
                    frame_html = markdown2.markdown_path(frame_file)
                    frame_html = frame_html.replace('h1>', 'h3>')
                    frame_html = re.sub(r'href="(\d+)/(\d+)"', r'href="#obs-tn-\1-\2"', frame_html)
                    if text:
                        notes_to_highlight = []
                        soup = BeautifulSoup(frame_html, 'html.parser')
                        headers = soup.find_all('h3')
                        for header in headers:
                            notes_to_highlight.append(header.text)
                        notes_to_highlight.sort(lambda x, y: cmp(len(y), len(x)))
                        for note in notes_to_highlight:
                            if self.highlight_text(orig_text, note) != orig_text:
                                if len(note) <= 60:
                                    text = self.highlight_text(text, note)
                            elif note not in ignore:
                                cf = '{0}-{1}'.format(chapter, frame)
                                if cf not in self.bad_notes:
                                    self.bad_notes[cf] = {
                                        'text': orig_text,
                                        'notes': []
                                    }
                                bad_note = {note: None}
                                alt_notes = [
                                    note.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                                    note.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                                    note.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                                    note.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                                    note.replace('“', '"').replace('”', '"'),
                                    note.replace('"', '”').replace('”', '“', 1),
                                    note.replace("'", '’').replace('’', '‘', 1),
                                    note.replace("'", '’'),
                                    note.replace('’', "'"),
                                    note.replace('‘', "'")]
                                for alt_note in alt_notes:
                                    if orig_text != self.highlight_text(orig_text, alt_note):
                                        bad_note[note] = alt_note
                                        break
                                self.bad_notes[cf]['notes'].append(bad_note)
                    content += '<div id="{0}-text" class="frame-text">\n{1}\n</div>\n'.format(id, text)
                    content += frame_html
                    content += '</div>\n\n'
                    # HANDLE RC LINKS
                    rc = 'rc://{0}/obs-tn/help/{1}/{2}'.format(self.lang_code, chapter, frame)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': id,
                        'link': '#' + id,
                        'title': title
                    }
                    self.get_resource_data_from_rc_links(frame_html, rc)
                content += '</div>\n\n'
        self.tn_content = content
        write_file(os.path.join(self.html_dir, '{0}_tn_content.html'.format(self.id)),
                   BeautifulSoup(content, 'html.parser').prettify())

    def get_tw_html(self):
        tw_html = ''
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/tw/' not in rc:
                continue
            html = self.resource_data[rc]['text']
            html = self.increase_headers(html)
            title = self.resource_data[rc]['title']
            alt_title = self.resource_data[rc]['alt_title']
            if alt_title:
                html = '<h2 class="hidden">{0}</h2><span class="h2 section-header">{1}</span>\n{2}{3}'.format(alt_title,
                                                                                                              title,
                                                                                                              self.get_reference_text(
                                                                                                                  rc),
                                                                                                              html)
            else:
                html = '<h2 class="section-header">{0}</h2>\n{1}{2}'.format(title, self.get_reference_text(rc), html)
            tw_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(self.resource_data[rc]['id'], html)
        if tw_html:
            tw_html = '<div id="tw" class="resource-title-page">\n<h1 class="section-header">Translation Words</h1>\n</div>\n\n' + tw_html
        return tw_html

    def get_ta_html(self):
        ta_html = '<div id="ta" class="resource-title-page">\n<h1 class="section-header">Translation Academy</h1>\n</div>\n\n'
        sorted_rcs = sorted(self.resource_data.keys(), key=lambda k: self.resource_data[k]['title'].lower())
        for rc in sorted_rcs:
            if '/ta/' not in rc:
                continue
            if self.resource_data[rc]['text']:
                html = self.resource_data[rc]['text']
                html = self.increase_headers(html)
                html = '<h2 class="section-header">{0}</h2>\n{1}<b>{2}</b>\n<br>{3}\n'.format(
                    self.resource_data[rc]['title'], self.get_reference_text(rc), self.resource_data[rc]['alt_title'],
                    html)
                ta_html += '<div id="{0}" class="article">\n{1}\n</div>\n\n'.format(self.resource_data[rc]['id'], html)
        return ta_html

    def get_reference_text(self, rc):
        uses = ''
        references = []
        done = {}
        for reference in self.rc_references[rc]:
            if '/tn/' in reference and reference not in done:
                parts = reference[5:].split('/')
                id = 'obs-tn-{0}-{1}'.format(parts[4], parts[5])
                text = '{0}:{1}'.format(parts[4].lstrip('0'), parts[5].lstrip('0'))
                references.append('<a href="#{0}">{1}</a>'.format(id, text))
                done[reference] = True
        if len(references):
            uses = '<p>\n(<b>Go back to:</b> {0})\n</p>\n'.format('; '.join(references))
        return uses

    def get_resource_data_from_rc_links(self, text, source_rc):
        rcs = re.findall(r'rc://[A-Z0-9/_\*-]+', text, flags=re.IGNORECASE | re.MULTILINE)
        for rc in rcs:
            parts = rc[5:].split('/')
            resource = parts[1]
            path = '/'.join(parts[3:])

            if resource not in ['ta', 'tw']:
                continue

            if rc not in self.rc_references:
                self.rc_references[rc] = []
            if source_rc not in self.rc_references[rc]:
                self.rc_references[rc].append(source_rc)
            title = ''
            t = ''
            anchor_id = '{0}-{1}'.format(resource, path.replace('/', '-'))
            link = '#{0}'.format(anchor_id)
            file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                     '{0}.md'.format(path))
            if not os.path.isfile(file_path):
                file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                         '{0}/01.md'.format(path))
            fix = None
            if not os.path.isfile(file_path):
                if resource == 'tw':
                    for category in ['kt', 'other', 'names']:
                        path2 = re.sub(r'^bible/([^/]+)/', r'bible/{0}/'.format(category), path.lower())
                        fix = 'rc://{0}/tw/dict/{1}'.format(self.lang_code, path2)
                        anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                        link = '#{0}'.format(anchor_id)
                        file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                                 '{0}.md'.format(path2))
                        if os.path.isfile(file_path):
                            break
                elif resource == 'ta':
                    bad_names = {
                        'figs-abstractnoun': 'translate/figs-abstractnouns'
                    }
                    if parts[3] in bad_names:
                        path2 = bad_names[parts[3]]
                    else:
                        path2 = path
                    fix = 'rc://{0}/ta/man/{1}'.format(self.lang_code, path2)
                    anchor_id = '{0}-{1}'.format(resource, path2.replace('/', '-'))
                    link = '#{0}'.format(anchor_id)
                    file_path = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource),
                                             '{0}/01.md'.format(path2))

            if os.path.isfile(file_path):
                if fix:
                    if source_rc not in self.bad_links:
                        self.bad_links[source_rc] = {}
                    self.bad_links[source_rc][rc] = fix
                if not rc in self.resource_data:
                    t = markdown2.markdown_path(file_path)
                    alt_title = ''
                    if resource == 'ta':
                        title_file = os.path.join(os.path.dirname(file_path), 'title.md')
                        question_file = os.path.join(os.path.dirname(file_path), 'sub-title.md')
                        if os.path.isfile(title_file):
                            title = read_file(title_file)
                        else:
                            title = self.get_first_header(t)
                            t = re.sub(r'\s*\n*\s*<h\d>[^<]+</h\d>\s*\n*', r'', t, 1,
                                       flags=re.IGNORECASE | re.MULTILINE)  # removes the header
                        if os.path.isfile(question_file):
                            question = read_file(question_file)
                            alt_title = 'This page answers the question: <i>{0}</i>'.format(question)
                        t = self.fix_ta_links(t, path.split('/')[0])
                    elif resource == 'tw':
                        title = self.get_first_header(t)
                        t = re.sub(r'\s*\n*\s*<h\d>[^<]+</h\d>\s*\n*', r'', t, 1,
                                   flags=re.IGNORECASE | re.MULTILINE)  # removes the header
                        if len(title) > 70:
                            alt_title = ','.join(title[:70].split(',')[:-1]) + ', ...'
                        t = re.sub(r'\n*\s*\(See [^\n]*\)\s*\n*', '\n\n', t,
                                   flags=re.IGNORECASE | re.MULTILINE)  # removes the See also line
                        t = self.fix_tw_links(t, path.split('/')[1])
                    self.resource_data[rc] = {
                        'rc': rc,
                        'link': link,
                        'id': anchor_id,
                        'title': title,
                        'alt_title': alt_title,
                        'text': t,
                        'references': [source_rc]
                    }
                    self.get_resource_data_from_rc_links(t, rc)
                else:
                    if source_rc not in self.resource_data[rc]['references']:
                        self.resource_data[rc]['references'].append(source_rc)
            else:
                if source_rc not in self.bad_links:
                    self.bad_links[source_rc] = {}
                if rc not in self.bad_links[source_rc]:
                    self.bad_links[source_rc][rc] = None

    @staticmethod
    def increase_headers(text, increase_depth=1):
        if text:
            for num in range(5, 0, -1):
                text = re.sub(r'<h{0}>\s*(.+?)\s*</h{0}>'.format(num), r'<h{0}>\1</h{0}>'.format(num + increase_depth),
                              text, flags=re.MULTILINE)
        return text

    @staticmethod
    def decrease_headers(text, minimum_header=1, decrease=1):
        if text:
            for num in range(minimum_header, minimum_header + 10):
                text = re.sub(r'<h{0}>\s*(.+?)\s*</h{0}>'.format(num),
                              r'<h{0}>\1</h{0}>'.format(num - decrease if (num - decrease) <= 5 else 5), text,
                              flags=re.MULTILINE)
        return text

    @staticmethod
    def get_first_header(text):
        lines = text.split('\n')
        if len(lines):
            for line in lines:
                if re.match(r'<h1>', line):
                    return re.sub(r'<h1>(.*?)</h1>', r'\1', line)
            return lines[0]
        return "NO TITLE"

    def fix_tn_links(self, text, chapter):
        text = re.sub(r'<a href="\.\./\.\./([^"]+)">([^<]+)</a>', r'\2', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)/([^"]+?)(\.md)*"', r'href="#tn-\1-\2"', text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^"]+?)(\.md)*"', r'href="#tn-\1"', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\./([^"]+?)(\.md)*"', r'href="#tn-{1}-\1"'.format(self.pad(chapter)), text,
                      flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\n__.*\|.*', r'', text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_tw_links(self, text, group):
        text = re.sub(r'href="\.\./([^/)]+?)(\.md)*"', r'href="rc://{0}/tw/dict/bible/{1}/\1"'.
                      format(self.lang_code, group), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./([^)]+?)(\.md)*"', r'href="rc://{0}/tw/dict/bible/\1"'.format(self.lang_code),
                      text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'(\(|\[\[)(\.\./)*(kt|names|other)/([^)]+?)(\.md)*(\)|\]\])(?!\[)',
                      r'[[rc://{0}/tw/dict/bible/\3/\4]]'.format(self.lang_code), text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_ta_links(self, text, manual):
        text = re.sub(r'href="\.\./([^/"]+)/01\.md"', r'href="rc://{0}/ta/man/{1}/\1"'.format(self.lang_code, manual),
                      text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="\.\./\.\./([^/"]+)/([^/"]+)/01\.md"', r'href="rc://{0}/ta/man/\1/\2"'.
                      format(self.lang_code), text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'href="([^# :/"]+)"', r'href="rc://{0}/ta/man/{1}/\1"'.format(self.lang_code, manual), text,
                      flags=re.IGNORECASE | re.MULTILINE)
        return text

    def replace(self, m):
        before = m.group(1)
        rc = m.group(2)
        after = m.group(3)
        if rc not in self.resource_data:
            return m.group()
        info = self.resource_data[rc]
        if (before == '[[' and after == ']]') or (before == '(' and after == ')') or before == ' ':
            return '<a href="{0}">{1}</a>'.format(info['link'], info['title'])
        if (before == '"' and after == '"') or (before == "'" and after == "'"):
            return info['link']
        self.logger.error("FOUND SOME MALFORMED RC LINKS: {0}".format(m.group()))
        return m.group()

    def replace_rc_links(self, text):
        # Change rc://... rc links to proper HTML links based on that links title and link to its article
        write_file(os.path.join(self.html_dir, '{0}_tn_content_rc1.html'.format(self.id)),
                   BeautifulSoup(text, 'html.parser').prettify())
        if self.lang_code != DEFAULT_LANG:
            text = re.sub('rc://en', 'rc://{0}'.format(self.lang_code), text, flags=re.IGNORECASE)
        joined = '|'.join(map(re.escape, self.resource_data.keys()))
        pattern = r'(\[\[|\(|["\']| |)\b(' + joined + r')\b(\]\]|\)|["\']|)(?!\]\)")'

        text = re.sub(pattern, self.replace, text, flags=re.IGNORECASE)
        # Remove other scripture reference not in this tN
        text = re.sub(r'<a[^>]+rc://[^>]+>([^>]+)</a>', r'\1', text, flags=re.IGNORECASE | re.MULTILINE)
        write_file(os.path.join(self.html_dir, '{0}_tn_content_rc2.html'.format(self.id)),
                   BeautifulSoup(text, 'html.parser').prettify())
        return text

    def fix_links(self, text):
        # Change [[http.*]] to <a href="http\1">http\1</a>
        text = re.sub(r'\[\[http([^\]]+)\]\]', r'<a href="http\1">http\1</a>', text, flags=re.IGNORECASE)

        # convert URLs to links if not already
        text = re.sub(r'([^">])((http|https|ftp)://[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])',
                      r'\1<a href="\2">\2</a>', text, flags=re.IGNORECASE)

        # URLS wth just www at the start, no http
        text = re.sub(r'([^\/])(www\.[A-Za-z0-9\/\?&_\.:=#-]+[A-Za-z0-9\/\?&_:=#-])', r'\1<a href="http://\2">\2</a>',
                      text, flags=re.IGNORECASE)

        # Removes leading 0s from verse references
        text = re.sub(r' 0*(\d+):0*(\d+)(-*)0*(\d*)', r' \1:\2\3\4', text, flags=re.IGNORECASE | re.MULTILINE)

        return text


def main(tn_tag, obs_tag, tw_tag, ta_tag, lang_code, working_dir, output_dir, owner, regenerate, logger):
    _print('Starting TN Converter for {0}...'.format(lang_code))
    tn_converter = TnConverter(tn_tag, obs_tag, tw_tag, ta_tag, working_dir, output_dir, lang_code, owner, regenerate, logger)
    tn_converter.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_codes', required=False, help='Language Code(s)', action='append')
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('--obs-tn-tag', dest='obs_tn', default=DEFAULT_TAG, required=False, help='OBS tN Tag')
    parser.add_argument('--obs-tag', dest='obs', default=DEFAULT_TAG, required=False, help='OBS Tag')
    parser.add_argument('--ta-tag', dest='ta', default=DEFAULT_TAG, required=False, help='tA Tag')
    parser.add_argument('--tw-tag', dest='tw', default=DEFAULT_TAG, required=False, help='tW Tag')
    parser.add_argument('-r', '--regenerate', dest='regenerate', action='store_true',
                        help='Regenerate PDF even if exists')

    args = parser.parse_args(sys.argv[1:])
    obs = args.obs
    if not obs:
        obs = args.obs_tn
    lang_codes = args.lang_codes
    if not lang_codes:
        lang_codes = ['en']

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    for lang_code in lang_codes:
        main(args.obs_tn, obs, args.tw, args.ta, lang_code, args.working_dir, args.output_dir, args.owner,
             args.regenerate, logger)
