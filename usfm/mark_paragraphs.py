# -*- coding: utf-8 -*-
# This script converts one or more valid .usfm files by adding paragraph marks.
# The model used for marking paragraphs are the USFM files in model_dir.
# Inserts paragraph marker after each chapter marker if needed, before verse 1.
# Does not insert paragraph marks in the middle of sentences, unless the sentence_sensitivity config setting is False.
# Marks unmarked text as section headings where present in model.
# The input file(s) should be verified, correct USFM, except for unmarked text which may become section headings.

import configmanager
import sys
import os
import parseUsfm
import io
import re
import shutil
import sentences
import usfm_verses
from usfmFile import usfmFile

gui = None
config = None
nCopied = 0     # number of paragraphs and sections copied from model
issuesFile = None
state = None

# Marker types
TEXT = 1
OTHER = 9

class State:
    def __init__(self):
        self.fname = ""
        self.chapter = 0
        self.verse = 0
        self.pChapter = 0    # location of latest paragraph mark already in input text
        self.pVerse = 0      # location of latest paragraph mark already in input text
        self.sChapter = 0    # location of latest section heading already in input text
        self.sVerse = 0      # location of latest section heading already in input text
        self.reference = ""
        self.paragraphs_model = []   # list of {mark, chapter, verse, located}
        self.sections_model = []
        self.expectText = False

    def __repr__(self):
        return f'State({self.reference})'

    def addFile(self, fname):
        self.fname = fname
        self.chapter = 0
        self.verse = 0
        self.bridge = 0
        self.pChapter = 0
        self.pVerse = 0
        self.reference = fname
        self.paragraphs_model = []
        self.sections_model = []
        self.expectText = False
        ## Open output USFM file for writing.
        global config
        tmpPath = os.path.join(config['source_dir'], fname + ".tmp")
        self.usfm = usfmFile(tmpPath)

    def addID(self, id):
        self.ID = id
        self.chapter = 0
        self.verse = 0
        self.bridge = 0
        self.expectText = False
        self.midSentence = False

    def addChapter(self, c):
        self.lastChapter = self.chapter
        self.chapter = int(c)
        self.verse = 0
        self.bridge = 0
        self.reference = self.ID[0:3].upper() + " chapter " + c
        self.expectText = False

    # Records the location of a paragraph marker found in the input text.
    def addP(self):
        self.pChapter = self.chapter
        self.pVerse = self.bridge + 1
        self.expectText = True

    def addText(self, endsSentence):
        self.expectText = False
        self.midSentence = not endsSentence

    def addVerse(self, v):
        v1 = v.split('-')[0]
        v2 = v.split('-')[-1]
        self.verse = int(v1)
        self.bridge = int(v2)
        self.reference = self.ID[0:3].upper() + " " + str(self.chapter) + ":" + v
        self.expectText = True

    def addFootnote(self):
        self.expectText = True

    # Returns True if a paragraph mark was already recorded for the current or next verse.
    # See addP()
    def pAlready(self, current):
        if current:
            already = self.pVerse == self.verse and self.pChapter == self.chapter
        else:       # paragraph mark for next verse
            already = self.pVerse == self.verse + 1 and self.pChapter == self.chapter
        return already

    # Returns the paragraph mark that occurred in the model file at the current location.
    def pmarkInModel(self):
        pmark = None
        for pp in self.paragraphs_model:
            if pp['chapter'] == self.chapter and pp['verse'] == self.verse and pp['located']:
                pmark = pp['mark']
                break
        return pmark

    # Returns True immediately after a verse or paragraph marker or footnote.
    def expectingText(self):
        return self.verse > 0 and self.expectText

    # Returns the section mark that occurred in the model file at the current location.
    def smarkInModel(self):
        smark = None
        for s in self.sections_model:
            if s['chapter'] == self.chapter and s['verse'] == self.verse and s['located']:
                smark = s['mark']
                break
        return smark

    # Returns True if current verse is the last verse in a chapter
    def isEndOfChapter(self):
        chaps = usfm_verses.verseCounts[self.ID]['verses']
        return (self.verse >= chaps[self.chapter-1])

    # Returns True if the most recent text does not end a sentence.
    def isMidSentence(self):
        return self.midSentence

    def usfmClose(self):
        self.usfm.close()


