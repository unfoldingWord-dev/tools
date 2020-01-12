#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
Class for a resource
"""
import os
import git
from collections import OrderedDict
from ..general_tools.file_utils import load_yaml_object

DEFAULT_OWNER = 'unfoldingWord'
DEFAULT_TAG = 'master'
OWNERS = [DEFAULT_OWNER, 'STR', 'Door43-Catalog']
LOGO_MAP = {
    'ta': 'uta',
    'tn': 'utn',
    'tw': 'utw',
    'obs-tn': 'obs',
    'obs-sn': 'obs',
    'obs-sq': 'obs'
}
RUN_LOCALLY = False


class Resource(object):

    def __init__(self, resource_name, repo_name, tag=DEFAULT_TAG, owner=DEFAULT_OWNER, manifest=None, url=None,
                 logo_url=None):
        self.resource_name = resource_name
        self.repo_name = repo_name
        self.tag = tag
        self.owner = owner
        self._manifest = manifest
        self.url = url
        self._logo_url = logo_url
        self.repo_dir = None
        self.git = None
        self.commit = None

    @property
    def logo_url(self):
        if not self._logo_url:
            if self.resource_name in LOGO_MAP:
                logo = LOGO_MAP[self.resource_name]
            else:
                logo = self.resource_name
            self._logo_url = f'https://cdn.door43.org/assets/uw-icons/logo-{logo}-256.png'
        return self._logo_url

    @property
    def logo_file(self):
        return os.path.basename(self.logo_url)

    @staticmethod
    def get_resource_git_url(resource, owner):
        return f'https://git.door43.org/{owner}/{resource}.git'

    def clone(self, working_dir):
        if not self.url:
            self.url = self.get_resource_git_url(self.repo_name, self.owner)
        self.repo_dir = os.path.join(working_dir, self.repo_name)
        if not os.path.isdir(self.repo_dir):
            try:
                git.Repo.clone_from(self.url, self.repo_dir)
            except git.GitCommandError:
                owners = OWNERS
                for owner in owners:
                    self.url = self.get_resource_git_url(self.repo_name, owner)
                    try:
                        git.Repo.clone_from(self.url, self.repo_dir)
                    except git.GitCommandError:
                        continue
                    if os.path.isdir(self.repo_dir):
                        break
        self.git = git.Git(self.repo_dir)
        if not RUN_LOCALLY:
            self.git.fetch()
        self.git.checkout(self.tag)
        if self.tag == DEFAULT_TAG and not RUN_LOCALLY:
            self.git.pull()
        self.commit = self.git.rev_parse('HEAD', short=10)

    @property
    def manifest(self):
        if not self._manifest and self.repo_dir:
            self._manifest = load_yaml_object(os.path.join(self.repo_dir, 'manifest.yaml'))
        return self._manifest

    @property
    def title(self):
        return self.manifest['dublin_core']['title']

    @property
    def simple_title(self):
        return self.title.replace('unfoldingWord® ', '')

    @property
    def type(self):
        return self.manifest['dublin_core']['type']

    @property
    def version(self):
        return self.manifest['dublin_core']['version']

    @property
    def publisher(self):
        return self.manifest['dublin_core']['publisher']

    @property
    def issued(self):
        return self.manifest['dublin_core']['issued']

    @property
    def contributors(self):
        return self.manifest['dublin_core']['contributor']

    @property
    def projects(self):
        return self.manifest['projects']

    def find_project(self, project_id):
        if self.projects:
            for project in self.projects:
                if project.identifier == project_id:
                    return project


class Resources(OrderedDict):
    @property
    def main(self) -> Resource:
        for key, value in self.items():
            return value
        else:
            raise IndexError("Empty ordered dict")
