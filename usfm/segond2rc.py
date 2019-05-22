# coding: latin-1

# This script add s5 markers at chunk boundaries to .usfm files.
# The source files must be generally correct USFM, including a correct \id field at the top.
# It also requires that the major USFM markers (id, mt, c, v, p, s5) occur at the beginning of lines.
# Chunk division locations are based on an English resource container of the same Bible book.
# Does not modify any lines in the file, just inserts \s5 markers.
# Also insert a \p marker after \c 1
# This script was originally written for converting French, Segond 1910 Bible in USFM format, which
# is heavily marked up for wordlist (\w ... \w*). The parseUsfm module practically chokes on it.

# The English RC folder is hard-coded in en_rc_dir.
# The output folder is also hard-coded.
# The input file(s) should be verified, correct USFM.

import sys
import os
import usfm_verses

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

import io
import codecs
import re

# Global variables
en_rc_dir = r'C:\Users\Larry\AppData\Local\translationstudio\library\resource_containers'
target_dir = r'C:\DCS\Kurdish Kalhori\kk_ulb'
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    ID = u""
    h = u""
    toc1 = u""
    toc2 = u""
    mt = u""
    title = u""
    chapter = 0
    verse = 0
    needPp = False
    s5marked = False
    reference = u""
    usfmFile = 0
    chunks = []
    chunkIndex = 0
    
    def addTOC1(self, toc):
        State.toc1 = toc
        if not State.mt:
            State.title = toc

    def addH(self, h):
        State.h = h
        if not State.mt and not State.toc1:
            State.title = h
        
    def addMT(self, mt):
        State.mt = mt
        State.title = mt

    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.verse = 0
        State.reference = id
        State.title = u""
        # Open output USFM file for writing.
        usfmPath = os.path.join(target_dir, makeUsfmFilename(id))
        State.usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
       
    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        if len(c) == 1:
            State.chapterPad = "0" + c
        else:
            State.chapterPad = c
        State.verse = 0
        State.reference = State.ID + " " + c
        State.chunks = loadChunks(State.ID, State.chapterPad)
        State.chunkIndex = 0
        # State.s5marked = False
        
    def addP(self):
        State.needPp = False

    def addS5(self):
        State.s5marked = True

    def addVerse(self, v):
        State.verse = int(v)
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
    
    def getChunkVerse(self):
        v = 999
        if State.chunkIndex < len(State.chunks):
            v = State.chunks[State.chunkIndex]
        return v
        
    def advanceChunk(self):
        State.chunkIndex += 1
        State.s5marked = False

    def hasS5(self):
        return State.s5marked

    def reset(self):
        State.ID = u""
        State.h = u""
        State.toc1 = u""
        State.toc2 = u""
        State.toc3 = u""
        State.mt = u""
        State.chapter = 0
        State.verse = 0
        State.needPp = True     # need at least one \p marker after \c 1 in each book
        State.s5marked = False
        State.reference = u""

chunk_re = re.compile(r'([0-9]{2,3}).usx')

# Makes an ordered list of the verse numbers that starts the chunks in the specified book and chapter
def loadChunks(id, chap):
    dir = os.path.join(en_rc_dir, "en_" + id + "_ulb")
    dir = os.path.join(dir, "content")
    dir = os.path.join(dir, chap)
    allnames = os.listdir(dir)
    chunks = []
    for name in allnames:
        match = chunk_re.match(name)
        if match:
            chunks.append( int(match.group(1)) )
    chunks.sort()
    return chunks

import json

"""
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
"""

# Returns path name for usfm file
def makeUsfmFilename(id):
#    loadVerseCounts()
    num = usfm_verses.verseCounts[id]['usfm_number']
    return str(num) + "-" + id + ".usfm"
    
# Returns path of temporary manifest file block listing projects converted
def makeManifestPath():
    return os.path.join(target_dir, "projects.yaml")
    
def takeId(value):
    state = State()
    state.addID(value)

def takeH(value):
    state = State()
    state.addH(value)

def takeToc1(value):
    state = State()
    state.addTOC1(value)

