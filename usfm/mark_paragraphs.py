# -*- coding: utf-8 -*-
# This script converts one or more valid .usfm files by adding paragraph marks.
# The model used for marking paragraphs are the USFM files in model_dir.
# Inserts paragraph marker after each chapter marker if needed, before verse 1.
# The input file(s) should be verified, correct USFM.

# Global variables
source_dir = r"C:\DCS\Havu\work"
target_dir = r'C:\DCS\Havu\hav_reg.ta'
model_dir = r'C:\DCS\English\en_ulb.WA-Nov-22'

removeS5markers = True

nCopied = 0
issuesFile = None

import sys
import os
import operator
import usfm_verses
import parseUsfm
import io
import codecs
import re

class State:
    fname = ""
    chapter = 0
    verse = 0
    pChapter = 0    # location of latest paragraph mark already in input text
    pVerse = 0      # location of latest paragraph mark already in input text
    reference = ""
    usfmFile = 0
    paragraphs_model = []   # list of {pmark, chapter, verse, located}

    def addFile(self, fname):
        State.fname = fname
        State.chapter = 0
        State.verse = 0
        State.pChapter = 0
        State.pVerse = 0
        State.reference = fname
        State.paragraphs_model = []
        # Open output USFM file for writing.
        usfmPath = os.path.join(target_dir, fname)
        State.usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')

    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.verse = 0

    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.verse = 0
        State.reference = State.ID + " chapter " + c

    # Records the location of a paragraph marker found in the input text.
    def addP(self):
        State.pChapter = State.chapter
        State.pVerse = State.verse + 1

    def addVerse(self, v):
        State.verse = int(v)
        State.reference = State.ID + " " + str(State.chapter) + ":" + v

    # Returns True if a paragraph mark was already recorded for the current verse.
    # See addP()
    def pAlready(self):
        return State.pVerse == State.verse and State.pChapter == State.chapter

    # Returns the paragraph mark that occurred in the model file at the current location.
    def pmarkInModel(self):
        pmark = None
        for pp in State.paragraphs_model:
            if pp['chapter'] == State.chapter and pp['verse'] == State.verse and pp['located']:
                pmark = pp['pmark']
                break
        return pmark

    #def recordModelParagraphs(self, bookchunks):
        #State.bookchunks_model = bookchunks

    #def recordChapterParagraphs(self, chunks):
        #State.paragraphs_output = chunks

    # Returns True if the specified verse number should start a new chunk.
    #def startsChunk(self, verse):
        #return (verse in State.paragraphs_output)

    #def needText(self):
        #return State.needVerseText
    def addText(self):
        State.needVerseText = False

# Looks up the English book name, for use when book name is not defined in the file
#def getDefaultName(id):
    #en_name = usfm_verses.verseCounts[id]['en_name']
    #return en_name

#def printToken(token):
    #if token.isV():
        #print("Verse number " + token.value)
    #elif token.isC():
        #print("Chapter " + token.value)
    #elif token.isS():
        #sys.stdout.write("Section heading: " + token.value)
    #elif token.isTEXT():
        #print("Text: <" + token.value + ">")
    #else:
        #print(token)

# Write to the file with or without a newline as appropriate
def takeAsIs(key, value):
    state = State()
    state.usfmFile.write("\n\\" + key)
    if value:
        state.usfmFile.write(" " + value)

def takeFootnote(key, value):
    state = State()
    state.usfmFile.write(" \\" + key)
    if value:
        state.usfmFile.write(" " + value)

def takeID(id):
    state = State()
    state.addID(id)
    state.usfmFile.write("\\id " + id)

# Copies paragraph marker to output unless output already has a paragraph there.
def takePQ(tag):
    state = State()
    state.addP()
    state.usfmFile.write("\n\\" + tag)

def takeS5():
    if not removeS5markers:
        state = State()
        state.usfmFile.write("\n\\s5")

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

def takeV(v):
    global nCopied
    state = State()
    v1 = v.split('-')[0]
    state.addVerse(v1)
    if not state.pAlready():
        if pmark := state.pmarkInModel():
            state.usfmFile.write("\n\\" + pmark)
            nCopied += 1
    state.usfmFile.write("\n\\v " + v + " ")

def takeText(t):
    state = State()
    state.addText()
    state.usfmFile.write(t)

# Settle where the chunk boundaries are going to be.
# Before writing chapter 1, we output the USFM header.
def takeC(c):
    state = State()
    state.addChapter(c)
    state.usfmFile.write("\n\\c " + c)

