#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Converts a tA repo into a PDF
'''

import os
import re
import sys
import json
import codecs
import urllib2
import argparse
import datetime
import yaml
import markdown
import markdown2

body_json = ''
refs = {}

reload(sys)
sys.setdefaultencoding('utf8')

manualDict = {}
pageDict = {}
taRoot = ''

def generatePage(f, myManual, data, header, pageBreak):
    global manualDict, pageDict
    slug = meta = html = ''

    if 'slug' in data:
        slug = data['slug']
        if 'meta' in pageDict[slug]:
            meta = pageDict[slug]['meta']
        if 'html' in pageDict[slug]:
            html = pageDict[slug]['html']

    if 'title' in data:
        title = data['title']
    elif meta:
        title = meta['title']

    f.write('<div')
    if pageBreak:
        f.write(' class="break"')
    if slug:
        f.write(' id="'+slug+'"')
    f.write('>')

    if title:
        f.write('<h'+str(header)+'>'+data['title']+'</h'+str(header)+'>')

    if meta and ('question' in meta or ('dependencies' in meta and meta['dependencies'] and meta['dependencies'][0])):
        top_box = '<div class="box" style="float:right;width:20%;">'
        if 'question' in meta:
            top_box += u'This page answers the question:<br/><span style="padding-top:.5em;"><em>'+meta['question'][0]+u'</em></span>'
        if 'dependencies' in meta and meta['dependencies'] and meta['dependencies'][0]:
            dependencies = json.loads(meta['dependencies'][0])
            if dependencies:
                top_box += u'<br/><br/>In order to understand this topic, it would be good to read:<ul style="list-style:none;padding-left:2px;margin-top:1px;">'
                for dep in dependencies:
                    if dep in pageDict:
                        manual = pageDict[dep]['manual']
                        depTitle = pageDict[dep]['title']
                        if myManual == manual:
                            top_box += u'<li style="padding-top:.5em;"><em><a href="#'+dep+'">'+depTitle+u'</a></em></li>'
                        else:
                            manualTitle = manualDict[manual]['meta']['manual_title']
                            top_box += u'<li style="padding-top:.5em;"><em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/'+dep+'.md">'+depTitle+u'</a></em> in <em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/">'+manualTitle+'</a></em></li>'
                top_box += u'</ul>'
        top_box += "</div>\n"
        f.write(top_box)
    if html:
        html = re.sub(u'https://git.door43.org/Door43/'+myManual+'/src/master/content/(.*)\.md', '#\\1', html, flags=re.MULTILINE)
        f.write(html+"\n")
    if meta and 'recommended' in meta and meta['recommended'] and meta['recommended'][0]:
        recommended = json.loads(meta['recommended'][0])
        if recommended:
            bottom_box = '<div class="box" style="margin:5px 10px;clear:both;">'
            bottom_box += 'Next we recommend you learn about:<ul style="margin-top:0;padding-top:0;list-style:none">'
            for rec in recommended:
                if rec in pageDict:
                    manual = pageDict[rec]['manual']
                    recTitle = pageDict[rec]['title']
                    if myManual == manual:
                        bottom_box += u'<li style="padding-top:.5em;"><em><a href="#'+rec+'">'+recTitle+u'</a></em></li>'
                    else:
                        manualTitle = manualDict[manual]['meta']['manual_title']
                        bottom_box += u'<li style="padding-top:.5em;"><em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/'+rec+'.md">'+recTitle+u'</a></em> in <em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/">'+manualTitle+'</a></em></li>'
                else:
                    bottom_box += u'<li style="padding-top:.5em;"><em>'+rec+u'</em></li>'
            bottom_box += u'</ul></div>'
            f.write(bottom_box)
    if 'subitems' in data:
        for idx, subitem in enumerate(data['subitems']):
            generatePage(f, myManual, subitem, header+1, (idx != 0 or header != 1))
    f.write("</div>\n")

def populatePageDict(manual, data):
    global manualDict, pageDict, taRoot
    slug = title = ''

    if 'title' in data:
       title = data['title']
    if 'slug' in data:
        slug = data['slug']
        manualDir = taRoot+os.path.sep+manual+os.path.sep
        filepath = manualDir+"content"+os.path.sep+slug+'.md'
        md = markdown.Markdown(extensions = ['markdown.extensions.extra','markdown.extensions.abbr','markdown.extensions.attr_list','markdown.extensions.def_list','markdown.extensions.fenced_code','markdown.extensions.footnotes','markdown.extensions.tables','markdown.extensions.smart_strong','markdown.extensions.admonition','markdown.extensions.codehilite','markdown.extensions.headerid','markdown.extensions.meta','markdown.extensions.nl2br','markdown.extensions.sane_lists','markdown.extensions.smarty','markdown.extensions.toc','markdown.extensions.wikilinks'])
        pageDict[slug] = {
            'title': title,
            'manual': manual,
            'html': md.convert(open(filepath).read()),
            'meta': md.Meta
        }
    if 'subitems' in data:
       for subitem in data['subitems']:
           populatePageDict(manual, subitem)

def populateManualDict():
    global taRoot, manualDict, pageDict

    manuals = next(os.walk(taRoot))[1]
    manuals[:] = [manual for manual in manuals if os.path.isdir(taRoot+os.path.sep+manual+os.path.sep+"content") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"toc.yaml") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"meta.yaml")]

    for manual in manuals:
        manualDir = taRoot+os.path.sep+manual+os.path.sep
        metaFile = open(manualDir+'meta.yaml', 'r')
        tocFile = open(manualDir+'toc.yaml', 'r')
        manualDict[manual] = {
            'meta': yaml.load(metaFile),
            'toc': yaml.load(tocFile),
        }
        metaFile.close()
        tocFile.close()

def main(inpath, outpath):
    global pageDict, manualDict, taRoot

    taRoot = inpath

    populateManualDict()

    for manual in manualDict.keys():
        for data in manualDict[manual]['toc']:
            populatePageDict(manual, data)

    for manual in manualDict.keys():
        manualOutpath = outpath+os.path.sep+manual+".html"
        f = codecs.open(manualOutpath, 'w', encoding='utf-8')
        f.write('''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
