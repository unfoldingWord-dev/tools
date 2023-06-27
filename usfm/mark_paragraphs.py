# -*- coding: utf-8 -*-
# This script converts one or more valid .usfm files by adding paragraph marks.
# The model used for marking paragraphs are the USFM files in model_dir.
# Inserts paragraph marker after each chapter marker if needed, before verse 1.
# Marks unmarked text as section headings where present in model.
# The input file(s) should be verified, correct USFM, except for unmarked text which may become section headings.

# Global variables
#model_dir = r'C:\DCS\English\en_udb.paragraphs'
model_dir = r'C:\DCS\Indonesian\id_ayt.TA'
source_dir = r"C:\DCS\Kodi\work\61-1PE.usfm"     # file(s) to be changed
removeS5markers = True
xlateS5markers = False   # Dubious validity, and not tested for texts that have both kinds of markers already. Translates most \s5 markers to \p markers.
copy_nb = False

nCopied = 0
issuesFile = None
reportFile = None

import sys
import os
import parseUsfm
import io
import re
import shutil
import usfm_verses

# Marker types
TEXT = 1
OTHER = 9

class State:
    fname = ""
    chapter = 0
    verse = 0
    pChapter = 0    # location of latest paragraph mark already in input text
    pVerse = 0      # location of latest paragraph mark already in input text
    sChapter = 0    # location of latest section heading already in input text
    sVerse = 0      # location of latest section heading already in input text
    reference = ""
    __usfmFile = 0
    paragraphs_model = []   # list of {mark, chapter, verse, located}
    sections_model = []
    expectText = False

    def addFile(self, fname):
        State.fname = fname
        State.chapter = 0
        State.verse = 0
        State.bridge = 0
        State.pChapter = 0
        State.pVerse = 0
        State.reference = fname
        State.paragraphs_model = []
        State.sections_model = []
        State.expectText = False
        # Open output USFM file for writing.
        tmpPath = os.path.join(source_dir, fname + ".tmp")
        State.__usfmFile = io.open(tmpPath, "tw", buffering=1, encoding='utf-8', newline='\n')
        State.__spaced = True   # no space wanted at top of file

    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.verse = 0
        State.bridge = 0
        State.expectText = False

    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.verse = 0
        State.bridge = 0
        State.reference = State.ID[0:3].upper() + " chapter " + c
        State.expectText = False

    # Records the location of a paragraph marker found in the input text.
    def addP(self):
        State.pChapter = State.chapter
        State.pVerse = State.bridge + 1
        State.expectText = True

    def addText(self):
        State.expectText = False

    def addVerse(self, v):
        v1 = v.split('-')[0]
        v2 = v.split('-')[-1]
        State.verse = int(v1)
        State.bridge = int(v2)
        State.reference = State.ID[0:3].upper() + " " + str(State.chapter) + ":" + v
        State.expectText = True

    def addFootnote(self):
        State.expectText = True

    # Returns True if a paragraph mark was already recorded for the current verse.
    # See addP()
    def pAlready(self):
        return State.pVerse == State.verse and State.pChapter == State.chapter

    # Returns the paragraph mark that occurred in the model file at the current location.
    def pmarkInModel(self):
        pmark = None
        for pp in State.paragraphs_model:
            if pp['chapter'] == State.chapter and pp['verse'] == State.verse and pp['located']:
                pmark = pp['mark']
                break
        return pmark

    def expectingText(self):
        return State.verse > 0 and State.expectText

    # Returns the section mark that occurred in the model file at the current location.
    def smarkInModel(self):
        smark = None
        for s in State.sections_model:
            if s['chapter'] == State.chapter and s['verse'] == State.verse and s['located']:
                smark = s['mark']
                break
        return smark

    # Returns True if current verse is the last verse in a chapter
    def isEndOfChapter(self):
        chaps = usfm_verses.verseCounts[State.ID]['verses']
        return (State.verse >= chaps[State.chapter-1])

    # Writes specified string to the usfm file, inserting spaces where needed.
    def usfmWrite(self, str):
        if not State.__spaced and str[0] != '\n':
            str = " " + str
        State.__usfmFile.write(str)
        State.__spaced = (str[-1] == ' ')

    def usfmClose(self):
        State.__usfmFile.close()


