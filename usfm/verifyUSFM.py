# -*- coding: utf-8 -*-
# Script for verifying proper USFM.
# Reports errors to stderr and issues.txt.
# Set source_dir and language_code to run.
# Detects whether files are aligned USFM.

# Global variables
source_dir = r"C:\DCS\Kubu\work\48-2CO.usfm"
language_code = 'kvb'
std_clabel = "Pasal"    # leave blank if you don't have a standard chapter label

suppress1 = False     # Suppress warnings about empty verses and verse fragments
suppress2 = False     # Suppress warnings about needing paragraph marker before \v1 (because tS doesn't care)
suppress3 = False    # Suppress bad punctuation warnings
suppress4 = False     # Suppress warnings about useless markers before section/title markers
suppress5 = False     # Suppress checks for verse counts
suppress6 = False    # Suppress warnings about straight quotes
suppress7 = False     # Suppress warnings about square brackets indicating footnotes
suppress9 = True     # Suppress warnings about ASCII content

max_chunk_length = 400

if language_code in {'diu','en','es','es-419','gl','ha','hr','id','kpj','nag','plt','pmy','pt-br','sw','tl','tpi'}:    # ASCII content
    suppress9 = True
if language_code in {'as','bn','gu','hi','kn','ml','mr','nag','ne','or','pa','ru','ta','te','zh'}:    # ASCII content
    suppress9 = False
#if language_code == 'ru':
    #suppress5 = True

lastToken = None
nextToken = None
aligned_usfm = False
issuesFile = None
issues = dict()

# Set Path for files in support
import os
import sys
import parseUsfm
import io
import footnoted_verses
import usfm_verses
import re
import usfm_utils
from datetime import date

# Marker types
PP = 1      # paragraph or quote
QQ = 2      # poetry
B = 3       # \b for blank line; no titles, text, or verse markers may immediately follow
C = 4       # \c
OTHER = 9

class State:
    IDs = []
    ID = ""
    titles = []
    chaptertitles = []
    nChapterLabels = 0
    chapter = 0
    verse = 0
    lastVerse = 0
    startChunkVerse = 1
    needPP = False
    needQQ = False
    needVerseText = False
    textLength = 0
    textOkayHere = False
    footnote_starts = 0
    footnote_ends = 0
    endnote_starts = 0
    endnote_ends = 0
    reference = ""
    lastRef = ""
    startChunkRef = ""
    errorRefs = set()
    currMarker = OTHER

    # Resets state data for a new book
    def addID(self, id):
        State.IDs.append(id)
        State.ID = id
        State.titles = []
        State.chaptertitles = []
        State.nChapterLabels = 0
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.startChunkVerse = 1
        State.footnote_starts = 0
        State.footnote_ends = 0
        State.endnote_starts = 0
        State.endnote_ends = 0
        State.needVerseText = False
        State.textLength = 0
        State.textOkayHere = False
        State.lastRef = State.reference
        State.startChunkRef = ""
        State.reference = id + " header/intro"
        State.currMarker = OTHER
        State.toc3 = None
        State.upperCaseReported = False

    def getIDs(self):
        return State.IDs

    def addTitle(self, bookTitle):
        State.titles.append(bookTitle)
        State.currMarker = OTHER

    def addToc3(self, toc3):
        State.toc3 = toc3

    def addB(self):
        State.currMarker = B

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
        State.startChunkRef = State.reference + ":1"
        State.currMarker = C

    def addChapterLabel(self, title):
        # first strip the chapter number and extraneous characters
        chend = " " + str(State.chapter)
        chstart = str(State.chapter) + " "
        chlen = len(chend)
        title.strip()
        if title.endswith(chend):
            title = title[:-chlen]
        elif title.startswith(chstart):
            title = title[chlen:]
        title = title.strip()
        title = re.sub(" +", " ", title)
        if title not in State.chaptertitles:
            State.chaptertitles.append(title)
        State.nChapterLabels += 1

    def addParagraph(self):
        State.needPP = False
        State.needQQ = False
        State.textOkayHere = True
        State.currMarker = PP
    def addPoetry(self):
        State.needQQ = False
        State.needPP = False
        State.textOkayHere = True
        State.currMarker = QQ
    def addSection(self):
        State.currMarker = OTHER

    # Records the start of a new chunk
    def addS5(self):
        State.startChunkVerse = State.verse + 1
        State.startChunkRef = State.ID + " " + str(State.chapter) + ":" + str(State.startChunkVerse)

    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        State.needVerseText = True
        State.textLength = 0
        State.textOkayHere = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
        State.currMarker = OTHER
        State.asciiVerse = True   # until proven False

    def addAcrosticHeading(self):
        State.textOkayHere = True
        State.needQQ = True

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
        if not text.isascii():
          State.asciiVerse = False

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

    # Increments \fe counter
    def addEndnoteStart(self):
        State.endnote_starts += 1
        State.currMarker = OTHER
        State.needVerseText = False
        State.textOkayHere = True

    # Increments \fe* counter
    def addEndnoteEnd(self):
        State.endnote_ends += 1
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

    def reportedUpperCase(self):
        State.upperCaseReported = True

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns file pointer.
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
        issuesFile.write(f"Issues generated {date.today()} from {source_dir}\n------------\n")
    return issuesFile

