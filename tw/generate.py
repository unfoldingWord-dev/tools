#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#
#  Converts a tA repo into a PDF
#
#  Usage: md_to_pdf.py -i <directory of all ta repos> -o <directory where html flies will be placed>
#

import os
import re
import sys
import json
import codecs
import argparse

reload(sys)
sys.setdefaultencoding('utf8')

tac = None

def generatePage(f, myManual, data, header, pageBreak):
    global tac

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

    f.write('<div class="section level'+str(header))
    if pageBreak:
        f.write(' break')
    f.write('"')
    if slug:
        id = manualSlug+u'_'+slug
        f.write(' id="'+id+'"')
    f.write('>')

    if title:
        f.write('<h'+str(header)+'>'+data['title']+'</h'+str(header)+'>')

    if meta and ('question' in meta or ('dependencies' in meta and meta['dependencies'] and meta['dependencies'])):
        top_box = '<div class="box" style="float:right;width:210px;">'
        if 'question' in meta:
            top_box += u'This page answers the question:<p><em>'+meta['question']+u'</em></p>'
        if 'dependencies' in meta and meta['dependencies'] and meta['dependencies']:
            print slug+": "+meta['dependencies']
            dependencies = json.loads(meta['dependencies'])
            if dependencies:
                top_box += u'In order to understand this topic, it would be good to read:<ul style="list-style:none;padding-left:2px;margin-top:1px;">'
                for dep in dependencies:
                    if dep in pageDict:
                        manual = pageDict[dep]['manual']
                        depTitle = pageDict[dep]['title']
                        if myManual == manual:
                            top_box += u'<li style="padding-top:.5em;"><em><a href="#'+dep+'">'+depTitle+u'</a></em></li>'
                        else:
                            manualTitle = manualDict[manual]['meta']['manual_title']
                            manualUrl = manualUrls[manual]
                            moduleUrl = manualUrl+u'#'+manualDict[manual]['meta']['slug']+u'_'+dep
                            top_box += u'<li style="padding-top:.5em;"><em><a href="'+moduleUrl+u'" target="_new">'+depTitle+u'</a></em> in <em><a href="'+manualUrl+u'" target="_new">'+manualTitle+'</a></em></li>'
                top_box += u'</ul>'
        top_box += "</div>\n"
        f.write(top_box)
    if html:
        html = re.sub(u'https://git.door43.org/Door43/'+myManual+'/src/master/content/(.*)\.md', u'#'+manualSlug+ur'_\1', html, flags=re.MULTILINE|re.UNICODE)
        for manual, url in manualUrls.iteritems():
            if manual != myManual:
                slug = manualDict[manual]['meta']['slug']
                html = re.sub(u'https://git.door43.org/Door43/'+manual+'/src/master/content/(.*)\.md', url+u'#'+slug+ur'\1', html, flags=re.MULTILINE|re.UNICODE)
        #html = re.sub(u"\n", " ", html, flags=re.MULTILINE|re.UNICODE)
        #html = re.sub(u'<h(\d)(.*?</p>)', u"<div class=\"firstp level\g<1>\">\n<h\g<1>\g<2>\n</div>\n", html, flags=re.MULTILINE|re.DOTALL|re.UNICODE)
        f.write(html+"\n")
    if meta and 'recommended' in meta and meta['recommended'] and meta['recommended']:
        print slug+": "+meta['recommended']
        recommended = json.loads(meta['recommended'])
        if recommended:
            bottom_box = '<div class="box" style="margin:5px 10px;clear:both;">'
            bottom_box += 'Next we recommend you learn about:<p>'
            for idx, rec in enumerate(recommended):
                print slug+" ==> "+rec
                if rec in pageDict:
                    manual = pageDict[rec]['manual']
                    recTitle = pageDict[rec]['title']
                    print "==> "+recTitle+" in "+manual
                    if myManual == manual:
                        bottom_box += u'<em><a href="#'+rec+'">'+recTitle+u'</a></em>'
                    else:
                        manualTitle = manualDict[manual]['meta']['manual_title']
                        manualUrl = manualUrls[manual]
                        moduleUrl = manualUrl+u'#'+manualDict[manual]['meta']['slug']+u'_'+rec
                        bottom_box += u'<em><a href="'+moduleUrl+u'" target="_new">'+recTitle+u'</a></em> in <em><a href="'+manualUrl+u'" target="_new">'+manualTitle+u'</a></em>'
                else:
                    bottom_box += u'<em>'+rec+u'</em>'
                if idx < len(recommended)-1:
                    bottom_box += u'; '
            bottom_box += u'</p></div>'
            f.write(bottom_box)
    if 'subitems' in data:
        for idx, subitem in enumerate(data['subitems']):
            generatePage(f, myManual, subitem, header+1, (idx != 0 or slug))
    f.write('</div><!-- end level'+str(header)+" -->\n")

