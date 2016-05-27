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
import re
from general_tools.git_wrapper import *

# use a path relative to the current file rather than a hard-coded path
tools_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

catalog_url = u'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
obs_web = '/var/www/vhosts/unfoldingword.org/httpdocs/'
unfolding_word_dir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
uw_img_api = 'https://api.unfoldingword.org/obs/jpg/1/'
commitmsg = u'Updated OBS slides'

# HTML templates
index_template_file = os.path.join(tools_dir, 'obs/js/index.template.html')
frame_template = u'<section data-background="{0}"><p>{1}</p></section>'
next_link_template = u'<section><a href="../{0}/index.html"><p>{1}</p></a></section>'
# to include literal braces in a format string, double them
menu_link_template = u'<li><a href="../{0}/{{{{ PATH_INDEX }}}}">{1}</a></li>'
title_template = u'''<section><h1>{0}</h1><h3>{1}</h3><div class="uwchecking">
    <a href="https://unfoldingword.org/quality/" target="_blank">
        <img src="https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level{2}-64px.png" />
    </a>
</section>'''

# template regex - uses Blade/Twig syntax
LANG_CODE_REGEX = re.compile(r"(\{{2}\s*LANG_CODE\s*\}{2})", re.DOTALL)
MENY_REGEX = re.compile(r"(\{{2}\s*MENY\s*\}{2})", re.DOTALL)
REVEAL_SLIDES_REGEX = re.compile(r"(\{{2}\s*REVEAL_SLIDES\s*\}{2})", re.DOTALL)

# paths for local and web files
PATH_INDEX_REGEX = re.compile(r"(\{{2}\s*PATH_INDEX\s*\}{2})", re.DOTALL)
PATH_CSS_REGEX = re.compile(r"(\{{2}\s*PATH_CSS\s*\}{2})", re.DOTALL)
PATH_JS_REGEX = re.compile(r"(\{{2}\s*PATH_JS\s*\}{2})", re.DOTALL)

# list layout [RegularExpression, LocalPath, WebPath]
res_paths = [[PATH_INDEX_REGEX, u'index.html', u''],
             [PATH_CSS_REGEX, u'../../css', u'/css'],
             [PATH_JS_REGEX, u'../../js', u'/js']
             ]


def build_reveal(outdir, lang_data, html_template, check_lev):
    """
    Builds reveal.js presentation for the given language.
    """
    lang = lang_data['language']
    resolutions = ['360px', '2160px']
    nextstory = lang_data['app_words']['next_chapter']
    chapters = get_chapters(lang_data['chapters'])
    meny = get_menu(chapters)

    for res in resolutions:
        num_chapters = len(lang_data['chapters'])

        for i in range(1, num_chapters):
            c = lang_data['chapters'][i - 1]

            page = []
            chpnum = c['number'].strip('.txt')

            # the title slide
            page.append(title_template.format(c['title'], c['ref'], check_lev))

            # a slides for each frame
            for f in c['frames']:
                img_url = get_img_url(lang, res, f['id'])
                page.append(frame_template.format(img_url, f['text']))

            # a slide that links to the next story
            if i < num_chapters:
                page.append(next_link_template.format(str(i + 1).zfill(2), nextstory))

            # put it together
            html = MENY_REGEX.sub(meny, html_template)
            html = REVEAL_SLIDES_REGEX.sub('\n'.join(page), html)
            html = LANG_CODE_REGEX.sub(lang, html)

            # save the html
            write_template(os.path.join(outdir, res, chpnum, 'index.html'),
                           os.path.join(unfolding_word_dir, lang, 'slides', res, chpnum, 'index.html'),
                           html)


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
        menu.append(menu_link_template.format(str(i).zfill(2), c))
        i += 1
    return u'\n        '.join(menu)


def write_template(wwwfile, localfile, page):
    """
    Writes out two versions, one for web viewer and one for local viewer.
    """
    local_page = page
    www_page = page

    # list layout [RegularExpression, LocalPath, WebPath]
    for itm in res_paths:
        local_page = itm[0].sub(itm[1], local_page)
        www_page = itm[0].sub(itm[2], www_page)

    write_file(localfile, local_page)
    write_file(wwwfile, www_page)


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
    template = read_file(index_template_file)
    for x in cat:
        lang = x['language']
        langjson = load_json(os.path.join(unfolding_word_dir, lang,
                                          'obs-{0}.json'.format(lang)), 'd')
        rjs_dir = os.path.join(obs_web, lang)

        build_reveal(rjs_dir, langjson, template, x['status']['checking_level'])
        unfolding_word_lang_dir = os.path.join(unfolding_word_dir, lang)
        github_export(unfolding_word_lang_dir)


if __name__ == '__main__':
    export()
