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

api_url = u'https://api.unfoldingword.org/ta/txt/1'

addHorizontalLine = False

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return False

def getHtmlFromHash(hash, level):
    global refs
    output = ''
    if 'chapters' in hash:
        for chapter in hash['chapters']:
            output += u'<h{0}>{1}</h{0}>'.format(level, chapter['title'])+"\n"
            output += getHtmlFromHash(chapter, level+1)
    if 'frames' in hash:
        for frame in hash['frames']:
            refs[frame['ref']] = '#'+frame['id']

            text = frame['text']
#            text = re.sub(u'<h4([^>]*)>\s*(.*?)\s*</h4>', u'<h7\g<1>>\g<2></h7>', text, flags=re.MULTILINE)
#            text = re.sub(u'<h3([^>]*)>\s*(.*?)\s*</h3>', u'<h6\g<1>>\g<2></h6>', text, flags=re.MULTILINE)
#            text = re.sub(u'<h2([^>]*)>\s*(.*?)\s*</h2>', u'<h5\g<1>>\g<2></h5>', text, flags=re.MULTILINE)

            text = re.sub(u'<h5([^>]*)>\s*(.*?)\s*</h5>', u'<h5\g<1>><em>\g<2></em></h5>', text)
            text = re.sub(u'<h4([^>]*)>\s*(.*?)\s*</h4>', u'<h5\g<1>><b><em>\g<2></em></b></h5>', text)
            text = re.sub(u'<h3([^>]*)>\s*(.*?)\s*</h3>', u'<h5\g<1>>\g<2></h5>', text)

            text = re.sub(u'<h2([^>]*)>\s*(.*?)\s*</h2>', u'<h{0}\g<1>>\g<2></h{0}>'.format(level), text)

            output += text
            if addHorizontalLine:
                output += "\n<hr/>\n"
            output += getHtmlFromHash(frame, level+1)
    if 'sections' in hash:
        for section in hash['sections']:
            output += u'<h{0}>{1}</h{0}>'.format(level, section['title'])+"\n"
            output += getHtmlFromHash(section, level+1)

    return output

def renderHTMLFromJSON():
    global body_json
    global refs

    j = u'\n\n'
    output = ''
    output += getHtmlFromHash(body_json, 1)

    for url in refs.keys():
        output = output.replace(u'href="{0}"'.format(url), u'href="{0}"'.format(refs[url]))

    #output = re.sub(' src="assets/img/ta/audio_ocenaudio_properties.jpg"', '', output)
    output = re.sub(' src="/', ' src="https://test.unfoldingword.org/', output)
    output = re.sub(' src="assets/', ' src="https://test.unfoldingword.org/assets/', output)
    output = re.sub('( src="https://test.unfoldingword.org/assets/img/ta/)[^"]+/', ' \g<1>', output)
    output = re.sub('href="/en/slack', 'href="https://door43.org/en/slack', output)
    output = re.sub('<img ([^>]*)>', '</p>\n<p><img \g<1>></p>\n<p>', output)
    output = re.sub('(?i)(help@door43.org)', '<a href="mailto:\g<1>">\g<1></a>', output)
    return output

