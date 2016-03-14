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
This class parses information in the Bible Status JSON
"""

import os
import re
import sys
import json
import codecs
import urllib2

class BibleStatus:
    status = None
    version = None
    lang = None

    jsonURL = bible_stat = u'https://api.unfoldingword.org/{0}/txt/1/{0}-{1}/status.json'

    def __init__(self, version, lang):
        sys.stdout = codecs.getwriter('utf8')(sys.stdout);
        # Get the JSON
        self.version = version
        self.lang = lang
        self.status = json.load(urllib2.urlopen(self.jsonURL.format(version, lang)))

    def getBooksPublished(self):
        return self.status['books_published']

    def getStatus(self):
        return self.status['status']

    def getBibleStatus(self, key):
        status = self.getStatus()
        if key in status:
            return status[key]
        else:
            return None

    def getBook(self, book):
        books = self.getBooksPublished()
        if book in books:
            return books[book]
        else:
            return None

    def getBookStatus(self, book, key):
        bookStatus = self.getBook(book)
        if key in bookStatus:
            return bookStatus[key]
        else:
            return None
