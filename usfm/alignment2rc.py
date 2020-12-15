# -*- coding: utf-8 -*-
# This script produces produces a resource container for one or more usfm files with
# Alignment USFM3 source text.
# It does minimal editing, and only up to the first \c marker.
# It will process only one usfm file per folder, so remove any extras before running this script.
# The usfm file must contain an \id field with the book ID.
# The output folder is also hard-coded, in target_dir.

import sys
import os

# Global variables
source_dir = r'C:\DCS\Marathi\IRV'   # folder containing usfm files to be converted
target_dir = r'C:\DCS\Marathi\mr_irv.new'
projects = []
# Set Path for files in support/
# rootdiroftools = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(rootdiroftools,'support'))

import usfm_verses
import io
import codecs
import re
import operator

class State:
    ID = ""
    identification = ""
    rem = ""
    h = ""
    toc1 = ""
    toc2 = ""
    toc3 = ""
    mt = ""
    title = ""         # updates to the best non-ascii title if any, or best ascii title 
    postHeader = ""
    prevkey = ""
    key = ""
    reference = ""
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
            State.postHeader += "\n\\" + key + " "
        else:
            State.postHeader = ""
        if value:
            State.postHeader += value
        State.key = key
    
    def addKey(self, key):
        State.prevkey = State.key
        State.key = key

    def addID(self, id):
        State.identification = id
        if len(id) >= 3:
            State.ID = id[0:3].upper()
        if not projectExists(State.ID):
            State.chapter = 0
            State.verse = 0
            State.reference = id
            State.title = getDefaultName(State.ID)
            # Open output USFM file for writing.
            usfmPath = os.path.join(target_dir, makeUsfmFilename(State.ID))
            State.usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
        else:
            raise RuntimeError("Duplicate USFM file for: " + State.ID)

    # Finds the best values for h, toc1, toc2, and mt1.
    # Prefers non-ascii values for all fields.
    # Sets these values in the State
    def optimizeTitles(self):
        if State.title.isascii() and not State.mt.isascii():
            State.title = State.mt
        elif State.title.isascii() and not State.toc1.isascii():
            State.title = State.toc1
        elif State.title.isascii() and not State.h.isascii():
            State.title = State.h
        elif State.title.isascii() and not State.toc2.isascii():
            State.title = State.toc2

        if State.h == "" or (State.h.isascii() and not State.title.isascii()):
            State.h = State.title
        if State.toc1 == "" or (State.toc1.isascii() and not State.title.isascii()):
            State.toc1 = State.title
        if State.toc2 == "" or (State.toc2.isascii() and not State.title.isascii()):
            State.toc2 = State.title
        if State.mt == "" or (State.mt.isascii() and not State.title.isascii()):
            State.mt = State.title

    def reset(self):
        State.ID = ""
        State.rem = ""
        State.h = ""
        State.toc1 = ""
        State.toc2 = ""
        State.toc3 = ""
        State.mt = ""
        State.postHeader = ""
        State.reference = ""

# class DuplicateBook(Exception):
#     def __init__(self, value):
#         self.value = value
#     def __str__(self):
# #        return repr(self.value)
#         return self.value

# Returns True if the project already exists in the array of projects.
def projectExists(id):
    exists = False
    global projects
    for p in projects:
        if p['id'] == id.lower():
            exists = True
            break
    return exists

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

        if marker == "id":
            state.addID(value)
        elif marker == "ide" or marker == "usfm":
            value = 0       # do nothing
        elif marker == "h":
            state.addH(value)
        elif marker == "toc1":
            state.addTOC1(value)
        elif marker == "toc2":
            state.addTOC2(value)
        elif marker == "toc3":
            state.addTOC3(value)
        elif marker == "mt":
            state.addMT(value)
        elif marker == "mt1":
            state.addMT1(value)
        elif marker == "imt" or marker == "mte":
            takeMTX(marker, value)
        else:
            # sys.stdout.write("Taking other token: ")
            # print token
            takeAsIs(marker, value)

    global lastToken
    lastToken = token

bodytoken_re = re.compile(r'\\([^\t \n]+)', re.UNICODE)

# After the header is fully processed with take() calls, takeBody() is called to do simpler processing on the body of the usfm file.
def takeBody(line):
    token = bodytoken_re.match(line)
    if token:
        state = State()
        marker = token.group(1)
        state.addKey(marker)

# Writes a corrected USFM header to the new USFM file, then writes the body.
def writeUsfm(body):
    state = State()
    state.optimizeTitles()
    # sys.stdout.write(u"Starting to write header.\n")
    state.usfmFile.write("\\id " + state.identification)
    state.usfmFile.write("\n\\usfm 3.0")
    state.usfmFile.write("\n\\ide UTF-8")
    if state.rem:
        state.usfmFile.write("\n\\rem " + state.rem)
    state.usfmFile.write("\n\\h " + state.h)
    state.usfmFile.write("\n\\toc1 " + state.toc1)
    state.usfmFile.write("\n\\toc2 " + state.toc2)
    toc3 = state.toc3
    if len(toc3) != 3:
        toc3 = state.ID.lower()
    state.usfmFile.write("\n\\toc3 " + toc3)
    state.usfmFile.write("\n\\mt1 " + state.mt)    # safest to use \mt1 always. When \mt2 exists, \mt1 is required.
    
    # Write post-header if any
    state.usfmFile.write('\n')
    state.usfmFile.write(state.postHeader)
    state.usfmFile.write('\n')
    
    # Write the rest of the file
    for line in body:
        takeBody(line)
        if line.startswith("\\v 1 ") and state.prevkey != "p":
            state.usfmFile.write("\\p\n")
        state.usfmFile.write(line)
    if line[-1] != '\n':
        state.usfmFile.write('\n')
    state.usfmFile.close()

# Makes minor corrections to specified usfm file and copies to properly named usfm file at target_dir.
def convertFile(usfmpath, fname):
    state = State()
    state.reset()
    
    print("CONVERTING " + fname + ":")
    sys.stdout.flush()
    input = io.open(usfmpath, "tr", 1, encoding="utf-8")
    try:
        line = input.readline()
        while line and line[0:3] != "\\c ":
            take(line)
            line = input.readline()
        if line[0:3] != "\\c ":
            printError("No chapters in file: " + fname)
        else:
            body = []
            body.append(line)
            body += input.readlines()    # read the remainder of the usfm file
            input.close
            writeUsfm(body)
    except RuntimeError as dup:
        input.close
        raise
    return True

# Appends information about the current book to the global projects list.
def appendToProjects():
    global projects
    state = State()

    sort = usfm_verses.verseCounts[state.ID]["sort"]
    testament = 'nt'
    if sort < 40:
        testament = 'ot'
    project = { "title": state.title, "id": state.ID.lower(), "sort": sort, \
                "path": "./" + makeUsfmFilename(state.ID), \
                "categories": "[ 'bible-" + testament + "' ]" }
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
            try:
                convertFile(path, fname)
                appendToProjects()
            except RuntimeError as dup:
                printError(str(dup))
            
# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects
    
    projects.sort(key=operator.itemgetter('sort'))
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    versification: 'ufw'\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: " + p['categories'] + "\n")
    manifest.close()

def printError(text):
    sys.stderr.write(text + '\n')

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    convertFolder(source_dir)
    dumpProjects()
    sys.stderr.flush()

    print("\nDone.")
