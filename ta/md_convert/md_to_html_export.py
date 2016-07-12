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
#  Converts a tA repo into a PDF
#
#  Usage: md_to_pdf.py -i <directory of all ta repos> -o <directory where html flies will be placed>
#

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
import time

academyUrl = u'https://unfoldingword.org/academy/'

manualOrder = ['en-ta-intro','en-ta-process','en-ta-translate-vol1','en-ta-translate-vol2','en-ta-checking-vol1','en-ta-checking-vol2','en-ta-gl','en-ta-audio']
manualUrls = {
  'en-ta-intro': u'ta-intro.html',
  'en-ta-process': u'ta-process.html',
  'en-ta-translate-vol1': u'ta-translation-1.html',
  'en-ta-translate-vol2': u'ta-translation-2.html',
  'en-ta-checking-vol1': u'ta-checking-1.html',
  'en-ta-checking-vol2': u'ta-checking-2.html',
  'en-ta-audio': u'ta-audio.html',
  'en-ta-gl': u'ta-gateway-language.html',
}

reload(sys)
sys.setdefaultencoding('utf8')

manualDict = {}
moduleDict = {}
taRoot = ''

def generatePage(myManual, data, header, pageBreak, complete=False):
    global manualDict, moduleDict, manualUrls

    ret = slug = id = meta = html = ''

    manualSlug = manualDict[myManual]['meta']['slug']

    if 'slug' in data:
        slug = data['slug']
        if 'meta' in moduleDict[slug]:
            meta = moduleDict[slug]['meta']
        if 'html' in moduleDict[slug]:
            html = moduleDict[slug]['html']
        id = manualSlug+u'_'+slug

    if 'title' in data:
        title = data['title']
    elif meta:
        title = meta['title']

    ret += '<div class="section level'+str(header)
    if pageBreak:
        ret += ' break'
    ret += '">'

    if title:
        ret += '<h'+str(header)+' class="h2"' # all headers at the top of the page get a class h2 so they are bigger than the headers in the page
        if id:
            ret += ' id="'+id+'"'
        ret += '>'+data['title']+'</h'+str(header)+'>'
    elif id:
        ren += '<a name="'+id+'"/>'

    if meta and ('question' in meta or ('dependencies' in meta and meta['dependencies'] and meta['dependencies'])):
        top_box = '<div class="box" style="float:right;width:210px;">'
        if 'question' in meta:
            top_box += u'This page answers the question:<p><em>'+meta['question']+u'</em></p>'
        if 'dependencies' in meta and meta['dependencies'] and meta['dependencies']:
            dependencies = json.loads(meta['dependencies'])
            if dependencies:
                top_box += u'In order to understand this topic, it would be good to read:<ul style="list-style:none;padding-left:2px;margin-top:1px;">'
                for dep in dependencies:
                    if dep in moduleDict:
                        manual = moduleDict[dep]['manual']
                        depTitle = moduleDict[dep]['title']
                        manualSlug = manualDict[manual]['meta']['slug']
                        if myManual == manual or complete:
                            top_box += u'<li style="padding-top:.5em;"><em><a href="#'+manualSlug+'_'+dep+'" class="internal">'+depTitle+u'</a></em></li>'
                        else:
                            manualTitle = manualDict[manual]['meta']['manual_title']
                            manualUrl = academyUrl+manualUrls[manual]
                            moduleUrl = manualUrl+u'#'+manualDict[manual]['meta']['slug']+u'_'+dep
                            top_box += u'<li style="padding-top:.5em;"><em><a href="'+moduleUrl+u'" class="external" target="_blank">'+depTitle+u'</a></em> in <em><a href="'+manualUrl+u'" class="external" target="_blank">'+manualTitle+'</a></em></li>'
                top_box += u'</ul>'
        top_box += "</div>\n"
        ret += top_box
    if html:
        #urlToLinkRe = re.compile(ur'([^"\/])(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))', re.UNICODE|re.IGNORECASE)
        #html = urlToLinkRe.sub(ur'\1<a href="\2" target="_blank" class="external link">\2</a>', html)
        html = re.sub(u'([^"])((http|https|ftp)://[A-Za-z0-9\/\?&_.:-]+)', ur'\1<a href="\2" class="external link" target="_blank">\2</a>', html, flags=re.UNICODE|re.IGNORECASE)
        html = re.sub(u'([^"\/])(www\.[A-Za-z0-9\/\?&_\.:-]+)', ur'\1<a href="http://\2" class="external link" target="_blank">\2</a>', html, flags=re.UNICODE|re.IGNORECASE)
        for manual, url in manualUrls.iteritems():
            url = academyUrl+url
            slug = manualDict[manual]['meta']['slug']
            if myManual == manual or complete:
                html = re.sub(u'href="https://git.door43.org/Door43/'+manual+'/src/master/content/([^"]+)\.md"', u'href="#'+slug+ur'_\1" class="internal"', html, flags=re.MULTILINE|re.UNICODE|re.IGNORECASE)
            else:
                html = re.sub(u'href="https://git.door43.org/Door43/'+manual+'/src/master/content/([^"]+)\.md"', u'href="'+url+u'#'+slug+ur'_\1" class="external" target="_blank"', html, flags=re.MULTILINE|re.UNICODE|re.IGNORECASE)

        #html = re.sub(u"\n", " ", html, flags=re.MULTILINE|re.UNICODE)
        #html = re.sub(u'<h(\d)(.*?</p>)', u"<div class=\"firstp level\g<1>\">\n<h\g<1>\g<2>\n</div>\n", html, flags=re.MULTILINE|re.DOTALL|re.UNICODE|re.IGNORECASE)
        ret += html+"\n"
    if meta and 'recommended' in meta and meta['recommended'] and meta['recommended']:
        recommended = json.loads(meta['recommended'])
        if recommended:
            bottom_box = '<div class="box" style="margin:5px 10px;clear:both;">'
            bottom_box += 'Next we recommend you learn about:<p>'
            for idx, rec in enumerate(recommended):
                if rec in moduleDict:
                    manual = moduleDict[rec]['manual']
                    recTitle = moduleDict[rec]['title']
                    manualSlug = manualDict[manual]['meta']['slug']
                    if myManual == manual or complete:
                        bottom_box += u'<em><a href="#'+manualSlug+u'_'+rec+'" class="internal">'+recTitle+u'</a></em>'
                    else:
                        manualTitle = manualDict[manual]['meta']['manual_title']
                        manualUrl = academyUrl+manualUrls[manual]
                        moduleUrl = manualUrl+u'#'+manualDict[manual]['meta']['slug']+u'_'+rec
                        bottom_box += u'<em><a href="'+moduleUrl+u'" class="external" target="_blank">'+recTitle+u'</a></em> in <em><a href="'+manualUrl+u'" class="external" target="_blank">'+manualTitle+u'</a></em>'
                else:
                    bottom_box += u'<em>'+rec+u'</em>'
                if idx < len(recommended)-1:
                    bottom_box += u'; '
            bottom_box += u'</p></div>'
            ret += bottom_box
    if 'subitems' in data:
        for idx, subitem in enumerate(data['subitems']):
            ret += generatePage(myManual, subitem, header+1, (idx > 0 or slug), complete)
    ret += '</div><!-- end level'+str(header)+" -->\n"

    return ret

