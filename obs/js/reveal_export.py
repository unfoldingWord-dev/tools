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
#  Requires PyGithub for unfoldingWord export.

import os
import re
import sys
import json
import codecs
import shlex
import datetime
from subprocess import *


obs_web = '/var/www/vhosts/unfolding/httpdocs/obs/'
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
uw_img_api = 'http://api.unfoldingword.org/obs/jpg/1/'
digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
rtl = ['he', 'ar', 'fa']
langnames = os.path.join('/var/www/vhosts/door43.org',
                        'httpdocs/lib/plugins/translation/lang/langnames.txt')
title = u'<section><h1>{0}</h1><h3>{1}</h3></section>'
frame = u'<section data-background="{0}"><p>{1}</p></section>'
head = u'''<!doctype html>
<html lang="en">

    <head>
        <meta charset="utf-8">

        <title>unfoldingWord Open Bible Stories</title>

        <meta name="description" content="an unrestricted visual mini-Bible in any language">
        <meta name="author" content="Created by Distant Shores Media (http://distantshores.org) and the Door43 world missions community (http://door43.org).">

        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

        <link rel="stylesheet" href="/reveal/css/reveal.min.css">
        <link rel="stylesheet" href="/reveal/css/theme/default.css" id="theme">

        <!-- For syntax highlighting -->
        <link rel="stylesheet" href="/reveal/lib/css/zenburn.css">

        <!-- If the query includes 'print-pdf', include the PDF print sheet -->
        <script>
            if( window.location.search.match( /print-pdf/gi ) ) {
                var link = document.createElement( 'link' );
                link.rel = 'stylesheet';
                link.type = 'text/css';
                link.href = '/reveal/css/print/pdf.css';
                document.getElementsByTagName( 'head' )[0].appendChild( link );
            }
        </script>

        <!--[if lt IE 9]>
        <script src="/reveal/lib/js/html5shiv.js"></script>
        <![endif]-->
    </head>
    <body>
        <div class="reveal">
            <div class="slides">'''
foot = u'''
            </div>
        </div>

        <script src="/reveal/lib/js/head.min.js"></script>
        <script src="/reveal/js/reveal.min.js"></script>

        <script>

            // Full list of configuration options available here:
            // https://github.com/hakimel/reveal.js#configuration
            Reveal.initialize({
                controls: true,
                progress: true,
                history: true,
                center: true,

                theme: Reveal.getQueryHash().theme, // available themes are in /css/theme
                transition: Reveal.getQueryHash().transition || 'default', // default/cube/page/concave/zoom/linear/fade/none

                // Parallax scrolling
                // parallaxBackgroundImage: 'https://s3.amazonaws.com/hakim-static/reveal-js/reveal-parallax-1.jpg',
                // parallaxBackgroundSize: '2100px 900px',

                // Optional libraries used to extend on reveal.js
                dependencies: [
                    { src: '/reveal/lib/js/classList.js', condition: function() { return !document.body.classList; } },
                    { src: '/reveal/plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                    { src: '/reveal/plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                    { src: '/reveal/plugin/highlight/highlight.js', async: true, callback: function() { hljs.initHighlightingOnLoad(); } },
                    { src: '/reveal/plugin/zoom-js/zoom.js', async: true, condition: function() { return !!document.body.classList; } },
                    { src: '/reveal/plugin/notes/notes.js', async: true, condition: function() { return !!document.body.classList; } }
                ]
            });

        </script>

    </body>
</html>
'''


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
    unfoldingwordexport = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '--unfoldingwordexport':
            sys.path.append('/var/www/vhosts/door43.org/tools/general_tools')
            try:
                from git_wrapper import *
            except:
                print "Please verify that"
                print "/var/www/vhosts/door43.org/tools/general_tools exists."
                sys.exit(1)
            unfoldingwordexport = True
            try:
                githuborg = getGithubOrg('unfoldingword')
            except:
                print 'Could not login to Github'
                sys.exit(1)
        else:
            print 'Unknown argument: {0}'.format(sys.argv[1])
    for lang in os.listdir(unfoldingWorddir):
        if os.path.isfile(os.path.join(unfoldingWorddir, lang)):
            continue

        langjson = loadJSON(os.path.join(unfoldingWorddir, lang,
                                           'obs-{0}.json'.format( lang)), 'd')
        langdirection = 'ltr'
        if lang in rtl:
            langdirection = 'rtl'
        rjs_dir = os.path.join(obs_web, lang)
        buildReveal(rjs_dir, langjson)
