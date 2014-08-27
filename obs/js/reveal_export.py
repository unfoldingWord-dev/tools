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
sys.path.append('/var/www/vhosts/door43.org/tools/general_tools')
try:
    from git_wrapper import *
except:
    print "Please verify that"
    print "/var/www/vhosts/door43.org/tools/general_tools exists."
    sys.exit(1)


obs_web = '/var/www/vhosts/unfoldingword.org/httpdocs/'
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
uw_img_api = 'http://api.unfoldingword.org/obs/jpg/1/'
title = u'<section><h1>{0}</h1><h3>{1}</h3></section>'
frame = u'<section data-background="{0}"><p>{1}</p></section>'
commitmsg = u'Updated OBS presentation'


def buildReveal(outdir, j, t):
    '''
    Builds reveal.js presentation for the given language.
    '''
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
                                     '\n'.join([t[0], '\n'.join(page), t[1]]))

def github_export(revealdir, gitdir)
    '''
    Copies reveal.js presentation into github repo for language, commits and
    pushes to github for the given langauge directory.
    '''
    slidedir = os.path.join(gitdir, u'slides/') # need trailing slash for rsync
    makeDir(slidedir)
    resourcedirs = [ os.path.join(obs_web, 'js'),
                     os.path.join(obs_web, 'css')
                   ]
    for d in resourcedirs:
        if not rsync(d, slidedir):
            print 'Failed to rsync {0} to {1}'.format(d, slidedir)
            sys.exit(1)
    gitCommit(gitdir, commitmsg)
    gitPush(gitdir)

def rsync(src, dst):
    '''
    Runs rsync with the specified src and destination, returns False unless
    an expected return code is found in rsync's output.
    runCommand is defined in git_wrapper.
    '''
    okrets = [0, 23, 24]
    c, ret = runCommand('rsync -havP {0} {1}'.format(src, dst))
    if ret in okrets:
        return True
    return False

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
        template = [readFile('index.head.html'), readFile('index.foot.html')]
        buildReveal(rjs_dir, langjson, template)
        unfoldingWordlangdir = os.path.join(unfoldingWorddir, lang)
        github_export(rjs_dir, unfoldingWordlangdir)
