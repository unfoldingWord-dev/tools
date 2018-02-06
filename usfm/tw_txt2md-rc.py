# coding: latin-1
# This script converts a repository of tW text files from tStudio to .md format,
# to create a valid resource container. It was developed in Oct 2017 specifically
# to convert the year-old Vietnamese translation Words, where the folder structure
# is different from the current standard. The old folder structure has only a single
# folder for all 1000+ files. This script is intended to do the following:
#    Convert each .txt file into an equivalent .md file.
#    Determine a location under the target folder for the .md file based on
#       matching the file name to a file in the English tW structure. Assumes that
#       folders are only one level deep under the English and target language folders.

# Global variables
en_tw_dir = r'C:\Users\Larry\Documents\GitHub\English\en_tw\bible'
target_dir = r'C:\Users\Larry\Documents\GitHub\Vietnamese\vi_bible_tw\vi_tw.temp\bible'

import re
import io
import os
import sys
import json

    
def makeMdPath(fname):
    mdName = os.path.splitext(fname)[0] + ".md"
    subdir = "other"
    for trydir in os.listdir(en_tw_dir):
        tryFolder = os.path.join(en_tw_dir, trydir)
        if os.path.isdir(tryFolder):
            if os.path.isfile( os.path.join(tryFolder, mdName) ):
                subdir = trydir
                break

    mdFolder = os.path.join(target_dir, subdir)
    if not os.path.isdir(mdFolder):
        os.mkdir(mdFolder)
    return os.path.join(mdFolder, mdName)

import string

# Converts .txt file in fullpath location to .md file in target dir.
def convertFile(fname, fullpath):
    # Open output .md file for writing.
    mdPath = makeMdPath(fname)
    mdFile = io.open(mdPath, "tw", buffering=1, encoding='utf-8', newline='\n')
    
    # Read input file
    if os.access(fullpath, os.F_OK):
        f = open(fullpath, 'r')
        word = json.load(f)
        f.close()

    for note in word:
        title = unicode(note['title']).strip()
        body = unicode(note['body']).strip()
        mdFile.write(u'# ' + string.replace(title, u'\r\n', u'\n') + u'\n\n')
        mdFile.write(string.replace(body, u'\r\n', u'\n') + u'\n\n')
    mdFile.close()

# This method is called to convert the text files in the specified folder.
def convertFolder(fullpath):
    for fname in os.listdir(fullpath):
        convertFile(fname, os.path.join(fullpath, fname))

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python txt2md <folder>\n  Use . for current folder.\n")
        folder = ""
    elif sys.argv[1] == 'hard-coded-path':
        folder = r'C:\Users\Larry\Documents\GitHub\Vietnamese\vi_bible_tw\01'
    else:       # the first command line argument presumed to be a folder
        folder = sys.argv[1]

    if os.path.isdir(folder):
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        convertFolder(folder)
    print "\nDone."
