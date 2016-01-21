#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

"""
This class parses information in the UW catalog.
"""

import os
import re
import sys
import json
import codecs
import urllib2

class UWCatalog:
    catalog = None

    jsonURL = 'https://api.unfoldingword.org/uw/txt/2/catalog.json'

    def __init__(self):
        sys.stdout = codecs.getwriter('utf8')(sys.stdout);
        # Get the JSON
        self.catalog = json.load(urllib2.urlopen(self.jsonURL))

    def getItem(self, item_slug):
        for item in self.catalog['cat']:
            if item['slug'] == item_slug:
               return item

    def getLanguage(self, item_slug, lc):
        item = self.getItem(item_slug)
        for lang in item['langs']:
            if lang['lc'] == lc:
               return lang

    def getBible(self, lc, bible_slug):
        lang = self.getLanguage('bible', lc)

        if lang:
            for bible in lang['vers']:
                if bible['slug'] == bible_slug:
                    return bible

    def getBibleBook(self, lc, bible_slug, book_slug):
        bible = self.getBible(lc, bible_slug)

        if bible:
            for book in bible['toc']:
                if book['slug'] == book_slug:
                    return book