# Handles the specified token from the input file.
# Inserts paragraph markers where needed from model.
def take(token):
    state = State()
    if token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isC():
        takeC(token.value)
    elif isParagraph(token) or isPoetry(token):
        takePQ(token.type)
    elif token.isS5():
        takeS5()
    elif token.isID():
        takeID(token.value[0:3].upper())   # use first 3 characters of \id value
    elif isFootnote(token):
        takeFootnote(token.type, token.value)
    else:
        takeAsIs(token.type, token.value)

# Returns true if token is part of a cross reference
def isCrossRef(token):
    return token.isX_S() or token.isX_E() or token.isXO() or token.isXT()

# Returns true if token is part of a footnote
def isFootnote(token):
    return token.isF_S() or token.isF_E() or token.isFR() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()

def isIntro(token):
    return token.is_is() or token.is_ip() or token.is_iot() or token.is_io()

def isParagraph(token):
    return token.isP() or token.isPI() or token.isPC() or token.isNB() or token.isB()

def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQ2() or token.isQ3() or \
token.isQA() or token.isSP() or token.isQR() or token.isQC() or token.isD()

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
    if not state.fname:
        reportError("Error: State is not initialized")
        sys.exit(-1)
    input = io.open(usfmpath, "tr", 1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close

    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        print("Converting " + fname)
        #state.addFile(fname)
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
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname[0] != '.' and os.path.isdir(path):
            convertFolder(path)
        elif fname.endswith('sfm'):
            model_path = os.path.join(model_dir, fname)
            if scanModelFile(model_path, fname):
                if not convertFile(path, fname):
                    reportError("File cannot be converted: " + fname)
            else:
                reportError("Model file is unusable: " + fname)

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global source_dir
        path = os.path.join(target_dir, "uncopied pp marks.txt")
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile

def closeIssuesFile():
    if issuesFile:
        issuesFile.close()

# Writes error message to stderr and to issues.txt.
def reportError(msg, writeToStderr=True):
    if writeToStderr:
        try:
            sys.stderr.write(msg + "\n")
        except UnicodeEncodeError as e:
            state = State()
            sys.stderr.write(state.reference + ": (Unicode...)\n")
    issues = openIssuesFile()
    issues.write(msg + "\n")

# Sets the chapter number in the state object
# If there is still a tentative paragraph mark, remove it.
def scanC(c):
    state = State()
    state.addChapter(c)

# Save the paragraph mark and its tentative location
# If the previous paragraph mark is still tentative, it is invalid, overwrite it in the state.
def scanPQ(type, value):
    state = State()
    p = {}
    p['pmark'] = type
    p['chapter'] = state.chapter
    p['verse'] = state.verse
    p['located'] = False
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            state.paragraphs_model.remove(pp)
    state.paragraphs_model.append(p)

# If there is a paragraph mark not assigned to a verse yet,
# report it because the paragraph apparently occurs in the middle of a verse.
def scanText(value):
    state = State()
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['pmark']}) within {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# v is the verse number or range
# Assign the verse number to the preceding paragraph mark, if any.
def scanV(v):
    state = State()
    v = v.split('-')[0]
    state.addVerse(v)
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            pp['verse'] = int(v)
            pp['located'] = True

# Analyzes the specified token in the model file.
# Only cares about locations of paragraphs.
def scan(token):
    state = State()
    if token.isC():
        scanC(token.value)
    elif token.isV():
        scanV(token.value)
    elif token.isTEXT():
        scanText(token.value)
    elif isParagraph(token) or isPoetry(token):
        scanPQ(token.type, token.value)
    elif token.isID():
        state.addID(token.value[0:3].upper())   # use first 3 characters of \id value

# Gathers the location and type of all paragraph marks in the model USFM file.
def scanModelFile(modelpath, fname):
    if os.path.isfile(modelpath):
        input = io.open(modelpath, "tr", 1, encoding="utf-8-sig")
        str = input.read(-1)
        input.close
        sys.stdout.flush()
        success = isParseable(str, os.path.basename(modelpath))
        if success:
            state = State()
            print("Parsing model file: " + fname)
            state.addFile(fname)
            tokens = parseUsfm.parseString(str)
            for token in tokens:
                scan(token)
    else:
        reportError("Model file does not exist: " + modelpath)
        success = False
    return success

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        fname = os.path.basename(path)
        model_path = os.path.join(model_dir, fname)
        if scanModelFile(model_path, fname):
            convertFile(path, fname)
        else:
            reportError("Model file is unusable: " + model_path)
    else:
        convertFolder(source_dir)
    closeIssuesFile()
    print(f"\nDone. Copied {nCopied} paragraph marks")
