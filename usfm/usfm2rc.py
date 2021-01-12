# -*- coding: utf-8 -*-
# This script produces one or more .usfm files in resource container format from valid USFM source text.
# Chunk division and paragraph locations are based on an English resource container of the same Bible book.
# Uses parseUsfm module.
# This script was originally written for converting Kannada translated text in USFM format to the
# official RC format.

# The English RC folder is hard-coded in en_rc_dir.
# The output folder is also hard-coded.
# The input file(s) should be verified, correct USFM.

# Global variables
source_dir = r'C:\DCS\Malayalam\IEV\Stage 3'
target_dir = r'C:\DCS\Malayalam\ml_iev.work2'
en_rc_dir = r'C:\Users\lvers\AppData\Local\BTT-Writer\library\resource_containers'

projects = []
lastToken = None
issuesFile = None

import sys
import os
import operator

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

import usfm_verses
import parseUsfm
import io
import codecs
import re

class State:
    ID = ""
    rem = ""
    h = ""
    toc1 = ""
    toc2 = ""
    toc3 = ""
    mt = ""
    title = ""  # title is the best rendition, among toc1, toc2, and mt
    sts = ""
    postHeader = ""
    chapter = 0
    verse = 0
    needVerseText = False
    needPp = None
    s5marked = False
    reference = ""
    usfmFile = 0
    chunks = []
    chunkIndex = 0  # reset at \c marker; 
    
    def addREM(self, rem):
        State.rem = rem

    def addTOC1(self, toc):
        State.toc1 = toc
        if toc and not State.title:
            State.title = toc
        elif State.title.isascii() and not toc.isascii():
            State.title = toc
        elif not State.mt:      # mt overrides toc1
            State.title = toc

    def addTOC2(self, toc):
        State.toc2 = toc
        if toc and not State.title:
            State.title = toc
        elif State.title.isascii() and not toc.isascii():
            State.title = toc
        elif not State.toc1 and not State.mt:
            State.title = toc

    def addTOC3(self, toc):
        State.toc3 = toc
    
    def addH(self, h):
        State.h = h
        if h and not State.title:
            State.title = h
        elif State.title.isascii() and not h.isascii():   # favor non-ASCII titles
            State.title = h
        
    def addMT(self, mt):
        State.mt = mt
        if not mt.isascii():    # mt is the highest priority title if not ascii
            State.title = mt
        elif mt and State.title.isascii():  # even if ascii, mt overrides ascii toc1, toc2, and h
            State.title = mt

    def addSTS(self, sts):
        sts = sts.strip()
        if sts:
            State.sts = sts
            
    def addPostHeader(self, key, value):
        if key:
            State.postHeader += "\n\\" + key + " "
        if value:
            State.postHeader += value

    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.verse = 0
        State.reference = id
        State.title = getDefaultName(id)
        State.needVerseText = False
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
        State.needVerseText = False
        State.reference = State.ID + " " + c
        State.chunks = loadChunks(State.ID, State.chapterPad)
        State.chunkIndex = 0
        State.needPp = "p"     # need \p marker after each \c marker

        # State.s5marked = False
        
    def addP(self):
        State.needPp = None
    
    # Called when a \p is encountered in the source but needs to be held for later output.
    def holdP(self, tag):
        State.needPp = tag

    def addS5(self):
        State.s5marked = True

    def addVerse(self, v):
        State.verse = int(v)
        State.needVerseText = True
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
    
    # Returns the  number of the first verse in the current chunk
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

    def needText(self):
        return State.needVerseText
    def addText(self):
        State.needVerseText = False

    def reset(self):
        State.ID = ""
        State.rem = ""
        State.h = ""
        State.toc1 = ""
        State.toc2 = ""
        State.toc3 = ""
        State.mt = ""
        State.sts = ""
        State.postHeader = ""
        State.chapter = 0
        State.verse = 0
        State.needVerseText = False
        State.needPp = "p"     # need at least one \p marker after \c 1 in each book
        State.s5marked = False
        State.reference = ""

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
           
def printToken(token):
    if token.isV():
        print("Verse number " + token.value)
    elif token.isC():
        print("Chapter " + token.value)
    elif token.isS():
        sys.stdout.write("Section heading: " + token.value)
    elif token.isTEXT():
        print("Text: <" + token.value + ">")
    else:
        print(token)