def takeMt(value):
    state = State()
    state.addMT(value)

def takeP(dummy):
    state = State()
    state.addP()

# Adds s5 marker where needed
def insertS5(v):
    state = State()
    vn = int(v)
    if state.getChunkVerse() == vn:
        if vn > 1 and not state.hasS5():
            state.usfmFile.write(u"\n\\s5\n")
        state.advanceChunk()
    if state.needPp:
        state.usfmFile.write(u"\\p\n")
        state.addP()

def takeS5(dummy):
    state = State()
    if state.chapter > 0:   # avoid copying \s5 before chapter 1 to simplify writing of header and other chapter 1 handling
        state.addS5()

def takeV(v):
    state = State()
    if v.find('-') > 0:
        vv_range = vv_re.search(v)
        v1 = vv_range.group(1)
        v2 = vv_range.group(2)
        state.addVerse(v1)
        print "Range of verses encountered at " + State.reference
        insertS5(v1)
        state.addVerse(v2)
    else:
        state.addVerse(v)
        insertS5(v)
    
# Insert an s5 marker before writing any chapter marker.
def takeC(c):
    state = State()
    state.addChapter(c)
    # print "Starting chapter " + c
    if not state.hasS5():
        state.usfmFile.write(u"\n\\s5\n")


id_re = re.compile(r'\\id[ \t]+([1-3A-Z]{3})\s')
h_re = re.compile(r'\\h[ \t]+(.*)$')
toc1_re = re.compile(r'\\toc1[ \t]+(.*)$')
mt_re = re.compile(r'\\mt1?[ \t]+(.*)$')
s5_re = re.compile(r'\\s5(\s)*')
p_re = re.compile(r'\\p(\s)*')
v_re = re.compile(r'\\v[ \t]+([0-9]+-?[0-9]*)\s')
c_re = re.compile(r'\\c[ \t]+([0-9]+)\s')
relist = [(v_re, takeV), (c_re, takeC), (id_re, takeId), (s5_re, takeS5), (p_re, takeP), (h_re, takeH), (toc1_re, takeToc1), (mt_re, takeMt)]

def process(line):
    state = State()
    exprNum = 0
    for r in relist:
        match = r[0].match(line)
        if match:
            r[1](match.group(1))    # call function associated to process this USFM token
            break
    state.usfmFile.write(line)

def convertFile(folder, fname):
    state = State()
    state.reset()
    
    usfmfile = os.path.join(folder, fname)
    # detect file encoding
    enc = detect_by_bom(usfmfile, default="utf-8")
    input = io.open(usfmfile, "tr", 1, encoding=enc)
    lines = input.readlines()
    input.close

    print "CONVERTING " + fname + ":"
    sys.stdout.flush()
    for line in lines:
        process(line)
    state.usfmFile.close()

def appendToManifest():
    state = State()
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    manifest.write(u"  -\n")
    manifest.write(u"    title: '" + state.title + u" '\n")
    manifest.write(u"    versification: 'ufw'\n")
    manifest.write(u"    identifier: '" + state.ID.lower() + u"'\n")
    manifest.write(u"    sort: " + str(usfm_verses.verseCounts[state.ID]['sort']) + u"\n")
    manifest.write(u"    path: './" + makeUsfmFilename(state.ID) + u"'\n")
    testament = u'nt'
    if usfm_verses.verseCounts[state.ID]['sort'] < 40:
        testament = u'ot'
    manifest.write(u"    categories: [ 'bible-" + testament + u"' ]\n")
    manifest.close()


# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        printError("Invalid folder path given: " + folder + '\n')
        return
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    for fname in os.listdir(folder):
        if fname[-4:].lower() == 'usfm':
            convertFile(folder, fname)
            appendToManifest()

def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default

def printError(text):
    sys.stderr.write(text + '\n')

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        folder = r'C:\DCS\Kurdish Kalhori'
    else:       # the first command line argument presumed to be a folder
        folder = sys.argv[1]
        
    if os.path.isdir(folder):
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        convertFolder(folder)
    print "\nDone."
