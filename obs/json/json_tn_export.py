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

'''
Exports the Key Terms and translationNotes to JSON files.
'''

import os
import re
import sys
import json
import glob
import codecs
import datetime


DEBUG = False
root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
api = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
ktaliases = {}

# Regexes for grabbing content
ktre = re.compile(ur'====== (.*?) ======', re.UNICODE)
subre = re.compile(ur'\n==== (.*) ====\n', re.UNICODE)
defre = re.compile(ur'===== Definition: =====(.*?)\[See also', re.UNICODE | re.DOTALL)
defre2 = re.compile(ur'===== Definition: =====(.*?)=====', re.UNICODE | re.DOTALL)
factre = re.compile(ur'===== Facts: =====(.*?)\[See also', re.UNICODE | re.DOTALL)
factre2 = re.compile(ur'===== Facts: =====(.*?)=====', re.UNICODE | re.DOTALL)
linknamere = re.compile(ur'\|(.*?)\]\]', re.UNICODE)
linkre = re.compile(ur':([^:]*\|.*?)\]\]', re.UNICODE)
cfre = re.compile(ur'See also.*', re.UNICODE)
examplesre = re.compile(ur'===== Examples from the Bible stories.*',
    re.UNICODE | re.DOTALL)
extxtre = re.compile(ur'\*\* (.*)', re.UNICODE)
fridre = re.compile(ur'[0-5][0-9]-[0-9][0-9]', re.UNICODE)
tNre = re.compile(ur'==== Translation Notes.*', re.UNICODE | re.DOTALL)
itre = re.compile(ur'==== Important Terms: ====(.*?)====', re.UNICODE | re.DOTALL)
tNtermre = re.compile(ur' \*\*(.*?)\*\* ', re.UNICODE)
tNtextre = re.compile(ur'\*\*  ?[–-]  ?(.*)', re.UNICODE)
qre = re.compile(ur'[–-] \*\*(.*)\*\*', re.UNICODE)
are = re.compile(ur'\* ?//(.*)//', re.UNICODE)
refre = re.compile(ur'\[(.*?)]', re.UNICODE)

# Regexes for DW to HTML conversion
boldstartre = re.compile(ur'([ ,.])(\*\*)', re.UNICODE)
boldstartre2 = re.compile(ur'\*\*', re.UNICODE)
boldstopre = re.compile(ur'''(\*\*)([ ,.'!])''', re.UNICODE)
lire = re.compile(ur' +\* ', re.UNICODE)
h3re = re.compile(ur'\n=== (.*?) ===\n', re.UNICODE)


def getKT(f):
    page = codecs.open(f, 'r', encoding='utf-8').read()
    kt = {}
    kt['filename'] = f.rsplit('/', 1)[1].replace('.txt', '')
    kt['term'] = ktre.search(page).group(1).strip()
    kt['sub'] = getKTSub(page)
    kt['def_title'], kt['def'] = getKTDef(page)
    kt['cf'] = getKTCF(page)
    kt['ex'] = getKTExamples(page)
    return kt

def getKTDef(page):
    def_title = 'Definition'
    defse = defre.search(page)
    if not defse:
        defse = defre2.search(page)
    if not defse:
        defse = factre.search(page)
        def_title = 'Facts'
    if not defse:
        defse = factre2.search(page)
        def_title = 'Facts'
    deftxt = defse.group(1).rstrip()
    return (def_title, getHTML(deftxt))

def getKTSub(page):
    sub = u''
    subse = subre.search(page)
    if subse:
        sub = subse.group(1)
    return sub.strip()

def getKTCF(page):
    cf = []
    cfse = cfre.search(page)
    if cfse:
        text = cfse.group(0)
        cf = linknamere.findall(text)
    return cf

def getKTExamples(page):
    examples = []
    text = examplesre.search(page).group(0)
    for i in text.split('***'):
        ex = {}
        frse = fridre.search(i)
        if not frse:
            continue
        ex['ref'] = frse.group(0)
        ex['text'] = extxtre.search(i).group(1).strip()
        ex['text'] = getHTML(ex['text'])
        examples.append(ex)
    return examples

def getHTML(text):
    text = boldstartre.sub(ur'\1<b>', text)
    text = boldstopre.sub(ur'</b>\2', text)
    text = boldstartre2.sub(ur'<b>', text)
    text = h3re.sub(ur'<h3>\1</h3>', text)
    text = getHTMLList(text)
    return text.strip()

