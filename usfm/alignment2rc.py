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
source_dir = r'C:\DCS\Persian\pes_opcb22'   # folder containing usfm files to be converted
target_dir = r'C:\DCS\Persian\work'
state = None
projects = []
contributors = []
checkers = []

import usfm_verses
import io
import codecs
import re
import operator
import json

class State:
    def __init__(self):
        self.ID = ""
        self.identification = ""
        self.rem = ""
        self.h = ""
        self.toc1 = ""
        self.toc2 = ""
        self.toc3 = ""
        self.mt = ""
        self.title = ""   # updates to the best non-ascii title if any, or best ascii title
        self.postHeader = ""
        self.prevkey = ""
        self.key = ""
        self.reference = ""
        self.usfmFile = 0

    def addTOC1(self, toc):
        self.toc1 = toc
        self.title = toc

    def addH(self, h):
        self.h = h
        if not self.toc1:
            self.title = h

    def addMT(self, mt):
        if not self.mt:
            self.mt = mt
            if not self.toc1 and not self.h:
                self.title = mt

    # \mt1 overrides \mt on input
    # On output, there is only \mt1
    def addMT1(self, mt1):
        self.mt = mt1
        if not self.toc1 and not self.h:
            self.title = mt1

    def addTOC2(self, toc):
        self.toc2 = toc
        if not self.toc1 and not self.h and not self.mt:
            self.title = toc

    def addTOC3(self, toc):
        self.toc3 = toc

    def addPostHeader(self, key, value):
        if key:
            self.postHeader += "\n\\" + key + " "
        else:
            self.postHeader = ""
        if value:
            self.postHeader += value
        self.key = key

    def addKey(self, key):
        self.prevkey = self.key
        self.key = key

    def addID(self, id):
        self.identification = id
        if len(id) >= 3:
            self.ID = id[0:3].upper()
        if not projectExists(self.ID):
            self.chapter = 0
            self.verse = 0
            self.reference = id
            self.title = getDefaultName(self.ID)
            # Open output USFM file for writing.
            usfmPath = os.path.join(target_dir, makeUsfmFilename(self.ID))
            self.usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
        else:
            raise RuntimeError("Duplicate USFM file for: " + self.ID)

    # Finds the best values for h, toc1, toc2, and mt1.
    # Prefers non-ascii values for all fields.
    # Sets these values in the State.
    def optimizeTitles(self):
        if self.title.isascii() and not self.mt.isascii():
            self.title = self.mt
        elif self.title.isascii() and not self.toc1.isascii():
            self.title = self.toc1
        elif self.title.isascii() and not self.h.isascii():
            self.title = self.h
        elif self.title.isascii() and not self.toc2.isascii():
            self.title = self.toc2          

        if self.h == "" or (self.h.isascii() and not self.title.isascii()):
            self.h = self.title
        if self.toc1 == "" or (self.toc1.isascii() and not self.title.isascii()):
            self.toc1 = self.title
        if self.toc2 == "" or (self.toc2.isascii() and not self.title.isascii()):
            state.toc2 = state.title
        if state.mt == "" or (state.mt.isascii() and not state.title.isascii()):
            state.mt = state.title

    def reset(self):
        state.ID = ""
        state.rem = ""
        state.h = ""
        state.toc1 = ""
        state.toc2 = ""
        state.toc3 = ""
        state.mt = ""
        state.postHeader = ""
        state.reference = ""

# class DuplicateBook(Exception):
#     def __init__(self, value):
#         self.value = value
#     def __str__(self):
# #        return repr(self.value)
#         return self.value

# Gets the translator and checker names from the manifest.json file in the specified folder.
# Adds them to the global list.
def parseManifestJson(folder):
    path = os.path.join(folder, "manifest.json")
    try:
        jsonFile = io.open(path, "tr", encoding='utf-8-sig')
    except IOError as e:
        sys.stderr.write("   Can't open: " + path + "\n")
        sys.stderr.flush()
    else:
        global contributors
        global checkers
        try:
            manifest = json.load(jsonFile)
        except ValueError as e:
            sys.stderr.write("   Can't parse: " + path + ".\n")
            sys.stderr.flush()
        else:
#            contributors += manifest['translators']
            contributors += [x.title() for x in manifest['translators']]
#            checkers += manifest['checkers']
            checkers += [x.title() for x in manifest['checkers']]
        jsonFile.close()

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
def makeProjectsPath():
    return os.path.join(target_dir, "projects.yaml")

# Looks up the English book name, for use when book name is not defined in the file
def getDefaultName(id):
    # loadVerseCounts()
    en_name = usfm_verses.verseCounts[id]['en_name']
    return en_name

def takeAsIs(key, value):
    state.addPostHeader(key, value)
    # sys.stdout.write(u"addPostHeader(" + key + u", " + str(len(value)) + u")\n")

# Treats the token as the book title if no \mt has been encountered yet.
# Calls takeAsIs() otherwise.
def takeMTX(key, value):
    if not state.mt:
        state.addMT(value)
    else:
        takeAsIs(key, value)

token_re = re.compile(r'\\([^\t ]+)[\t ](.*)', re.UNICODE)

# Parses the specified line and updates the state.
def take(line):
    token = token_re.match(line)
    if token:
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
        marker = token.group(1)
        state.addKey(marker)

# Writes a corrected USFM header to the new USFM file, then writes the body.
def writeUsfm(body):
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
            input.close()
            writeUsfm(body)
    except RuntimeError as dup:
        input.close()
        raise
    return True

# Appends information about the current book to the global projects list.
def appendToProjects():
    global projects

    sort = usfm_verses.verseCounts[state.ID]["sort"]
    testament = 'nt'
    if sort < 40:
        testament = 'ot'
    project = { "title": state.toc2, "id": state.ID.lower(), "sort": sort, \
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
                parseManifestJson(folder)
                appendToProjects()
            except RuntimeError as dup:
                printError(str(dup))

# Eliminates duplicates from contributors list and sorts the list.
# Outputs list to contributors.txt.
def dumpContributors():
    global contributors
    contribs = list(set(contributors))
    if len(contribs) > 0:
        contribs.sort()
        path = os.path.join(target_dir, "contributors.txt")
        f = io.open(path, 'tw', encoding='utf-8', newline='\n')
        f.write("Translators:\n")
        for name in contribs:
            if name:
                f.write('    - "' + name + '"\n')

        checkrs = list(set(checkers))
        checkrs.sort()
        f.write("\nCheckers:\n")
        for name in checkrs:
            if name:
                f.write('    - "' + name + '"\n')
        f.close()

# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects

    projects.sort(key=operator.itemgetter('sort'))
    path = makeProjectsPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    manifest.write("projects:\n")
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
def main():
    global state
    state = State()
    if os.path.isfile( makeProjectsPath() ):
        os.remove( makeProjectsPath() )
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    convertFolder(source_dir)
    dumpProjects()
    dumpContributors()
    sys.stderr.flush()

    print("\nDone.")

if __name__ == "__main__":
    main()