# -*- coding: utf-8 -*-

# Script for verifying proper USFM.
# Uses parseUsfm module.
# Place this script in the USFM-Tools folder.

# Global variables
usfmVersion = 2     # if version 3.0 or greater, tolerates unknown tokens and verse fragments
suppress1 = False       # Suppress warnings about empty verses and verse fragments
suppress9 = False       # Suppress warnings about ASCII content

if usfmVersion >= 3.0:
    suppress1 = True

lastToken = None
issuesFile = None
usfmDir = ""

# Set Path for files in support/
import os
import sys
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

#from subprocess import Popen, PIPE, call
import parseUsfm
import io
import codecs
# import chardet # $ pip install chardet
import usfm_verses
import re
if usfmVersion >= 3.0:
    import usfm_utils

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

# Marker types
PP = 1      # paragraph or quote
QQ = 2
OTHER = 9


class State:
    IDs = []
    ID = ""
    titles = []
    chapter = 0
    nParagraphs = 0
    verse = 0
    lastVerse = 0
    needVerseText = False
    textOkayHere = False
    reference = ""
    lastRef = ""
    errorRefs = set()
    currMarker = OTHER
    
    
    # Resets state data for a new book
    def addID(self, id):
        State.IDs.append(id)
        State.ID = id
        State.titles = []
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = id
        State.currMarker = OTHER
        
    def getIDs(self):
        return State.IDs
        
    def addTitle(self, bookTitle):
        State.titles.append(bookTitle)
        State.currMarker = OTHER
        
    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.nParagraphs = 0
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c
        State.currMarker = OTHER
    
    def addParagraph(self):
        State.nParagraphs += 1
        State.textOkayHere = True
        State.currMarker = PP

    # supports a span of verses, e.g. 3-4, if needed. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        vlist = []
        if vv.find('-') > 0:
            vv_range = vv_re.search(vv)
            if vv_range:
                vn = int(vv_range.group(1))
                vnEnd = int(vv_range.group(2))
                while vn <= vnEnd:
                    vlist.append(vn)
                    vn += 1
            else:
                reportError("Problem in verse range near " + State.reference)
        else:
            vlist.append(int(vv))
            
        for vn in vlist:
            self.addVerse(str(vn))

    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        State.needVerseText = True
        State.textOkayHere = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
        State.currMarker = OTHER

    def textOkay(self):
        return State.textOkayHere
    
    def needText(self):
        return State.needVerseText
        
    def addText(self):
