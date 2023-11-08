# -*- coding: utf-8 -*-
# This script produces one or more .usfm files in resource container format from valid USFM source text.
# Chunk division and paragraph locations are based on pre-existing usfm files in chunk_model_dir.
# Inserts paragraph marker before verse 1 in each chapter.
# The input file(s) should be verified, correct USFM.
#
# Set these configuration values in your config file before running script:
#    source_dir
#    target_dir
#    file           Leave blank to process all files in source_dir
#    mark_chunks      True or False, to mark chunks in output USFM files
#    chunk_model_dir   Folder containing model text for placement of \s5 chunk markers

import configreader
import sys
import os
import operator
from pathlib import Path
import usfm_verses
import parseUsfm
import io
import re
import yaml

projects = []
translators = []
source_versions = []
lastToken = None
issuesFile = None
max_chunk_size = 8

class State:
    ID = ""
    rem = []
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
    s5marked = 0
    reference = ""
    usfmFile = 0
    bookchunks_input = []
    bookchunks_model = []
    chunks_output = []      # for current chapter

    def addREM(self, rem):
        State.rem.append(rem)

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
        usfmPath = makeUsfmPath(id)
        State.usfmFile = io.open(usfmPath, "tw", encoding='utf-8', newline='\n')

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
        State.needPp = "p"     # need \p marker after each \c marker

    def addP(self):
        State.needPp = None

    # Called when a \p is encountered in the source but needs to be held for later output.
    def holdP(self, tag):
        State.needPp = tag

    def addS5(self, v):
        State.s5marked = v

    def addVerse(self, v):
        State.verse = int(v)
        State.needVerseText = True
        State.reference = State.ID + " " + str(State.chapter) + ":" + v

    def recordInputChunks(self, bookchunks):
        State.bookchunks_input = bookchunks

    def recordModelChunks(self, bookchunks):
        State.bookchunks_model = bookchunks

    def recordChapterChunks(self, chunks):
        State.chunks_output = chunks

    # Returns True if the specified verse number should start a new chunk.
    def startsChunk(self, verse):
        return (verse in State.chunks_output)

    def hasS5(self, v):
        return (State.s5marked == v)

    def needText(self):
        return State.needVerseText
    def addText(self):
        State.needVerseText = False

    def reset(self):
        State.ID = ""
        State.rem = []
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
        State.s5marked = 0     # last verse for which chunk has been marked
        State.reference = ""

chunk_re = re.compile(r'([0-9]{2,3}).usx')

usfmchapter_re = re.compile(r'\\c +([0-9]+)')
usfmverse_re = re.compile(r'\\v +([0-9]+)')
vrange_re = re.compile(r'\\v +([0-9]+)-([0-9]+)')

