# -*- coding: utf-8 -*-
# This script produces produces a resource container for one or more usfm files with
# Alignment USFM3 source text.
# It does minimal editing, and only up to the first \c marker.
# It will process only one usfm file per folder, so remove any extras before running this script.
# The usfm file must contain an \id field with the book ID.
# The English RC folder is hard-coded in en_rc_dir.
# The output folder is also hard-coded, in target_dir.

import sys
import os

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

import usfm_verses
import io
import codecs
import re
import operator

# Global variables
en_rc_dir = r'E:\Users\Larry\AppData\Local\translationstudio\library\resource_containers'
target_dir = r'E:\DCS\Hindi\hi_irv'
projects = []

class State:
    ID = u""
    identification = u""
    rem = u""
    h = u""
    toc1 = u""
    toc2 = u""
    toc3 = u""
    mt = u""
    title = u""
    postHeader = u""
    reference = u""
    usfmFile = 0
    
    def addTOC1(self, toc):
        State.toc1 = toc
        State.title = toc

    def addH(self, h):
        State.h = h
        if not State.toc1:
            State.title = h
        
    def addMT(self, mt):
        if not State.mt:
            State.mt = mt
            if not State.toc1 and not State.h:
                State.title = mt

    # \mt1 overrides \mt on input
    # On output, there is only \mt1
    def addMT1(self, mt1):
        State.mt = mt1
        if not State.toc1 and not State.h:
            State.title = mt1

    def addTOC2(self, toc):
        State.toc2 = toc
        if not State.toc1 and not State.h and not State.mt:
            State.title = toc

    def addTOC3(self, toc):
        State.toc3 = toc
    
    def addPostHeader(self, key, value):
        if key:
            State.postHeader += u"\n\\" + key + u" "
        if value:
            State.postHeader += value

    def addID(self, id):
        State.identification = id
        if len(id) >= 3:
            State.ID = id[0:3].upper()
            State.chapter = 0
            State.verse = 0
            State.reference = id
            State.title = getDefaultName(State.ID)
            # Open output USFM file for writing.
            usfmPath = os.path.join(target_dir, makeUsfmFilename(State.ID))
            State.usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
       
    def reset(self):
        State.ID = u""
        State.rem = u""
        State.h = u""
        State.toc1 = u""
        State.toc2 = u""
        State.toc3 = u""
        State.mt = u""
        State.postHeader = u""
        State.reference = u""

# Returns path name for usfm file
def makeUsfmFilename(id):
    # loadVerseCounts()
    num = usfm_verses.verseCounts[id]['usfm_number']
    return str(num) + "-" + id + ".usfm"
    
# Returns path of temporary manifest file block listing projects converted
def makeManifestPath():
    return os.path.join(target_dir, "projects.yaml")
    
# Looks up the English book name, for use when book name is not defined in the file
def getDefaultName(id):
    # loadVerseCounts()
    en_name = usfm_verses.verseCounts[id]['en_name']
    return en_name
           
def takeAsIs(key, value):
    state = State()
    state.addPostHeader(key, value)
    # sys.stdout.write(u"addPostHeader(" + key + u", " + str(len(value)) + u")\n")

# Treats the token as the book title if no \mt has been encountered yet.
# Calls takeAsIs() otherwise.
def takeMTX(key, value):
    state = State()
    if not state.mt:
        state.addMT(value)
    else:
        takeAsIs(key, value)

token_re = re.compile(r'\\([^\t ]+)[\t ](.*)', re.UNICODE)

# Parses the specified line and updates the state.
def take(line):
    token = token_re.match(line)
    if token:
        state = State()
        marker = token.group(1)
        value = token.group(2)

        if marker == u"id":
            state.addID(value)
        elif marker == u"ide" or marker == u"usfm":
            value = 0       # do nothing
        elif marker == u"h":
            state.addH(value)
        elif marker == u"toc1":
            state.addTOC1(value)
        elif marker == u"toc2":
            state.addTOC2(value)
        elif marker == u"toc3":
            state.addTOC3(value)
        elif marker == u"mt":
            state.addMT(value)
        elif marker == u"mt1":
            state.addMT1(value)
        elif marker == u"imt" or marker == u"mte":
            takeMTX(marker, value)
        else:
            # sys.stdout.write("Taking other token: ")
            # print token
            takeAsIs(marker, value)

    global lastToken
    lastToken = token
     
