# coding: latin-1

# Script for verifying proper USFM.
# Uses parseUsfm module.
# Place this script in the USFM-Tools folder.

import sys
import os

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

#from subprocess import Popen, PIPE, call
import parseUsfm
import io
import codecs
# import chardet # $ pip install chardet
import json
import re

# Global variables
lastToken = None
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    IDs = []
    ID = u""
    titles = []
    chapter = 0
    nParagraphs = 0
    verse = 0
    lastVerse = 0
    needVerseText = False
    textOkayHere = False
    reference = u""
    lastRef = u""
    verseCounts = {}
    errorRefs = set()
    
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
        
    def getIDs(self):
        return State.IDs
        
    def addTitle(self, bookTitle):
        State.titles.append(bookTitle)
        
    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c
    
    def addParagraph(self):
        State.nParagraphs += State.nParagraphs + 1
        State.textOkayHere = True

    # supports a span of verses, e.g. 3-4, if needed. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        vlist = []
        if vv.find('-') > 0:
            vv_range = vv_re.search(vv)
            vn = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            while vn <= vnEnd:
                vlist.append(vn)
                vn += 1
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

    def textOkay(self):
        return State.textOkayHere
    
    def needText(self):
        return State.needVerseText
        
    def addText(self):
        State.needVerseText = False
        State.textOkayHere = True
        
    def addQuote(self):
        State.textOkayHere = True

    
    # Adds the specified reference to the set of error references
    # Returns True if reference can be added
    # Returns False if reference was previously added
    def addError(self, ref):
        success = False
        if ref not in State.errorRefs:
            self.errorRefs.add(ref)
            success = True
        return success
        
    def loadVerseCounts(self):
        jsonPath = 'verses.json'
        if not os.access(jsonPath, os.F_OK):
            jsonPath = os.path.dirname(os.path.abspath(__file__)) + "\\" + jsonPath
        if os.access(jsonPath, os.F_OK):
            f = open(jsonPath, 'r')
            State.verseCounts = json.load(f)
            f.close()
        else:
            sys.stderr.write("File not found: verses.json\n")

    # Returns the number of chapters that the specified book should contain
    def nChapters(self, id):
        n = 0
        if len(State.verseCounts) == 0:
            self.loadVerseCounts()
        n = State.verseCounts[id]['chapters']
        return n   
                 
    # Returns the number of verses that the specified chapter should contain
    def nVerses(self, id, chap):
        n = 0
        if len(State.verseCounts) == 0:
            self.loadVerseCounts()
        chaps = State.verseCounts[id]['verses']
        n = chaps[chap-1]
        return n  
        
    # Returns the English title for the specified book
    def bookTitleEnglish(self, id):
        if len(State.verseCounts) == 0:
            self.loadVerseCounts()
        return State.verseCounts[id]['en_name']    

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
        sys.stderr.write("No non-English book title for " + state.ID + "\n")

# Verifies correct number of verses for the current chapter.
# This method is called just before the next chapter begins.
def verifyVerseCount():
    state = State()
    if state.chapter > 0 and state.verse != state.nVerses(state.ID, state.chapter):
        # Revelation 12 may have 17 or 18 verses
        # 3 John may have 14 or 15 verses
        if state.reference != 'REV 12:18' and state.reference != '3JN 1:15' and state.reference != '2CO 13:13':
            sys.stderr.write("Chapter should have " + str(state.nVerses(state.ID, state.chapter)) + " verses: "  + state.reference + '\n')

def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        sys.stderr.write(filename + u" -- may be empty.\n")

def verifyChapterCount():
    state = State()
    if state.ID and state.chapter != state.nChapters(state.ID):
        sys.stderr.write(state.ID + " should have " + str(state.nChapters(state.ID)) + " chapters but " + str(state.chapter) + " chapters are found.\n")

def printToken(token):
    if token.isV():
        print "Verse number " + token.value
    elif token.isC():
        print "Chapter " + token.value
    elif token.isP():
        print "Paragraph " + token.value
    elif token.isTEXT():
        print "Text: <" + token.value + ">"
    else:
        print token

def takeID(id):
    state = State()
    if id in state.getIDs():
        sys.stderr.write("Duplicate ID: " + id + '\n')
    if len(id) < 3:
        sys.stderr.write("Invalid ID: " + id + '\n')
    state.addID(id[0:3])
    
def takeC(c):
    state = State()
    state.addChapter(c)
    if len(state.IDs) == 0:
        sys.stderr.write("Missing ID before chapter: " + c + '\n')
    if state.chapter < state.lastChapter:
        sys.stderr.write("Chapter out of order: " + state.reference + '\n')
    elif state.chapter == state.lastChapter:
        sys.stderr.write("Duplicate chapter: " + state.reference + '\n')
    elif state.chapter > state.lastChapter + 2:
        sys.stderr.write("Missing chapters before: " + state.reference + '\n')
    elif state.chapter > state.lastChapter + 1:
        sys.stderr.write("Missing chapter(s) between: " + state.lastRef + " and " + state.reference + '\n')

def takeP():
    state = State()
    state.addParagraph()

