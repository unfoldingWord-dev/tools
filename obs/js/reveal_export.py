#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>

import os
import codecs
import sys
import urllib2

# use a path relative to the current file rather than a hard-coded path
tools_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
general_dir = os.path.join(tools_dir, 'general_tools')
git_wrapper_file = os.path.join(general_dir, 'git_wrapper.py')

# be sure the git_wrapper.py file exists because import does not throw an exception if the name is not found
if (not os.path.isdir(general_dir)) or (not os.path.isfile(git_wrapper_file)):
    print "Please verify that"
    print git_wrapper_file + " exists."
    sys.exit(1)

sys.path.append(general_dir)
from git_wrapper import *


catalog_url = u'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
obs_web = '/var/www/vhosts/unfoldingword.org/httpdocs/'
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
uw_img_api = 'https://api.unfoldingword.org/obs/jpg/1/'
title = u'''    <div class="meny-arrow"></div>
    <div class="reveal">
        <div class="slides">
            <section><h1>{0}</h1><h3>{1}</h3><div class="uwchecking">
                <a href="https://unfoldingword.org/quality/" target="_blank">
                    <img src="https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level{2}-64px.png" />
                </a>
            </section>'''
frame = u'<section data-background="{0}"><p>{1}</p></section>'
nextlink = u'<section><a href="../{0}/index.html"><p>{1}</p></a></section>'
menulink = u'<li><a href="../{0}/PATH_INDEX">{1}</a></li>'
menutmpl = u'''    <div class="meny">
        <ul>
            {0}
        </ul>
        <p><a href="https://unfoldingword.org/stories/">Open Bible Stories Home</a></p>
    </div>'''
commitmsg = u'Updated OBS slides'
index_head = os.path.join(tools_dir, 'obs/js/index.head.html')
index_foot = os.path.join(tools_dir, 'obs/js/index.foot.html')
localrespaths = {u'PATH_CSS': u'../../css', u'PATH_JS': u'../../js', u'PATH_INDEX': u'index.html'}
wwwrespaths = {u'PATH_CSS': u'/css', u'PATH_JS': u'/js', u'PATH_INDEX': u''}


def build_reveal(outdir, j, t, check_lev):
    """
    Builds reveal.js presentation for the given language.
    """
    lang = j['language']
    resolutions = ['360px', '2160px']
    nextstory = j['app_words']['next_chapter']
    chapters = get_chapters(j['chapters'])
    menu = get_menu(chapters)
    for res in resolutions:
        i = 1
        for c in j['chapters']:
            page = []
            chpnum = c['number'].strip('.txt')
            page.append(menu)
            page.append(title.format(c['title'], c['ref'], check_lev))
            for f in c['frames']:
                img_url = get_img_url(lang, res, f['id'])
                page.append(frame.format(img_url, f['text']))
            if i < 50:
                page.append(nextlink.format(str(i + 1).zfill(2), nextstory))
            i += 1
            write_template(os.path.join(outdir, res, chpnum, 'index.html'),
                           os.path.join(unfoldingWorddir, lang, 'slides', res, chpnum,
                                        'index.html'), '\n'.join([t[0], '\n'.join(page), t[1]]))


def get_chapters(chps):
    """
    Returns list of chapters.
    """
    return [c['title'] for c in chps]


def get_menu(chps):
    """
    Returns an HTML list formated string of the chapters with links.
    """
    menu = []
    i = 1
    for c in chps:
        menu.append(menulink.format(str(i).zfill(2), c))
        i += 1
    return menutmpl.format(u'\n            '.join(menu))


def write_template(wwwfile, localfile, page):
    """
    Writes out two versions, one for web viewer and one for local viewer.
    """
    localpage = page
    wwwpage = page
    for k, v in localrespaths.iteritems():
        localpage = localpage.replace(k, v)
    write_file(localfile, localpage)
    for k, v in wwwrespaths.iteritems():
        wwwpage = wwwpage.replace(k, v)
    write_file(wwwfile, wwwpage)


def github_export(gitdir):
    """
    Copies reveal.js presentation into github repo for language, commits and
    pushes to github for the given langauge directory.
    """
    slidedir = os.path.join(gitdir, u'slides/')  # need trailing slash for rsync
    make_dir(slidedir)
    resourcedirs = [os.path.join(obs_web, 'js'),
                    os.path.join(obs_web, 'css')
                    ]
    for d in resourcedirs:
        if not rsync(d, slidedir):
            print 'Failed to rsync {0} to {1}'.format(d, slidedir)
            sys.exit(1)
    gitCommit(gitdir, commitmsg, 'slides')
    gitPush(gitdir)


def rsync(src, dst):
    """
    Runs rsync with the specified src and destination, returns False unless
    an expected return code is found in rsync's output.
    runCommand is defined in git_wrapper.
    """
    okrets = [0, 23, 24]
    c, ret = runCommand('rsync -havP {0} {1}'.format(src, dst))
    if ret in okrets:
        return True
    return False


def get_img_url(lang, res, fid):
    return '{0}{1}/{2}/obs-{3}-{4}.jpg'.format(uw_img_api, lang, res, lang, fid)


def read_file(infile):
    f = codecs.open(infile, 'r', encoding='utf-8').read()
    return f


def write_file(outfile, page):
    make_dir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(page)
    f.close()


def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)


def load_json(f, t):
    if os.path.isfile(f):
        return json.load(codecs.open(f, 'r', encoding='utf-8'))
    if t == 'd':
        return json.loads('{}')
    else:
        return json.loads('[]')


def get_url(url):
    # noinspection PyBroadException
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)


def export():
    cat = json.loads(get_url(catalog_url))
    for x in cat:
        lang = x['language']
        langjson = load_json(os.path.join(unfoldingWorddir, lang,
                                          'obs-{0}.json'.format(lang)), 'd')
        rjs_dir = os.path.join(obs_web, lang)
        template = [read_file(index_head), read_file(index_foot)]
        build_reveal(rjs_dir, langjson, template, x['status']['checking_level'])
        unfolding_word_lang_dir = os.path.join(unfoldingWorddir, lang)
        github_export(unfolding_word_lang_dir)


if __name__ == '__main__':
    export()
