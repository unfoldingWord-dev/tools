#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

import os
import re
import sys
import json
import codecs
import shlex
import datetime
from subprocess import *


obs_web = '/var/www/vhosts/unfoldingword.org/httpdocs/obs/'
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
uw_img_api = 'http://api.unfoldingword.org/obs/jpg/1/'
title = u'<section><h1>{0}</h1><h3>{1}</h3></section>'
frame = u'<section data-background="{0}"><p>{1}</p></section>'
head = readFile('index.head.html')
foot = readFile('index.foot.html')
#single_head = readFile('single_index.head.html')
#single_foot = readFile('single_index.foot.html')


def buildReveal(outdir, j):
    ldirection = j['direction']
    lang = j['language']
    resolutions = ['360px', '2160px']
    for res in resolutions:
        for c in j['chapters']:
            page = []
            chpnum = c['number'].strip('.txt')
            page.append(title.format(c['title'], c['ref']))
            for f in c['frames']:
                imgURL = getImgURL(lang, res, f['id'])
                page.append(frame.format(imgURL, f['text']))
            writeFile(os.path.join(outdir, res, chpnum, 'index.html'),
                                     '\n'.join([head, '\n'.join(page), foot]))

def getImgURL(lang, res, fid):
    return '{0}{1}/{2}/obs-{3}-{4}.jpg'.format(uw_img_api, lang, res, lang, fid)

def readFile(infile):
    f = codecs.open(infile, 'r', encoding='utf-8').read()
    return f

def writeFile(outfile, page):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(page)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(codecs.open(f, 'r', encoding='utf-8'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')


if __name__ == '__main__':
    for lang in os.listdir(unfoldingWorddir):
        if os.path.isfile(os.path.join(unfoldingWorddir, lang)):
            continue

        langjson = loadJSON(os.path.join(unfoldingWorddir, lang,
                                           'obs-{0}.json'.format( lang)), 'd')
        rjs_dir = os.path.join(obs_web, lang)
        buildReveal(rjs_dir, langjson)
