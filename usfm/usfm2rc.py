# -*- coding: utf-8 -*-
# This script produces one or more .usfm files in resource container format from valid USFM source text.
# Chunk division and paragraph locations are based on an English resource container of the same Bible book.
# Uses parseUsfm module.
# This script was originally written for converting Kannada translated text in USFM format to the
# official RC format.

# The English RC folder is hard-coded in en_rc_dir.
# The output folder is also hard-coded.
# The input file(s) should be verified, correct USFM.


import sys
import os

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

import usfm_verses
import parseUsfm
import io
import codecs
import re

# Global variables
en_rc_dir = r'C:\Users\Larry\AppData\Local\translationstudio\library\resource_containers'
target_dir = r'C:\DCS\Portuguese-Brazil\pt-br_ulb2'
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    ID = u""
    rem = u""
    h = u""
    toc1 = u""
    toc2 = u""
    toc3 = u""
    mt = u""
    title = u""
    sts = u""
    postHeader = u""
    chapter = 0
    verse = 0
    needPp = False
    s5marked = False
    reference = u""
    usfmFile = 0
    chunks = []
    chunkIndex = 0
    
    def addREM(self, rem):
        State.rem = rem

    def addTOC1(self, toc):
        State.toc1 = toc
        State.title = toc

    def addH(self, h):
        State.h = h
        if not State.toc1:
            State.title = h
        
    def addMT(self, mt):
        State.mt = mt
        if not State.toc1 and not State.h:
            State.title = mt

    def addTOC2(self, toc):
        State.toc2 = toc
        if not State.toc1 and not State.h and not State.mt:
            State.title = toc

    def addTOC3(self, toc):
        State.toc3 = toc
    
    def addSTS(self, sts):
        sts = sts.strip()
        if sts:
            State.sts = sts
            
    def addPostHeader(self, key, value):
        if key:
            State.postHeader += u"\n\\" + key + u" "
        if value:
            State.postHeader += value

    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.verse = 0
        State.reference = id
        State.title = getDefaultName(id)
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
        State.needPp = True     # need \p marker after each \c marker

        # State.s5marked = False
        
    def addP(self):
        State.needPp = False

    # Reports if vv is a range of verses, e.g. 3-4. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        if vv.find('-') > 0:
            vv_range = vv_re.search(vv)
            self.addVerse(vv_range.group(1))
            # sys.stderr.write("Range of verses encountered at " + State.reference + "\n")
            self.addVerse(vv_range.group(2))
        else:
            self.addVerse(vv)

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
        State.rem = u""
        State.h = u""
        State.toc1 = u""
        State.toc2 = u""
        State.toc3 = u""
        State.mt = u""
        State.sts = u""
        State.postHeader = u""
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
            print "Verse number " + token.value
        elif token.isC():
            print "Chapter " + token.value
        elif token.isS():
            sys.stdout.write(u"Section heading: " + token.value)
        elif token.isTEXT():
            print "Text: <" + token.value + ">"
        else:
            print token

def takeAsIs(key, value):
    state = State()
    if state.chapter < 1:       # header has not been written, chapter 1 has not started
        state.addPostHeader(key, value)
        # sys.stdout.write(u"addPostHeader(" + key + u", " + str(len(value)) + u")\n")
    else:
        # sys.stdout.write(u"takeAsIs(" + key + u"," + str(len(value)) + u"), chapter is " + str(state.chapter) + u"\n")
        state.usfmFile.write(u"\n\\" + key)
        if value:
            state.usfmFile.write(u" " + value)    

# Treats the token as the book title if no \mt has been encountered yet.
# Calls takeAsIs() otherwise.
def takeMTX(key, value):
    state = State()
    if not state.mt:
        state.addMT(value)
    else:
        takeAsIs(key, value)

def takeP():
    state = State()
    state.addP()
    state.usfmFile.write(u"\n\\p")

def addSection(v):
    state = State()
    vn = int(v)
    if state.getChunkVerse() == vn:
        if vn > 1 and not state.hasS5():
            state.usfmFile.write(u"\n\\s5")
        state.advanceChunk()
    if state.needPp:
        state.usfmFile.write(u"\n\\p")
        state.addP()

def takeS5():
    state = State()
    if state.chapter > 0:   # avoid copying \s5 before chapter 1 to simplify writing of header and other chapter 1 handling
        state.addS5()
        state.usfmFile.write(u"\n\\s5")

