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
idre = re.compile(ur'\\id.*', re.UNICODE)

LICENSE = u'''~~NOCACHE~~
\mt unfoldingWord | Literal Bible

\p \\bd an unrestricted Bible intended for translation into any language \\bd*

\p \em http://unfoldingWord.org/Bible \em*

\p unfoldingWord Literal Bible, v. 0.1

This work is based on \em The American Standard Version \em*, which is in the public domain.


\p License:

\p This work is made available under a Creative Commons Attribution-ShareAlike 4.0 International License (http://creativecommons.org/licenses/by-sa/4.0/).

\p You are free:

\p \\bd Share \\bd* — copy and redistribute the material in any medium or format
\p \\bd Adapt \\bd* — remix, transform, and build upon the material for any purpose, even commercially.

\p Under the following conditions:

\p \\bd Attribution \\bd* — You must attribute the work as follows: "Original work available at http://openbiblestories.com." Attribution statements in derivative works should not in any way suggest that we endorse you or your use of this work.
\p \\bd ShareAlike \\bd* — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

\p Use of trademarks: \\bd unfoldingWord \\bd* is a trademark of Distant Shores Media and may not be included on any derivative works created from this content.    Unaltered content from http://unfoldingWord.org must include the \\bd unfoldingWord \\bd* logo when distributed to others. But if you alter the content in any way, you must remove the \\bd unfoldingWord \\bd* logo before distributing your work.
'''


def main(resource, outdir):
    local_res = '/tmp/{0}'.format(resource.rpartition('/')[2])
    sourceDir = '/tmp/{0}'.format(resource.rpartition('/')[2].strip('.zip'))

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
        writeFile('{0}/{1}'.format(outdir, path.rpartition('/')[2]),
                                                         u''.join(newlines))

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
    parser.add_argument('-o', '--output', dest="outputDir", default=False,
        required=True, help = "Output Directory")
    parser.add_argument('-r', '--resource', dest="resource", default=False,
        required=True, help="URL of zip file.")

    args = parser.parse_args(sys.argv[1:])
    main(args.resource, args.outputDir)