def takeAsIs(key, value):
    state = State()
    if state.chapter < 1:       # header has not been written, chapter 1 has not started
        state.addPostHeader(key, value)
        # sys.stdout.write(u"addPostHeader(" + key + u", " + str(len(value)) + u")\n")
    else:
        # sys.stdout.write(u"takeAsIs(" + key + u"," + str(len(value)) + u"), chapter is " + str(state.chapter) + u"\n")
        state.usfmFile.write("\n\\" + key)
        if value:
            state.usfmFile.write(" " + value)    

# Treats the token as the book title if no \mt has been encountered yet.
# Calls takeAsIs() otherwise.
def takeMTX(key, value):
    state = State()
    if not state.mt:
        state.addMT(value)
    else:
        takeAsIs(key, value)

# Copies paragraph marker to output unless a section 5 break is just ahead.
# In that case, the paragraph marker will automatically be added after \s5.
def takeP(tag):
    state = State()
    if state.getChunkVerse() != state.verse + 1:
        state.addP()
        state.usfmFile.write("\n\\" + tag)
    else:
        state.holdP(tag)

# Copies paragraph marker to output unless a section 5 break is just ahead.
# In that case, the paragraph marker will automatically be added after \s5.
def takeQ(tag):
    state = State()
    if state.getChunkVerse() != state.verse + 1:
        state.addP()
        state.usfmFile.write("\n\\" + tag)
    else:
        state.holdP(tag)

# Called each time a verse marker is encountered, before the verse marker is written to the output stream.
# Writes an \s5 section marker if it is the first verse in the chunk.
# Writer a \p marker before verse 1 or when a \p marker from input is on hold.
def addSection(v):
    state = State()
    vn = int(v)
    if state.getChunkVerse() == vn:
        if vn > 1 and not state.hasS5():
            state.usfmFile.write("\n\\s5")
        state.advanceChunk()
    if state.needPp:
        state.usfmFile.write("\n\\" + state.needPp)
        state.addP()

def takeS5():
    state = State()
    if state.chapter > 0:   # avoid copying \s5 before chapter 1 to simplify writing of header and other chapter 1 handling
        state.addS5()
        state.usfmFile.write("\n\\s5")

vv_re = re.compile(r'([0-9]+)-([0-9]+)')
def takeV(v):
    state = State()
    vv_range = vv_re.search(v)
    if vv_range:
        v1 = vv_range.group(1)
        v2 = vv_range.group(2)
        state.addVerse(v1)
        # print "Range of verses encountered at " + State.reference
        addSection(v1)
        state.addVerse(v2)
    else:
        v = v.strip("-")    # A verse marker like this has occurred:  \v 19-
        state.addVerse(v)
        addSection(v)
    state.usfmFile.write("\n\\v " + v)
    
def takeText(t):
    state = State()
    # sys.stdout.write(u"takeText(" + str(len(t)) + u")\n")
    if state.chapter < 1:       # header has not been written, add text to post-header
        state.addPostHeader("", t)
    else:
        if state.needPp:
            state.usfmFile.write("\n\\" + state.needPp)
            state.addP()
        state.usfmFile.write(" " + t)
    state.addText()
        
# Insert an s5 marker before writing any chapter marker.
# Before writing chapter 1, we output the USFM header.
def takeC(c):
    state = State()
    if not state.ID:
        sys.stderr.write("Error: no book ID\n")
        sys.exit(-1)
    state.addChapter(c)
    if state.chapter == 1:
        writeHeader()
    if not state.hasS5():
        state.usfmFile.write("\n\n\\s5")
    state.usfmFile.write("\n\\c " + c)
 
# Handle the unmarked chapter label
def takeCL(cl):
    state = State()
    state.usfmFile.write("\n\\cl " + cl)

