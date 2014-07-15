#!/usr/bin/env python
# -*- coding: utf8 -*-
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#
# Author: Joel Neutrino <joel@neutrinographics.com>
# Revised: Jesse Griffin <jesse@distantshores.org>


"""
This script splits the USFM files from T4T (http://ebible.org/t4t/) into
separate chapters and does some basic text to footnote conversions.
"""

import os
import re
import sys
import argparse
import zipfile
import os.path
import shutil
import glob
import codecs

footnote = u'\\f + \\ft {0} \\f*'
refootnote = ur'\\f + \\ft {0} \\f*'
arrowp = re.compile(ur'◄([^/]*)/(.*)►', flags=32) # Matches: ◄option1/option2►
slashinft = re.compile(ur'(\\ft .*)/', flags=32) # Matches: \ft option2/option3
orp = re.compile(ur'[(]OR,(.*)[)]', flags=16) # Matches: (OR alternative text)
slashp = re.compile(ur'(\w*)/(\w*)', flags=32) # Matches: option1/option2
abbvtable = {
  u'[APO]': u'apostrophe',
  u'[CHI]': u'chiasmus',
  u'[DOU]': u'doublet',
  u'[EUP]': u'euphemism',
  u'[HEN]': u'hendiadys',
  u'[HYP]': u'hyperbole',
  u'[IDM]': u'idiom',
  u'[IRO]': u'irony',
  u'[LIT]': u'litotes',
  u'[MET]': u'metaphor',
  u'[MTY]': u'metonymy',
  u'[PRS]': u'personification',
  u'[RHQ]': u'rhetorical question',
  u'[SIM]': u'simile',
  u'[SYM]': u'symbol',
  u'[SAR]': u'sarcasm',
  u'[SYN]': u'synecdoche',
  u'[TRI]': u'triple',
}

def main(arguments):

  parser = argparse.ArgumentParser(description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-o', '--output', dest="outputDir", default=False,
    required=True, help = "Output Directory")
  parser.add_argument('infile', help = "Input file",
    type = argparse.FileType('r'))
  parser.add_argument('-c', '--clean', dest="clean", default=False, action="store_const", const="sum", help = "Clean workspace")

  args = parser.parse_args(arguments)

  sourceDir = 'usfm_t4t_source/'
  if args.outputDir:
    outputDir = args.outputDir
    if not os.path.isdir(outputDir):
      os.mkdir(outputDir)

  bookTags = ['\id', '\ide', '\h', '\\toc1', '\\toc2', '\\toc3', '\mt']

  # clean the workspace
  if args.clean:
    print('cleaning workspace..')
    if os.path.isdir(outputDir) or os.path.isdir(args.infile.name):
      if os.path.isdir(outputDir):
        shutil.rmtree(outputDir)

      if os.path.isdir(args.infile.name):
        shutil.rmtree(args.infile.name)
    print('done')
    return

  # extract the archive
  unzip(args.infile.name, sourceDir)

  # list books
  fileList = []
  files = glob.glob(sourceDir + '*.usfm')
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
            writeFile(outputFile, convert(''.join(chapterLines)))
            fileList.append('{0}:{1}.usfm'.format(bookID, chapterNum))

          # begin reading new chapter
          chapterNum = l.split(None,2)[1]
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
      writeFile(outputFile, convert(''.join(chapterLines)))
      fileList.append('{0}:{1}.usfm'.format(bookID, chapterNum))
    # write book information
    book = str(outputDir+bookID).lower()
    if not os.path.isdir(book):
      os.mkdir(book)
    outputFile = book+'/0.usfm.txt'
    writeFile(outputFile, ''.join(bookHeader))
    fileList.append('{0}:0.usfm'.format(bookID))

  # clean up after ourselves
  shutil.rmtree(sourceDir)

  f = codecs.open('{0}/uwb.txt'.format(outputDir), encoding='utf-8', mode='w')
  for e in fileList:
    f.write('  * [[playground:uwb:{0}|{1}]]\n'.format(e.lower(), 
      e.strip('.usfm').replace(':', ' ')))
  f.close()


def writeFile(f, content):
  out = codecs.open(f, encoding='utf-8', mode='w')
  out.write(content)
  out.close()


def convert(f):
  '''
  Converts T4T features into footnotes.
  '''
  f = arrowp.sub(ur'\1{0}'.format(refootnote.format(ur'Or: \2')), f)
  f = slashinft.sub(r'\1, Or: ', f)
  f = orp.sub(refootnote.format(ur'Or:\1'), f)
  f = slashp.sub(ur'\1{0}'.format(refootnote.format(ur'Or: \2')), f)
  for k,v in abbvtable.iteritems():
    f = f.replace(k, footnote.format(v))
  return f


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


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
