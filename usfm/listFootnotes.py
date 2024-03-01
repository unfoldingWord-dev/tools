# -*- coding: utf-8 -*-
# This script goes through USFM files, generating a list of verses that contain properly marked footnotes.
# Reports errors to stderr and issues.txt.
# Set source_dir and usfmVersion to run.

# Global variables
source_dir = r'C:\DCS\Portuguese\pt-br_ulb'
usfmVersion = 2     # if version 3.0 or greater, tolerates unknown tokens and verse fragments
state = None

import os
import sys
import parseUsfm
import io
import re
import json
if usfmVersion >= 3.0:
    import usfm_utils

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    def __init__(self):
        self.IDs = []
        self.ID = ""
        self.chapter = 0
        self.verse = 0
        self.reference = ""
        self.footnoteRefs = list()
    
    # Resets state data for a new book
    def addID(self, id):
        self.IDs.append(id)
        self.ID = id
        self.chapter = 0
        self.verse = 0
        self.reference = id
        
    def getIDs(self):
        return self.IDs
        
    def addChapter(self, c):
        self.chapter = int(c)
        self.verse = 0
        self.reference = self.ID + " " + c
    
    def addVerse(self, v):
        self.verse = int(v)
        self.reference = self.ID + " " + str(self.chapter) + ":" + v

    # Adds the current reference to the list of footnote references
    def addFootnote(self):
        if self.reference not in self.footnoteRefs:
            self.footnoteRefs.append(self.reference)
    
    # Returns list of footnote references as a json string
    def getFootnoteReferences(self):
        return json.dumps(self.footnoteRefs)

    def countFootnotes(self):
        return len(self.footnoteRefs)    

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def takeID(id):
    if len(id) < 3:
        reportError("Invalid ID: " + id)
    id = id[0:3].upper()
    if id in state.getIDs():
        reportError("Duplicate ID: " + id)
    state.addID(id)
    
def takeC(c):
    state.addChapter(c)

# Receives a string containing a verse number or range of verse numbers.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def takeV(vstr):
    vlist = []
    if vstr.find('-') > 0:
        vv_range = vv_re.search(vstr)
        if vv_range:
            vn = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            while vn <= vnEnd:
                vlist.append(vn)
                vn += 1
        else:
            reportError("Problem in verse range near " + state.reference)
    else:
        vlist.append(int(vstr))

    for vn in vlist:
        v = str(vn)
        state.addVerse(str(vn))
        
# Writes error message to stderr and to issues.txt.
def reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        sys.stderr.write(state.reference + ": (Unicode...)\n")
 
# Returns true if token is a countable part of a footnote
def isFootnote(token):
    # return token.isF_S() or token.isF_E() or token.isFR() or token.isFR_E() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()
    return token.isF_S() or token.isF_E()

def take(token):
    global usfmVersion

    if isFootnote(token):
        state.addFootnote()
    if token.isID():
        takeID(token.value)
    elif token.isC():
        if not state.ID:
            reportError("Missing book ID: " + state.reference)
            sys.exit(-1)
        takeC(token.value)
    elif token.isV():
        takeV(token.value)

# Corresponding entry point in tx-manager code is verify_contents_quiet()
def processFile(path):
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close()
    if usfmVersion >= 3.0:
        str = usfm_utils.usfm3_to_usfm2(str)

    print("CHECKING " + shortname(path))
    sys.stdout.flush()
    for token in parseUsfm.parseString(str):
        take(token)
    state.addID("")
    sys.stderr.flush()

# Verifies all .usfm files under the specified folder.
def processDir(dirpath):
    for f in os.listdir(dirpath):
        if f[0] != '.':         # ignore hidden files
            path = os.path.join(dirpath, f)
            if os.path.isdir(path):
                # It's a directory, recurse into it
                processDir(path)
            elif os.path.isfile(path) and path[-3:].lower() == 'sfm':
                processFile(path)

# Writes list of footnote references to a file.
def dumpFootnoteReferences():
    refs = state.getFootnoteReferences()
    if refs:
        path = os.path.join(source_dir, "footnotedVerses.json")
        footnoteFile = io.open(path, "tw", encoding='utf-8', newline='\n')
        footnoteFile.write(refs)
        footnoteFile.close()
    sys.stdout.write("Found " + str(state.countFootnotes()) + " footnotes.\n")

def main():
    global state
    state = State()
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    
    if os.path.isdir(source_dir):
        processDir(source_dir)
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        processFile(path)
    else:
        reportError("File not found: " + source_dir)
    
    dumpFootnoteReferences()

if __name__ == "__main__":
    main()