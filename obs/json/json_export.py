#!/usr/bin/env python2
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
import glob
import shlex
import codecs
import argparse
import datetime
from subprocess import *
from general_tools.git_wrapper import *
from general_tools.smartquotes import smartquotes

gen_tools = '/var/www/vhosts/door43.org/tools/general_tools'
sys.path.append(gen_tools)

try:
    from github import Github
    from github import GithubException
except:
    print "Please install PyGithub with pip"
    sys.exit(1)


root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
uwadmindir = os.path.join(pages, 'en/uwadmin')
exportdir = '/var/www/vhosts/door43.org/httpdocs/exports'
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
rtl = ['he', 'ar', 'fa']
imgurl = 'https://api.unfoldingword.org/obs/jpg/1/{0}/360px/obs-{0}-{1}.jpg'
langnames = os.path.join('/var/www/vhosts/door43.org',
                  'httpdocs/lib/plugins/door43translation/lang/langnames.txt')
statusheaders = ( 'publish_date',
                  'version',
                  'contributors',
                  'checking_entity',
                  'checking_level',
                  'source_text',
                  'source_text_version',
                  'comments',
                )
readme = u'''
unfoldingWord | Open Bible Stories
==================================

*an unrestricted visual mini-Bible in any language*

http://openbiblestories.com

Created by Distant Shores Media (http://distantshores.org) and the Door43 world missions community (http://door43.org).


License
=======

This work is made available under a Creative Commons Attribution-ShareAlike 4.0 International License (http://creativecommons.org/licenses/by-sa/4.0/).

You are free:

* Share — copy and redistribute the material in any medium or format
* Adapt — remix, transform, and build upon the material for any purpose, even commercially.

Under the following conditions:

* Attribution — You must attribute the work as follows: "Original work available at http://openbiblestories.com." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
* ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

Use of trademarks: unfoldingWord is a trademark of Distant Shores Media and may not be included on any derivative works created from this content.  Unaltered content from http://openbiblestories.com must include the unfoldingWord logo when distributed to others. But if you alter the content in any way, you must remove the unfoldingWord logo before distributing your work.

Attribution of artwork: All images used in these stories are © Sweet Publishing (www.sweetpublishing.com) and are made available under a Creative Commons Attribution-Share Alike License (http://creativecommons.org/licenses/by-sa/3.0).
'''

# Regexes for splitting the chapter into components
titlere = re.compile(ur'======.*', re.UNICODE)
refre = re.compile(ur'//.*//', re.UNICODE)
framere = re.compile(ur'{{[^{]*', re.DOTALL | re.UNICODE)
fridre = re.compile(ur'[0-5][0-9]-[0-9][0-9]', re.UNICODE)
numre = re.compile(ur'([0-5][0-9]).txt', re.UNICODE)

# Regexes for removing text formatting
htmltagre = re.compile(ur'<.*?>', re.UNICODE)
linktagre = re.compile(ur'\[\[.*?\]\]', re.UNICODE)
imgtagre = re.compile(ur'{{.*?}}', re.UNICODE)
imglinkre = re.compile(ur'https://.*\.(jpg|jpeg|gif)', re.UNICODE)

# Regexes for front matter
obsnamere = re.compile(ur'\| (.*)\*\*', re.UNICODE)
taglinere = re.compile(ur'\n\*\*.*openbiblestories', re.UNICODE | re.DOTALL)
linkre = re.compile(ur'\[\[.*?\]\]', re.UNICODE)