# Writes a corrected USFM header to the new USFM file, then writes the body.
def writeUsfm(body):
    state = State()
    h = state.h
    toc1 = state.toc1
    toc2 = state.toc2
    mt = state.mt
    if not h:
        h = state.title
    if not toc1:
        toc1 = state.title
    if not toc2:
        toc2 = state.title
    if not mt:
        mt = state.title
    # sys.stdout.write(u"Starting to write header.\n")
    state.usfmFile.write(u"\\id " + state.identification)
    state.usfmFile.write(u"\n\\usfm 3.0")
    state.usfmFile.write(u"\n\\ide UTF-8")
    if state.rem:
        state.usfmFile.write(u"\n\\rem " + state.rem)
    state.usfmFile.write(u"\n\\h " + h)
    state.usfmFile.write(u"\n\\toc1 " + toc1)
    state.usfmFile.write(u"\n\\toc2 " + toc2)
    state.usfmFile.write(u"\n\\toc3 " + state.ID.lower())
    state.usfmFile.write(u"\n\\mt1 " + mt)      # safest to use \mt1 always. When \mt2 exists, \mt1 is required.
    
    # Write post-header if any
    state.usfmFile.write(u'\n')
    state.usfmFile.write(state.postHeader)
    state.usfmFile.write(u'\n')
    for line in body:
        state.usfmFile.write(line)
    state.usfmFile.close()

def convertFile(usfmpath, fname):
    state = State()
    state.reset()
    
    print "CONVERTING " + fname + ":"
    sys.stdout.flush()
    input = io.open(usfmpath, "tr", 1, encoding="utf-8")
    line = input.readline()
    while line[0:3] != u"\\c ":
        take(line)
        line = input.readline()
    body = []
    body.append(line)
    body += input.readlines()    # read the remainder of the usfm file
    input.close
    writeUsfm(body)
    return True

# Appends information about the current book to the global projects list.
def appendToProjects():
    global projects
    state = State()

    sort = usfm_verses.verseCounts[state.ID]["sort"]
    testament = u'nt'
    if sort < 40:
        testament = u'ot'
    project = { "title": state.title, "id": state.ID.lower(), "sort": str(sort), \
                "path": "./" + makeUsfmFilename(state.ID), \
                "categories": "[ 'bible-" + testament + u"' ]" }
    projects.append(project)

# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        printError("Invalid folder path given: " + folder)
        return
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
        
    usfmcount = 0
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if os.path.isdir(path) and fname[0] != '.':
            convertFolder(path)
        elif fname[-3:].lower() == 'sfm':
            usfmcount += 1
            if usfmcount < 2:
                convertFile(path, fname)
                appendToProjects()
            else:
                printError("Extra USFM file found. Script allows only one in folder: " + folder)
                
# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects
    
    projects.sort(key=operator.itemgetter('sort'))
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    for p in projects:
        manifest.write(u"  -\n")
        manifest.write(u"    title: '" + p['title'] + u"'\n")
        manifest.write(u"    versification: 'ufw'\n")
        manifest.write(u"    identifier: '" + p['id'] + u"'\n")
        manifest.write(u"    sort: " + str(p['sort']) + "\n")
        manifest.write(u"    path: '" + p['path'] + u"'\n")
        manifest.write(u"    categories: " + p['categories'] + u"\n")
    manifest.close()

def printError(text):
    sys.stderr.write(text + '\n')

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
         convertFolder(r'E:\DCS\Hindi\IRV')
    else:       # the first command line argument is presumed to be the folder containing usfm files to be converted
        convertFolder(sys.argv[1])
    dumpProjects()

    print "\nDone."
