#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

'''
Returns version number of specified language.
'''

import os
import sys
import json
import urllib2

catalog_url = u'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'


def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return


if __name__ == '__main__':
    lang = sys.argv[1]
    cat = json.loads(getURL(catalog_url))
    for x in cat:
        if lang == x['language']:
            print x['status']['version']
            sys.exit(0)
    print 'NOT FOUND'
