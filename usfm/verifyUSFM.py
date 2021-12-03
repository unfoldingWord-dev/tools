# -*- coding: utf-8 -*-
# Script for verifying proper USFM.
# Reports errors to stderr and issues.txt.
# Set source_dir and usfmVersion to run.
# Detects whether files are aligned USFM.

# Global variables
source_dir = r'C:\DCS\PapuanMalay\pmy_ulb.DCS'
language_code = 'pmy'

suppress1 = False     # Suppress warnings about empty verses and verse fragments
suppress2 = False     # Suppress warnings about needing paragraph marker before \v1 (because tS doesn't care)
suppress3 = True     # Suppress bad punctuation warnings
suppress4 = False     # Suppress warnings about useless markers before section markers
suppress5 = False     # Suppress checks for verse counts
suppress9 = False     # Suppress warnings about ASCII content

if language_code in {'en','es-419','ha','hr','id','nag','pmy','sw','tpi'}:    # ASCII content
    suppress9 = True
if language_code == 'ru':
    suppress5 = True

lastToken = None
nextToken = None
issuesFile = None
aligned_usfm = None

# Set Path for files in support
import os
import sys
import parseUsfm
import io
import footnoted_verses
import usfm_verses
import re
import usfm_utils

# Marker types
PP = 1      # paragraph or quote
QQ = 2
MM = 3
OTHER = 9


class State:
    IDs = []
    ID = ""
    titles = []
    chapter = 0
    verse = 0
    lastVerse = 0
    needPP = False
    needQQ = False
    needVerseText = False
    textLength = 0
    textOkayHere = False
    footnote_starts = 0
    footnote_ends = 0
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
        State.footnote_starts = 0
        State.footnote_ends = 0
        State.needVerseText = False
        State.textLength = 0
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = id + " header/intro"
        State.currMarker = OTHER
        
    def getIDs(self):
        return State.IDs
        
    def addTitle(self, bookTitle):
        State.titles.append(bookTitle)
        State.currMarker = OTHER
        
    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.needPP = True
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c
        State.currMarker = OTHER
    
    def addParagraph(self):
        State.needPP = False
        State.textOkayHere = True
        State.currMarker = PP

    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        State.needVerseText = True
        State.textLength = 0
        State.textOkayHere = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
        State.currMarker = OTHER

    def addPoetryHeading(self):
        State.textOkayHere = True
        State.needQQ = True

    def addPoetry(self):
        State.needQQ = False
        State.needPP = False
        State.currMarker = QQ
        State.textOkayHere = True
    
    # Resets needQQ flag so that errors are not repeated verse after verse
    def resetPoetry(self):
        State.needQQ = False

    def textOkay(self):
        return State.textOkayHere
    
    def needText(self):
        return State.needVerseText

    def getTextLength(self):
        return State.textLength
        
    def addText(self, text):
        State.currMarker = OTHER
        State.needVerseText = False
        State.textLength += len(text)
        State.textOkayHere = True
    
#    def footnotes_started(self):
#        return State.footnote_starts
#    def footnotes_ended(self):
#        return State.footnote_ends
        
    # Increments \f counter
    def addFootnoteStart(self):
        State.footnote_starts += 1
        State.currMarker = OTHER
        State.needVerseText = False
        State.textOkayHere = True

    # Increments \f* counter
    def addFootnoteEnd(self):
        State.footnote_ends += 1
        State.needVerseText = False
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

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

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

# Report missing text in previous verse
def emptyVerseCheck():
    state = State()
    if not suppress1 and not isOptional(state.reference) and state.getTextLength() < 10 and state.verse != 0:
        if state.getTextLength() == 0:
            reportError("Empty verse: " + state.reference)
        else:
            reportError("Verse fragment: " + state.reference)

# Verifies that at least one book title is specified, other than the English book title.
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
        # Acts may have 40 o4 41 verses, normally 41.
        # 2 Cor. may have 13 or 14 verses, normally 14.
        # 3 John may have 14 or 15 verses, normally 14.
        # Revelation 12 may have 17 or 18 verses, normally 17.
        if state.reference != 'REV 12:18' and state.reference != '3JN 1:15' and state.reference != '2CO 13:13' \
            and state.reference != 'ACT 19:40':
            reportError("Chapter should have " + str(state.nVerses(state.ID, state.chapter)) + " verses: "  + state.reference)

def verifyFootnotes():
    state = State()
    if state.footnote_starts != state.footnote_ends:
        reportError(state.ID + ": mismatched footnote tags (" + str(state.footnote_starts) + " started and " + str(state.footnote_ends) + " ended)")