# Write to the file with or without a newline as appropriate
def takeStyle(key):
    state.usfm.writeUsfm(key, None)

# Write to the file with or without a newline as appropriate
def takeAsIs(key, value):
    state.usfm.writeUsfm(key, value)

def takeFootnote(key, value):
    state.addFootnote()
    state.usfm.writeUsfm(key, value)

def takeID(id):
    if len(id) < 3:
        reportError("Invalid ID: " + id)
    id = id[0:3].upper()
    state.addID(id)
    state.usfm.writeUsfm("id", id)

# Copies paragraph marker to output unless output already has a paragraph there.
def takePQ(tag, value):
    if not state.pAlready(current=False):
        state.addP()
        state.usfm.writeUsfm(tag)
    if value:
        state.usfm.writeStr(value)

def takeS5():
    if not config.getboolean('removeS5markers', fallback=True):
        state.usfm.writeUsfm("s5", None)
    # elif xlateS5markers and state.chapter > 0 and not state.isEndOfChapter():
    #     global nCopied
    #     nCopied += 1
    #     takePQ("p", None)      # this adds \p before \c, so must run usfm_cleanup afterwards

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

def takeV(v):
    global nCopied
    state.addVerse(v)
    if not state.pAlready(current=True) and (not state.isMidSentence() or not config.getboolean('sentence_sensitivity', fallback=True)):
        if pmark := state.pmarkInModel():
            state.usfm.writeUsfm(pmark)
            nCopied += 1
    state.usfm.writeUsfm("v", v)

def takeText(t):
    global nCopied
    smark = None
    if not state.expectingText() and (not state.isMidSentence() or not config.getboolean('sentence_sensitivity', fallback=True)):
        smark = state.smarkInModel()
    if smark:
        state.usfm.writeUsfm(smark, t)
        nCopied += 1
        state.addP()           # PTXprint wants a paragraph or poetry mark after section heading
        state.usfm.writeUsfm("p")
    else:
        state.usfm.writeStr(t)
        state.addText( sentences.endsSentence(t) )

# Output chapter
def takeC(c):
    state.addChapter(c)
    state.usfm.writeUsfm("c", c)

# Handles the specified token from the input file.
# Inserts paragraph and section markers where needed from model.
def take(token):
    if token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isC():
        takeC(token.value)
    elif isParagraph(token) or isPoetry(token):
        takePQ(token.type, token.value)
    elif token.isS5():
        takeS5()
    elif token.isID():
        takeID(token.value)
    elif isFootnote(token):
        takeFootnote(token.type, token.value)
    elif isCharacterStyle(token):
        takeStyle(token.type)
    else:
        takeAsIs(token.type, token.value)

# Returns true if token is part of a cross reference
def isCrossRef(token):
    return token.isX_S() or token.isX_E() or token.isXO() or token.isXT()

# Returns true if token is part of a footnote or cross reference
def isFootnote(token):
    return token.isF_S() or token.isF_E() or token.isFR() or token.isFT() or token.isFP() or \
token.isFE_S() or token.isFE_E() or token.isRQS() or token.isRQE()

def isCharacterStyle(token):
    return token.isBDS() or token.isBDE() or token.isITS() or token.isITE() or token.isBDITS() or token.isBDITE() \
or token.isADDS() or token.isADDE() or token.isPNS() or token.isPNE()

def isParagraph(token):
    pmark = token.isP() or token.isM() or token.isPI() or token.isPC() or token.isNB() or token.isB() \
        or token.is_ip() or token.is_iot() or token.is_io() or token.is_io2()
    if (token.isNB() or token.isB() or token.isM()) and not config.getboolean('copy_nb', fallback=False):
        pmark = False
    return pmark

