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

'''
Writes a JSON catalog of in progress OBS translations based on door43.org.
'''

import os
import sys
import json
import shlex
import codecs
import urllib2
import datetime
from subprocess import *

pages = "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"
lang_names = u'http://td.unfoldingword.org/exports/langnames.json'
obs_cat = u'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
obsinprogress = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/obs-in-progress.json'


def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return

def runCommand(c):
    '''
    Runs a command in a shell.  Returns output and return code of command.
    '''
    command = shlex.split(c)
    com = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate()).strip()
    return comout, com.returncode

def writeJSON(outfile, p):
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(getDump(p))
    f.close()

def getDump(j):
    return json.dumps(j, sort_keys=True)

def main(cat, today, pub_cat):
    pub_list = [x['language'] for x in pub_cat]
    in_progress = []
    out, ret = runCommand('find {0} -maxdepth 2 -type d -name obs'.format(
                                                                       pages))
    for line in out.split('\n'):
        lc = line.split('/')[9]
        if lc in pub_list: continue
        for x in cat:
            if lc == x['lc']:
                ln = x['ln']
        in_progress.append({ 'lc': lc, 'ln': ln })
    in_progress.sort(key=lambda x: x['lc'])
    in_progress.append({'date_modified': today})
    writeJSON(obsinprogress, in_progress)


if __name__ == '__main__':
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    cat = json.loads(getURL(lang_names))
    pub_cat = json.loads(getURL(obs_cat))
    main(cat, today, pub_cat)