# Checks whether the entire file was empty or unreadable
def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        if not state.ID in {'FRT','BAK'}:
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
    
# Processes a chapter tag
def takeC(c):
    state = State()
    # Report missing text in previous verse
    if c != "1":
        emptyVerseCheck()

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

# Handles all the footnote token types
def takeFootnote(token):
    if token.isF_S():
        State().addFootnoteStart()
    elif token.isF_E():
        State().addFootnoteEnd()

def takeP():
    state = State()
    if state.currMarker in {QQ,PP} and not suppress4:
        reportError("Warning: \"useless \p or \q before paragraph marker\" at: " + state.reference)
    state.addParagraph()

def takeSection():
    if not suppress4:
        state = State()
        if state.currMarker == PP:
            reportError("Warning: \"useless paragraph {p,m,nb} marker before section marker\" at: " + state.reference)
        elif state.currMarker == QQ:
            reportError("Warning: \"useless \q before section marker\" at: " + state.reference)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')
vinvalid_re = re.compile(r'[^\d\-]')

# Receives a string containing a verse number or range of verse numbers.
# Reports missing text in previous verse.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def takeV(vstr):
    state = State()
    if vstr != "1":
        emptyVerseCheck()   # Checks previous verse
#    if vinvalid_re.search(vstr):
#        reportError("Non-numeric verse number near " + State.reference)
#    else:
    vlist = []
    if vstr.find('-') > 0:
        vv_range = vv_re.search(vstr)
        if vv_range:
            vn = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            while vn <= vnEnd:
                vlist.append(vn)
                vn += 1
        else:
            reportError("Problem in verse range near " + State.reference)
    else:
        vlist.append(int(vstr))

    for vn in vlist:
        v = str(vn)
        state.addVerse(str(vn))
        if len(state.IDs) == 0 and state.chapter == 0:
            reportError("Missing ID before verse: " + v)
        if state.chapter == 0:
            reportError("Missing chapter tag: " + state.reference)
        if state.verse == 1 and state.needPP and not suppress2:
            reportError("Need paragraph marker before: " + state.reference)
        if state.needQQ:
            reportError("Need \\q or \\p after poetry heading before: " + state.reference)
            state.resetPoetry()
        if state.verse < state.lastVerse and state.addError(state.lastRef):
            reportError("Verse out of order: " + state.reference + " after " + state.lastRef)
            state.addError(state.reference)
        elif state.verse == state.lastVerse:
            reportError("Duplicated verse number: " + state.reference)
        elif state.verse == state.lastVerse + 2 and not isOptional(state.reference, True):
            if state.addError(state.lastRef):
                reportError("Missing verse between: " + state.lastRef + " and " + state.reference)
        elif state.verse > state.lastVerse + 2 and state.addError(state.lastRef):
            reportError("Missing verses between: " + state.lastRef + " and " + state.reference)
 
reference_re = re.compile(r'[0-9]\: *[0-9]', re.UNICODE)

# Looks for possible verse references and square brackets in the text, not preceded by a footnote marker.
# This function is only called when parsing a piece of text preceded by a verse marker.
def reportFootnotes(text):
    global lastToken
    if not lastToken.getType().startswith('f'):
        if reference_re.search(text):
            reportFootnote(':')
        elif "[" in text:
            reportFootnote('[')
        else:
            state = State()
            if '(' in text and isOptional(state.reference):
                reportFootnote('(')

def reportFootnote(trigger):
    state = State()
    reference = state.reference
    if trigger == ':' or isOptional(reference) or reference in footnoted_verses.footnotedVerses:
        reportError("Probable untagged footnote at " + reference)
    else:
        reportError("Possible untagged footnote at square bracket at " + reference)        
#    reportError("  preceding Token.type was " + lastToken.getType())   # 

punctuation_re = re.compile(r'([\.\?!;\:,][^\s\u200b\)\]\'"’”»›])', re.UNICODE)  # note: \u200b is an invisible character, used like a space in Laotian
spacey_re = re.compile(r'[\s\n]([\.\?!;\:,\)’”»›])', re.UNICODE)
spacey2_re = re.compile(r'[\s]([\(\'"])[\s]', re.UNICODE)