# Returns the longest common substring at the start of s1 and s2
def long_substring(s1, s2):
    if s1.startswith(s2):
        return s2
    i = 0
    while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
        i += 1
    return s1[0:i]

# Writes error message to stderr and to issues.txt.
# Keeps track of how many errors of each type.
def reportError(msg, errorId = 0):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        state = State()
        sys.stderr.write(state.reference + ": (Unicode...)\n")
    issuesfile = openIssuesFile()
    issuesfile.write(msg + "\n")

    if errorId > 0:
        global issues
        if errorId in issues:
            newmsg = long_substring(msg, issues[errorId][0])
            newcount = issues[errorId][1] + 1
        else:
            newmsg = msg
            newcount = 1
        issues[errorId] = (newmsg, newcount)

# Write summary of issues to issuesFile
def reportIssues():
    global issues
    issuesfile = openIssuesFile()
    issuesfile.write("\nSUMMARY:\n")
    for issue in issues.items():
        #issuesfile.write(f"{issue[1][1]} occurrence(s) of \"{issue[1][0]}\"\n")
        issuesfile.write(f"{issue[1][0]} --- {issue[1][1]} occurrence(s).\n")

# Report missing text or all ASCII text, in previous verse
def previousVerseCheck():
    state = State()
    if not suppress1 and not isOptional(state.reference) and state.getTextLength() < 10 and state.verse != 0:
        if state.getTextLength() == 0:
            reportError("Empty verse: " + state.reference, 1)
        elif not isShortVerse(state.reference):
            reportError("Verse fragment: " + state.reference, 2)
    if not suppress9 and state.asciiVerse and state.getTextLength() > 0:
        reportError("Verse is entirely ASCII: " + state.reference, 3)

def longChunkCheck():
    state = State()
    if not aligned_usfm and state.verse - (max_chunk_length-1) > state.startChunkVerse:
        reportError("Long chunk: " + state.startChunkRef + "-" + str(state.verse) + "   (" + str(state.verse-state.startChunkVerse+1) + " verses)", 4)

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
        reportError("No non-English book title for " + state.ID, 5)

# Reports inconsistent chapter titling
def verifyChapterTitles():
    state = State()
    if len(state.chaptertitles) > 1:
        reportError(f"Inconsistent chapter titling: {state.chaptertitles} in {state.ID}", 6)
    if state.nChapterLabels > 1 and state.nChapterLabels != state.chapter:
        reportError(f"Some chapters do not have chapter labels but {state.nChapterLabels} do.", 7)

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
            reportError(f"Chapter {state.chapter} normally has {state.nVerses(state.ID, state.chapter)} verses: {state.reference}", 8)

def verifyFootnotes():
    state = State()
    if state.footnote_starts != state.footnote_ends:
        reportError("Mismatched footnote tags (" + str(state.footnote_starts) + " started and " + str(state.footnote_ends) + " ended) in " + state.ID, 9)
    if state.endnote_starts != state.endnote_ends:
        reportError("Mismatched endnote tags (" + str(state.endnote_starts) + " started and " + str(state.endnote_ends) + " ended) in " + state.ID, 10)