def takeV(v):
    state = State()
    state.addVerses(v)
    if len(state.IDs) == 0 and state.chapter == 0:
        sys.stderr.write("Missing ID before verse: " + v + '\n')
    if state.chapter == 0:
        sys.stderr.write("Missing chapter tag: " + state.reference + '\n')
    if state.chapter <= 1 and state.verse == 1 and state.nParagraphs == 0:
        sys.stderr.write("Missing paragraph marker before: " + state.reference + '\n')
    if state.verse < state.lastVerse and state.addError(state.lastRef):
        sys.stderr.write("Verse out of order: " + state.reference + " after " + state.lastRef + '\n')
        state.addError(state.reference)
    elif state.verse == state.lastVerse:
        sys.stderr.write("Duplicated verse: " + state.reference + '\n')
    elif state.verse > state.lastVerse + 1 and state.addError(state.lastRef):
        if state.lastRef == 'MAT 17:20' and state.reference == 'MAT 17:22':
            exception = 'MAT 17:21'
        elif state.lastRef == 'MAT 18:10' and state.reference == 'MAT 18:12':
            exception = 'MAT 18:11'
        elif state.lastRef == 'MAT 23:13' and state.reference == 'MAT 23:15':
            exception = 'MAT 23:14'
        elif state.lastRef == 'LUK 17:35' and state.reference == 'LUK 17:37':
            exception = 'LUK 17:36'
        else:
            sys.stderr.write("Missing verse(s) between: " + state.lastRef + " and " + state.reference + '\n')
 
def takeText(t):
    state = State()
    global lastToken
    if not state.textOkay() and not isTextCarryingToken(lastToken):
        if t[0] == '\\':
            sys.stderr.write("Uncommon or invalid marker around " + state.reference + '\n')
        else:
            # print u"Missing verse marker before text: <" + t.encode('utf-8') + u"> around " + state.reference
            # sys.stderr.write(u"Missing verse marker or extra text around " + state.reference + u": <" + t[0:10] + u'>.\n')
            sys.stderr.write(u"Missing verse marker or extra text around " + state.reference + '\n')
        # if lastToken:
        #     sys.stderr.write("  preceding Token.type was " + lastToken.getType() + '\n')
        # else:
        #     sys.stderr.write("  no preceding Token\n")
    state.addText()

# Returns true if token is part of a footnote
def isFootnote(token):
    return token.isFS() or token.isFE() or token.isFR() or token.isFRE() or token.isFT()

# Returns true if token is part of a cross reference
def isCrossReference(token):
    return token.isXS() or token.isXE() or token.isXO() or token.isXT()

# Returns True if the current reference is a verse that does not appear in some manuscripts.
def isOptional(ref):
    return ref in { 'MAT 17:21', 'MAT 18:11', 'MAT 23:14', 'MRK 7:16', 'MRK 9:44', 'MRK 9:46', 'MRK 11:26', 'MRK 15:28', 'MRK 16:9', 'MRK 16:12', 'MRK 16:14', 'MRK 16:17', 'MRK 16:19', 'LUK 17:36', 'LUK 23:17', 'JHN 5:4', 'JHN 7:53', 'JHN 8:1', 'JHN 8:4', 'JHN 8:7', 'JHN 8:9', 'ACT 8:37', 'ACT 15:34', 'ACT 24:7', 'ACT 28:29', 'ROM 16:24' }

def isPoetry(token):
    return token.isQ() or token.isQ1()
    
def isTextCarryingToken(token):
    return token.isB() or token.isM() or token.isD() or isFootnote(token) or isCrossReference(token) or isPoetry(token)
    
def take(token):
    global lastToken
    state = State()
    if isOptional(state.reference):
        state.addText()        # counts as text for our purposes
    elif state.needText() and not token.isTEXT() and not isTextCarryingToken(token):
        sys.stderr.write("Empty verse: " + state.reference + '\n')
        sys.stderr.write("  preceding Token.type was " + lastToken.getType() + '\n')
        sys.stderr.write("  current Token.type is " + token.getType() + '\n')
    if token.isID():
        takeID(token.value)
    elif token.isC():
        verifyVerseCount()  # for the preceding chapter
        if token.value == "1":
            verifyBookTitle()
        takeC(token.value)
    elif token.isP() or token.isPI() or token.isPC():
        takeP()
        if token.value:     # paragraph markers can be followed by text
            sys.stderr.write("Unexpected: text returned as part of paragraph token." +  state.reference + '\n')
            takeText(token.value)
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isQ() or token.isQ1() or token.isQ2() or token.isQ3():
        state.addQuote()
    elif token.isH() or token.isTOC1() or token.isTOC2() or token.isMT() or token.isIMT():
        state.addTitle(token.value)
    elif token.isUnknown():
        sys.stderr.write("Unknown token at " + state.reference + '\n')
        
    lastToken = token
     
def verifyFile(filename):
    # detect file encoding
    enc = detect_by_bom(filename, default="utf-8")
    # print "DECODING: " + enc
    input = io.open(filename, "tr", 1, encoding=enc)
    str = input.read(-1)
    input.close

    print "CHECKING " + filename + ":"
    sys.stdout.flush()
    for token in parseUsfm.parseString(str):
        take(token)
    verifyNotEmpty(filename)
    verifyVerseCount()      # for the last chapter
    verifyChapterCount()
    state = State()
    state.addID(u"")
    sys.stderr.flush()
    print "FINISHED CHECKING.\n"

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

def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path):
            # It's a directory, recurse into it
            verifyDir(path)
        elif os.path.isfile(path) and path[-3:].lower() == 'sfm':
            verifyFile(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        source = raw_input("Enter path to .usfm file or directory containing .usfm files: ")
    elif sys.argv[1] == 'hard-coded-path':
        source = r'C:\Users\Larry\Documents\GitHub\Gujarati\GUJARATI-ULB-OT.BCS\temp'
    else:
        source = sys.argv[1]
        
    if os.path.isdir(source):
        verifyDir(source)
    elif os.path.isfile(source):
        verifyFile(source)
    else:
        sys.stderr.write("File not found: " + source + '\n')
