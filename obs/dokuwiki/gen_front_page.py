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
Generates the front page for door43.org
'''

import os
import sys
import json
import codecs
import urllib2

outfile = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/home.txt'
lang_url = u'http://td.unfoldingword.org/exports/langnames.json'
conf_path = u'/var/www/vhosts/door43.org/httpdocs/conf/local.php'
entry_tmpl = u'  * [[:{0}:home|{1} ({0})]]'
page_tmpl = u'''
**Choose your language:**

{0}

----

Looking for a language that is not here yet? [[https://door43.org/obs-setup|Setup OBS]] for your language (it only takes a moment).
'''

lang_dict = {}

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return

def getConf(path):
    for line in open(path, 'r').readlines():
        if 'translations' in line:
            codes = line.split(';')[0].replace("'", "").split(' ')[2:]
            break
    return codes

def genPage(codes, langs):
    for e in langs:
        lang_dict[e['lc']] = e['ln']
    code_list = []
    for lc in codes:
        if not lang_dict.has_key(lc):
            print "Code not found: {0}".format(lc)
            continue
        code_list.append(entry_tmpl.format(lc, lang_dict[lc]))
    page = page_tmpl.format(u'\n'.join(code_list))
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(page)
    f.close()


if __name__ == '__main__':
    langs = json.loads(getURL(lang_url))
    conf = getConf(conf_path)
    genPage(conf, langs)
