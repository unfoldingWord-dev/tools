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

import sys
import json
import codecs
import urllib2


class UWCatalog:
    catalog = None

    jsonURL = 'https://api.door43.org/v3/catalog.json'

    def __init__(self, url=None):
        if not url:
            url = self.jsonURL
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
        # Get the JSON
        self.catalog = json.load(urllib2.urlopen(url))

    def get_language(self, lc):
        for lang in self.catalog['languages']:
            if lang['identifier'] == lc:
               return lang

    def get_resource(self, lc, resource_id):
        lang = self.get_language(lc)
        if lang:
            for resource in lang['resources']:
                if resource['identifier'] == resource_id:
                    return resource

    def get_project(self, lc, resource_id, project_id):
        resource = self.get_resource(lc, resource_id)
        if resource:
            for project in resource['projects']:
                if project['identifier'] == project_id:
                    return project