def main(inpath, outpath):
    global tac

    tac = taCollection(inpath)

    for manual in tac.manuals:
        manualOutpath = outpath+os.path.sep+manual+".html"
        f = codecs.open(manualOutpath, 'w', encoding='utf-8')
        f.write('''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
<style type="text/css" media="screen,print">
h1, h2, h3, h4, h5, h6 {
  page-break-before: auto !important;
  page-break-after: avoid !important;
  break-after: avoid-page !important;
}

h1 + *,
h2 + *,
h3 + *,
h4 + *,
h5 + *,
h6 + *,
.section > p:first-child {
  page-break-before: avoid;
  page-break-after: auto;
}

.section > p:last-child {
  page-break-inside: avoid;
}

li {
  page-break-before: avoid;
  page-break-after: auto;
}

.break {
  page-break-before: always !important;
  clear: both;
}

.box {
  display: block;
  border-style: solid;
  border-width: 1px;
  border-color: #999999;
  padding: 5px;
  font-size: .8em;
  margin: 5px;
  page-break-inside: avoid;
}

body {
  font-family: 'Noto Sans', sans-serif;
  font-size: 1em;
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
  border-collapse: collapse;
  border-spacing: 0;
}
thead {
  box-shadow: none;
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
table td, table th {
    -webkit-transition: background .1s ease,color .1s ease;
    transition: background .1s ease,color .1s ease;
}

thead th {
    cursor: auto;
    background: #f9fafb;
    text-align: inherit;
    color: rgba(0,0,0,.87);
    padding: .92857143em .71428571em;
    vertical-align: inherit;
    font-style: none;
    font-weight: 700;
    text-transform: none;
    border-bottom: 1px solid rgba(34,36,38,.1);
    border-left: none;
}
thead tr>th:first-child {
    border-left: none;
}
thead tr:first-child>th:first-child {
    border-radius: .28571429rem 0 0;
}

a {
    text-decoration: none;
    display: inline-block;
}
a:link {
    color: #15c;
}
a:visited {
    color: #61c;
}

.docs-bubble-link, .docs-bubble a {
    color: #15c!important;
    cursor: pointer;
    text-decoration: none!important;
}

img {
  max-width: 600px;
  text-align: center;
}

ul li, ul li p {
  margin: 0;
}
div > ul > li:first-child, ol > li > ul > li:first-child {
  margin-top: 1em;
}
div > ul > li:last-child, ol > li > ul > li:last-child {
  margin-bottom: 1em;
}
ul li li:last-child {
  margin-bottom: .5em;
}

ol > li > ul {
  list-style-type: disc;
}
ol > li > ul > li > ul {
  list-style-type: circle;
}
ol > li > ul > li > ul > li > ul {
  list-style-type: square;
}

</style>
</head>
<body>
''')
        for data in tac.manualDict[manual]['toc']:
            generatePage(f, tacManual[manual], data, 1, True)
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
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <style type="text/css">
    body {
      font-family: 'Noto Sans', sans-serif;
    }
  </style>
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
      Version 5
     </p>
  </div>
</body>
</html>
''')
        f.close()

        manualHeader = outpath+os.path.sep+manual+"-header.html"
        f = codecs.open(manualHeader, 'w', encoding="utf-8")
        f.write('''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
    <style type="text/css">
        body {
            font-family: 'Noto Sans', sans-serif;
            font-size:1em;
        }
    </style>
    <script>
        function subst() {
            var vars = {};

            var valuePairs = document.location.search.substring(1).split('&');
            for (var i in valuePairs) {
                var valuePair = valuePairs[i].split('=', 2);
                vars[valuePair[0]] = decodeURIComponent(valuePair[1]);
            }
            var replaceClasses = ['frompage','topage','page','webpage','section','subsection','subsubsection'];

            for (var i in replaceClasses) {
                var hits = document.getElementsByClassName(replaceClasses[i]);

                for (var j = 0; j < hits.length; j++) {
                    hits[j].textContent = vars[replaceClasses[i]];
                }
            }
        }
    </script>
</head>
<body style="border:0; margin: 0px;" onload="subst()">
<div style="font-style:italic;height:2em;"><span class="manual" style="display;block;float:left;">'''+manualDict[manual]['meta']['manual_title']+'''</span><span class="section" style="float:right;display:block;"></span></div>
</body>
</html>
''')
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tA repos to be compiled into html", required=True)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path of html files")

    args = parser.parse_args(sys.argv[1:])

    main(args.inpath, args.outpath)
