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
Exports the key terms and translationNotes to JSON files.
'''

import os
import re
import sys
import json
import glob
import codecs
import datetime


root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
api_v2 = '/var/www/vhosts/api.unfoldingword.org/httpdocs/ts/txt/2/'
ktaliases = {}
def_titles = ['Definition', 'Facts', 'Description']

# Regexes for grabbing content
ktre = re.compile(ur'====== (.*?) ======', re.UNICODE)
subre = re.compile(ur'\n==== (.*) ====\n', re.UNICODE)
linknamere = re.compile(ur':([A-Za-z0-9\-]*)\]\]', re.UNICODE)
linkre = re.compile(ur':([^:]*\|.*?)\]\]', re.UNICODE)
cfre = re.compile(ur'See also.*', re.UNICODE)
examplesre = re.compile(ur'===== Examples from the Bible stories.*',
    re.UNICODE | re.DOTALL)
extxtre = re.compile(ur'\*\* (.*)', re.UNICODE)
fridre = re.compile(ur'[0-5][0-9]/[0-9][0-9]', re.UNICODE)
tNre = re.compile(ur'==== Translation Notes.*', re.UNICODE | re.DOTALL)
itre = re.compile(ur'==== Important Terms: ====(.*?)====', re.UNICODE | re.DOTALL)
tNtermre = re.compile(ur' \*\*(.*?)\*\*', re.UNICODE)
tNtextre = re.compile(ur' [–-] ?(.*)', re.UNICODE)
tNtextre2 = re.compile(ur'\* (.*)', re.UNICODE)
pubre = re.compile(ur'tag>.*publish.*', re.UNICODE)

# Regexes for DW to HTML conversion
boldstartre = re.compile(ur'([ ,.])(\*\*)', re.UNICODE)
boldstartre2 = re.compile(ur'\*\*', re.UNICODE)
boldstopre = re.compile(ur'''(\*\*)([ ,.'!])''', re.UNICODE)
lire = re.compile(ur' +\* ', re.UNICODE)
h3re = re.compile(ur'\n=== (.*?) ===\n', re.UNICODE)


def getKT(f):
    page = codecs.open(f, 'r', encoding='utf-8').read()
    if not pubre.search(page): return False
    kt = {}
    kt['filename'] = f.rsplit('/', 1)[1].replace('.txt', '')
    ktse = ktre.search(page)
    if not ktse:
        print 'Term not found for {}'.format(kt['filename'])
        return False
    kt['term'] = ktse.group(1).strip()
    kt['sub'] = getKTSub(page)
    kt['def_title'], kt['def'] = getKTDef(page)
    if not kt['def_title']:
        print 'Definition or Facts not found for {}'.format(kt['filename'])
        return False
    kt['cf'] = getKTCF(page)
    return kt

def getKTDef(page):
    for def_title in def_titles:
        defre = re.compile(ur'===== {0}: =====(.*?)\(See also'.format(
                                           def_title), re.UNICODE | re.DOTALL)
        defse = defre.search(page)
        if not defse:
            defre = re.compile(ur'===== {0}: =====(.*?)====='.format(
                                           def_title), re.UNICODE | re.DOTALL)
            defse = defre.search(page)
        if defse: break
    try:
        deftxt = defse.group(1).rstrip()
    except:
        return (False, False)
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
        cf = [x.group(1) for x in linknamere.finditer(text)]
    return cf

def getHTML(text):
    # add ul/li
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

def makeDir(d):
    '''
    Simple wrapper to make a directory if it does not exist.
    '''
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def writeJSON(outfile, p):
    '''
    Simple wrapper to write a file as JSON.
    '''
    makeDir(outfile.rsplit('/', 1)[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(getDump(p))
    f.close()

def getDump(j):
    return json.dumps(j, sort_keys=True)

def getFrame(f):
    page = codecs.open(f, 'r', encoding='utf-8').read()
    if not pubre.search(page): return False
    getAliases(page)
    frame = {}
    frame['id'] = fridre.search(f).group(0).strip().replace('/', '-')
    frame['tn'] = gettN(page, f)
    return frame

def getAliases(page):
    text = itre.search(page).group(1).strip()
    its = linkre.findall(text)
    for t in its:
        term, alias = t.split('|')
        if not ktaliases.has_key(term):
            ktaliases[term] = []
        ktaliases[term].append(alias)

def gettN(page, f):
    tN = []
    text = tNre.search(page).group(0)
    page_url = u'https://door43.org/{0}'.format(f.split('pages/')[1].rstrip('.txt'))
    for i in text.split('\n'):
        if ( not i.strip() or 'Comprehension Questions' in i or u'>>]]**' in i
            or u'<<]]**' in i or u'====' in i
            or i.startswith((u'{{tag>', u'~~', u'**[[', u'\\\\')) ):
            continue
        item = {'ref': u''}
        tNtermse = tNtermre.search(i)
        if tNtermse:
            item['ref'] = tNtermse.group(1)
        tNtextse = tNtextre.search(i)
        if not tNtextse:
            tNtextse = tNtextre2.search(i)
        try:
            item_text = tNtextse.group(1).strip()
        except AttributeError:
            item_text = i
        item['text'] = getHTML(item_text)
        tN.append(item)
    return tN

def runKT(lang, today):
    ktpath = os.path.join(pages, lang, 'obe')
    keyterms = []
    for f in glob.glob('{0}/*/*.txt'.format(ktpath)):
        if 'home.txt' in f or '1-discussion-topic.txt' in f: continue
        kt = getKT(f)
        if kt:
            keyterms.append(kt)
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
    apipath = os.path.join(api_v2, 'bible', lang)
    writeJSON('{0}/terms.json'.format(apipath), keyterms)

def runtN(lang, today):
    tNpath = os.path.join(pages, lang, 'bible/notes')
    for book in os.listdir(tNpath):
        book_path = os.path.join(tNpath, book)
        if len(book) > 3: continue
        if not os.path.isdir(book_path): continue
        apipath = os.path.join(api_v2, book, lang)
        if not os.path.isdir(apipath): continue
        frames = []
        for chapter in os.listdir(book_path):
            try:
                int(chapter)
            except ValueError:
                continue
            for f in glob.glob('{0}/{1}/*.txt'.format(book_path, chapter)):
                if 'home.txt' in f: continue
                frame = getFrame(f)
                if frame: 
                    frames.append(frame)

        frames.sort(key=lambda x: x['id'])
        frames.append({'date_modified': today})
        writeJSON('{0}/notes.json'.format(apipath), frames)


if __name__ == '__main__':
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    runtN('en', today)
    runKT('en', today)