obsframeset = set([
    "01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07", "01-08", "01-09", "01-10", "01-11", "01-12", "01-13", "01-14", "01-15", "01-16",
    "02-01", "02-02", "02-03", "02-04", "02-05", "02-06", "02-07", "02-08", "02-09", "02-10", "02-11", "02-12",
    "03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10", "03-11", "03-12", "03-13", "03-14", "03-15", "03-16",
    "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09",
    "05-01", "05-02", "05-03", "05-04", "05-05", "05-06", "05-07", "05-08", "05-09", "05-10",
    "06-01", "06-02", "06-03", "06-04", "06-05", "06-06", "06-07",
    "07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07", "07-08", "07-09", "07-10",
    "08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08", "08-09", "08-10", "08-11", "08-12", "08-13", "08-14", "08-15",
    "09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07", "09-08", "09-09", "09-10", "09-11", "09-12", "09-13", "09-14", "09-15",
    "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07", "10-08", "10-09", "10-10", "10-11", "10-12",
    "11-01", "11-02", "11-03", "11-04", "11-05", "11-06", "11-07", "11-08",
    "12-01", "12-02", "12-03", "12-04", "12-05", "12-06", "12-07", "12-08", "12-09", "12-10", "12-11", "12-12", "12-13", "12-14",
    "13-01", "13-02", "13-03", "13-04", "13-05", "13-06", "13-07", "13-08", "13-09", "13-10", "13-11", "13-12", "13-13", "13-14", "13-15",
    "14-01", "14-02", "14-03", "14-04", "14-05", "14-06", "14-07", "14-08", "14-09", "14-10", "14-11", "14-12", "14-13", "14-14", "14-15",
    "15-01", "15-02", "15-03", "15-04", "15-05", "15-06", "15-07", "15-08", "15-09", "15-10", "15-11", "15-12", "15-13",
    "16-01", "16-02", "16-03", "16-04", "16-05", "16-06", "16-07", "16-08", "16-09", "16-10", "16-11", "16-12", "16-13", "16-14", "16-15", "16-16", "16-17", "16-18",
    "17-01", "17-02", "17-03", "17-04", "17-05", "17-06", "17-07", "17-08", "17-09", "17-10", "17-11", "17-12", "17-13", "17-14",
    "18-01", "18-02", "18-03", "18-04", "18-05", "18-06", "18-07", "18-08", "18-09", "18-10", "18-11", "18-12", "18-13",
    "19-01", "19-02", "19-03", "19-04", "19-05", "19-06", "19-07", "19-08", "19-09", "19-10", "19-11", "19-12", "19-13", "19-14", "19-15", "19-16", "19-17", "19-18",
    "20-01", "20-02", "20-03", "20-04", "20-05", "20-06", "20-07", "20-08", "20-09", "20-10", "20-11", "20-12", "20-13",
    "21-01", "21-02", "21-03", "21-04", "21-05", "21-06", "21-07", "21-08", "21-09", "21-10", "21-11", "21-12", "21-13", "21-14", "21-15",
    "22-01", "22-02", "22-03", "22-04", "22-05", "22-06", "22-07",
    "23-01", "23-02", "23-03", "23-04", "23-05", "23-06", "23-07", "23-08", "23-09", "23-10",
    "24-01", "24-02", "24-03", "24-04", "24-05", "24-06", "24-07", "24-08", "24-09",
    "25-01", "25-02", "25-03", "25-04", "25-05", "25-06", "25-07", "25-08",
    "26-01", "26-02", "26-03", "26-04", "26-05", "26-06", "26-07", "26-08", "26-09", "26-10",
    "27-01", "27-02", "27-03", "27-04", "27-05", "27-06", "27-07", "27-08", "27-09", "27-10", "27-11",
    "28-01", "28-02", "28-03", "28-04", "28-05", "28-06", "28-07", "28-08", "28-09", "28-10",
    "29-01", "29-02", "29-03", "29-04", "29-05", "29-06", "29-07", "29-08", "29-09",
    "30-01", "30-02", "30-03", "30-04", "30-05", "30-06", "30-07", "30-08", "30-09",
    "31-01", "31-02", "31-03", "31-04", "31-05", "31-06", "31-07", "31-08",
    "32-01", "32-02", "32-03", "32-04", "32-05", "32-06", "32-07", "32-08", "32-09", "32-10", "32-11", "32-12", "32-13", "32-14", "32-15", "32-16",
    "33-01", "33-02", "33-03", "33-04", "33-05", "33-06", "33-07", "33-08", "33-09",
    "34-01", "34-02", "34-03", "34-04", "34-05", "34-06", "34-07", "34-08", "34-09", "34-10",
    "35-01", "35-02", "35-03", "35-04", "35-05", "35-06", "35-07", "35-08", "35-09", "35-10", "35-11", "35-12", "35-13",
    "36-01", "36-02", "36-03", "36-04", "36-05", "36-06", "36-07",
    "37-01", "37-02", "37-03", "37-04", "37-05", "37-06", "37-07", "37-08", "37-09", "37-10", "37-11",
    "38-01", "38-02", "38-03", "38-04", "38-05", "38-06", "38-07", "38-08", "38-09", "38-10", "38-11", "38-12", "38-13", "38-14", "38-15",
    "39-01", "39-02", "39-03", "39-04", "39-05", "39-06", "39-07", "39-08", "39-09", "39-10", "39-11", "39-12",
    "40-01", "40-02", "40-03", "40-04", "40-05", "40-06", "40-07", "40-08", "40-09",
    "41-01", "41-02", "41-03", "41-04", "41-05", "41-06", "41-07", "41-08",
    "42-01", "42-02", "42-03", "42-04", "42-05", "42-06", "42-07", "42-08", "42-09", "42-10", "42-11",
    "43-01", "43-02", "43-03", "43-04", "43-05", "43-06", "43-07", "43-08", "43-09", "43-10", "43-11", "43-12", "43-13",
    "44-01", "44-02", "44-03", "44-04", "44-05", "44-06", "44-07", "44-08", "44-09",
    "45-01", "45-02", "45-03", "45-04", "45-05", "45-06", "45-07", "45-08", "45-09", "45-10", "45-11", "45-12", "45-13",
    "46-01", "46-02", "46-03", "46-04", "46-05", "46-06", "46-07", "46-08", "46-09", "46-10",
    "47-01", "47-02", "47-03", "47-04", "47-05", "47-06", "47-07", "47-08", "47-09", "47-10", "47-11", "47-12", "47-13", "47-14",
    "48-01", "48-02", "48-03", "48-04", "48-05", "48-06", "48-07", "48-08", "48-09", "48-10", "48-11", "48-12", "48-13", "48-14",
    "49-01", "49-02", "49-03", "49-04", "49-05", "49-06", "49-07", "49-08", "49-09", "49-10", "49-11", "49-12", "49-13", "49-14", "49-15", "49-16", "49-17", "49-18",
    "50-01", "50-02", "50-03", "50-04", "50-05", "50-06", "50-07", "50-08", "50-09", "50-10", "50-11", "50-12", "50-13", "50-14", "50-15", "50-16", "50-17"
])