# Checks whether the entire file was empty or unreadable
def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        if not state.ID in {'FRT','BAK'}:
            reportError("File may be empty, or open in another program: " + filename, 11)

def verifyChapterCount():
    state = State()
    if state.ID and state.chapter != state.nChapters(state.ID):
        reportError("There should be " + str(state.nChapters(state.ID)) + " chapters in " + state.ID + " but " + str(state.chapter) + " chapters are found.", 12)

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

# \b is used to indicate additional white space between paragraphs.
# No text or verse marker should follow this marker
# and it should not be used before or after titles to indicate white space.
def takeB():
    State().addB()

# Processes a chapter tag
def takeC(c):
    state = State()
    # Report missing text in previous verse
    if c != "1":
        previousVerseCheck()
        longChunkCheck()
    state.addChapter(c)
    if len(state.IDs) == 0:
        reportError("Missing ID before chapter: " + c, 13)
    if state.chapter < state.lastChapter:
        reportError("Chapter out of order: " + state.reference, 14)
    elif state.chapter == state.lastChapter:
        reportError("Duplicate chapter: " + state.reference, 15)
    elif state.chapter > state.lastChapter + 2:
        reportError("Missing chapters before: " + state.reference, 16)
    elif state.chapter > state.lastChapter + 1:
        reportError("Missing chapter(s) between: " + state.lastRef + " and " + state.reference, 17)

# Processes a chapter label
def takeCL(label):
    global std_clabel
    state = State()
    # Report missing text in previous verse
    state.addChapterLabel(label)
    if std_clabel and not std_clabel in label:
        reportError(f"Non-standard chapter label at {state.reference}: {label}", 42)

# Handles all the footnote and endnote token types
def takeFootnote(token):
    state = State()
    if token.isF_S():
        if state.footnote_starts != state.footnote_ends:
            reportError(f"Footnote starts before previous one is terminated at {state.reference}", 18)
        state.addFootnoteStart()
    elif token.isFE_S():
        if state.endnote_starts != state.endnote_ends:
            reportError(f"Endnote starts before previous one is terminated at {state.reference}", 19)
        reportError(f"Warning: endnote \\fe ... \\fe* at {state.reference} may break USFM Converter and Scripture App Builder.", 20)
        state.addEndnoteStart()
    elif token.isF_E():
        state.addFootnoteEnd()
    elif token.isFE_E():
        state.addEndnoteEnd()
    else:
        if state.footnote_starts <= state.footnote_ends and state.endnote_starts <= state.endnote_ends:
            reportError(f"Footnote marker ({token.type}) not between \\f ... \\f* pair at {state.reference}", 21)
    takeText(token.value, footnote=True)

def takeID(id):
    state = State()
    if len(id) < 3:
        reportError("Invalid ID: " + id, 22)
    id = id[0:3].upper()
    if id in state.getIDs():
        reportError("Duplicate ID: " + id, 23)
    state.addID(id)

def takeP(type):
    state = State()
    if state.currMarker in {QQ,PP} and not suppress4:
        reportError("Warning: back to back paragraph/poetry markers after: " + state.reference, 24)
    if state.needText() and not isOptional(state.reference):
        reportError("Paragraph marker after verse marker, or empty verse: " + state.reference, 25)
    if type == 'nb' and state.currMarker != C:
        reportError("\\nb marker should follow chapter marker: " + state.reference, 26)
    state.addParagraph()

def takeQ(type):
    takeP(type)
    State().addPoetry()

def takeS5():
    longChunkCheck()
    State().addS5()
    takeSection('s5')

def takeSection(tag):
    state = State()
    if not suppress4:
        state = State()
        if state.currMarker == PP:
            reportError(f"Warning: useless paragraph (p,m,nb) marker before \\{tag} marker at: {state.reference}", 27)
        elif state.currMarker == QQ:
            reportError(f"Warning: useless \q before \\{tag} marker at: {state.reference}", 28)
        elif state.currMarker == B:
            reportError(f"\\b may not be used before or after section heading. {state.reference}", 29)
    state.addSection()

