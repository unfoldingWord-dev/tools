#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright (c) 2014 unfoldingWord
#    http://creativecommons.org/licenses/MIT/
#    See LICENSE file for details.
#
#    Contributors:
#    Jesse Griffin <jesse@distantshores.org>


"""
This script imports USFM files from a zip file and prepares them for use in
translationStudio.
"""

import os
import re
import sys
import glob
import json
import codecs
import shutil
import urllib2
import zipfile
import argparse
import datetime


chunkurl = u'https://api.unfoldingword.org/ts/txt/2/{0}/en/ulb/chunks.json'
outtmp = '/var/www/vhosts/api.unfoldingword.org/httpdocs/{0}/txt/1/{0}-{1}'
idre = re.compile(ur'\\id.*', re.UNICODE)
chpre = re.compile(ur'\\c [0-9]* ', re.UNICODE)



def main(resource, lang, slug):
    local_res = '/tmp/{0}'.format(resource.rpartition('/')[2])
    sourceDir = '/tmp/{0}'.format(resource.rpartition('/')[2].strip('.zip'))
    outdir = outtmp.format(slug, lang)

    if not os.path.isfile(local_res):
        getZip(resource, local_res)
    unzip(local_res, sourceDir)

    files = glob.glob('{0}/{1}'.format(sourceDir, '*[Ss][Ff][Mm]'))
    for path in files:
        lines = codecs.open(path, encoding='utf-8').readlines()
        book = getbook('\n'.join(lines[:10]))
        print book
        if not book: continue
        verses = getVerses(book)
        if not verses: continue
        newlines = addSections(lines, verses)
        print '--> {0}/{1}'.format(outdir, path.rpartition('/')[2])
        writeFile('{0}/{1}'.format(outdir,
                                 path.rpartition('/')[2]), u''.join(newlines))

def getVerses(book):
    chunkstr = getURL(chunkurl.format(book.lower()))
    if not chunkstr: return False
    chunks = json.loads(chunkstr)
    return [x['firstvs'] for x in chunks]

def addSections(lines, verses):
    newlines = []
    i = 0
    for line in lines:
        if line in [u'', u' ', u'\n']: continue
        chpse = chpre.search(line)
        if chpse:
            newlines.append(u'\\s5\n')
            newlines.append(line)
            i += 1
            continue
        if i < len(verses):
            versese = re.search(ur'\\v {0} '.format(verses[i]), line)
            if versese:
                newlines.append(u'\\s5\n')
                i += 1
        newlines.append(line)
    return newlines

def getbook(text):
    idse = idre.search(text)
    if not idse:
        return False
    return idse.group(0).split()[1]

def writeFile(f, content):
    makeDir(f.rpartition('/')[0])
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def unzip(source, dest):
    with zipfile.ZipFile(source) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)

def getZip(url, outfile):
    print "Getting ZIP"
    try:
        request = urllib2.urlopen(url)
    except:
        print "    => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)

def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return u''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-r', '--resource', dest="resource", default=False,
        required=True, help="URL of zip file.")
    parser.add_argument('-l', '--lang', dest="lang", default=False,
        required=True, help="Language code of resource.")
    parser.add_argument('-s', '--slug', dest="slug", default=False,
        required=True, help="Slug of resource name (e.g. NIV).")

    args = parser.parse_args(sys.argv[1:])
    main(args.resource, args.lang, args.slug)