def takeV(v):
    state = State()
    if v.find('-') > 0:
        vv_range = vv_re.search(v)
        v1 = vv_range.group(1)
        v2 = vv_range.group(2)
        state.addVerse(v1)
        # print "Range of verses encountered at " + State.reference
        addSection(v1)
        state.addVerse(v2)
    else:
        state.addVerse(v)
        addSection(v)
    state.usfmFile.write(u"\n\\v " + v)
    
def takeText(t):
    state = State()
    # sys.stdout.write(u"takeText(" + str(len(t)) + u")\n")
    if state.chapter < 1:       # header has not been written, add text to post-header
        state.addPostHeader(u"", t)
    else:
        state.usfmFile.write(u" " + t)
        
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
#    state.usfmFile.write(u"\n")
    if not state.hasS5():
        state.usfmFile.write(u"\n\n\\s5")
    state.usfmFile.write(u"\n\\c " + c)
    
def take(token):
    state = State()
    if token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isC():
        takeC(token.value)
    elif token.isP():
        takeP()
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
    elif token.isIMT() or token.isMTE():
        takeMTX(token.type, token.value)
    elif token.isIDE():
        x = 0       # do nothing
    elif token.isREM() and state.chapter < 1:   # remarks before first chapter go in the header
        state.addREM(token.value)
    else:
        # sys.stdout.write("Taking other token: ")
        # print token
        takeAsIs(token.type, token.value)

    global lastToken
    lastToken = token
     
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
    state.usfmFile.write(u"\\id " + state.ID)
    if state.sts and state.sts != state.ID:
        state.usfmFile.write(u" " + state.sts)
    state.usfmFile.write(u"\n\\ide UTF-8")
    if state.rem:
        state.usfmFile.write(u"\n\\rem " + state.rem)
    state.usfmFile.write(u"\n\\h " + h)
    state.usfmFile.write(u"\n\\toc1 " + toc1)
    state.usfmFile.write(u"\n\\toc2 " + toc2)
    state.usfmFile.write(u"\n\\toc3 " + state.ID.lower())
    state.usfmFile.write(u"\n\\mt1 " + mt)      # safest to use \mt1 always. When \mt2 exists, \mt1 us required.
    
    # Write post-header if any
    if state.postHeader:
        state.usfmFile.write(state.postHeader)
    state.usfmFile.write(u'\n')     # blank line between header and chapter 1

backslash_re = re.compile(r'\\\s')
jammed_re = re.compile(r'(\\v [-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'\\[^A-Za-z]', re.UNICODE)

def isParseable(str, fname):
    parseable = True
    if backslash_re.search(str):
        printError("File contains stranded backslash(es): " + fname)
        parseable = False
    if jammed_re.search(str):
        printError("File contains verse number(s) not followed by space: " + fname)
        parseable = True   # let it convert because the bad spots are easier to locate in the converted USFM
    if usfmcode_re.search(str):
        printError("File contains foreign usfm code(s): " + fname)
        parseable = False
    return parseable
        

def convertFile(usfmpath, fname):
    state = State()
    state.reset()
    
    # detect file encoding
    enc = detect_by_bom(usfmpath, default="utf-8")
    input = io.open(usfmpath, "tr", 1, encoding=enc)
    str = input.read(-1)
    input.close

    print "CONVERTING " + fname + ":"
    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        for token in parseUsfm.parseString(str):
            take(token)
        state.usfmFile.close()
    return success

def appendToManifest():
    state = State()
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    manifest.write(u"  -\n")
    manifest.write(u"    title: '" + state.title + u" '\n")
    manifest.write(u"    versification: ufw\n")
    manifest.write(u"    identifier: " + state.ID.lower() + u"\n")
    manifest.write(u"    sort: " + '{0:02d}'.format(usfm_verses.verseCounts[state.ID]['sort']) + u"\n")
    manifest.write(u"    path: ./" + makeUsfmFilename(state.ID) + u"\n")
    testament = u'nt'
    if usfm_verses.verseCounts[state.ID]['sort'] < 40:
        testament = u'ot'
    manifest.write(u"    categories: [ 'bible-" + testament + u"' ]\n")
    manifest.close()


# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        printError("Invalid folder path given: " + folder)
        return
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if os.path.isdir(path):
            convertFolder(path)
        elif fname[-3:].lower() == 'sfm':
            if convertFile(path, fname):
                appendToManifest()
            else:
                printError("File cannot be converted: " + fname)
                

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
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
         convertFolder(r'C:\DCS\Portuguese-Brazil\pt-br_ulb')
    else:       # the first command line argument is presumed to be the folder containing usfm files to be converted
        convertFolder(sys.argv[1])

    print "\nDone."