def reportPunctuation(text):
    global lastToken
    state = State()
    if bad := punctuation_re.search(text):
        if text[bad.start():bad.end()+1] != '...':
            chars = bad.group(1)
            if not (chars[0] in ',.' and chars[1] in "0123456789"):   # it's a number
                if not (chars[0] == ":" and chars[1] in "0123456789"):
                    reportError("Bad punctuation at " + state.reference + ": " + chars)
                elif not (lastToken.getType().startswith('f') or lastToken.getType().startswith('io') \
                          or lastToken.getType().startswith('ip')):
                    reportError("Possible verse reference (" + chars + ") out of place: " + state.reference)
    if bad := spacey_re.search(text):
        reportError("Space before phrase ending mark at " + state.reference + ": " + bad.group(1))
    if bad := spacey2_re.search(text):
        reportError("Free floating mark at " + state.reference + ": " + bad.group(1))
    if "''" in text:
        reportError("Repeated quotes at " + state.reference)
        
def takeText(t):
    global lastToken
    state = State()
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
    if "<" in t and not ">" in t:
        if "<< HEAD" in t:
            reportError("Unresolved translation conflict near " + state.reference)
        else:
            reportError("Angle bracket not closed at " + state.reference)
    if not suppress3 and not aligned_usfm:
        reportPunctuation(t)
    if lastToken.isV() and not aligned_usfm:
        reportFootnotes(t)
    state.addText(t)

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
'ACT 24:7', 'ACT 28:29', 'ROM 16:24', 'REV 12:18' }

def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQ2() or token.isQ3() or token.isQA() or \
           token.isQR() or token.isQC()

def isIntro(token):
    return token.is_is() or token.is_ip() or token.is_iot() or token.is_io() or token.is_im()

def isSpecialText(token):
    return token.isWJS() or token.isADDS() or token.isNDS() or token.isPNS() or token.isQTS() or token.is_k_s()
    
def isTextCarryingToken(token):
    return token.isB() or token.isM() or isSpecialText(token) or token.isD() or token.isSP() or \
           isFootnote(token) or isCrossRef(token) or isPoetry(token) or isIntro(token)

def isTitleToken(token):
    return token.isH() or token.isTOC1() or token.isTOC2() or token.isMT() or token.is_imt()

# Returns True if the token value should be checked for Arabic numerals
def isNumericCandidate(token):
    return token.isTEXT() or isTitleToken(token) or token.isCL() or token.isCP() or token.isFT()
    
def take(token):
    global lastToken

    state = State()
    # if state.needText() and not isTextCarryingToken(token) and not suppress1 and not isOptional(state.reference):
    #     if not token.isTEXT():
    #         reportError("Empty verse: " + state.reference)
    #     elif len(token.value) < 14 and not isPoetry(nextToken):      # Text follows verse marker but is very short
    #         reportError("Verse fragment: " + state.reference)
    if token.isID():
        takeID(token.value)
    elif token.isC():
        if not suppress5:
            verifyVerseCount()  # for the preceding chapter
        if not state.ID:
            reportError("Missing book ID: " + state.reference)
            sys.exit(-1)
        if token.value == "1":
            verifyBookTitle()
        takeC(token.value)
    elif token.isP() or token.isPI() or token.isPC() or token.isNB() or token.isM():
        takeP()
        if token.value:     # paragraph markers can be followed by text
            reportError("Unexpected: text returned as part of paragraph token." +  state.reference)
            takeText(token.value)
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif isFootnote(token):
        takeFootnote(token)
    elif token.isS5() or token.isS():
        takeSection()
    elif token.isQA():
        state.addPoetryHeading()
    elif isPoetry(token):
        state.addPoetry()
    elif isTitleToken(token):
        state.addTitle(token.value)
        if token.isMT() and token.value.isascii() and not suppress9:
            reportError("mt token has ASCII value in " + state.reference)
        if token.value.isupper():
            reportError("Upper case book title in " + state.reference)
    elif token.isTOC3() and (len(token.value) != 3 or not token.value.isascii()):
        reportError("Invalid toc3 value in " + state.reference)
    elif token.isUnknown():
        if token.value == "p":
            reportError("Orphaned paragraph marker after " + state.reference)
        elif token.value == "v":
            reportError("Unnumbered verse after " + state.reference)
        elif not aligned_usfm:
            reportError("Invalid USFM token (\\" + token.value + ") near " + state.reference)
    
    if language_code in {"ur"} and isNumericCandidate(token) and re.search(r'[0-9]', token.value, re.UNICODE):
        reportError("Arabic numerals in footnote at " + State().reference)
        
    lastToken = token