def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQ2() or token.isQ3() or \
token.isQA() or token.isSP() or token.isQR() or token.isQC() or token.isD() or\
token.isQSS()

def isSection(token):
    return token.isS() or token.isS2() or token.isS3() or token.isS4() or token.isSR() \
        or token.isR() or token.isD() or token.isSP()

backslash_re = re.compile(r'\\\s')
jammed_re = re.compile(r'(\\v +[-0-9]+[^-\s0-9])', re.UNICODE)
usfmcode_re = re.compile(r'(\\[^a-z\+])', re.UNICODE)

def isParseable(str, fname):
    parseable = True
    if backslash_re.search(str):
        reportError(f"{fname} contains stranded backslash(es) followed by space or newline")
    if bad := jammed_re.search(str):
        reportError(f"{fname} contains verse number(s) not followed by space: {bad.group(1)}")
        parseable = True   # let it convert because the bad spots are easier to locate in the converted USFM
    if badcode := usfmcode_re.search(str):
        reportError(f"{fname} contains foreign usfm code(s): {badcode.group(1)}")
        parseable = False
    return parseable

# Returns False if the usfm file is not parseable.
def convertFile(usfmpath, fname):
    global nCopied
    startn = nCopied
    if not state.fname:
        reportError("Internal error: State is not initialized")  # first pass (scan) sets the state
        sys.exit(-1)
    with io.open(usfmpath, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)

    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        reportProgress(f"Converting {fname}")
        sys.stdout.flush()
        tokens = parseUsfm.parseString(str)
        for token in tokens:
            take(token)
        state.usfmClose()
        if nCopied > startn:
            renameUsfmFiles(usfmpath)
        else:
            sys.stdout.write(f"  No changes to {fname}\n")
            removeTempFiles(usfmpath)
    else:
        state.usfmClose()
        removeTempFiles(usfmpath)
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
            processFile(path)

# Copies specified file to same file name with orig appended.
# Does not overwrite existing backup file.
def backupUsfmFile(path):
    bakpath = path + "orig"
    if not os.path.isfile(bakpath):
        shutil.copyfile(path, bakpath)

# Deletes temp file and backup file, and leaves original file unchanged.
def removeTempFiles(path):
    tmppath = path + ".tmp"
    os.remove(tmppath)
    bakpath = path + "orig"
    os.remove(bakpath)

# Renames temp usfmfile to its original name, overwriting the original usfm file.
def renameUsfmFiles(usfmpath):
    tmppath = usfmpath + ".tmp"
    if os.path.isfile(tmppath):
        if os.path.isfile(usfmpath):
            os.remove(usfmpath)
        os.rename(tmppath, usfmpath)

# If issues.txt file is not already open, opens it for writing.
# Overwrites existing issues.txt file, if any.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global config
        if os.path.isdir(config['source_dir']):
            path = os.path.join(config['source_dir'], "issues.txt")
            issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
            issuesFile.write("Issues detected by MarkParagraphs:\n------------------------------------\n")
    return issuesFile

#def openReportFile():
    #global reportFile
    #if not reportFile:
        #global source_dir
        #path = os.path.join(source_dir, "uncopied pp marks.txt")
        #reportFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    #return reportFile

def closeIssuesFiles():
    global issuesFile
    if issuesFile:
        issuesFile.close()
        issuesFile = None

# Writes message to stderr and to issues.txt.
# If it is not a real issue, writes message to report file.
def reportError(msg, realIssue=True):
    if realIssue:
        reportStatus(msg)     # message to gui
        try:
            sys.stderr.write(msg + "\n")
        except UnicodeEncodeError as e:
            sys.stderr.write(state.reference + ": (Unicode...)\n")
        if issues := openIssuesFile():
            issues.write(msg + "\n")
    #else:
        #report = openReportFile()
        #report.write(msg + "\n")

