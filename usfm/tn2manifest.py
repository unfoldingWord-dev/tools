# coding: latin-1

# Requires that the directory specified on the command line contains folders
# with 3-character names corresponding to USFM book abbreviations.
# Assumes it is a tN directory, unless the name ends in Q, in which case it is a tQ directory.
# Creates a manifest.txt file in the specified directory.

import sys
import os
import io
import codecs
import re
import json

# Global variables
verseCounts = {}
home_dir = ""

# Opens the verses.json file, which must reside in the same path as this .py script.
def loadVerseCounts():
    global verseCounts
    if len(verseCounts) == 0:
        jsonPath = os.path.dirname(os.path.abspath(__file__)) + "\\" + "verses.json"
        if os.access(jsonPath, os.F_OK):
            f = open(jsonPath, 'r')
            verseCounts = json.load(f)
            f.close()
        else:
            sys.stderr.write("File not found: verses.json\n")
            sys.exit(-1)

def makeManifestPath():
    return os.path.join(home_dir, "manifest.txt")

def appendToManifest(directory, bookTitle):
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    manifest.write(u"  -\n")
    title = bookTitle + u" translationNotes"
    if home_dir[-1:].upper() == 'Q':
        title = bookTitle + u" translationQuestions"
    manifest.write(u"    title: '" + title + u"'\n")
    manifest.write(u"    versification: ''\n")
    manifest.write(u"    identifier: '" + directory.lower() + u"'\n")
    manifest.write(u"    sort: 0\n")
    manifest.write(u"    path: './" + directory + u"'\n")
    manifest.write(u"    categories: []\n")
    manifest.close()

def isBookDir(name):
    isbook = False
    path = os.path.join(home_dir, name)
    if len(name) == 3 and os.path.isdir(path):
        isbook = verseCounts[name]
    return isbook

# Returns the desired name of the book.
# For now, just returns the English name.
def getBookName(bookId):
    return verseCounts[bookId]['en_name']

# Extracts the folder names and corresponding book ID information
# into a manifest.txt file, which will be appropriate for pasting into
# the manifest.yaml file for tN.
def extract(dir):
    if not os.path.isdir(dir):
        sys.stderr.write("Invalid directory: " + dir + "\n")
        sys.exit(-1)

    global home_dir
    home_dir = dir
    loadVerseCounts()
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    alldirs = os.listdir(dir)
    for directory in alldirs:
        if isBookDir(directory.upper()):
            bookname = getBookName(directory.upper())
            appendToManifest(directory, bookname)


# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python tn2manifest <folder>\n  Use . for current folder.\n")
    elif sys.argv[1] == 'hard-coded-path':
        extract(r'C:\Users\Larry\Documents\GitHub\Malayalam\BCS.ml_tQ\content')
    else:       # the first command line argument presumed to be a folder
        extract(sys.argv[1])

    print "\nDone."