# Write to the file with or without a newline as appropriate
def takeStyle(key):
    State().usfmWrite("\n\\" + key)

# Write to the file with or without a newline as appropriate
def takeAsIs(key, value):
    state = State()
    state.usfmWrite("\n\\" + key)
    if value:
        state.usfmWrite(value)

def takeFootnote(key, value):
    state = State()
    state.addFootnote()
    if key in {"f", "fe"}:
        state.usfmWrite("\n\\" + key)
    else:
        state.usfmWrite("\\" + key)
    if value:           # or key in {"f*", "fp"}
        state.usfmWrite(value)

def takeID(id):
    state = State()
    if len(id) < 3:
        reportError("Invalid ID: " + id)
    id = id[0:3].upper()
    state.addID(id)
    state.usfmWrite("\\id " + id)

# Copies paragraph marker to output unless output already has a paragraph there.
def takePQ(tag, value):
    state = State()
    state.addP()
    state.usfmWrite("\n\\" + tag)
    if value:
        state.usfmWrite(value)

def takeS5():
    state = State()
    if not removeS5markers:
        state.usfmWrite("\n\\s5")
    elif xlateS5markers and state.chapter > 0 and not state.isEndOfChapter():
        global nCopied
        nCopied += 1
        takePQ("p", None)      # this adds \p before \c, so must run usfm_cleanup afterwards

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

def takeV(v):
    global nCopied
    state = State()
    state.addVerse(v)
    if not state.pAlready():
        if pmark := state.pmarkInModel():
            state.usfmWrite("\n\\" + pmark)
            nCopied += 1
    state.usfmWrite("\n\\v " + v)

def takeText(t):
    state = State()
    smark = None if state.expectingText() else state.smarkInModel()
    if smark:
        state.usfmWrite(f"\n\\{smark} {t}")
        state.addP()           # PTXprint wants a paragraph or poetry mark after section heading
        state.usfmWrite("\n\\p")
    else:
        state.usfmWrite(t)
        state.addText()

# Output chapter
def takeC(c):
    state = State()
    state.addChapter(c)
    state.usfmWrite("\n\\c " + c)

# Handles the specified token from the input file.
# Inserts paragraph and section markers where needed from model.
def take(token):
    state = State()
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
token.isFE_S() or token.isFE_E() # or token.isX_S() or token.isX_E()

def isCharacterStyle(token):
    return token.isBDS() or token.isBDE() or token.isITS() or token.isITE() or token.isBDITS() or token.isBDITE() \
or token.isADDS() or token.isADDE() or token.isPNS() or token.isPNE()

def isParagraph(token):
    pmark = token.isP() or token.isM() or token.isPI() or token.isPC() or token.isNB() or token.isB() \
        or token.is_ip() or token.is_iot() or token.is_io() or token.is_io2()
    if (token.isNB() or token.isB() or token.isM()) and not copy_nb:
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
        reportError(f"{fname} contains stranded backslash(es) followed by space")
#        parseable = False
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
    state = State()
    if not state.fname:
        reportError("Internal error: State is not initialized")  # first pass (scan) sets the state
        sys.exit(-1)
    with io.open(usfmpath, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)

    sys.stdout.flush()
    success = isParseable(str, fname)
    if success:
        sys.stdout.write(f"Converting {fname}\n")
        sys.stdout.flush()
        tokens = parseUsfm.parseString(str)
        for token in tokens:
            take(token)
        state.usfmWrite("\n")
        state.usfmClose()
        if nCopied > startn:
            renameUsfmFiles(usfmpath)
        else:
            removeTempFiles(usfmpath)
            sys.stdout.write(f"  No changes to {fname}\n")
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
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
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
    global reportFile
    if issuesFile:
        issuesFile.close()
        issuesFile = None
    if reportFile:
        reportFile.close()
        reportFile = None