def populateModuleDict(manual, data):
    global manualDict, moduleDict, taRoot
    slug = title = ''

    if 'title' in data:
       title = data['title']
    if 'slug' in data:
        slug = data['slug']
        manualDir = taRoot+os.path.sep+manual+os.path.sep
        filepath = manualDir+"content"+os.path.sep+slug+'.md'
        content = open(filepath).read()

        # Fix bullets that don't have a blank line before them
        #content = re.sub(u"^([^\n]+)\n( *1\. )", u"\g<1>\n\n\g<2>", content, flags=re.MULTILINE|re.UNICODE)
        #content = re.sub(u"^([^ \n][^\n]*)\n(  [\*-] )", u"\g<1>\n\n\g<2>", content, flags=re.MULTILINE|re.UNICODE)
        #content = re.sub(u"^\* ", u"  * ", content, flags=re.MULTILINE|re.UNICODE)

        html = markdown2.markdown(content, extras=["tables", "metadata"])
        meta = html.metadata

        html = re.sub(u'<(h\d)', ur'<span class="\1"', html, flags=re.MULTILINE|re.UNICODE|re.IGNORECASE)
        html = re.sub(u'</(h\d)', u'</span', html, flags=re.MULTILINE|re.UNICODE|re.IGNORECASE)
        moduleDict[slug] = {
            'title': title,
            'manual': manual,
			'html': html,
			'meta': meta
         }
    if 'subitems' in data:
       for subitem in data['subitems']:
           populateModuleDict(manual, subitem)

def populateManualDict():
    global taRoot, manualDict, moduleDict

    manuals = next(os.walk(taRoot))[1]
    manuals[:] = [manual for manual in manuals if os.path.isdir(taRoot+os.path.sep+manual+os.path.sep+"content") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"toc.yaml") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"meta.yaml")]

    for manual in manuals:
        manualDir = taRoot+os.path.sep+manual+os.path.sep
        metaFile = open(manualDir+'meta.yaml', 'r')
        meta = yaml.load(metaFile)
        metaFile.close()
        tocFile = open(manualDir+'toc.yaml', 'r')
        toc = yaml.load(tocFile)
        tocFile.close()
        license = markdown2.markdown_path(manualDir+'LICENSE.md')
        meta['slug'] = u'vol'+meta['volume']+u'_'+meta['manual']
        manualDict[manual] = {
            'meta': meta,
            'toc': toc,
            'license': license,
        }

