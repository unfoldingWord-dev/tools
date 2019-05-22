# -*- coding: utf-8 -*-
# This program converts a folder of OBS text files
# from the newer format (multiple .txt files per OBS story)
# to a set of corresponding, OBS story files in Markdown format.
# Does nothing if the files are .md files already.
#    Specify target output folder.
#    Fixes links of this form [[:en:...]]

# Global variables
language_code = u'ilo'
target_dir = r'C:\Users\Larry\Documents\GitHub\Ilocano\ilo_obs-tq\content'
ta_dir = r'C:\Users\Larry\Documents\GitHub\English\en_ta'

import re
import io
import os
import sys
import json
import convert2md
# import usfm_verses
    
def makeMdPath(story, chunk):
    mdPath = os.path.join(target_dir, story)
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)

    return os.path.join(mdPath, chunk[0:-4]) + ".md"

# Returns True if the specified file name matches a pattern that indicates
# the file contains text to be converted.
def isChunk(filename):
    isSect = False
    if re.match('\d\d\.txt', filename) and filename != '00.txt':
        isSect = True;
    return isSect

# Returns True if the specified directory is a story number
def isChapter(dirname):
    return dirname != '00' and re.match('[0-5][0-9]$', dirname)

prefix_re = re.compile(r'C:\\Users\\Larry\\Documents\\GitHub')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[31:]
    return shortname

def dumpArticles(dir):
    pages = convert2md.getBadReferences()
    if len(pages) > 0:
        pagelist = list(set(pages))
        pagelist.sort()
        path = os.path.join(dir, "articles.txt")
        file = io.open(path, "tw", encoding='utf-8', newline='\n')
        for article in pagelist:
            file.write(article + '\n')
        file.close()
        sys.stderr.write("Unresolved links, see " + shortname(path) + '\n')

# Converts .txt file in fullpath location to .md file in target dir.
def convertFile(chap, fname, fullpath):
    if os.access(fullpath, os.F_OK):
        mdPath = makeMdPath(chap, fname)
        convert2md.json2md(fullpath, mdPath, ta_dir, language_code, shortname)

# This method is called to convert the text files in the specified chapter folder
# If it is not a chapter folder
def convertChapter(dir, fullpath):
    for fname in os.listdir(fullpath):
        if isChunk(fname):
            convertFile(dir, fname, os.path.join(fullpath, fname))

# Converts the OBS stories contained in the specified folder
def convert(path):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    sys.stdout.write("Converting: " + shortname(path) + "\n")
    sys.stdout.flush()
    for dir in os.listdir(path):
        if isChapter(dir):
            sys.stdout.write( " " + dir )
            convertChapter(dir, os.path.join(path, dir))

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python txt2md <folder>\n  Use . for current folder.\n")
    elif sys.argv[1] == 'hard-coded-path':
        convert(r'C:\Users\Larry\Documents\GitHub\Ilocano\TQ-OBS\ilo_obs_text_tq_l3')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print "\nDone."
