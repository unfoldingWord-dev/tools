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
Classes for a resource containers
"""

import os
import re
import json
from bs4 import BeautifulSoup, Tag


class ResourceContainerLink(object):

    def __init__(self, rc_link, article='', title=None, linking_level=0, article_id=None):
        self._rc_link = rc_link
        parts = rc_link[5:].split('/')
        self.lang_code = parts[0]
        self.resource = parts[1]
        self.type = parts[2] if len(parts) > 2 else None
        self.project = parts[3] if len(parts) > 3 else None
        self.extra_info = parts[4:]
        self._article = article
        self._title = title
        self.linking_level = linking_level
        self._article_id = article_id
        self.references = []

    @property
    def rc_link(self):
        return 'rc://' + '/'.join(filter(None, [self.lang_code, self.resource, self.type, self.project] +
                                         self.extra_info))

    @property
    def chapter(self):
        if self.extra_info:
            return self.extra_info[0]

    @property
    def verse(self):
        if self.extra_info and len(self.extra_info) > 1:
            return self.extra_info[1]

    @property
    def story(self):
        return self.chapter

    @property
    def frame(self):
        return self.verse

    @property
    def path(self):
        return os.path.sep.join(self.extra_info)

    @property
    def article_id(self):
        if not self._article_id:
            return self.rc_link[5:].replace('/', '-')
        else:
            return self._article_id

    @property
    def title(self):
        if not self._title and self._article:
            soup = BeautifulSoup(self._article, 'html.parser')
            for header in soup.find_all(re.compile(r'^h\d')):
                if 'class' in header and 'hidden' not in header['class']:
                    self._title = header.text()
                    break
        if self._title:
            return self._title

    @property
    def toc_title(self):
        title = self.title
        if len(title) > 70:
            return ' '.join(title[:70].split(' ')[:-1]) + ' ...'
        else:
            return title

    @property
    def article(self):
        return self._article

    @property
    def article_with_toc_title(self):
        if self._article:
            soup = BeautifulSoup(self._article, 'html.parser')
            header = soup.find(re.compile(r'^h\d'))
            if header:
                toc_header = Tag(None, header.builder, header.name, header.namespace, header.nsprefix)
                toc_header['class'] = ['hidden', 'section-header']
                toc_header.string = self.toc_title
                toc_header.insert_before(header)
                header['class'] = []
            return str(soup)

    def set_title(self, title):
        self._title = title

    def set_article(self, article):
        self._article = article

    def set_article_id(self, article_id):
        self._article_id = article_id

    def add_reference(self, rc):
        if rc.rc_link not in self.references:
            self.references.append(rc.rc_link)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