bad_chapter_re1 = re.compile(r'[^\n](\\c\s*\d+)', re.UNICODE)
bad_chapter_re2 = re.compile(r'(\\c[0-9]+)', re.UNICODE)
bad_chapter_re3 = re.compile(r'(\\c\s*\d+)[^\d\s]+[\n\r]', re.UNICODE)
bad_verse_re1 = re.compile(r'([^\n\r\s]\\v\s*\d+)', re.UNICODE)
bad_verse_re2 = re.compile(r'(\\v[0-9]+)', re.UNICODE)
bad_verse_re3 = re.compile(r'(\\v\s*[-0-9]+[^-\d\s])', re.UNICODE)

# Receives the text of an entire book as input.
# Reports bad patterns.
def verifyChapterAndVerseMarkers(text, path):
    state = State()
    for badactor in bad_chapter_re1.finditer(text):
        reportError(path + ": missing newline before chapter marker: " + badactor.group(1))
    for badactor in bad_chapter_re2.finditer(text):
        reportError(path + ": missing space before chapter number: " + badactor.group(0))
    for badactor in bad_chapter_re3.finditer(text):
        reportError(path + ": missing space after chapter number: " + badactor.group(1))
    for badactor in bad_verse_re1.finditer(text):
        str = badactor.group(1)
        if str[0] < ' ' or str[0] > '~': # not printable ascii
            str = str[1:]
        reportError(path + ": missing white space before verse marker: " + str)
    for badactor in bad_verse_re2.finditer(text):
        reportError(path + ": missing space before verse number: " + badactor.group(0))
    for badactor in bad_verse_re3.finditer(text):
        str = badactor.group(1)
#        if str[-1] < ' ' or str[-1] > '~': # not printable ascii
#            str = str[:-1]
        reportError(path + ": missing space after verse number: " + str)

orphantext_re = re.compile(r'\n\n[^\\]', re.UNICODE)

# Receives the text of an entire book as input.
# Verifies things that are better done as a whole file.
# Can't report verse references because we haven't started to parse the book yet.
def verifyWholeFile(str, path):
    verifyChapterAndVerseMarkers(str, path)

    lines = str.split('\n')
    orphans = orphantext_re.search(str)
    if orphans:
        reportOrphans(lines, path)

conflict_re = re.compile(r'<+ HEAD', re.UNICODE)   # conflict resolution tag

def reportOrphans(lines, path):
    prevline = "xx"
    lineno = 0
    for line in lines:
        lineno += 1
        if not prevline and line and line[0] != '\\':
            if not conflict_re.match(line):
                reportError(path + ": unmarked text at line " + str(lineno))
            # else:
                #  Will be reported later as an unresolved translation conflict
        prevline = line

wjwj_re = re.compile(r' \\wj +\\wj\*', flags=re.UNICODE)
backslasheol_re = re.compile(r'\\ *\n')


# Corresponding entry point in tx-manager code is verify_contents_quiet()
def verifyFile(path):
    global aligned_usfm
    input = io.open(path, "r", buffering=1, encoding="utf-8-sig")
    str = input.read(-1)
    input.close()
    
    if wjwj_re.search(str):
        reportError(shortname(path) + " - contains empty \\wj \\wj* pair(s)")
    if backslasheol_re.search(str):
        reportError(shortname(path) + " - contains stranded backslash(es) at end of line(s)")
    aligned_usfm = ("lemma=" in str)
    if aligned_usfm:
        str = usfm_utils.unalign_usfm(str)

    print("CHECKING " + shortname(path))
    sys.stdout.flush()
    verifyWholeFile(str, shortname(path))
    tokens = parseUsfm.parseString(str)
    n = 0
    global nextToken
    for token in tokens:
        if n + 1 < len(tokens):
            nextToken = tokens[n+1]
        take(token)
        n += 1
    emptyVerseCheck()       # checks last verse in the file
    verifyNotEmpty(path)
    if not suppress5:
        verifyVerseCount()      # for the last chapter
    verifyChapterCount()
    verifyFootnotes()
    state = State()
    state.addID("")
    sys.stderr.flush()

# Verifies all .usfm files under the specified folder.
def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        if f[0] != '.':         # ignore hidden files
            path = os.path.join(dirpath, f)
            if os.path.isdir(path):
                # It's a directory, recurse into it
                verifyDir(path)
            elif os.path.isfile(path) and path[-3:].lower() == 'sfm':
                verifyFile(path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    
    if os.path.isdir(source_dir):
        verifyDir(source_dir)
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        verifyFile(path)
    else:
        sys.stderr.write("No such folder: " + source_dir)
        exit(-1)
    
    if issuesFile:
        issuesFile.close()
    else:
        print("No issues found!")
    print("Done.\n")