def takeTitle(token):
    state = State()
    state.addTitle(token.value)
    if token.isMT() and token.value.isascii() and not suppress9:
        reportError("mt token has ASCII value in " + state.reference, 30)
    if token.value.isupper() and not state.upperCaseReported:
        reportError("Upper case book title in " + state.reference, 31)
        state.reportedUpperCase()
    if state.currMarker == B:
        reportError("\\b may not be used before or after titles or headings. " + state.reference, 32)

vv_re = re.compile(r'([0-9]+)-([0-9]+)')
vinvalid_re = re.compile(r'[^\d\-]')

# Receives a string containing a verse number or range of verse numbers.
# Reports missing text in previous verse.
# Reports errors related to the verse number(s), such as missing or duplicated verses.
def takeV(vstr):
    state = State()
    if state.currMarker == B:
        reportError(f"\\b should be used only between paragraphs. {state.reference}", 33)
    if vstr != "1":
        previousVerseCheck()   # Checks previous verse
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
            reportError("Problem in verse range near " + State.reference, 34)
    else:
        vlist.append(int(vstr))

    for vn in vlist:
        v = str(vn)
        state.addVerse(str(vn))
        if len(state.IDs) == 0 and state.chapter == 0:
            reportError("Missing ID before verse: " + v, 35)
        if state.chapter == 0:
            reportError("Missing chapter tag: " + state.reference, 36)
        if state.verse == 1 and state.needPP and not suppress2:
            reportError("Need paragraph marker before: " + state.reference, 37)
        if state.needQQ:
            reportError("Need \\q or \\p after acrostic heading before: " + state.reference, 38)
            state.resetPoetry()
        if state.verse < state.lastVerse and state.addError(state.lastRef):
            reportError("Verse out of order: " + state.reference + " after " + state.lastRef, 39)
            state.addError(state.reference)
        elif state.verse == state.lastVerse:
            reportError("Duplicated verse number: " + state.reference, 40)
        elif state.verse == state.lastVerse + 2 and not isOptional(state.reference, True):
            if state.addError(state.lastRef):
                reportError("Missing verse between: " + state.lastRef + " and " + state.reference, 41)
        elif state.verse > state.lastVerse + 2 and state.addError(state.lastRef):
            reportError("Missing verses between: " + state.lastRef + " and " + state.reference, 41)

reference_re = re.compile(r'[0-9]\: *[0-9]', re.UNICODE)
bracketed_re = re.compile(r'\[ *([^\]]+) *\]', re.UNICODE)

# Looks for possible verse references and square brackets in the text, not preceded by a footnote marker.
# This function is only called when parsing a piece of text preceded by a verse marker.
def reportFootnotes(text):
    global lastToken
    state = State()
    if not isFootnote(lastToken):
        if ref := reference_re.search(text):
            reportFootnote(ref.group(0))
        elif ('(' in text or '[' in text) and (isOptional(state.reference) or state.reference in footnoted_verses.footnotedVerses):
            reportFootnote('(')
        elif "[" in text:
            fn = bracketed_re.search(text)
            if not fn or ' ' in fn.group(1):    # orphan [, or more than one word between brackets
                reportFootnote('[')

def reportFootnote(trigger):
    state = State()
    reference = state.reference
    if ':' in trigger:
        reportError(f"Probable chapter:verse reference ({trigger}) at {reference} belongs in a footnote", 43)
    elif isOptional(reference) or reference in footnoted_verses.footnotedVerses:
        reportError(f"Bracket or parens found in {reference}, a verse that is often footnoted", 43.1)
    else:
        reportError(f"Optional text or possible untagged footnote at {reference}", 44)

# Returns a string containing text preceding specified start position and following end position
def context(text, start, end):
    start = 0 if start < 0 else 1 + text.rfind(' ', 0, start)
    end = text.find(' ', end, -1)
    return text[start:end] if end > start else text[start:]

