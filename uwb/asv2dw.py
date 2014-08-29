#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Joel Neutrino <joel@neutrinographics.com>
#  Jesse Griffin <jesse@distantshores.org>


"""
This script splits the USFM files from ASV
(http://ebible.org/asv/eng-asv_usfm.zip) into separate chapters and does some
basic language substitutions.
"""

import os
import re
import sys
import glob
import codecs
import shutil
import urllib2
import zipfile
import argparse
import datetime

words_path = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ulb/v1/subs.txt'
phrases_path = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ulb/v1/phrase_subs.txt'
asvp = re.compile(ur'[tT]ranslation 4 .*$', re.UNICODE)
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

\p Use of trademarks: \\bd unfoldingWord \\bd* is a trademark of Distant Shores Media and may not be included on any derivative works created from this content.  Unaltered content from http://unfoldingWord.org must include the \\bd unfoldingWord \\bd* logo when distributed to others. But if you alter the content in any way, you must remove the \\bd unfoldingWord \\bd* logo before distributing your work.
'''


def main(arguments):
  parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-o', '--output', dest="outputDir", default=False,
    required=True, help = "Output Directory")
  parser.add_argument('-c', '--clean', dest="clean", default=False, action="store_const", const="sum", help = "Clean workspace")

  args = parser.parse_args(arguments)

  sourceDir = 'usfm_asv_source/'
  if args.outputDir:
    outputDir = args.outputDir
    if not os.path.isdir(outputDir):
      os.mkdir(outputDir)

  bookTags = ['\id', '\ide', '\h', '\\toc1', '\\toc2', '\\toc3', '\mt', '\mt1']
  asvzip = '/tmp/eng-asv_usfm.zip_{0}'.format(str(datetime.date.today()))

  # clean the workspace
  if args.clean:
    print('cleaning workspace..')
    if os.path.isdir(outputDir):
      shutil.rmtree(outputDir)
    os.remove(asvzip)
    print('done')
    return

  # Download ASV zip
  if not os.path.isfile(asvzip):
    getURL('http://ebible.org/asv/eng-asv_usfm.zip', asvzip)

  # Get language update table
  word_sub = getLangTable(words_path)
  phrase_sub = getLangTable(phrases_path)

  # extract the archive
  unzip(asvzip, sourceDir)

  # list books
  fileList = []
  files = glob.glob(sourceDir + '*[Ss][Ff][Mm]')
  for path in files:
    # open a new book
    f = codecs.open(path, encoding='utf-8')
    bookHeader = []
    bookID = None
    chapterNum = None
    chapterLines = [] # emptied after each chapter

    lines = f.readlines()
    f.close()
    for l in lines:
      tag = l.split(None,1)[0]
        # load the book header
      if tag in bookTags:
        bookHeader.append(l)
        #if tag == '\h':
          #print('exploding '+l.split(None,1)[1])
        if tag == '\id':
          bookID = l.split(None,2)[1]
      else:
        if tag == '\c':
          # write finished chapter
          if chapterNum is not None:
            book = str(outputDir+bookID).lower()
            if not os.path.isdir(book):
              os.mkdir(book)
            outputFile = book+'/'+chapterNum+'.usfm.txt'
            writeFile(outputFile, convert(chapterLines, word_sub, phrase_sub))
            fileList.append('{0}:{1}.usfm'.format(bookID, chapterNum))

          # begin reading new chapter
          chapterNum = str(l.split(None,2)[1]).zfill(3)
          chapterLines = []
          chapterLines.append(l)
        else:
          # load chapter lines
          chapterLines.append(l)
    # write the last chapter
    if chapterNum is not None:
      book = str(outputDir+bookID).lower()
      if not os.path.isdir(book):
        os.mkdir(book)
      outputFile = book+'/'+chapterNum+'.usfm.txt'
      writeFile(outputFile, convert(chapterLines, word_sub, phrase_sub))
      fileList.append('{0}:{1}.usfm'.format(bookID, chapterNum))
    # write book information
    book = str(outputDir+bookID).lower()
    if not os.path.isdir(book):
      os.mkdir(book)
    outputFile = book+'/000.usfm.txt'
    writeFile(outputFile, ulbize(bookHeader))
    fileList.append('{0}:000.usfm'.format(bookID))

  # clean up after ourselves
  shutil.rmtree(sourceDir)

  f = codecs.open('{0}/ulb.txt'.format(outputDir), encoding='utf-8', mode='w')
  for e in fileList:
    f.write('  * [[en:ulb:v1:{0}|{1}]]\n'.format(e.lower(),
      e.strip('.usfm').replace(':', ' ')))
  f.close()
  #writeFile('{0}/frt/000.usfm.txt'.format(outputDir), LICENSE)


def writeFile(f, content):
  out = codecs.open(f, encoding='utf-8', mode='w')
  out.write(content)
  out.close()


def ulbize(l):
  s = u''.join(l)
  return asvp.sub(ur"unfoldingWord | Literal Bible", s)


def convert(lines, words, phrases):
  '''
  Converts antiquated English into modern.
  '''
  newlines = []
  for l in lines:
    l = l.replace(u'æ', 'ae')
    tokens = l.split()
    # Update word language
    for k,v in words.iteritems():
      if k in tokens:
        tokens = [x.replace(k,v) for x in tokens]
    newlines.append(u' '.join(tokens))
  newstr = u'\n'.join(newlines)
  # Update phrase language
  for k,v in phrases.iteritems():
    newstr.replace(k, v)
  return newstr


def getLangTable(f):
  langDict = {}
  fd = codecs.open(f, 'r', encoding='utf-8').readlines()
  for l in fd:
    items = l.strip().split(u'/')
    k = u'{0}'.format(items[0])
    v = u'{0}'.format(items[1])
    langDict[k] = v
  return langDict


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


def getURL(url, outfile):
  print "Getting ZIP"
  try:
    request = urllib2.urlopen(url)
  except:
    print "  => ERROR retrieving %s\nCheck the URL" % url
    sys.exit(1)
  with open(outfile, 'wb') as fp:
    shutil.copyfileobj(request, fp)


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