def getChapter(chapterpath, jsonchapter, lang):
    chapter = codecs.open(chapterpath, 'r', encoding='utf-8').read()
    # Get title for chapter
    title = titlere.search(chapter)
    if title:
        jsonchapter['title'] = title.group(0).replace('=', '').strip()
    else:
        jsonchapter['title'] = u'NOT FOUND'
        print u'NOT FOUND: title in {0}'.format(chapterpath)
    # Get reference for chapter
    ref = refre.search(chapter)
    if ref:
        jsonchapter['ref'] = ref.group(0).replace('/', '').strip()
    else:
        jsonchapter['ref'] = u'NOT FOUND'
        print u'NOT FOUND: reference in {0}'.format(chapterpath)
    # Get the frames
    for fr in framere.findall(chapter):
        frlines = fr.split('\n')
        frse = fridre.search(fr)
        if frse:
            frid = frse.group(0)
        else:
            frid = u'NOT FOUND'
            print u'NOT FOUND: frame id in {0}'.format(chapterpath)
        frame = { 'id': frid,
                  'img': getImg(frlines[0].strip(), lang, frid),
                  'text': getText(frlines[1:], lang, frid)
                }
        jsonchapter['frames'].append(frame)
    # Sort frames
    jsonchapter['frames'].sort(key=lambda frame: frame['id'])
    return jsonchapter

def getImg(link, lang, frid):
    linkse = imglinkre.search(link)
    if linkse:
        link = linkse.group(0)
        return link
    return imgurl.format('en', frid)

def getText(lines, lang, frid):
    '''
    Groups lines into a string and runs through cleanText and smartquotes.
    '''
    text = u''.join([x for x in lines[1:] if u'//' not in x]).strip()
    text = text.replace(u'\\\\', u'').replace(u'**', u'').replace(u'__', u'')
    text = cleanText(text, lang, frid)
    text = smartquotes(text)
    return text

def cleanText(text, lang, frid):
    '''
    Cleans up text from possible DokuWiki and HTML tag pollution.
    '''
    if htmltagre.search(text):
        text = htmltagre.sub(u'', text)
    if linktagre.search(text):
        text = linktagre.sub(u'', text)
    if imgtagre.search(text):
        text = imgtagre.sub(u'', text)
    return text
        
