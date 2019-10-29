#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#  Copyright (c) 2019 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

import os
import sys
import argparse
import logging
import tempfile
import shutil
import subprocess
import json
import git
import markdown2
import string
import codecs
from glob import glob
from shutil import copy
from bs4 import BeautifulSoup
from general_tools.file_utils import load_yaml_object

DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
DEFAULT_LANG = 'en'
OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']


def debug(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))

class TaConverter(object):

    def __init__(self, ta_tag=None, working_dir=None, output_dir=None, lang_code=DEFAULT_LANG, owner=DEFAULT_OWNER,
                 regenerate=False, logger=None):
        self.ta_tag = ta_tag
        self.working_dir = working_dir
        self.output_dir = output_dir
        self.lang_code = lang_code
        self.owner = owner
        self.regenerate = regenerate
        self.logger = logger
        self.ta_dir = None
        self.html_dir = ''
        self.manifest = None
        self.ta_html = ''
        self.version = None
        self.publisher = None
        self.contributors = None
        self.issued = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.generation_info = {}
        self.file_id = None
        self.title = 'unfoldingWord® Translation Academy'

    def run(self):
        if not self.working_dir:
            self.working_dir = tempfile.mkdtemp(prefix='ta-')
        if not self.output_dir:
            self.output_dir = self.working_dir
        self.html_dir = os.path.join(self.output_dir, 'html')
        self.logger.info('WORKING DIR IS {0} FOR {1}'.format(self.working_dir, self.lang_code))
        self.ta_dir = os.path.join(self.working_dir, '{0}_ta'.format(self.lang_code))
        self.html_dir = os.path.join(self.output_dir, 'html')
        if not os.path.isdir(self.html_dir):
            os.makedirs(self.html_dir)
        self.setup_resource_files()
        self.manifest = load_yaml_object(os.path.join(self.ta_dir, 'manifest.yaml'))
        self.version = self.manifest['dublin_core']['version']
        self.title = self.manifest['dublin_core']['title']
        self.contributors = '<br/>'.join(self.manifest['dublin_core']['contributor'])
        self.publisher = self.manifest['dublin_core']['publisher']
        self.issued = self.manifest['dublin_core']['issued']
        debug(self.manifest)

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
                if self.owner not in owners:
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
        # if tag == DEFAULT_TAG:
        #     g.pull()
        commit = g.rev_parse('HEAD', short=10)
        self.generation_info[resource] = {'tag': tag, 'commit': commit}

    def setup_resource_files(self):
        self.clone_resource('ta', self.ta_tag)
        if not os.path.isfile(os.path.join(self.html_dir, 'logo-uta.png')):
            command = 'curl -o {0}/logo-uta.png https://cdn.door43.org/assets/uw-icons/logo-uta-256.png'.format(
                self.html_dir)
            subprocess.call(command, shell=True)


def main(ta_tag, lang_codes, working_dir, output_dir, owner, regenerate):
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
        print('Starting TA Converter for {0}...'.format(lang_code))
        ta_converter = TaConverter(ta_tag, working_dir, output_dir, lang_code, owner, regenerate, logger)
        ta_converter.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang_codes', required=False, help='Language Code(s)', action='append')
    parser.add_argument('-w', '--working', dest='working_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    parser.add_argument('--owner', dest='owner', default=DEFAULT_OWNER, required=False, help='Owner')
    parser.add_argument('--ta-tag', dest='ta', default=DEFAULT_TAG, required=False, help='tA Tag')
    parser.add_argument('-r', '--regenerate', dest='regenerate', action='store_true',
                        help='Regenerate PDF even if exists')
    args = parser.parse_args(sys.argv[1:])
    main(args.ta, args.lang_codes, args.working_dir, args.output_dir, args.owner, args.regenerate)