def take(token):
    global lastToken

    state = State()
    if state.needText() and not isTextCarryingToken(token):    # and not isOptional(state.reference):
        if not token.isTEXT():
            reportError("Empty verse: " + state.reference)
    if token.isV():
        takeV(token.value)
    elif token.isTEXT():
        if lastToken.isC():
            takeCL(token.value)
        else:
            takeText(token.value)
    elif token.isC():
        takeC(token.value)
    elif token.isP() or token.isPI() or token.isPC() or token.isNB():
        takeP(token.type)
    elif token.isQ() or token.isQ1() or token.isQA() or token.isSP() or token.isQR() or token.isQC():
        takeQ(token.type)
    elif token.isS():
        takeAsIs(token.type, token.value)
    elif token.isS5():
        takeS5()
    elif token.isID():
        state.addID(token.value[0:3].upper())   # use first 3 characters of \id value
        if len(token.value) > 3:
            state.addSTS(token.value[3:])
    elif token.isH():
        state.addH(token.value)
    elif token.isTOC1():
        state.addTOC1(token.value)
    elif token.isTOC2():
        state.addTOC2(token.value)
    elif token.isTOC3():
        state.addTOC3(token.value)
    elif token.isMT():
        state.addMT(token.value)
    elif token.is_imt() or token.isMTE():
        takeMTX(token.type, token.value)
    elif token.isIDE():
        x = 0       # do nothing
    elif token.isREM() and state.chapter < 1:   # remarks before first chapter go in the header
        state.addREM(token.value)
    else:
        # sys.stdout.write("Taking other token: ")
        # print token
        takeAsIs(token.type, token.value)

    lastToken = token
     
# Returns true if token is part of a cross reference
def isCrossRef(token):
    return token.isX_S() or token.isX_E() or token.isXO() or token.isXT()

# Returns true if token is part of a footnote
def isFootnote(token):
    return token.isF_S() or token.isF_E() or token.isFR() or token.isFR_E() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()

def isIntro(token):
    return token.is_is() or token.is_ip() or token.is_iot() or token.is_io()
    
def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQA() or token.isSP() or token.isQR() or \
token.isQC() or token.isD()

def isTextCarryingToken(token):
    return token.isB() or token.isM() or token.isD() or isFootnote(token) or isCrossRef(token) or isPoetry(token) or isIntro(token)
    
def writeHeader():
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
    state.usfmFile.write("\\id " + state.ID)
    if state.sts and state.sts != state.ID:
        state.usfmFile.write(" " + state.sts)
    state.usfmFile.write("\n\\ide UTF-8")
    if state.rem:
        state.usfmFile.write("\n\\rem " + state.rem)
    state.usfmFile.write("\n\\h " + h)
    state.usfmFile.write("\n\\toc1 " + toc1)
    state.usfmFile.write("\n\\toc2 " + toc2)
    state.usfmFile.write("\n\\toc3 " + state.ID.lower())
    state.usfmFile.write("\n\\mt1 " + mt)      # safest to use \mt1 always. When \mt2 exists, \mt1 us required.
    
    # Write post-header if any
    if state.postHeader:
        state.usfmFile.write(state.postHeader)
    state.usfmFile.write('\n')     # blank line between header and chapter 1

backslash_re = re.compile(r'\\\s')
jammed_re = re.compile(r'(\\v [-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'\\[^A-Za-z]', re.UNICODE)

def isParseable(str, fname):
    parseable = True
    if backslash_re.search(str):
        reportError("File contains stranded backslash(es): " + fname)
#        parseable = False
    if jammed_re.search(str):
        reportError("File contains verse number(s) not followed by space: " + fname)
        parseable = True   # let it convert because the bad spots are easier to locate in the converted USFM
    if usfmcode_re.search(str):
        reportError("File contains foreign usfm code(s): " + fname)
#        parseable = False
    return parseable
        

def convertFile(usfmpath, fname):
    state = State()
    state.reset()
    
    input = io.open(usfmpath, "tr", 1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close

    print("CONVERTING " + fname + ":")
    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        for token in parseUsfm.parseString(str):
            take(token)
        state.usfmFile.write("\n")    
        state.usfmFile.close()
    return success

# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        reportError("Invalid folder path given: " + folder)
        return
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if os.path.isdir(path):
            convertFolder(path)
        elif fname[-3:].lower() == 'sfm':
            if convertFile(path, fname):
                appendToProjects()
            else:
                reportError("File cannot be converted: " + fname)
                
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

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(source_dir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile

# Writes error message to stderr and to issues.txt.
def reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        state = State()
        sys.stderr.write(state.reference + ": (Unicode...)\n")
    issues = openIssuesFile()       
    issues.write(msg + "\n")

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    convertFolder(source_dir)
    dumpProjects()
    if issuesFile:
        issuesFile.close()
    print("\nDone.")