def main(inpath, outpath):
    global moduleDict, manualDict, taRoot, academyUrl, manualUrls, manualOrder

    taRoot = inpath

    populateManualDict()

    for manual in manualDict.keys():
        for data in manualDict[manual]['toc']:
            populateModuleDict(manual, data)

    intro_content = ''

    for manual in manualOrder:

        cover = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="'''+manualUrls[manual]+'''">
    <img src="https://unfoldingword.org/assets/img/icon-ta.png" width="120">
    <h1 class="h1">translationAcademy</h1>
    <h2 class="h2">'''+manualDict[manual]['meta']['manual_title']+'''</h2>
    <h3 class="h3">Version '''+manualDict[manual]['meta']['version']+'''</h3>
  </div>
</body>
</html>
'''

        license = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
'''+manualDict[manual]['license']+'''
    <p>
      <strong>Date:</strong> '''+time.strftime("%Y-%m-%d")+'''<br/>
      <strong>Version:</strong> '''+manualDict[manual]['meta']['version']+'''
    </p>
  </div>
</body>
</html>
'''

        header = '''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
    <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
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
<div style="font-style:italic;height:1.5em;"><span class="manual" style="display;block;float:left;">'''+manualDict[manual]['meta']['manual_title']+' (ver '+manualDict[manual]['meta']['version']+''')</span><span class="section" style="float:right;display:block;"></span></div>
</body>
</html>
'''

        content = intro_content 
        for data in manualDict[manual]['toc']:
            content += generatePage(manual, data, 1, True, False)
        if manual == "en-ta-intro":
            intro_content = content

        body = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
  </style>
</head>
<body>
'''+content+'''
</body>
</html>
'''

        coverFile = outpath+os.path.sep+manual+"-cover.html"
        f = codecs.open(coverFile, 'w', encoding='utf-8')
        f.write(cover)
        f.close()

        licenseFile = outpath+os.path.sep+manual+"-license.html"
        f = codecs.open(licenseFile, 'w', encoding='utf-8')
        f.write(license)
        f.close()

        headerFile = outpath+os.path.sep+manual+"-header.html"
        f = codecs.open(headerFile, 'w', encoding="utf-8")
        f.write(header)
        f.close()

        bodyFile = outpath+os.path.sep+manual+"-body.html"
        f = codecs.open(bodyFile, 'w', encoding='utf-8')
        f.write(body)
        f.close()

    cover = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
</head>
<body>
  <div style="text-align:center;padding-top:200px" class="break" id="'''+manualUrls[manual]+'''">
    <img src="http://unfoldingword.org/assets/img/icon-ta.png" width="120">
    <span class="h1">translationAcademy</span>
    <span class="h3">Version '''+manualDict[manual]['meta']['version']+'''</span>
  </div>
</body>
</html>
'''

    license = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
</head>
<body>
  <div class="break">
    <span class="h1">Copyrights & Licensing</span>
'''+manualDict['en-ta-intro']['license']+'''
    <p>
      <strong>Date:</strong> '''+time.strftime("%Y-%m-%d")+'''<br/>
      <strong>Version:</strong> '''+manualDict['en-ta-intro']['meta']['version']+'''
    </p>
  </div>
</body>
</html>
'''

    header = '''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
    <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
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
<div style="font-style:italic;height:1.5em;"><span class="section" style="display;block;float:left;"></span><span class="subsection" style="float:right;display:block;"></span></div>
</body>
</html>
'''

    body = '''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link href="https://fonts.googleapis.com/css?family=Noto+Sans" rel="stylesheet">
  <link href="https://api.unfoldingword.org/test/ta7/html/style.css" rel="stylesheet">
  <style type="text/css" media="screen,print">
  </style>
</head>
<body>
'''
    for manual in manualOrder:
        body += '''
  <div style="text-align:center;padding-top:100px" class="break" id="'''+manualUrls[manual]+'''">
    <img src="http://unfoldingword.org/assets/img/icon-ta.png" width="120">
    <h1 class="h1">'''+manualDict[manual]['meta']['manual_title']+'''</h1>
    <span class="h3">Version '''+manualDict[manual]['meta']['version']+'''</span>
  </div>
'''
        for data in manualDict[manual]['toc']:
            body += generatePage(manual, data, 2, True, True)
        body += '''
</body>
</html>
'''

    coverFile = outpath+os.path.sep+'en-ta-complete-cover.html'
    f = codecs.open(coverFile, 'w', encoding="utf-8")
    f.write(cover)
    f.close()

    licenseFile = outpath+os.path.sep+'en-ta-complete-license.html'
    f = codecs.open(licenseFile, 'w', encoding="utf-8")
    f.write(license)
    f.close()

    headerFile = outpath+os.path.sep+'en-ta-complete-header.html'
    f = codecs.open(headerFile, 'w', encoding="utf-8")
    f.write(header)
    f.close()

    bodyFile = outpath+os.path.sep+'en-ta-complete-body.html'
    f = codecs.open(bodyFile, 'w', encoding="utf-8")
    f.write(body)
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