def getHTMLList(text):
    started = False
    newtext = []
    for line in text.split(u'\n'):
        if lire.search(line):
            if not started:
                started = True
                newtext.append(u'<ul>')
            line = lire.sub(u'<li>', line)
            newtext.append(u'{0}</li>'.format(line))
        else:
            if started:
                started = False
                newtext.append(u'</ul>')
            newtext.append(line)
    if started:
        newtext.append(u'</ul>')
    return u''.join(newtext)

def writeJSON(outfile, p):
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(getDump(p))
    f.close()

def getDump(j):
    return json.dumps(j, indent=2, sort_keys=True)

def getFrame(f):
    if DEBUG: print f
    page = codecs.open(f, 'r', encoding='utf-8').read()
    getAliases(page)
    frame = {}
    frame['id'] = fridre.search(f).group(0).strip()
    frame['tn'] = gettN(page)
    return frame

def getCQ(f):
    page = codecs.open(f, 'r', encoding='utf-8').read()
    story = {}
    story['id'] = f.rsplit('/')[-1].rstrip('.txt')
    story['cq'] = getQandA(page)
    return story

def getQandA(text):
    cq = []
    for line in text.splitlines():
        if not line.startswith(u'  '): continue
        if qre.search(line):
            item = {}
            item['q'] = qre.search(line).group(1).strip()
        elif are.search(line):
            item['a'] = are.search(line).group(1).strip()
            item['ref'] = refre.findall(item['a'])
            item['a'] = item['a'].split('[')[0].strip()
            cq.append(item)
            continue
        else:
            print line
    return cq

def getAliases(page):
    text = itre.search(page).group(1).strip()
    its = linkre.findall(text)
    for t in its:
        term, alias = t.split('|')
        if not ktaliases.has_key(term):
            ktaliases[term] = []
        ktaliases[term].append(alias)

def gettN(page):
    tN = []
    text = tNre.search(page).group(0)
    for i in text.split('\n'):
        item = {}
        tNtermse = tNtermre.search(i)
        if not tNtermse:
            continue
        if DEBUG: print i
        item['ref'] = tNtermse.group(1)
        item['text'] = tNtextre.search(i).group(1).strip()
        item['text'] = getHTML(item['text'])
        tN.append(item)
    return tN

def runKT(lang, today):
    ktpath = os.path.join(pages, lang, 'obs/notes/key-terms')
    apipath = os.path.join(api, lang)
    keyterms = []
    for f in glob.glob('{0}/*.txt'.format(ktpath)):
        if 'home.txt' in f or '1-discussion-topic.txt' in f: continue
        keyterms.append(getKT(f))
    for i in keyterms:
        try:
            i['aliases'] = list(set([x for x in ktaliases[i['filename']]
                                                          if x != i['term']]))
        except KeyError:
            # this just means no aliases were found
            pass
        del i['filename']
    keyterms.sort(key=lambda x: len(x['term']), reverse=True)
    keyterms.append({'date_modified': today})
    writeJSON('{0}/kt-{1}.json'.format(apipath, lang), keyterms)

def runtN(lang, today):
    tNpath = os.path.join(pages, lang, 'obs/notes/frames')
    apipath = os.path.join(api, lang)
    frames = []
    for f in glob.glob('{0}/*.txt'.format(tNpath)):
        if 'home.txt' in f: continue
        frames.append(getFrame(f))
    frames.sort(key=lambda x: x['id'])
    frames.append({'date_modified': today})
    writeJSON('{0}/tN-{1}.json'.format(apipath, lang), frames)

def runCQ(lang, today):
    CQpath = os.path.join(pages, lang, 'obs/notes/questions')
    apipath = os.path.join(api, lang)
    stories = []
    for f in glob.glob('{0}/*.txt'.format(CQpath)):
        if 'home.txt' in f: continue
        stories.append(getCQ(f))
    stories.sort(key=lambda x: x['id'])
    stories.append({'date_modified': today})
    writeJSON('{0}/CQ-{1}.json'.format(apipath, lang), stories)


if __name__ == '__main__':
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    runtN('en', today)
    runKT('en', today)
    runCQ('en', today)
