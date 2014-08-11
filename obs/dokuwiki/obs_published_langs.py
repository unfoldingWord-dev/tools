#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

import os
import sys
import json
import codecs
import urllib2

caturl = 'http://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
uwstatpage = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/uwadmin/pub_status.txt'
pub_statustmpl = u'''====== unfoldingWord OBS Published Languages ======
'''
langtmpl = u'''
===== {0} =====
^Language   ^Publish Date   ^Version ^
| [[:en:uwadmin:{0}:obs:status|{1}]]      | {2}           | {3}    |
'''

def getCat(url):
    '''
    Get's latest catalog from server.
    '''
    try:
        request = urllib2.urlopen(url).read()
    except:
        print "  => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    return json.loads(request)

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def updateUWStatus(cat, fd):
    for e in cat:
        fd.write(langtmpl.format(e['language'],
                                 e['string'],
                                 e['status']['publish_date'],
                                 e['status']['version']))

def createStatfile(f):
    f = codecs.open(f, encoding='utf-8', mode='w')
    f.write(pub_statustmpl)
    return f

def updatePage(caturl, uwstatpage):
    cat = getCat(caturl)
    uwstatfd = createStatfile(uwstatpage)
    updateUWStatus(cat, uwstatfd)
    uwstatfd.close()

if __name__ == '__main__':
    updatePage(caturl, uwstatpage)