def main(lang, inpath, outpath):
    global tocData, refs

    refs['/{0}/ta/vol1/intro/toc_intro'.format(lang)] = u'#the-unfoldingword-project'
    refs['/{0}/ta/vol1/translate/toc_transvol1_2'.format(lang)] = u'#introduction-to-translation-manual'
    refs['/{0}/ta/vol1/checking/toc_checkvol1_2'.format(lang)] = u'#introduction-to-the-checking-manual'
    refs['/{0}/ta/vol1/tech/toc_techvol1_2'.format(lang)] = u'#welcome-to-the-technology-manual'
    refs['/{0}/ta/vol1/tech/toc_techvol1'.format(lang)] = u'#welcome-to-the-technology-manual'
    refs['/{0}/ta/vol1/process/toc_processvol1_2'.format(lang)] = u'#introduction-to-the-process-manual'
    refs['/{0}/ta/vol1/tech/uw_intro'.format(lang)] = u'#unfoldingword-mobile-app'
    refs['/{0}/obs'.format(lang)] = u'http://www.openbiblestories.com'
    refs['/{0}/bible/intro'.format(lang)] = u'https://unfoldingword.org/bible'
    refs['/{0}/obs/notes'.format(lang)] = u'https://unfoldingword.org/translationnotes/'
    refs['/{0}/bible/notes/home'.format(lang)] = u'https://unfoldingword.org/translationnotes/'
    refs['/{0}/obs/notes/questions/home'.format(lang)] = u'https://unfoldingword.org/translationquestions/'
    refs['/{0}/bible/questions/home'.format(lang)] = u'https://unfoldingword.org/translationquestions/'
    refs['/{0}/obe/home'.format(lang)] = u'https://unfoldingword.org/translationwords/'
    refs['/{0}/ta/vol1/tech/uw_app'.format(lang)] = u'https://unfoldingword.org/apps'
    refs['/{0}/ta'.format(lang)] = u'https://unfoldingword.org/academy'

    myManual = os.path.basename(inpath)
    taRoot = os.path.dirname(inpath)+os.path.sep
    manuals = next(os.walk(taRoot))[1]
    manuals[:] = [manual for manual in manuals if os.path.isdir(taRoot+manual+os.path.sep+"content") and os.path.exists(taRoot+manual+os.path.sep+"toc.yaml") and os.path.exists(taRoot+manual+os.path.sep+"meta.yaml")]

    if not myManual in manuals:
        print "There is no manual with that name."
        exit(1)

    manualDict = {}
    pagesDict = {}
    for manual in manuals:
        manualDir = taRoot+manual+os.path.sep
        metaFile = open(manualDir+'meta.yaml', 'r')
        tocFile = open(manualDir+'toc.yaml', 'r')
        manualDict[manual] = {
            'meta': yaml.load(metaFile),
            'toc': yaml.load(tocFile),
            'pages':{}
        }
        metaFile.close()
        tocFile.close()
        for data in manualDict[manual]['toc']:
            if 'slug' in data:
                data['subitems'] = [{'title': data['title'], 'slug': data['slug']}]
            if 'subitems' in data:
                for item in data['subitems']:
                    filepath = manualDir+"content"+os.path.sep+item['slug']+'.md'
                    print filepath
                    md = markdown.Markdown(extensions = ['markdown.extensions.meta'])
                    pagesDict[item['slug']] = {
                        'title': item['title'],
                        'manual': manual,
                        'html': md.convert(open(filepath).read()),
                        'meta': md.Meta
                    }
                    manualDict[manual]['pages']['slug'] = pagesDict[item['slug']]

    f = codecs.open(outpath, 'w', encoding='utf-8')
    f.write('<style type="text/css">@media print { .module-page {page-break-before: always; overflow: visible;} }</style>')
    for data in manualDict[myManual]['toc']:
        if 'slug' in data:
            data['subitems'] = [{'title': data['title'], 'slug': data['slug']}]
        if 'subitems' in data:
            for item in data['subitems']:
                slug = item['slug']
                meta = pagesDict[slug]['meta']
                html = pagesDict[slug]['html']
                html = re.sub(u'https://git.door43.org/Door43/'+myManual+'/src/master/content/(.*)\.md', '#\\1', html, flags=re.MULTILINE)
                f.write('<div class="module-page" id="'+slug+'"><h2>'+meta['title'][0]+'</h2>')
                if 'question' in meta or 'recommended' in meta:
                    top_box = '<div style="float:right;border:solid 1px;padding:5px;margin:5px;width:25%;">'
                    if 'question' in meta:
                        top_box += "This page answers the question:<br/><em>"+meta['question'][0]+"</em>"
                    if 'dependencies' in meta and len(meta['dependencies'][0]) > 0:
                        top_box += '<br/><br/>In order to understand this topic, it would be good to read:<ul style="list-style:none">'
                        dependencies = json.loads(meta['dependencies'][0])
                        for dep in dependencies:
                            if dep in pagesDict:
                                manual = pagesDict[dep]['manual']
                                depTitle = pagesDict[dep]['title']
                                if myManual == manual:
                                    top_box += '<li><em><a href="#'+dep+'">'+depTitle+'</a></em></li>'
                                else:
                                    manualTitle = manualDict[manual]['meta']['manual']
                                    top_box += u'<li><em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/'+dep+'.md">'+depTitle+u'</a></em> in <em><a href="https://git.door43.org/Door43/'+manual+u'/content/">'+manualTitle+'</a></em></li>'
                        top_box += u'</ul>'
                    top_box += "</div>\n"
                    f.write(top_box)
                f.write(html+"\n")
        if 'recommended' in meta and meta['recommended']:
            recommended = json.loads(meta['recommended'][0])
            if recommended:
                bottom_box = '<div style="border:solid 1px;padding:5px;margin:5px 10px">'
                bottom_box += 'Next we recommend you learn about:<ul style="list-style:none">'
                for rec in recommended:
                    if rec in pagesDict:
                        manual = pagesDict[rec]['manual']
                        recTitle = pagesDict[rec]['title']
                        if myManual == manual:
                            bottom_box += '<li><em><a href="#'+rec+'">'+recTitle+'</a></em></li>'
                        else:
                            manualTitle = manualDict[manual]['meta']['manual']
                            bottom_box += u'<li><em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/'+rec+'.md">'+recTitle+u'</a></em> in <em><a href="https://git.door43.org/Door43/'+manual+u'/src/master/content/">'+manualTitle+'</a></em></li>'
                bottom_box += u'</ul>'
                f.write(bottom_box)
        
        f.write("</div>\n")
    f.close()
    exit(1)

    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    if inpath.startswith('http'):
        body_json = json.load(urllib2.urlopen(inpath))
    else:
        with open(inpath) as data:
             body_json = json.load(data)
    output = renderHTMLFromJSON()

#    license = getURL(u'https://door43.org/_export/xhtmlbody/{0}/legal/license/uw-trademark'.format(lang))
#    license += '<p><b>{0}</b></p>'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
#    output = license + output

    f = codecs.open(outpath, 'w', encoding='utf-8')
    f.write(output)
    f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default='en',
        required=False, help="Language code")
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tA repo to be made into a PDF.", required=True)
    parser.add_argument('-s', '--section-separator', dest="addHorizontalLine",
        help="Add a horizontal line between sections", required=False, default=False, action="store_true")

    args = parser.parse_args(sys.argv[1:])

    addHorizontalLine = args.addHorizontalLine
    main(args.lang, args.inpath, args.outpath)
