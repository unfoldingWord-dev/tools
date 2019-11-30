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
This script generates the HTML and PDF OBS SN document
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
from bs4 import BeautifulSoup
from ..general_tools.file_utils import write_file, read_file, load_json_object, unzip, load_yaml_object
from ..general_tools.url_utils import download_file

_print = print
DEFAULT_LANG = 'en'
DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']
LANGUAGE_FILES = {
    'fr': 'French-fr_FR.json',
    'en': 'English-en_US.json'
}


def print(obj):
    _print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


class ObsSnSqConverter(object):

    def __init__(self, obs_sn_tag=None, obs_sq_tag=None, obs_tag=None, working_dir=None, output_dir=None,
                 lang_code=DEFAULT_LANG, owner=DEFAULT_OWNER, regenerate=False, logger=None):
        self.obs_sn_tag = obs_sn_tag
        self.obs_sq_tag = obs_sq_tag
        self.obs_tag = obs_tag
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.owner = owner
        self.regenerate = regenerate
        self.logger = logger

        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='obs-sn-')
        if not self.output_dir:
            self.output_dir = self.working_dir

        self.logger.info('WORKING DIR IS {0} FOR {1}'.format(self.working_dir, self.lang_code))

        self.obs_sn_dir = os.path.join(self.working_dir, '{0}_obs-sn'.format(lang_code))
        self.obs_sq_dir = os.path.join(self.working_dir, '{0}_obs-sq'.format(lang_code))
        self.obs_dir = os.path.join(self.working_dir, '{0}_obs'.format(lang_code))
        self.html_dir = os.path.join(self.output_dir, 'html')
        if not os.path.isdir(self.html_dir):
            os.makedirs(self.html_dir)

        self.obs_manifest = None
        self.obs_sn_manifest = None
        self.obs_sq_manifest = None
        self.obs_sn_sq_text = ''
        self.bad_notes = {}
        self.resource_data = {}
        self.rc_references = {}
        self.file_id = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.generation_info = {}
        self.title = 'unfoldingWord® Open Bible Stories Study Notes'
        self.translations = {}

    def translate(self, key):
        if not self.translations:
            if self.lang_code not in LANGUAGE_FILES:
                self.logger.error('No locale file for {0}.'.format(self.lang_code))
                exit(1)
            locale_file = os.path.join(self.my_path, '..', 'locale', LANGUAGE_FILES[self.lang_code])
            if not os.path.isfile(locale_file):
                self.logger.error('No locale file found at {0} for {1}.'.format(locale_file, self.lang_code))
                exit(1)
            self.translations = load_json_object(locale_file)
        keys = key.split('.')
        t = self.translations
        for key in keys:
            t = t.get(key, None)
            if t is None:
                # handle the case where the self.translations doesn't have that (sub)key
                self.logger.error("No translation for `{0}`".format(key))
                exit(1)
                break
        return t

    def run(self):
        self.setup_resource_files()
        self.file_id = '{0}_obs-sn-sq_{1}_{2}'.format(self.lang_code, self.obs_sn_tag, self.generation_info['obs-sn']['commit'])
        self.determine_if_regeneration_needed()
        self.obs_manifest = load_yaml_object(os.path.join(self.obs_dir, 'manifest.yaml'))
        self.obs_sn_manifest = load_yaml_object(os.path.join(self.obs_sn_dir, 'manifest.yaml'))
        self.obs_sq_manifest = load_yaml_object(os.path.join(self.obs_sq_dir, 'manifest.yaml'))
        self.file_id = self.file_id
        if self.regenerate or not os.path.exists(os.path.join(self.output_dir, '{0}.html'.format(self.file_id))):
            self.logger.info('Creating OBS SN & SQ HTML files for {0}...'.format(self.file_id))
            self.generate_obs_sn_sq_content()
            self.logger.info('Generating Body HTML for {0}...'.format(self.file_id))
            self.generate_body_html()
            self.logger.info('Generating Cover HTML for {0}...'.format(self.file_id))
            self.generate_cover_html()
            self.logger.info('Generating License HTML for {0}...'.format(self.file_id))
            self.generate_license_html()
            self.logger.info('Copying style sheet file for {0}...'.format(self.file_id))
            style_file = os.path.join(self.my_path, 'style.css')
            shutil.copy2(style_file, self.html_dir)
            self.save_resource_data()
            self.save_bad_notes()
        else:
            self.logger.info('HTML file is already current')
        if self.regenerate or not os.path.exists(os.path.join(self.output_dir, '{0}.pdf'.format(self.file_id))):
            self.logger.info('Generating PDF {0}/{1}.pdf...'.format(self.output_dir, self.file_id))
            self.generate_obs_sn_sq_pdf()
        else:
            self.logger.info('PDF file is already current')
        self.logger.info('PDF file can be found at {0}/{1}.pdf'.format(self.output_dir, self.file_id))

    def save_bad_notes(self):
        bad_notes = '<!DOCTYPE html><html lang="en-US"><head data-suburl=""><title>NON-MATCHING NOTES</title><meta charset="utf-8"></head><body><p>NON-MATCHING NOTES (i.e. not found in the frame text as written):</p><ul>'
        for cf in sorted(self.bad_notes.keys()):
            bad_notes += '<li><a href="html/{0}.html#obs-sn-{1}" title="See in the OBS SN Docs (HTML)" target="obs-sn-html">{1}</a><a href="https://git.door43.org/{6}/{2}_obs-sn/src/branch/{7}/content/{3}/{4}.md" style="text-decoration:none" target="obs-sn-git"><img src="http://www.myiconfinder.com/uploads/iconsets/16-16-65222a067a7152473c9cc51c05b85695-note.png" title="See OBS UTN note on DCS"></a><a href="https://git.door43.org/{6}/{2}_obs/src/branch/master/content/{3}.md" style="text-decoration:none" target="obs-git"><img src="https://cdn3.iconfinder.com/data/icons/linecons-free-vector-icons-pack/32/photo-16.png" title="See OBS story on DCS"></a>:<br/><i>{5}</i><br/><ul>'.format(
                self.file_id, cf, self.lang_code, cf.split('-')[0], cf.split('-')[1], self.bad_notes[cf]['text'], self.owner, DEFAULT_TAG)
            for note in self.bad_notes[cf]['notes']:
                for key in note.keys():
                    if note[key]:
                        bad_notes += '<li><b><i>{0}</i></b><br/>{1} (QUOTE ISSUE)</li>'.format(key, note[key])
                    else:
                        bad_notes += '<li><b><i>{0}</i></b></li>'.format(key)
            bad_notes += '</ul></li>'
        bad_notes += "</u></body></html>"
        save_file = os.path.join(self.output_dir, '{0}_bad_notes.html'.format(self.file_id))
        write_file(save_file, bad_notes)
        self.logger.info('BAD NOTES file can be found at {0}'.format(save_file))

    @staticmethod
    def get_resource_git_url(resource, lang, owner):
        return 'https://git.door43.org/{0}/{1}_{2}.git'.format(owner, lang, resource)

    def clone_resource(self, resource, tag=DEFAULT_TAG, url=None):
        if not url:
            url = self.get_resource_git_url(resource, self.lang_code, self.owner)
        repo_dir = os.path.join(self.working_dir, '{0}_{1}'.format(self.lang_code, resource))
        if not os.path.isdir(repo_dir):
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
            # self.logger.info("NOT PULLING...")
            g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource('obs-sn', self.obs_sn_tag)
        self.clone_resource('obs-sq', self.obs_sn_tag)
        self.clone_resource('obs', self.obs_tag)
        if not os.path.isfile(os.path.join(self.html_dir, 'logo-obs-sn-sq.png')):
            command = 'curl -o {0}/logo-obs-sn-sq.png https://cdn.door43.org/assets/uw-icons/logo-obs-256.png'.format(
                self.html_dir)
            subprocess.call(command, shell=True)

    def determine_if_regeneration_needed(self):
        # check if any commit hashes have changed
        old_info = self.get_previous_generation_info()
        if not old_info:
            self.logger.info('Looks like this is a new commit of {0}. Generating PDF.'.format(self.file_id))
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
        obs_title = self.obs_manifest['dublin_core']['title']
        obs_sn_title = self.obs_sn_manifest['dublin_core']['title']
        obs_sq_title = self.obs_sq_manifest['dublin_core']['title']

        obs_contributors = '<br/>'.join(self.obs_manifest['dublin_core']['contributor'])
        obs_sn_contributors = '<br/>'.join(self.obs_sn_manifest['dublin_core']['contributor'])
        obs_sq_contributors = '<br/>'.join(self.obs_sq_manifest['dublin_core']['contributor'])

        tr_contributors = self.translate('contributors')
        contributors_html = '''
<div id="contributors" class="article">
  <h1 class="section-header">{0}</h1>
'''.format(tr_contributors)
        if obs_contributors and len(obs_contributors):
            contributors_html += '<h2>{0} {1}</h2>\n<p>{2}</p>'.format(obs_title, obs_contributors, tr_contributors)
        if obs_sn_contributors and len(obs_sn_contributors):
            contributors_html += '<h2>{0} {1}</h2>\n<p>{2}</p>'.format(obs_sn_title, obs_sn_contributors,
                                                                       tr_contributors)
        if obs_sq_contributors and len(obs_sq_contributors):
            contributors_html += '<h2>{0} {1}</h2>\n<p>{2}</p>'.format(obs_sq_title, obs_sq_contributors,
                                                                       tr_contributors)
        contributors_html += '</div>'
        return contributors_html

    def save_resource_data(self):
        save_dir = os.path.join(self.output_dir, 'save')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_file = os.path.join(save_dir, '{0}_resource_data.json'.format(self.file_id))
        write_file(save_file, self.resource_data)
        save_file = os.path.join(save_dir, '{0}_references.json'.format(self.file_id))
        write_file(save_file, self.rc_references)
        save_file = os.path.join(save_dir, '{0}_bad_notes.json'.format(self.file_id))
        write_file(save_file, self.bad_notes)
        save_file = os.path.join(save_dir, '{0}_obs-sn-sq_{1}_generation_info.json'.format(self.lang_code,
                                                                                           self.obs_sn_tag))
        write_file(save_file, self.generation_info)

    def get_previous_generation_info(self):
        save_dir = os.path.join(self.output_dir, 'save')
        save_file = os.path.join(save_dir, '{0}_obs-sn-sq_{1}_generation_info.json'.format(self.lang_code,
                                                                                           self.obs_sn_tag))
        if os.path.isfile(save_file):
            return load_json_object(save_file)
        else:
            return {}

    def generate_body_html(self):
        obs_sn_sq_html = self.obs_sn_sq_text
        contributors_html = self.get_contributors_html()
        obs_sn_title = self.obs_sn_manifest['dublin_core']['title']
        obs_sn_version = self.obs_sn_manifest['dublin_core']['version']
        obs_sq_title = self.obs_sq_manifest['dublin_core']['title']
        html = '\n'.join([obs_sn_sq_html, contributors_html])
        html = self.fix_links(html)
        html = self.replace_rc_links(html)
        html = '''<!DOCTYPE html>
<html lang="en-US">
  <head data-suburl="">
    <meta charset="utf-8"/>
    <title>{0} & {1} - v{2}</title>
  </head>
  <body>
{3}
  </body>
</html>
'''.format(obs_sn_title, obs_sq_title, obs_sn_version, html)
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

        soup.head.append(soup.new_tag('link', href="html/style.css", rel="stylesheet"))

        html = unicode(soup)
        html_file = os.path.join(self.output_dir, '{0}.html'.format(self.file_id))
        write_file(html_file, html)
        self.logger.info('Wrote HTML to {0}'.format(html_file))

    def generate_cover_html(self):
        obs_sn_title = self.obs_sn_manifest['dublin_core']['title']
        obs_sn_version = self.obs_sn_manifest['dublin_core']['version']
        obs_sq_title = self.obs_sq_manifest['dublin_core']['title']
        cover_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break" id="cover">
    <img src="logo-obs-sn-sq.png" width="120">
    <span class="h1">{0}<br/>&<br/>{1}</span>
    <span class="h3">{2} {3}</span>
  </div>