#adjacent_re = re.compile(r'([\.\?!;\:,][\.\?!;\:,])', re.UNICODE)
punctuation_re = re.compile(r'([\.\?!;\:,][^\s\u200b\)\]\'"’”»›])', re.UNICODE)     # phrase ending punctuation that doesn't actually end
# note: \u200b indicates word boundaries in scripts that do not use explicit spacing, but is used (seemingly incorrectly) like a space in Laotian
spacey_re = re.compile(r'[\s\n]([\.\?!;\:,\)’”»›])', re.UNICODE)    # space before phrase-ending mark
spacey2_re = re.compile(r'[\s][\(\'"«“‘’”»›][\s]', re.UNICODE)    # free floating marks
spacey3_re = re.compile(r'[\(\'"«“‘’”»›][\s]', re.UNICODE)       # quote-space at beginning of verse
spacey4_re = re.compile(r'[\s][\(\'"«“‘’”»›]$', re.UNICODE)       # quote-space at end of verse
#wordmedial_punct_re = re.compile(r'[\w][\.\?!;\:,\(\)\[\]"«“‘’”»›][\.\?!;\:,\(\)\[\]\'"«“‘’”»›]*[\w]', re.UNICODE)
wordmedial_punct_re = re.compile(r'[\w][\.\?!;\:,\(\)\[\]"«“‘”»›][\.\?!;\:,\(\)\[\]\'"«“‘’”»›]*[\w]', re.UNICODE)
outsidequote_re = re.compile(r'([\'"’”»›][\.!])', re.UNICODE)   # Period or exclamation outside closing quote.

def reportPunctuation(text):
    global lastToken
    state = State()
    if bad := punctuation_re.search(text):
        i = bad.start()
        if text[i:i+3] != '...' or text[i:i+4] == "....":
            chars = bad.group(1)
            if not (chars[0] in ',.' and chars[1] in "0123456789"):   # it's a number
                if not (chars[0] == ":" and chars[1] in "0123456789"):
                    reportError("Check the punctuation at " + state.reference + ": " + chars, 45)
                elif not (lastToken.getType().startswith('f') or lastToken.getType().startswith('io') \
                          or lastToken.getType().startswith('ip')):
                    str = context(text, bad.start()-2, bad.end()+1)
                    reportError(f"Untagged footnote (probable) at {state.reference}: {str}", 43)
    #if bad := adjacent_re.search(text):
        #i = bad.start()
        #if text[i:i+3] != "..." or text[i:i+4] == "....":   # Don't report proper ellipses ...
            #reportError("Check repeated punctuation at " + state.reference + ": " + bad.group(1), 47)
    if bad := spacey_re.search(text):
        reportError("Space before phrase ending mark at " + state.reference + ": " + bad.group(1), 48)
    if bad := outsidequote_re.search(text):
        i = bad.start()
        if text[i+1:i+4] != "...":
            reportError(f"Punctuation after quote mark at {state.reference}: {bad.group(1)}", 50)

    if bad := spacey2_re.search(text):
        str = context(text, bad.start()-2, bad.end()+2)
    elif bad := spacey3_re.match(text):
        str = context(text, 0, bad.end()+2)
    elif bad := spacey4_re.search(text):
        str = context(text, bad.start()-2, len(text))
    if bad:
        reportError(f"Free floating mark at {state.reference}: {str}", 49)

    if "''" in text or '""' in text:
        reportError("Repeated quotes at " + state.reference, 51)
    bad = wordmedial_punct_re.search(text)
    if bad and text[bad.end()-1] not in "0123456789":
        str = context(text, bad.start(), bad.end())
        reportError(f"Word medial punctuation in {state.reference}: {str}", 52)

period_re = re.compile(r' *\.', re.UNICODE)    # detects period starting a phrase
numberprefix_re = re.compile(r'[^\s,.0-9\(][0-9]+', re.UNICODE)
unsegmented_re = re.compile(r'[0-9][0-9][0-9][0-9]+')
numberformat_re = re.compile(r'[0-9]+[\.,]?\s[\.,]?[0-9]+')
leadingzero_re = re.compile(r'[\s]0[0-9,]*', re.UNICODE)