#        if State.currMarker == QQ:
#            State.currMarker = OTHER
        State.currMarker = OTHER
        State.needVerseText = False
        State.textOkayHere = True
        
    def addQuote(self):
        State.textOkayHere = True
        State.currMarker = QQ

    
    # Adds the specified reference to the set of error references
    # Returns True if reference can be added
    # Returns False if reference was previously added
    def addError(self, ref):
        success = False
        if ref not in State.errorRefs:
            self.errorRefs.add(ref)
            success = True
        return success
        
    # Returns the number of chapters that the specified book should contain
    def nChapters(self, id):
        return usfm_verses.verseCounts[id]['chapters']
                 
    # Returns the number of verses that the specified chapter should contain
    def nVerses(self, id, chap):
        chaps = usfm_verses.verseCounts[id]['verses']
        n = chaps[chap-1]
        return n  
        
    # Returns the English title for the specified book
    def bookTitleEnglish(self, id):
        return usfm_verses.verseCounts[id]['en_name']

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global usfmDir
        path = os.path.join(usfmDir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(usfmDir, "issues-oldest.txt")
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
    issues.write(msg + ".\n")

# Verifies that at least one book title is specified, other than the Engligh book title.
# This method is called just before chapter 1 begins, so there has been every
# opportunity for the book title to be specified.
def verifyBookTitle():
    title_ok = False
    state = State()
    en_name = state.bookTitleEnglish(state.ID)
    for title in state.titles:
        if title and title != en_name:
            title_ok = True
    if not title_ok:
        reportError("No non-English book title for " + state.ID)

# Verifies correct number of verses for the current chapter.
# This method is called just before the next chapter begins.
def verifyVerseCount():
    state = State()
    if state.chapter > 0 and state.verse != state.nVerses(state.ID, state.chapter):
        # Revelation 12 may have 17 or 18 verses
        # 3 John may have 14 or 15 verses
        if state.reference != 'REV 12:18' and state.reference != '3JN 1:15' and state.reference != '2CO 13:13':
            reportError("Chapter should have " + str(state.nVerses(state.ID, state.chapter)) + " verses: "  + state.reference)

def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        reportError(filename + " -- may be empty, or open in another program.")

def verifyChapterCount():
    state = State()
    if state.ID and state.chapter != state.nChapters(state.ID):
        reportError(state.ID + " should have " + str(state.nChapters(state.ID)) + " chapters but " + str(state.chapter) + " chapters are found.")

def printToken(token):
    if token.isV():
        print("Verse number " + token.value)
    elif token.isC():
        print("Chapter " + token.value)
    elif token.isP():
        print("Paragraph " + token.value)
    elif token.isTEXT():
        print("Text: <" + token.value + ">")
    else:
        print(token)

def takeID(id):
    state = State()
    if len(id) < 3:
        reportError("Invalid ID: " + id)
    id = id[0:3].upper()
    if id in state.getIDs():
        reportError("Duplicate ID: " + id)
    state.addID(id)
    
def takeC(c):
    state = State()
    state.addChapter(c)
    if len(state.IDs) == 0:
        reportError("Missing ID before chapter: " + c)
    if state.chapter < state.lastChapter:
        reportError("Chapter out of order: " + state.reference)
    elif state.chapter == state.lastChapter:
        reportError("Duplicate chapter: " + state.reference)
    elif state.chapter > state.lastChapter + 2:
        reportError("Missing chapters before: " + state.reference)
    elif state.chapter > state.lastChapter + 1:
        reportError("Missing chapter(s) between: " + state.lastRef + " and " + state.reference)

def takeP():
    state = State()
    state.addParagraph()

def takeSection():
    state = State()
    if state.currMarker == PP:
        reportError("Warning: \"useless \p before \s marker\" at: " + state.reference)
    elif state.currMarker == QQ:
        reportError("Warning: \"useless \q before \s marker\" at: " + state.reference)

def takeV(v):
    state = State()
    state.addVerses(v)
    if len(state.IDs) == 0 and state.chapter == 0:
        reportError("Missing ID before verse: " + v)
    if state.chapter == 0:
        reportError("Missing chapter tag: " + state.reference)
    if state.verse == 1 and state.nParagraphs == 0:
        reportError("Missing paragraph marker before: " + state.reference)

    if state.verse < state.lastVerse and state.addError(state.lastRef):
        reportError("Verse out of order: " + state.reference + " after " + state.lastRef)
        state.addError(state.reference)
    elif state.verse == state.lastVerse:
        reportError("Duplicated verse: " + state.reference)
    elif state.verse == state.lastVerse + 2 and not isOptional(state.reference, True):
        if state.addError(state.lastRef):
            reportError("Missing verse between: " + state.lastRef + " and " + state.reference)
    elif state.verse > state.lastVerse + 2 and state.addError(state.lastRef):
        reportError("Missing verses between: " + state.lastRef + " and " + state.reference)
 
def takeText(t):
    state = State()
    global lastToken
    if not state.textOkay() and not isTextCarryingToken(lastToken):
        if t[0] == '\\':
            reportError("Uncommon or invalid marker near " + state.reference)
        else:
            # print u"Missing verse marker before text: <" + t.encode('utf-8') + u"> around " + state.reference
            # reportError(u"Missing verse marker or extra text around " + state.reference + u": <" + t[0:10] + u'>.')
            reportError("Missing verse marker or extra text near " + state.reference)
        if lastToken:
            reportError("  preceding Token.type was " + lastToken.getType())
        else:
            reportError("  no preceding Token")
    state.addText()

# Returns true if token is part of a footnote
def isFootnote(token):
    return token.isF_S() or token.isF_E() or token.isFR() or token.isFR_E() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()

# Returns true if token is part of a cross reference
def isCrossRef(token):
    return token.isX_S() or token.isX_E() or token.isXO() or token.isXT()

# Returns True if the specified verse reference is an optional verse.
# Pass previous=True to check the previous verse.
def isOptional(ref, previous=False):
    if previous:
        # Returns True if the specified reference immediately FOLLOWS a verse that does not appear in some manuscripts.
        # Does not handle optional passages, such as John 7:53-8:11, or Mark 16:9-20.
        return ref in { 'MAT 17:22', 'MAT 18:12', 'MAT 23:15', 'MRK 7:17', 'MRK 9:45', 'MRK 9:47',\
'MRK 11:27', 'MRK 15:29', 'LUK 17:37', 'LUK 23:18', 'JHN 5:5', 'ACT 8:38', 'ACT 15:35',\
'ACT 24:8', 'ACT 28:30', 'ROM 16:25' }
    else:
        # May not handle the optional John 7:53-8:11 passage
        return ref in { 'MAT 17:21', 'MAT 18:11', 'MAT 23:14', 'MRK 7:16', 'MRK 9:44', 'MRK 9:46',\
'MRK 16:9', 'MRK 16:10', 'MRK 16:11', 'MRK 16:12', 'MRK 16:13', 'MRK 16:14', 'MRK 16:15', 'MRK 16:16',\
'MRK 16:17', 'MRK 16:18', 'MRK 16:19', 'MRK 16:20', 
'MRK 11:26', 'MRK 15:28', 'LUK 17:36', 'LUK 23:17', 'JHN 5:4', 'JHN 7:53', 'JHN 8:1', 'ACT 8:37', 'ACT 15:34',\
'ACT 24:7', 'ACT 28:29', 'ROM 16:24' }

def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQA() or token.isSP()

def isIntro(token):
    return token.is_is() or token.is_ip() or token.is_iot() or token.is_io()
    
def isTextCarryingToken(token):
    return token.isB() or token.isM() or token.isD() or isFootnote(token) or isCrossRef(token) or isPoetry(token) or isIntro(token)
    
def take(token):
    global lastToken
    global usfmVersion

    state = State()
    if isFootnote(token):
        state.addText()     # footnote replaces need for text
    if state.needText() and not isTextCarryingToken(token) and not suppress1 and not isOptional(state.reference):
        if not token.isTEXT():
            reportError("Empty verse: " + state.reference)
        elif len(token.value) < 7:      # Text follows verse marker but is very short
            reportError("Verse fragment: " + state.reference)
    if token.isID():
        takeID(token.value)
    elif token.isC():
        verifyVerseCount()  # for the preceding chapter
        if not state.ID:
            reportError("Missing book ID: " + state.reference)
            sys.exit(-1)
        if token.value == "1":
            verifyBookTitle()
        takeC(token.value)
    elif token.isP() or token.isPI() or token.isPC() or token.isNB():
        takeP()
        if token.value:     # paragraph markers can be followed by text
            reportError("Unexpected: text returned as part of paragraph token." +  state.reference)
            takeText(token.value)
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isS5() or token.isS():
        takeSection()
    elif token.isQ() or token.isQ1() or token.isQ2() or token.isQ3():
        state.addQuote()
    elif token.isH() or token.isTOC1() or token.isTOC2() or token.isMT() or token.is_imt():
        state.addTitle(token.value)
        if token.isMT() and token.value.isascii() and not suppress9:
            reportError("mt token has ASCII value in " + state.reference)
    elif token.isTOC3() and (len(token.value) != 3 or not token.value.isascii() or token.value.lower() != token.value):
        reportError("Invalid toc3 value in " + state.reference)
    elif token.isUnknown():
        if token.value == "p":
            reportError("Orphaned paragraph marker after " + state.reference)
        elif usfmVersion < 3.0:
            reportError("Unknown USFM token following " + state.reference)
        
    lastToken = token

bad_chapter_re1 = re.compile(r'[^\n\r](\\c\s*\d+)', re.UNICODE)
bad_chapter_re2 = re.compile(r'(\\c[0-9]+)', re.UNICODE)
bad_chapter_re3 = re.compile(r'(\\c\s*\d+)[^\d\s]+[\n\r]', re.UNICODE)
bad_verse_re1 = re.compile(r'([^\n\r\s]\\v\s*\d+)', re.UNICODE)
bad_verse_re2 = re.compile(r'(\\v[0-9]+)', re.UNICODE)
bad_verse_re3 = re.compile(r'(\\v\s*[-0-9]+[^-\d\s])', re.UNICODE)

# Receives the text of an entire book as input.
# Reports bad patterns.
# Can't report verse references because we haven't started to parse the book yet.
def verifyChapterAndVerseMarkers(text, book):
    state = State()
    for badactor in bad_chapter_re1.finditer(text):
        reportError(book + ": missing newline before chapter marker: " + badactor.group(1))
    for badactor in bad_chapter_re2.finditer(text):
        reportError(book + ": missing space before chapter number: " + badactor.group(0))
    for badactor in bad_chapter_re3.finditer(text):
        reportError(book + ": missing space after chapter number: " + badactor.group(1))
    for badactor in bad_verse_re1.finditer(text):
        str = badactor.group(1)
        if str[0] < ' ' or str[0] > '~': # not printable ascii
            str = str[1:]
        reportError(book + ": missing space before verse marker: " + str)
    for badactor in bad_verse_re2.finditer(text):
        reportError(book + ": missing space before verse number: " + badactor.group(0))
    for badactor in bad_verse_re3.finditer(text):
        str = badactor.group(1)
        if str[-1] < ' ' or str[-1] > '~': # not printable ascii
            str = str[:-1]
        reportError(book + ": missing space after verse number: " + str + " near " + state.reference)

# Corresponding entry point in tx-manager code is verify_contents_quiet()
def verifyFile(filename):
    input = io.open(filename, "tr", 1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close()
    if usfmVersion >= 3.0:
        str = usfm_utils.usfm3_to_usfm2(str)

    print("CHECKING " + filename + ":")
    sys.stdout.flush()
    verifyChapterAndVerseMarkers(str, filename)
    for token in parseUsfm.parseString(str):
        take(token)
    verifyNotEmpty(filename)
    verifyVerseCount()      # for the last chapter
    verifyChapterCount()
    state = State()
    state.addID("")
    sys.stderr.flush()

def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path):
            # It's a directory, recurse into it
            verifyDir(path)
        elif os.path.isfile(path) and path[-3:].lower() == 'sfm':
            verifyFile(path)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        source = r'E:\DCS\Kannada\temp'
    else:
        source = sys.argv[1]
        
    if os.path.isdir(source):
        usfmDir = source
        verifyDir(source)
    elif os.path.isfile(source):
        usfmDir = os.path.dirname(source)
        verifyFile(source)
    else:
        reportError("File not found: " + source)
    
    if issuesFile:
        issuesFile.close()
    print("Done.\n")