</body>
</html>
'''.format(obs_sn_title, obs_sq_title, self.translate('license.version'), obs_sn_version)
        html_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.file_id))
        write_file(html_file, cover_html)

    def generate_license_html(self):
        obs_sn_license_file = os.path.join(self.obs_sn_dir, 'LICENSE.md')
        obs_sn_license = markdown2.markdown_path(obs_sn_license_file)

        obs_title = self.obs_manifest['dublin_core']['title']
        obs_version = self.obs_manifest['dublin_core']['version']
        obs_publisher = self.obs_manifest['dublin_core']['publisher']
        obs_issued = self.obs_manifest['dublin_core']['issued']

        obs_sn_title = self.obs_sn_manifest['dublin_core']['title']
        obs_sn_version = self.obs_sn_manifest['dublin_core']['version']
        obs_sn_publisher = self.obs_sn_manifest['dublin_core']['publisher']
        obs_sn_issued = self.obs_sn_manifest['dublin_core']['issued']

        obs_sq_title = self.obs_sq_manifest['dublin_core']['title']
        obs_sq_version = self.obs_sq_manifest['dublin_core']['version']
        obs_sq_publisher = self.obs_sq_manifest['dublin_core']['publisher']
        obs_sq_issued = self.obs_sq_manifest['dublin_core']['issued']

        license_html = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="style.css" rel="stylesheet"/>
</head>
<body>
  <div class="break">
    <span class="h1">{13}</span>
    <p>
      <strong>{0}</strong><br/>
      <strong>{14}:</strong> {1}<br/>
      <strong>{15}:</strong> {2}<br/>
      <strong>{16}:</strong> {3}<br/>
    </p>
    <p>
      <strong>{4}</strong><br/>
      <strong>{14}:</strong> {5}<br/>
      <strong>{15}:</strong> {6}<br/>
      <strong>{16}:</strong> {7}<br/>
    </p>
    <p>
      <strong>{8}</strong><br/>      
      <strong>{14}:</strong> {9}<br/>
      <strong>{15}:</strong> {10}<br/>
      <strong>{16}:</strong> {11}<br/>
    </p>
    {12}
  </div>
</body>
</html>
'''.format(obs_title, obs_issued, obs_version, obs_publisher,
           obs_sn_title, obs_sn_issued, obs_sn_version, obs_sn_publisher,
           obs_sq_title, obs_sq_issued, obs_sq_version, obs_sq_publisher,
           obs_sn_license,
           self.translate('license.copyrights_and_licensing'),
           self.translate('license.date'),
           self.translate('license.version'),
           self.translate('license.published_by'))
        html_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.file_id))
        write_file(html_file, license_html)

    def generate_obs_sn_sq_pdf(self):
        cover_file = os.path.join(self.html_dir, '{0}_cover.html'.format(self.file_id))
        license_file = os.path.join(self.html_dir, '{0}_license.html'.format(self.file_id))
        header_file = os.path.join(self.my_path, 'header.html')
        footer_file = os.path.join(self.my_path, 'footer.html')
        body_file = os.path.join(self.output_dir, '{0}.html'.format(self.file_id))
        output_file = os.path.join(self.output_dir, '{0}.pdf'.format(self.file_id))
        template_file = os.path.join(self.my_path, '{0}_toc_template.xsl'.format(self.lang_code))
        command = '''wkhtmltopdf 
                        --javascript-delay 2000 
                        --debug-javascript
                        --cache-dir "{6}"
                        --run-script "setInterval(function(){{if(document.readyState=='complete') setTimeout(function() {{window.status='done';}}, 100);}},200)"
                        --encoding utf-8 
                        --outline-depth 3 
                        -O portrait 
                        -L 15 -R 15 -T 15 -B 15 
                        --header-html "{0}"
                        --header-spacing 2
                        --footer-html "{7}" 
                        cover "{1}" 
                        cover "{2}" 
                        toc 
                        --disable-dotted-lines 
                        --enable-external-links 
                        --xsl-style-sheet "{3}" 
                        "{4}" 
                        "{5}"
                    '''.format(header_file, cover_file, license_file, template_file, body_file, output_file,
                               os.path.join(self.working_dir, 'wkhtmltopdf'), footer_file)
        command = re.sub(r'\s+', ' ', command, flags=re.MULTILINE)
        self.logger.info(command)
        subprocess.call(command, shell=True)
        link_file = os.path.join(self.output_dir, '{0}_obs-sn-sq_{1}.pdf'.format(self.lang_code, self.obs_sn_tag))
        subprocess.call('ln -sf "{0}" "{1}"'.format(output_file, link_file), shell=True)

    @staticmethod
    def highlight_text(text, note):
        parts = re.split(r"\s*…\s*|\s*\.\.\.\s*", note)
        processed_text = ''
        to_process_text = text
        for idx, part in enumerate(parts):
            split_pattern = re.escape(part)
            if '<span' in text:
                split_pattern = '({0})'.format(re.sub('(\\\\ )+', '(\s+|(\s*</*span[^>]*>\s*)+)', split_pattern))
            else:
                split_pattern = '({0})'.format(split_pattern)
            splits = re.split(split_pattern, to_process_text, 1)
            processed_text += splits[0]
            if len(splits) > 1:
                processed_text += '<span class="highlight{0}">{1}</span>'.format(' split' if len(parts) > 1 else '',
                                                                                 splits[1])
                if len(splits) > 2:
                    to_process_text = splits[-1]
        if to_process_text:
            processed_text += to_process_text
        return processed_text

    def highlight_text_with_phrases(self, orig_text, phrases, cf):
        ignore = []
        highlighted_text = orig_text
        phrases.sort(key=len, reverse=True)
        for phrase in phrases:
            new_highlighted_text = self.highlight_text(highlighted_text, phrase)
            if new_highlighted_text != highlighted_text:
                highlighted_text = new_highlighted_text
            elif phrase not in ignore:
                if cf not in self.bad_notes:
                    self.bad_notes[cf] = {
                        'text': orig_text,
                        'notes': []
                    }
                bad_note = {phrase: None}
                alt_phrase = [
                    phrase.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                    phrase.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                    phrase.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"'),
                    phrase.replace("'", '’').replace('’', '‘', 1).replace('"', '”').replace('”', '“', 1),
                    phrase.replace('“', '"').replace('”', '"'),
                    phrase.replace('"', '”').replace('”', '“', 1),
                    phrase.replace("'", '’').replace('’', '‘', 1),
                    phrase.replace("'", '’'),
                    phrase.replace('’', "'"),
                    phrase.replace('‘', "'")]
                for alt_phrase in alt_phrase:
                    if orig_text != self.highlight_text(orig_text, alt_phrase):
                        bad_note[phrase] = alt_phrase
                        break
                self.bad_notes[cf]['notes'].append(bad_note)
        return highlighted_text

    def generate_obs_sn_sq_content(self):
        content = ''
        intro_file = os.path.join(self.obs_sq_dir, 'content', '00.md')
        if os.path.isfile(intro_file):
            intro_id = 'obs-sq-intro'
            intro_content = markdown2.markdown_path(intro_file)
            content += '<div id="{0}" class="chapter break">{1}</div>\n\n'.format(intro_id, intro_content)
        for chapter_num in range(1, 51):
            chapter = str(chapter_num).zfill(2)
            obs_chapter_file = os.path.join(self.obs_dir, 'content', '{0}.md'.format(chapter))
            sn_chapter_dir = os.path.join(self.obs_sn_dir, 'content', chapter)
            sq_chapter_file = os.path.join(self.obs_sq_dir, 'content', '{0}.md'.format(chapter))
            if os.path.isfile(obs_chapter_file):
                soup = BeautifulSoup(
                    markdown2.markdown_path(os.path.join(self.obs_dir, 'content', '{0}.md'.format(chapter))),
                    'html.parser')
                title = soup.h1.text
                paragraphs = soup.find_all('p')
                frames = []
                images = []
                bible_reference = None
                for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
                    if idx % 2 == 1:
                        frames.append(p.text)
                    elif p.img:
                        src = p.img['src'].split('?')[0]
                        basename = os.path.basename(src)
                        images.append(basename)
                        image_file = os.path.join(self.html_dir, basename)
                        if not os.path.isfile(image_file):
                            self.logger.info("Downloading {0}...".format(src))
                            download_file(src, os.path.join(self.html_dir, basename))
                    else:
                        bible_reference = p.text
                content += '<div id="obs-{0}" class="chapter break">\n<h1>{1}</h1>\n'.format(chapter, title)
                if bible_reference:
                    content += '<p class="bible_reference">{0}</p>'.format(bible_reference)
                content += '<h2 class="no-break">{0}</h2>'.format(self.translate('study_notes'))
                for frame_idx in range(0, len(frames)):
                    frame = str(frame_idx+1).zfill(2)
                    obs_sn_file = os.path.join(sn_chapter_dir, '{0}.md'.format(frame))
                    obs_text = re.sub(r'[\n\s]+', ' ', frames[frame_idx], flags=re.MULTILINE)
                    obs_sn_notes = ''
                    if os.path.isfile(obs_sn_file):
                        obs_sn_notes = markdown2.markdown_path(obs_sn_file)
                        phrases = []
                        soup = BeautifulSoup(obs_sn_notes, 'html.parser')
                        for header in soup.find_all('h1'):
                            phrases.append(header.text)
                            header['class'] = header.get('class', []) + ['h4']
                            header.name = 'span'
                        obs_text = self.highlight_text_with_phrases(obs_text, phrases, '{0}:{1}'.format(chapter, frame))
                        obs_sn_notes = unicode(soup)
                    else:
                        obs_sn_notes = '<p class="obs-sn_note"><em>(No study notes for this frame)</em></p>'
                    content += '''
<div id="obs-sn-{0}-{1}" class="obs-sn-article {5}break">
  <h3>{0}:{1}</h3>
  <div class="obs-img-and-text">
    <img src="html/{2}" class="obs-img"/>
    <div class="obs-text">
        {3}
    </div>
  </div>
  <span class="obs-sn-notes">
    {4}
  </span>
</div>
'''.format(chapter, frame, images[frame_idx], obs_text, obs_sn_notes, 'no-' if frame_idx == 0 else '')
                    # HANDLE RC LINKS
                    rc = 'rc://{0}/obs/book/obs/{1}/{2}'.format(self.lang_code, chapter, frame)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': 'obs-sn-{0}-{1}'.format(chapter, frame),
                        'link': '#obs-sn-{0}-{1}'.format(chapter, frame),
                         'title': '{0}:{1}'.format(chapter, frame)
                    }
                    rc = 'rc://{0}/obs-sn/help/obs/{1}/{2}'.format(self.lang_code, chapter, frame)
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': 'obs-sn-{0}-{1}'.format(chapter, frame),
                        'link': '#obs-sn-{0}-{1}'.format(chapter, frame),
                        'title': '{0}:{1}'.format(chapter, frame)
                    }
                content += '</div>\n\n'
            if os.path.isfile(sq_chapter_file):
                obs_sq_id = 'obs-sq-{0}'.format(chapter)
                soup = BeautifulSoup(markdown2.markdown_path(sq_chapter_file), 'html.parser')
                title = soup.h1.text
                for header in soup.find_all(re.compile("h\d")):
                    if header.name == 'h1':
                        header.extract()
                    else:
                        header['class'] = header.get('class', []) + ['h{0}'.format(int(header.name[1])+1)]
                        header.name = 'span'
                content += '''
<div id="{0}" class="chapter break">
  <h2>{1}</h2>
  {2}
</div>
'''.format(obs_sq_id, self.translate('study_questions'), unicode(soup))
                # HANDLE RC LINKS
                rc = 'rc://{0}/obs-sq/help/obs/{1}'.format(self.lang_code, chapter)
                self.resource_data[rc] = {
                    'rc': rc,
                    'id': obs_sq_id,
                    'link': '#{0}'.format(obs_sq_id),
                    'title': title
                }
        self.obs_sn_sq_text = content
        write_file(os.path.join(self.html_dir, '{0}_obs-sn-sq_content.html'.format(self.file_id)),
                   content)

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

    def replace(self, m):
        before = m.group(1)
        rc = m.group(2)
        after = m.group(3)
        if rc not in self.resource_data:
            return m.group()
        info = self.resource_data[rc]
        if (before == '[[' and after == ']]') or (before == '(' and after == ')') or before == ' ' \
                or (before == '>' and after == '<'):
            return '<a href="{0}">{1}</a>'.format(info['link'], info['title'])
        if (before == '"' and after == '"') or (before == "'" and after == "'"):
            return info['link']
        self.logger.error("FOUND SOME MALFORMED RC LINKS: {0}".format(m.group()))
        return m.group()

    def replace_rc_links(self, text):
        # Change rc://... rc links to proper HTML links based on that links title and link to its article
        if self.lang_code != DEFAULT_LANG:
            text = re.sub('rc://en', 'rc://{0}'.format(self.lang_code), text, flags=re.IGNORECASE)
        joined = '|'.join(map(re.escape, self.resource_data.keys()))
        pattern = r'(\[\[|\(|["\']| |>|)\b(' + joined + r')\b(\]\]|\)|["\']|<|)(?!\]\)")'

        text = re.sub(pattern, self.replace, text, flags=re.IGNORECASE)
        # Remove other scripture reference not in this tN
        text = re.sub(r'<a[^>]+rc://[^>]+>([^>]+)</a>', r'\1', text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def fix_links(self, text):
        # Changes references to chapter/frame in links
        # <a href="1/10">Text</a> => <a href="rc://obs-sn/help/obs/01/10">Text</a>
        # <a href="10-1">Text</a> => <a href="rc://obs-sn/help/obs/10/01">Text</a>
        text = re.sub(r'href="(\d)/(\d+)"', r'href="0\1/\2"', text)  # prefix 0 on single-digit chapters
        text = re.sub(r'href="(\d+)/(\d)"', r'href="\1/0\2"', text)  # prefix 0 on single-digit frames
        text = re.sub(r'href="(\d\d)/(\d\d)"', r'href="rc://{0}/obs-sn/help/obs/\1/\2"'.format(self.lang_code), text)

        # Changes references to chapter/frame that are just chapter/frame prefixed with a #
        # #1:10 => [[rc://obs-sn/help/obs/01/10]]
        # #10/1 => [[rc://obs-sn/help/obs/10/01]]
        text = re.sub(r'#(\d)[:/-](\d+)', r'#0\1-\2', text)  # prefix 0 on single-digit chapters
        text = re.sub(r'#(\d+)[:/-](\d)\b', r'#\1-0\2', text)  # prefix 0 on single-digit frames
        text = re.sub(r'#(\d\d)[:/-](\d\d)', r'[[rc://{0}/obs/book/obs/\1/\2]]'.format(self.lang_code), text)

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


def main(obs_sn_tag, obs_sq_tag, obs_tag, lang_codes, working_dir, output_dir, owner, regenerate):
    if not lang_codes:
        lang_codes = [DEFAULT_LANG]

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if not working_dir and 'WORKING_DIR' in os.environ:
        working_dir = os.environ['WORKING_DIR']
        print('Using env var WORKING_DIR: {0}'.format(working_dir))
    if not output_dir and 'OUTPUT_DIR' in os.environ:
        output_dir = os.environ['OUTPUT_DIR']
        print('Using env var OUTPUT_DIR: {0}'.format(output_dir))

    for lang_code in lang_codes:
        logger.info('Starting OBS SN Converter for {0}...'.format(lang_code))
        obs_sn_converter = ObsSnSqConverter(obs_sn_tag, obs_sq_tag, obs_tag, working_dir, output_dir, lang_code, owner, regenerate, logger)
        obs_sn_converter.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_codes', required=False, help='Language Code(s)', action='append')
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('--obs-sn-tag', dest='obs_sn', default=DEFAULT_TAG, required=False, help='OBS SN Tag')
    parser.add_argument('--obs-sq-tag', dest='obs_sq', default=DEFAULT_TAG, required=False, help='OBS SQ Tag')
    parser.add_argument('--obs-tag', dest='obs', default=DEFAULT_TAG, required=False, help='OBS Tag')
    parser.add_argument('-r', '--regenerate', dest='regenerate', action='store_true',
                        help='Regenerate PDF even if exists')
    args = parser.parse_args(sys.argv[1:])
    main(args.obs_sn, args.obs_sq, args.obs, args.lang_codes, args.working_dir, args.output_dir, args.owner, args.regenerate)