def takeText(t, footnote=False):
    global lastToken
    state = State()
    if not state.textOkay() and not isTextCarryingToken(lastToken):
        if t[0] == '\\':
            reportError("Uncommon or invalid marker near " + state.reference, 53)
        else:
            # print u"Missing verse marker before text: <" + t.encode('utf-8') + u"> around " + state.reference
            # reportError(u"Missing verse marker or extra text around " + state.reference + u": <" + t[0:10] + u'>.')
            reportError("Missing verse marker or extra text near " + state.reference, 54)
        if lastToken:
            reportError("  preceding Token was \\" + lastToken.getValue(), 0)
        else:
            reportError("  no preceding Token", 0)
    if "<" in t and not ">" in t:
        if "<< HEAD" in t:
            reportError("Unresolved translation conflict near " + state.reference, 55)
        else:
            reportError("Angle bracket not closed at " + state.reference, 56)
    if "Conflict Parsing Error" in t:
        reportError("BTT Writer artifact in " + state.reference, 57)
    if not suppress3 and not aligned_usfm:
        reportPunctuation(t)
    if lastToken.isV() and not aligned_usfm and not suppress7:
        reportFootnotes(t)
    if period_re.match(t):
        reportError("Misplaced period in " + state.reference, 58)
    if not footnote and t.startswith(str(state.verse) + " "):
        reportError("Verse number in text (probable): " + state.reference, 59)
    if prefixed := numberprefix_re.search(t):
        if not footnote or (prefixed.group(0)[0] not in {':','-'}):
            reportError(f"Invalid number prefix: {prefixed.group(0)} at {state.reference}", 60)
    if unsegmented := unsegmented_re.search(t):
        reportError(f"Unsegmented number: {unsegmented.group(0)} at {state.reference}", 61.5)
    if fmt := numberformat_re.search(t):
        reportError(f"Space in number {fmt.group(0)} at {state.reference}", 61.6)
    elif leadzero := leadingzero_re.search(t):
        reportError(f"Invalid leading zero: {leadzero.group(0)} at {state.reference}", 61)
    state.addText(t)

# Returns true if token is part of a footnote
def isFootnote(token):
    return (token.getType().startswith("f") and token.getType() != "fig")
    #return token.isF_S() or token.isF_E() or token.isFR() or token.isFT() or token.isFP() or token.isFE_S() or token.isFE_E()

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

def isShortVerse(ref):
    return ref in { 'LEV 11:15', 'DEU 5:19', \
'JOB 3:2', 'JOB 9:1', 'JOB 12:1', 'JOB 16:1', 'JOB 19:1', 'JOB 21:1', 'JOB 27:1', 'JOB 29:1', 'LUK 20:30' }

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
            reportError("Missing book ID: " + state.reference, 62)
            sys.exit(-1)
        if token.value == "1":
            verifyBookTitle()
        takeC(token.value)
    elif token.isCL():
        takeCL(token.value)
    elif token.isP() or token.isPI() or token.isPC() or token.isNB() or token.isM():
        takeP(token.type)
        if token.value:     # paragraph markers can be followed by text
            reportError("Unexpected: text returned as part of paragraph token." +  state.reference, 63)
            takeText(token.value)
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value, state.footnote_starts > state.footnote_ends)
    elif isFootnote(token):
        takeFootnote(token)
    elif token.isS5():
        takeS5()
    elif token.isS() or token.isMR() or token.isMS() or token.isD() or token.isSP():
        takeSection(token.type)
    elif token.isQA():
        state.addAcrosticHeading()
    elif isPoetry(token):
        takeQ(token.type)
    elif token.isB():
        takeB()
    elif isTitleToken(token):
        takeTitle(token)
    elif token.isTOC3():
        state.addToc3(token.value)
        if (len(token.value) != 3 or not token.value.isascii()):
            reportError("Invalid toc3 value in " + state.reference, 64)
        elif token.value.upper() != state.ID:
            reportError(f"toc3 value ({token.value}) not the same as book ID in {state.reference}", 64.5)
    elif token.isUnknown():
        if token.value == "p":
            reportError("Orphaned paragraph marker after " + state.reference, 65)
        elif token.value == "v":
            reportError("Unnumbered verse after " + state.reference, 66)
        elif not aligned_usfm:
            reportError("Invalid USFM token (\\" + token.value + ") near " + state.reference, 67)

    if language_code in {"ur"} and isNumericCandidate(token) and re.search(r'[0-9]', token.value, re.UNICODE):
        reportError("Arabic numerals in footnote at " + State().reference, 68)

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
        reportError("Missing newline before chapter marker: " + badactor.group(1) + " in " + path, 69)
    for badactor in bad_chapter_re2.finditer(text):
        reportError("Missing space before chapter number: " + badactor.group(0) + " in " + path, 70)
    for badactor in bad_chapter_re3.finditer(text):
        reportError("Missing space after chapter number: " + badactor.group(1) + " in " + path, 71)
    for badactor in bad_verse_re1.finditer(text):
        str = badactor.group(1)
        if str[0] < ' ' or str[0] > '~': # not printable ascii
            str = str[1:]
        reportError("Missing white space before verse marker: " + str + " in " + path, 72)
    for badactor in bad_verse_re2.finditer(text):
        reportError("Missing space before verse number: " + badactor.group(0) + " in " + path, 73)
    for badactor in bad_verse_re3.finditer(text):
        str = badactor.group(1)