# Sends a progress report to the GUI, and to stdout.
def reportProgress(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptProgress>>', when="tail")
    print(msg)

def reportStatus(msg):
    global gui
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate('<<ScriptMessage>>', when="tail")
    print(msg)


# Sets the chapter number in the state object
# If there is still a tentative paragraph mark, remove it.
def scanC(c):
    state.addChapter(c)
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) before {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# Save the paragraph mark and its tentative location
# If the previous paragraph mark is still tentative, it is invalid, overwrite it in the state.
def scanPQ(type):
    p = {}
    p['mark'] = type
    p['chapter'] = state.chapter
    p['verse'] = 0      # verse unknown
    p['located'] = False
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            state.paragraphs_model.remove(pp)
    state.paragraphs_model.append(p)

# Save the section mark and its location.
# Unlike paragraph marks, sections marks take the previous verse number as their location.
def scanS(type):
    section = {}
    section['mark'] = type
    section['chapter'] = state.chapter
    section['verse'] = state.verse
    section['located'] = True
    state.sections_model.append(section)

# If there is a paragraph mark not assigned to a verse yet,
# report it because it apparently occurs in the middle of a verse.
def scanText(value):
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) within {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# v is the verse number or range
# Assign the verse number to the preceding paragraph mark, if any.
# Unlike sections, paragraphs take the location of the following verse.
def scanV(v):
    state.addVerse(v)
    v1 = v.split('-')[0]
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]     # the last pq found
        if not pp['located']:
            pp['verse'] = int(v1)
            pp['located'] = True

# Analyzes the specified token in the model file.
# Only cares about locations of paragraphs.
def scan(token):
    if token.isC():
        scanC(token.value)
    elif token.isV():
        scanV(token.value)
    elif token.isTEXT():
        scanText(token.value)
    elif isParagraph(token) or isPoetry(token):
        scanPQ(token.type)
    elif isSection(token):
        scanS(token.type)
    elif token.isID():
        state.addID(token.value)

# Gathers the location and type of all paragraph marks in the model USFM file.
def scanModelFile(modelpath, fname):
    success = False
    if os.path.isfile(modelpath):
        input = io.open(modelpath, "tr", 1, encoding="utf-8-sig")
        str = input.read(-1)
        input.close()
        sys.stdout.flush()
        success = isParseable(str, os.path.basename(modelpath))
        if success:
            reportProgress(f"Parsing model file: {fname}")
            sys.stdout.flush()
            state.addFile(fname)
            tokens = parseUsfm.parseString(str)
            for token in tokens:
                scan(token)
    return success

def countParagraphs(path):
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)
    nchapters = str.count("\\c ")
    nparagraphs = str.count("\\p") + str.count("\\nb") + str.count("\\li")
    npoetry = str.count("\\q")
    return (nchapters, nparagraphs, npoetry)

def processFile(path):
    global config
    fname = os.path.basename(path)
    (nChapters, nParagraphs, nPoetry) = countParagraphs(path)

    #if nParagraphs / nChapters < 2.5 and nPoetry / nChapters < 15:
    model_path = os.path.join(config['model_dir'], fname)
    if os.path.isfile(model_path):
        if scanModelFile(model_path, fname):
            backupUsfmFile(path)
            if not convertFile(path, fname):
                reportError("File cannot be converted: " + fname)
        else:
            reportError("Model file is unusable; file cannot be processed " + fname)
    else:
        reportError("Model file not found; file cannot be processed: " + fname)

# Processes each directory and its files one at a time
def main(app = None):
    global gui
    gui = app
    global nCopied
    nCopied = 0
    global config
    config = configmanager.ToolsConfigManager().get_section('MarkParagraphs')   # configmanager version
    if config:
        global state
        state = State()
        source_dir = config['source_dir']
        file = config['filename']    # configmanager version
        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                processFile(path)
            else:
                reportError(f"File does not exist: {path}")
        else:
            convertFolder(source_dir)

    closeIssuesFiles()
    reportStatus(f"\nDone. Introduced {nCopied} paragraphs / sections")
    gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()