def writePage(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile.replace('.txt', '.json'), 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getDump(j):
    return json.dumps(j, sort_keys=True)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def loadLangStrings(path):
    langdict = {}
    if not os.path.isfile(path):
        return langdict
    for line in codecs.open(path, 'r', encoding='utf-8').readlines():
        if ( line.startswith(u'#') or line.startswith(u'\n')
                                                  or line.startswith(u'\r') ):
            continue
        code,string = line.split(None, 1)
        langdict[code.strip()] = string.strip()
    return langdict

def getJSONDict(statfile):
    status = {}
    if os.path.isfile(statfile):
        for line in codecs.open(statfile, 'r', encoding='utf-8'):
            if ( line.startswith(u'#') or line.startswith(u'\n')
                              or line.startswith(u'{{') or u':' not in line ):
                continue
            newline = cleanText(line, statfile, line)
            k, v = newline.split(u':', 1)
            status[k.strip().lower().replace(u' ', u'_')] = v.strip()
    return status

def cleanStatus(status):
    for k in [x for x in status.iterkeys()]:
        if k not in statusheaders:
            del status[k]
    return status

def exportunfoldingWord(status, gitdir, json, lang, githuborg, frontj, backj):
    '''
    Exports JSON data for each language into its own Github repo.
    '''
    makeDir(gitdir)
    writePage(os.path.join(gitdir, 'obs-{0}.json'.format(lang)), json)
    writePage(os.path.join(gitdir, 'obs-{0}-front-matter.json'.format(lang)), 
                                                                       frontj)
    writePage(os.path.join(gitdir, 'obs-{0}-back-matter.json'.format(lang)), 
                                                                        backj)
    statjson = getDump(cleanStatus(status))
    writePage(os.path.join(gitdir, 'status-{0}.json'.format(lang)), statjson)
    writePage(os.path.join(gitdir, 'README.md'), readme)
    gitCreate(gitdir)
    name = 'obs-{0}'.format(lang)
    desc = 'Open Bible Stories for {0}'.format(lang)
    url = 'http://unfoldingword.org/{0}/'.format(lang)
    githubCreate(gitdir, name, desc, url, githuborg)
    commitmsg = str(status)
    gitCommit(gitdir, commitmsg)
    gitPush(gitdir)

def uwQA(jsd, lang, status, frontj, backj):
    '''
    Implements basic quality control to verify correct number of frames,
    correct JSON formatting, and correct status headers.
    '''
    flag = True
    for header in statusheaders:
        if not status.has_key(header):
            print ('==> !! Cannot export {0}, status page missing header {1}'
                                                        .format(lang, header))
            flag = False
    if 'NOT FOUND.' in str(jsd):
        print '==> !! Cannot export {0}, invalid JSON format'.format(lang)
        flag = False
    framelist = []
    for c in jsonlang['chapters']:
        for f in c['frames']:
            if len(f['text']) > 10:
                framelist.append(f['id'])
    frameset = set(framelist)
    obslangdiff = obsframeset.difference(frameset)
    if obslangdiff:
        print '==> !! Cannot export {0}, missing frames:'.format(lang)
        for x in obslangdiff:
            print x
        flag = False
    langobsdiff = frameset.difference(obsframeset)
    if langobsdiff:
        print '==> !! Cannot export {0}, extra frames:'.format(lang)
        for x in langobsdiff:
            print x
        flag = False
    return flag

def updateUWAdminStatusPage():
    sys.path.append('/var/www/vhosts/door43.org/tools/obs/dokuwiki')
    try:
        import obs_published_langs
    except:
        print 'Could not import obs_published_langs, check path.'
    obs_published_langs.updatePage(obs_published_langs.caturl,
                                              obs_published_langs.uwstatpage)

def getFrontMatter(lang, today):
    frontpath = os.path.join(pages, lang, 'obs', 'front-matter.txt')
    if not os.path.exists(frontpath):
        return getDump({})
    front = codecs.open(frontpath, 'r', encoding='utf-8').read()

    for l in linkre.findall(front):
        if '|' in l:
            cleanurl = l.split(u'|')[1].replace(u']', u'')
        else:
            cleanurl = l.replace(u']', u'').replace(u'[', u'')
        front = front.replace(l, cleanurl)

    obsnamese = obsnamere.search(front)
    if obsnamese:
        obsname = obsnamese.group(1)
    else:
        obsname = 'Open Bible Stories'
    taglinese = taglinere.search(front)
    if taglinese:
        tagline = taglinese.group(0).split('**')[1].strip()
    else:
        tagline = 'an unrestricted visual mini-Bible in any language'
    return getDump({ 'language': lang,
                     'name': obsname,
                     'tagline': tagline,
                     'front-matter': front,
                     'date_modified': today
                   })

def getBackMatter(lang, today):
    backpath = os.path.join(pages, lang, 'obs', 'back-matter.txt')
    if not os.path.exists(backpath):
        return getDump({})
    back = codecs.open(backpath, 'r', encoding='utf-8').read()
    return getDump({ 'language': lang,
                     'back-matter': cleanText(back, lang, 'back-matter'),
                     'date_modified': today
                   })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest="lang", default=False,
        required=True, help="Language code of resource.")
    parser.add_argument('-e', '--export', dest="uwexport", default=False,
        action='store_true', help="Export to unfoldingWord.")
    parser.add_argument('-t', '--testexport', dest="testexport", default=False,
        action='store_true', help="Test export to unfoldingWord.")

    args = parser.parse_args(sys.argv[1:])
    lang = args.lang
    uwexport = args.uwexport
    testexport = args.testexport
    
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    langdict = loadLangStrings(langnames)
    uwcatpath = os.path.join(unfoldingWorddir, 'obs-catalog.json')
    uwcatalog = loadJSON(uwcatpath, 'l')
    uwcatlangs = [x['language'] for x in uwcatalog]
    catpath = os.path.join(exportdir, 'obs-catalog.json')
    catalog = loadJSON(catpath, 'l')

    if 'obs' not in os.listdir(os.path.join(pages, lang)):
        print 'OBS not configured in Door43 for {0}'.format(lang)
        sys.exit(1)
    app_words = getJSONDict(os.path.join(pages, lang, 'obs/app_words.txt'))
    langdirection = 'ltr'
    if lang in rtl:
        langdirection = 'rtl'
    jsonlang = { 'language': lang,
                 'direction': langdirection,
                 'chapters': [],
                 'app_words': app_words,
                 'date_modified': today,
               }
    page_list = glob.glob('{0}/{1}/obs/[0-5][0-9].txt'.format(pages, lang))
    page_list.sort()
    for page in page_list:
        jsonchapter = { 'number': numre.search(page).group(1),
                        'frames': [],
                      }
        jsonlang['chapters'].append(getChapter(page, jsonchapter, lang))
    jsonlang['chapters'].sort(key=lambda frame: frame['number'])
    jsonlangfilepath = os.path.join(exportdir, lang, 'obs',
                                        'obs-{0}.json'.format(lang))
    prevjsonlang = loadJSON(jsonlangfilepath, 'd')
    curjson = getDump(jsonlang)
    prevjson = getDump(prevjsonlang)
    try:
        langstr = langdict[lang]
    except KeyError:
        print "Configuration for language {0} missing in {1}.".format(lang,
                                                                 langnames)
        sys.exit(1)
    status = getJSONDict(os.path.join(uwadmindir, lang, 'obs/status.txt'))
    langcat =  { 'language': lang,
                 'string': langstr,
                 'direction': langdirection,
                 'date_modified': today,
                 'status': status,
               }
    if not lang in [x['language'] for x in catalog]:
        catalog.append(langcat)
    if str(curjson) != str(prevjson):
        ( [x for x in catalog if x['language'] ==
                                        lang][0]['date_modified']) = today
        writePage(jsonlangfilepath, curjson)
    if testexport:
        print 'Testing {0} export...'.format(lang)
        frontjson = getFrontMatter(lang, today)
        backjson = getBackMatter(lang, today)
        if not uwQA(jsonlang, lang, status, frontjson, backjson):
            print '---> QA Failed.'
            sys.exit(1)
        print '---> QA Passed.'
        sys.exit()
    if uwexport:
        try:
            pw = open('/root/.github_pass', 'r').read().strip()
            guser = githubLogin('dsm-git', pw)
            githuborg = getGithubOrg('unfoldingword', guser)
        except GithubException as e:
            print 'Problem logging into Github: {0}'.format(e)
            sys.exit(1)

        unfoldingWordlangdir = os.path.join(unfoldingWorddir, lang)
        if status.has_key('checking_level') and status.has_key(
                                                          'publish_date'):
            if ( status['checking_level'] in ['1', '2', '3'] and 
                   status['publish_date'] == str(datetime.date.today()) ):
                print "=========="
                frontjson = getFrontMatter(lang, today)
                backjson = getBackMatter(lang, today)
                if not uwQA(jsonlang, lang, status, frontjson, backjson):
                    print "=========="
                    sys.exit(1)
                print "---> Exporting to unfoldingWord: {0}".format(lang)
                exportunfoldingWord(status, unfoldingWordlangdir, curjson,
                                     lang, githuborg, frontjson, backjson)
                if lang in uwcatlangs:
                    uwcatalog.pop(uwcatlangs.index(lang))
                    uwcatlangs.pop(uwcatlangs.index(lang))
                uwcatalog.append(langcat)
                print "=========="

    catjson = getDump(catalog)
    writePage(catpath, catjson)
    if uwexport:
        uwcatjson = getDump(uwcatalog)
        writePage(uwcatpath, uwcatjson)
        updateUWAdminStatusPage()
