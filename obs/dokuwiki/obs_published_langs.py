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

import os
import sys
import json
import codecs
import urllib2

caturl = 'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
uwstatpage = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/uwadmin/pub_status.txt'
iconsdir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/checkinglevels'
pub_statustmpl = u'''====== unfoldingWord OBS Published Languages ======
'''
langtmpl = u'''
===== {0} =====
^Language   ^Publish Date   ^Version    ^Checking Level ^
|  [[:en:uwadmin:{0}:obs:status|{1}]]  |  {2}  |  {3}  |  {{{{https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level{4}-32px.png}}}}  |
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
                                 e['status']['version'],
                                 e['status']['checking_level']))

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