#        if str[-1] < ' ' or str[-1] > '~': # not printable ascii
#            str = str[:-1]
        reportError("Missing space after verse number: " + str + " in " + path, 74)

orphantext_re = re.compile(r'\n\n[^\\]', re.UNICODE)
embeddedquotes_re = re.compile(r"\w'\w")

# Receives the text of an entire book as input.
# Verifies things that are better done as a whole file.
# Can't report verse references because we haven't started to parse the book yet.
# Returns False if the file is hopelessly invalid.
def verifyWholeFile(str, path):
    verifyChapterAndVerseMarkers(str, path)

    lines = str.split('\n')
    orphans = orphantext_re.search(str)
    if orphans:
        reportOrphans(lines, path)

    if not suppress6:
        nsingle = str.count("'") - len(embeddedquotes_re.findall(str))
        ndouble = str.count('"')
        if nsingle > 0 or ndouble > 0:
            reportError(f"Straight quotes found in {shortname(path)}: {ndouble} doubles, {nsingle} singles not counting word-medial, ", 75)


conflict_re = re.compile(r'<+ HEAD', re.UNICODE)   # conflict resolution tag

def reportOrphans(lines, path):
    prevline = "xx"
    lineno = 0
    for line in lines:
        lineno += 1
        if not prevline and line and line[0] != '\\':
            if not conflict_re.match(line):
                reportError("Unmarked text at line " + str(lineno) + " in " + path, 76)
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
        reportError("Empty \\wj \\wj* pair(s) in " + shortname(path), 77)
    if backslasheol_re.search(str):
        reportError("Stranded backslash(es) at end of line(s) in " + shortname(path), 78)
    if '\x00' in str:
        reportError("Null bytes found in " + shortname(path), 79)
    aligned_usfm = ("lemma=" in str or "x-occurrences" in str)
    if aligned_usfm:
        str = usfm_utils.unalign_usfm(str)

    print("CHECKING " + shortname(path))
    sys.stdout.flush()
    if len(str) < 100:
        reportError("Incomplete file: " + shortname(path), 80)
    else:
        verifyWholeFile(str, shortname(path))
        tokens = parseUsfm.parseString(str)
        n = 0
        global nextToken
        for token in tokens:
            if n + 1 < len(tokens):
                nextToken = tokens[n+1]
            take(token)
            n += 1
        state = State()
        if not state.toc3:
            reportError("No \\toc3 tag in " + shortname(path), 81)
        previousVerseCheck()       # checks last verse in the file
        verifyNotEmpty(path)
        if not suppress5:
            verifyVerseCount()      # for the last chapter
        verifyChapterCount()
        verifyFootnotes()
        verifyChapterTitles()
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
        sys.stderr.write("No such folder or file: " + source_dir)
        exit(-1)

    if issuesFile:
        reportIssues()
        issuesFile.close()
    else:
        print("No issues found!")
    print("Done.\n")