<style type="text/css" media="screen,print">
.break{
  display: block;
  clear: both;
  page-break-before: always;
}
.box{
  page-break-inside: avoid;
}
</style>
<style type="text/css">
body {
  font-family: 'Noto Sans', sans-serif;
  font-size: 1em;
}
.box {
  display: block;
  border: solid 1px;
  padding: 5px;
  font-size: .8em;
  margin:5px;
}
dl {
  padding: 0;
}
dl dt {
  padding: 0;
  margin-top: 16px;
  font-size: 1em;
  font-style: italic;
  font-weight: bold;
}
dl dd {
  padding: 0 16px;
  margin-bottom: 16px;
}
blockquote {
  padding: 0 15px;
  color: #777;
  border-left: 4px solid #ddd;
}
blockquote > :first-child {
  margin-top: 0;
}
blockquote > :last-child {
  margin-bottom: 0;
}
table {
  display: block;
  width: 100%;
  overflow: auto;
  word-break: normal;
  word-break: keep-all;
}
table th {
  font-weight: bold;
}
table th,
table td {
  padding: 6px 13px !important;
  border: 1px solid #ddd !important;
}
table tr {
  background-color: #fff;
  border-top: 1px solid #ccc;
}
table tr:nth-child(2n) {
  background-color: #f8f8f8;
}
</style>
</head>
<body>
''')
        for data in manualDict[manual]['toc']:
            generatePage(f, manual, data, 1, True)
        f.write('''
</body>
</html>
''')
        f.close()

        manualCover = outpath+os.path.sep+manual+"-cover.html"
        f = codecs.open(manualCover, 'w', encoding='utf-8')
        f.write('''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
</head>
<body>
  <div style="text-align:center;padding-top:100px">
    <img src="http://unfoldingword.org/assets/img/icon-ta.png" width="120">
    <p style="font-size:2em;font-weight:bold;">
      translationAcademy
    </p>
    <p style="font-size:1.5em;font-weight:bold;">
      '''+manualDict[manual]['meta']['manual_title']+'''
    </p>
    <p style="font-size:1.2em">
      Version: 5.0
     </p>
  </div>
</body>
</html>
''')
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path")
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tA repo to be made into a PDF.", required=True)

    args = parser.parse_args(sys.argv[1:])

    main(args.inpath, args.outpath)