# Returns a list (chapters) of lists (verse numbers that start the chunks) for the specified book.
# Appends a generated verse number (last verse + 1) to the end of each verse number list
def loadChunksUsfm(usfmpath):
    chapters = []
    chunks = []
    nv = 1
    with io.open(usfmpath, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    for line in lines:
        if line.startswith("\\s5") and nv > 1:
            chunks.append(nv)
        elif versematch := usfmverse_re.match(line):
            if rangematch := vrange_re.match(line):
                nv = int(rangematch.group(2)) + 1
            else:
                nv = int(versematch.group(1)) + 1
        elif chaptermatch := usfmchapter_re.match(line):
            chunks.append(nv)
            nc = int(chaptermatch.group(1))
            if nc > 1 and len(chapters) != nc - 2:
                reportError("Chapter (" + str(nc) + ") out of order in: " + usfmpath)
            if nc > 1:
                chapters.append(chunks)
            chunks = [1]    # verse 1 is assumed to always start a chunk
            nv = 1
    chunks.append(nv)
    chapters.append(chunks)
    return chapters

# Returns None if there are no long chunks in arr after the specified starting position.
# Returns a (start, next, index) tuple specifying the next long chunk found.
# (starting verse, starting verse of next chunk or 999, and index of next starting verse in arr)
def longchunk(arr, pos=0):
    rtnval = (None,None,None)
    i = pos + 1
    while i < len(arr) and arr[i] - arr[i-1] < max_chunk_size+1:
        i += 1
    if i < len(arr):
        rtnval = (arr[i-1], arr[i], i)
    return rtnval

# Returns a list of verse numbers between start and next in model.
# Returns empty list if there are none between.
# Model is assumed to be a non-empty array of verse numbers in ascending order.
def chunkAt(start, next, model):
    chunkverses = []
    for n in model:
        if n > start and n < next:
            chunkverses.append(n)
    return chunkverses

# Compares the chunks from the input file and the model for the current chapter.
# Determines where to break the chunks in the output usfm, and saves those verse numbers in state.chunks_output.
def settleChapterChunks():
    state = State()
    model = []
    output = []
    if len(state.bookchunks_model) >= state.chapter:    # should always be true
        model = state.bookchunks_model[state.chapter-1]
    else:
        reportError("Internal error 1")
    if len(state.bookchunks_input) >= state.chapter:    # should always be true
        output = state.bookchunks_input[state.chapter-1]
    else:
        reportError("Internal error 2")
    (start, next, pos) = longchunk(output)
    while pos:
        if chunkverses := chunkAt(start, next, model):
            chunkverses.reverse()
            for v in chunkverses:
                output.insert(pos, v)
            pos += len(chunkverses)
        (start, next, pos) = longchunk(output, pos)
    state.recordChapterChunks(output)

# Generates name for usfm file
def makeUsfmPath(bookId):
    global target_dir
    return os.path.join(target_dir, makeUsfmFilename(bookId))

# Returns path name for usfm file
def makeUsfmFilename(id):
    num = usfm_verses.verseCounts[id]['usfm_number']
    return str(num) + "-" + id + ".usfm"

# Looks up the English book name, for use when book name is not defined in the file
def getDefaultName(id):
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

# Write to the file with or without a newline as appropriate
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

def takeFootnote(key, value):
    state = State()
    state.usfmFile.write(" \\" + key)
    if value:
        state.usfmFile.write(" " + value)

def takeMTX(key, value):
    state = State()
    if not state.mt:
        state.addMT(value)
    else:
        takeAsIs(key, value)

# Copies paragraph marker to output unless a section 5 break is just ahead.
# In that case, the paragraph marker will automatically be added after \s5.
def takePQ(tag):
    state = State()
    if state.startsChunk(state.verse + 1):
        state.holdP(tag)
    else:
        state.addP()
        state.usfmFile.write("\n\\" + tag)

# Called each time a verse marker is encountered, before the verse marker is written to the output stream.
# Writes an \s5 section marker if it is the first verse in the chunk.
# Writes a \p marker before verse 1 or when a \p marker from input is on hold.
def addSection(v):
    state = State()
    if mark_chunks:
        vn = int(v)
        if state.startsChunk(vn):
            if vn > 1 and not state.hasS5(vn):
                state.usfmFile.write("\n\\s5")
            state.addS5(vn)
    if state.needPp:
        state.usfmFile.write("\n\\" + state.needPp)
        state.addP()

def takeS5():
    state = State()
    if state.chapter > 0:   # avoid copying \s5 before chapter 1 to simplify writing of header and other chapter 1 handling
        if not state.hasS5(state.verse + 1):
            state.addS5(state.verse + 1)
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
    if (v == "1" or v.startswith("1-")) and state.needPp:
        state.usfmFile.write("\n\\" + state.needPp)
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

def takeVPS(pubv):
    State().usfmFile.write(" \\vp" + pubv)

def takeVPE():
    State().usfmFile.write("\\vp*")

# Settle where the chunk boundaries are going to be.
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
        if mark_chunks:
            modelpath = os.path.join(chunk_model_dir, makeUsfmFilename(state.ID))
            state.recordModelChunks( loadChunksUsfm(modelpath) )
    if mark_chunks:
        settleChapterChunks()
    if mark_chunks and not state.hasS5(1):
        state.usfmFile.write("\n\n\\s5")
        state.addS5(1)
    state.usfmFile.write("\n\\c " + c)

# Handle the unmarked chapter label
def takeCL(cl):
    state = State()
    state.usfmFile.write("\n\\cl " + cl)

def take(token):
    global lastToken

    state = State()
    # if state.needText() and not isTextCarryingToken(token):    # and not isOptional(state.reference):
    #     if not token.isTEXT():
    #         reportError("Empty verse: " + state.reference)
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
        takePQ(token.type)
    elif token.isQ() or token.isQ1() or token.isQA() or token.isSP() or token.isQR() or token.isQC():
        takePQ(token.type)
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
    elif token.isVPS():
        takeVPS(token.value)
    elif token.isVPE():
        takeVPE()
    elif isFootnote(token):
        takeFootnote(token.type, token.value)
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
    return token.isF_S() or token.isF_E() or token.isFR() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()

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
        for rem in state.rem:
            state.usfmFile.write("\n\\rem " + rem)
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
jammed_re = re.compile(r'(\\v +[-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'\\[^A-Za-z\+]', re.UNICODE)

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
        parseable = False
    return parseable

def convertFile(usfmpath, fname):
    state = State()
    state.reset()
    state.recordInputChunks( loadChunksUsfm(usfmpath) )
    input = io.open(usfmpath, "tr", 1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close()

    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        print("CONVERTING " + fname + ":")
        tokens = parseUsfm.parseString(str)
        for token in tokens:
            take(token)
        state.usfmFile.write("\n")
        state.usfmFile.close()
    return success

# Converts the book or books contained in the specified folder
def convertFolder(folder):
    if not os.path.isdir(folder):
        reportError("Invalid folder path given: " + folder)
        return
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname[0] != '.' and os.path.isdir(path):
            convertFolder(path)
        elif fname.endswith('sfm'):
            if convertFile(path, fname):
                appendToProjects()
                getContributors(folder)
            else:
                reportError("File cannot be converted: " + fname)

# Reads list of contributors (translators) from manifest.yaml file if it exists.
# Also gets source version.
def getContributors(folder):
    manifestpath = os.path.join(folder, 'manifest.yaml')
    if os.path.isfile(manifestpath):
        global translators
        global source_versions
        manifestFile = io.open(manifestpath, "tr", encoding='utf-8-sig')
        manifest = yaml.safe_load(manifestFile)
        manifestFile.close()
        if manifest['dublin_core']['source']:
            source_versions += manifest['dublin_core']['source'][0]['version']
        translators += manifest['dublin_core']['contributor']

def dumpContributors(path):
    global translators
    global source_versions
    if len(translators) > 0 or len(source_versions) > 0:
        contribs = list(set(translators))
        contribs.sort()
        f = io.open(path, 'tw', encoding='utf-8', newline='\n')
        for name in contribs:
            f.write('    - "' + name + '"\n')

        # Also dump the list of source versions used
        f.write('\n\nSource versions used:\n')
        for version in source_versions:
            f.write(version + ' ')
        f.write('\n')
        f.close()

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
def dumpProjects(path):
    global projects
    projects.sort(key=operator.itemgetter('sort'))

    manifest = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
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

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile(dirpath):
    global issuesFile
    if not issuesFile:
        path = os.path.join(dirpath, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(dirpath, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile

def closeIssuesFile():
    if issuesFile:
        issuesFile.close()

# Writes error message to stderr and to issues.txt.
def reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        state = State()
        sys.stderr.write(state.reference + ": (Unicode...)\n")
    issues.write(msg + "\n")

# Processes each directory and its files one at a time
if __name__ == "__main__":
    config = configreader.get_config(sys.argv, 'usfm2rc')
    if config:
        source_dir = config['source_dir']
        file = config['file']
        target_dir = config['target_dir']
        chunk_model_dir = config['chunk_model_dir']
        mark_chunks = config.getboolean('mark_chunks', fallback=False)
        Path(target_dir).mkdir(exist_ok=True)
        issues = openIssuesFile(source_dir)
        if mark_chunks and not os.path.isdir(chunk_model_dir):
            reportError(f"chunk_model_dir: ({chunk_model_dir}) is not a valid folder.")
            sys.exit(-1)

        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                if convertFile(path, file):
                    appendToProjects()
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(source_dir)
            if projects:
                dumpProjects( os.path.join(target_dir, "projects.yaml") )
                dumpContributors( os.path.join(target_dir, "translators.txt") )

        closeIssuesFile()
        print("\nDone.")