# Writes message to stderr and to issues.txt.
# If it is not a real issue, writes message to report file.
def reportError(msg, realIssue=True):
    if realIssue:
        try:
            sys.stderr.write(msg + "\n")
        except UnicodeEncodeError as e:
            state = State()
            sys.stderr.write(state.reference + ": (Unicode...)\n")
        issues = openIssuesFile()
        issues.write(msg + "\n")
    #else:
        #report = openReportFile()
        #report.write(msg + "\n")

# Sets the chapter number in the state object
# If there is still a tentative paragraph mark, remove it.
def scanC(c):
    state = State()
    state.addChapter(c)
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) before {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# Save the paragraph mark and its tentative location
# If the previous paragraph mark is still tentative, it is invalid, overwrite it in the state.
def scanPQ(type):
    state = State()
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
    state = State()
    section = {}
    section['mark'] = type
    section['chapter'] = state.chapter
    section['verse'] = state.verse
    section['located'] = True
    state.sections_model.append(section)

# If there is a paragraph mark not assigned to a verse yet,
# report it because it apparently occurs in the middle of a verse.
def scanText(value):
    state = State()
    if len(state.paragraphs_model) > 0:
        pp = state.paragraphs_model[-1]
        if not pp['located']:
            reportError(f"Paragraph mark (\\{pp['mark']}) within {state.reference} not copied", False)
            state.paragraphs_model.remove(pp)

# v is the verse number or range
# Assign the verse number to the preceding paragraph mark, if any.
# Unlike sections, paragraphs take the location of the following verse.
def scanV(v):
    state = State()
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
    state = State()
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
    if os.path.isfile(modelpath):
        input = io.open(modelpath, "tr", 1, encoding="utf-8-sig")
        str = input.read(-1)
        input.close()
        sys.stdout.flush()
        success = isParseable(str, os.path.basename(modelpath))
        if success:
            state = State()
            sys.stdout.write(f"Parsing model file: {fname}\n")
            sys.stdout.flush()
            state.addFile(fname)
            tokens = parseUsfm.parseString(str)
            for token in tokens:
                scan(token)
    else:
        reportError("Model file does not exist: " + modelpath)
        success = False
    return success

def countParagraphs(path):
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)
    nchapters = str.count("\\c ")
    nparagraphs = str.count("\\p") + str.count("\\nb") + str.count("\\li")
    npoetry = str.count("\\q")
    return (nchapters, nparagraphs, npoetry)

def processFile(path):
    global model_dir
    fname = os.path.basename(path)
    (nChapters, nParagraphs, nPoetry) = countParagraphs(path)
    if nParagraphs / nChapters < 2.5 and nPoetry / nChapters < 15:
        model_path = os.path.join(model_dir, fname)
        if scanModelFile(model_path, fname):
            backupUsfmFile(path)
            if not convertFile(path, fname):
                reportError("File cannot be converted: " + fname)
        else:
            reportError("Model file is unusable: " + model_path)
    else:
        reportError(f"{fname} has {nParagraphs} paragraphs and {nPoetry} poetry marks in {nChapters} chapters. No need to mark additional paragraphs.", False)
        #reportError(f"  p/c = {nParagraphs / nChapters}", False)
        #reportError(f"  q/c = {nPoetry / nChapters}", False)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if os.path.isdir(source_dir):
        convertFolder(source_dir)
    elif os.path.isfile(source_dir) and source_dir.endswith("sfm"):
        path = source_dir
        source_dir = os.path.dirname(path)
        processFile(path)
    else:
        sys.stderr.write("Invalid folder or file: " + source_dir)
        exit(-1)
    closeIssuesFiles()
    print(f"\nDone. Introduced {nCopied} paragraphs")
