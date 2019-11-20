# verifyUSFM.py

# Script for verifying proper USFM.
# Uses parseUsfm module.
# Place this script in the USFM-Tools folder.

import re
import sys
import logging

from . import parseUsfm, usfm_verses


# Global variables
lastToken = None
vv_re = re.compile(r'([0-9]+)-([0-9]+)')
error_log = None

chapter_marker_re = re.compile(r'\\c(?!a)') # Don't match on \ca
verse_marker_re = re.compile(r'\\v(?!a)') # Don't match on \va

WHITE_SPACE = [' ', '\u00A0', '\r', '\n', '\t']
SPACE = [' ', '\u00A0']
NON_CHAPTER_BOOK_CODES = ('FRT','BAK','OTH','INT','CNC','GLO','TDX','NDX')


class State:
    IDs = []
    ID = ''
    IDE = ''
    usfm = ''
    toc1 = ''
    toc2 = ''
    toc3 = ''
    mt = ''
    heading = ''
    master_chapter_label = ''
    chapter_label = ''
    chapter = 0
    nParagraphs = 0
    nMargin = 0
    nQuotes = 0
    verse = 0
    lastVerse = 0
    needVerseText = False
    textOkayHere = False
    referenceString = ''
    lastReferenceString = ''
    chapters = set()
    verseCounts = {}
    errorRefs = set()
    englishWords = []
    lang_code = None
    book_code = None

    def reset_all(self):
        self.reset_book()
        State.IDs = []
        State.errorRefs = set()

    def reset_book(self):
        State.ID = ''
        State.IDE = ''
        State.usfm = ''
        State.toc1 = ''
        State.toc2 = ''
        State.toc3 = ''
        State.mt = ''
        State.heading = ''
        State.master_chapter_label = ''
        State.chapter_label = ''
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.chapters = set()
        State.nParagraphs = 0
        State.nMargin = 0
        State.nQuotes = 0
        State.lastReferenceString = ''
        State.referenceString = ''
        State.book_code = None

    def set_book_code(self, book):
        State.book_code = book
        State.referenceString = book  # default

    def setLanguageCode(self, code):
        State.lang_code = code

    def addID(self, id):
        self.reset_book()
        State.IDs.append(id)
        State.ID = id
        State.lastReferenceString = State.referenceString
        State.referenceString = id

    def getIDs(self):
        return State.IDs

    def addHeading(self, heading):
        State.heading = heading

    def addIDE(self, ide):
        State.IDE = ide

    def addUSFM(self, usfm):
        State.usfm = usfm

    def addTOC1(self, toc):
        State.toc1 = toc

    def addTOC2(self, toc):
        State.toc2 = toc

    def addTOC3(self, toc):
        State.toc3 = toc

    def addMT(self, mt):
        State.mt = mt

    def addChapterLabel(self, text):
        if State.chapter == 0:
            State.master_chapter_label = text
        else:
            State.chapter_label = text

    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.chapters.add(State.chapter)
        State.lastVerse = 0
        State.nParagraphs = 0
        State.nMargin = 0
        State.nQuotes = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastReferenceString = State.referenceString
        State.referenceString = self.get_id() + ' ' + str(State.chapter)

    def get_id(self):
        id = State.ID
        if not State.ID:
            id = State.book_code  # use book code if no ID given
        return id

    def addParagraph(self):
        State.nParagraphs += 1
        State.textOkayHere = True

    def addMargin(self):
        State.nMargin += State.nMargin + 1
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
        State.lastReferenceString = State.referenceString
        State.referenceString = self.get_id() + ' ' + str(State.chapter) + ':' + v

    def textOkay(self):
        return State.textOkayHere

    def needText(self):
        return State.needVerseText

    def addText(self):
        State.needVerseText = False
        State.textOkayHere = True

    def addQuote(self):
        State.nQuotes += State.nQuotes + 1
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


    def getEnglishWords(self):
        if not State.englishWords:
            for book in usfm_verses.verses:
                book_data = usfm_verses.verses[book]
                english_name = book_data['en_name'].lower()
                english_words = english_name.split(' ')
                for word in english_words:
                    if word and not isNumber(word):
                        State.englishWords.append(word)
            State.englishWords.sort()
        return State.englishWords


    def loadVerseCounts(self):
        if not State.verseCounts:
            State.verseCounts = usfm_verses.verses


    # Returns the number of chapters that the specified book should contain
    def nChapters(self, book_id):
        self.loadVerseCounts()
        try: return State.verseCounts[book_id]['chapters']
        except KeyError as e:
            logging.error(f"verifyUSFM.State.nChapters failed for book_id={book_id} with {e}")
            return 0


    # Returns the number of verses that the specified chapter should contain
    def nVerses(self, book_id, chap):
        self.loadVerseCounts()
        try:
            chaps = State.verseCounts[book_id]['verses']
            return chaps[chap-1]
        except (KeyError, IndexError) as e:
            logging.error(f"verifyUSFM.State.nVerses failed for book_id={book_id} chap={chap} with {e}")
            return 0
# end of State class



def report_error(msg):
    if error_log is None:  # if error logging is enabled then don't print
        sys.stderr.write(msg)
    else:
        error_log.append(msg.rstrip(' \t\n\r'))


def verifyVerseCount():
    state = State()
    if not state.ID:
        return -1

    if state.chapter > 0 and state.verse != state.nVerses(state.ID, state.chapter):
        # Revelation 12 may have 17 or 18 verses
        # 3 John may have 14 or 15 verses
        if state.referenceString != 'REV 12:18' and state.referenceString != '3JN 1:15':
            report_error(f"{state.referenceString} - Should have {state.nVerses(state.ID, state.chapter)} verses\n")


def verifyNotEmpty(filename, book_code):
    state = State()
    if not state.ID \
    or (state.chapter==0 and book_code not in NON_CHAPTER_BOOK_CODES):
        report_error(f"{filename} - File may be empty.")


def verifyIdentification(book_code):
    state = State()
    if not state.ID:
        report_error(f"{book_code} - Missing \\id tag")
    elif (book_code is not None) and (book_code != state.ID):
        report_error(f"{state.ID} - Found in \\id tag does not match code '{book_code}' found in filename")

    if not state.IDE:
        report_error(f"{book_code} - Missing \\ide tag")

    if state.heading:
        if state.heading.isupper():
            report_error(f"{book_code} - \\h '{state.heading}' shouldn't be UPPERCASE")
    else:
        report_error(f"{book_code} - Missing \\h tag")

    if not state.toc1:
        report_error(f"{book_code} - Missing \\toc1 tag")

    if not state.toc2:
        report_error(f"{book_code} - Missing \\toc2 tag")

    if not state.toc3:
        report_error(f"{book_code} - Missing \\toc3 tag")

    if not state.mt:
        if book_code not in NON_CHAPTER_BOOK_CODES:
            report_error(f"{book_code} - Missing \\mt or \\mt1 tag")
# end of verifyIdentification function


def make_reference_string(book, chapter, verse=None):
    ref = book + ' ' + str(chapter)
    if verse is not None:
          ref += ":" + verse
    return ref
# end of make_reference_string function


def verifyChapterAndVerseMarkers(text, book):
    pos = 0
    last_ch = 1
    for chapter_current in chapter_marker_re.finditer(text):
        start_index = chapter_current.start()
        end_index = chapter_current.end()
        end_char = text[end_index]
        if (end_char >= 'a') and (end_char <= 'z'):
            continue  #  skip non-chapter markers
        has_space = end_char in SPACE
        if has_space:
            end_index += 1
        previous_char = text[start_index - 1]
        newline_before = (previous_char == '\n') or (previous_char == '\r')
        ch_num, has_space_after = get_chapter_number(text, end_index)
        if ch_num >= 0:
            if not has_space:
                add_error(text, book, "Missing space before chapter number: '{0}'", start_index, last_ch)
            elif not has_space_after:
                add_error(text, book, "Missing new line after chapter number: '{0}'", start_index, last_ch)
            elif not newline_before:
                add_error(text, book, "Missing new line before chapter marker: '{0}'", start_index-4, last_ch)
            check_chapter(text, book, last_ch, pos, start_index)
            last_ch = ch_num
            pos = end_index
        else:
            add_error(text, book, "Invalid chapter number format: '{0}'", start_index, last_ch)

    check_chapter(text, book, last_ch, pos, len(text))  # check last chapter


def add_error(text, book, message, pos, chapter, verse=None):
    length = 8
    example = text[pos: pos + length]
    report_error(make_reference_string(book, chapter, verse) + " - " + message.format(example))


def check_chapter(text, book, chapter_num, start, end):
    last_vs_range = '1'
    for verse_current in verse_marker_re.finditer(text, start, end):
        start = verse_current.start()
        end = verse_current.end()
        char = text[end]
        has_space = char in SPACE
        if has_space:
            end += 1
        char = text[start - 1]
        space_before = char in WHITE_SPACE
        vs_range, has_space_after = get_verse_range(text, end)
        if vs_range != '':
            if not has_space:
                add_error(text, book, "Missing space before verse number: '{0}'", start, chapter_num, vs_range)
            elif not has_space_after:
                add_error(text, book, "Missing space after verse number: '{0}'", start, chapter_num, vs_range)
            elif not space_before:
                add_error(text, book, "Missing space before verse marker: '{0}'", start-1, chapter_num, vs_range)
            last_vs_range = vs_range
        else:
            # print("book", book, "chapter", chapter_num, "verse_current", verse_current)
            # print(f"start='{start}' end='{end}'")
            # print(f"char='{char}'")
            # print(f"space_before={space_before} vs_range={vs_range} has_space_after={has_space_after}")
            add_error(text, book, "Invalid verse number: '{0}'", start, chapter_num, last_vs_range)


def get_verse_range(text, start):
    pos = start
    verse, c, end = get_number(text, pos)
    if verse == '':
        return verse, False

    if c != '-':  # not verse range
        has_white_space = (c in WHITE_SPACE)
        return verse, has_white_space

    second_vs, c, end = get_number(text, end+1)
    if second_vs == '':
        return '', False

    verse += '-' + second_vs
    has_white_space = (c in WHITE_SPACE)
    return verse, has_white_space


def get_chapter_number(text, start):
    pos = start
    digits, c, _end = get_number(text, pos)
    has_white_space = (c in WHITE_SPACE)
    if digits:
        return int(digits), has_white_space
    return -1, has_white_space


def get_number(text, start_index):
    """
    Called by get_verse_range() and get_chapter_number()
    """
    digits = ''
    end_index = start_index
    c = ''
    for pos in range(start_index, len(text)):
        c = text[pos]
        if c=='0' and not digits:
            state = State()
            report_error(f"{state.referenceString} has leading zero in following chapter/verse number")
        if (c >= '0') and (c <= '9'):
            digits += c
            continue
        end_index = pos
        break
    return digits, c, end_index

def verifyChapterCount():
    state = State()
    if state.ID:
        expected_chapters = state.nChapters(state.ID)
        if len(state.chapters) != expected_chapters:
            for i in range(1, expected_chapters + 1):
                if i not in state.chapters:
                    report_error(f"{state.ID} {i} - Missing chapter\n")


def verifyTextTranslated(text, token):
    found, word = needsTranslation(text)
    if found:
        report_error(f"Token '\\{token}' has possible untranslated word '{word}'")


def needsTranslation(text):
    state = State()
    if state.lang_code and state.lang_code[0:2]!='en':  # no need to translate english
        english = state.getEnglishWords()
        words = text.split(' ')
        for word in words:
            if word:
                found = binarySearch(english, word.lower())
                if found:
                    return True, word
    return False, None


def binarySearch(alist, item):
    first = 0
    last = len(alist)-1
    found = False

    while first <= last and not found:
        midpoint = (first + last)//2
        mid_value = alist[midpoint]
        if mid_value == item:
            found = True
        else:
            if item < mid_value:
                last = midpoint-1
            else:
                first = midpoint+1

    return found


def isNumber(s):
    if s:
        char = s[0]
        if (char >= '0') and (char <= '9'):
            return True
    return False


def takeCL(text):
    state = State()
    state.addChapterLabel(text)
    verifyTextTranslated(text, 'cl')

def takeTOC1(text):
    state = State()
    state.addTOC1(text)
    verifyTextTranslated(text, 'toc1')

def takeTOC2(text):
    state = State()
    state.addTOC2(text)
    verifyTextTranslated(text, 'toc2')

def takeTOC3(text):
    state = State()
    state.addTOC3(text)
    # verifyTextTranslated(text, 'toc3') # toc3 commonly has 3-letter book code, not to be translated

def takeMT(text):
    state = State()
    state.addMT(text)
    verifyTextTranslated(text, 'mt')

def takeH(heading):
    state = State()
    state.addHeading(heading)
    verifyTextTranslated(heading, 'h')

def takeIDE(ide):
    state = State()
    state.addIDE(ide)

def takeUSFM(usfm):
    state = State()
    state.addUSFM(usfm)


def takeID(id):
    state = State()
    code = '' if not id else id.split(' ')[0] # Take the first token in the \id field
    if len(code) < 3:
        report_error(f"{state.referenceString} - Invalid ID: '{id}'\n")
        return
    if code in state.getIDs():
        report_error(f"{state.referenceString} - Duplicate ID: '{id}'\n")
        return
    if code in NON_CHAPTER_BOOK_CODES: # Books without chapters/verses
        state.addID(code)
        return
    state.loadVerseCounts()
    for k in State.verseCounts:  # look for match in bible names
        if k == code:
            state.addID(code)
            return
    report_error(f"{state.referenceString} - Invalid Code '{code}' in ID: '{id}'\n")


def takeC(c):
    state = State()
    state.addChapter(c)
    if not state.IDs:
        report_error(f"{state.referenceString} - Missing ID before chapter\n")
    if state.chapter < state.lastChapter:
        report_error(f"{state.referenceString} - Chapter out of order\n")
    elif state.chapter == state.lastChapter:
        report_error(f"{state.referenceString} - Duplicate chapter\n")
    elif state.chapter > state.lastChapter + 2:
        report_error(f"{state.lastReferenceString} - Missing chapters between this and: {state.referenceString}\n")
    elif state.chapter > state.lastChapter + 1:
        report_error(f"{state.lastReferenceString} - Missing chapter between this and: {state.referenceString}\n")


def takeP():
    state = State()
    state.addParagraph()

def takeM():
    state = State()
    state.addMargin()


def takeV(v):
    state = State()
    state.addVerses(v)
    if state.lastVerse == 0:  # if first verse in chapter
        if not state.IDs and state.chapter == 0:
            report_error(f"{state.referenceString} {v} - Missing ID before verse\n")
        if state.chapter == 0:
            report_error(f"{state.referenceString} - Missing chapter tag\n")
        if (state.nParagraphs == 0) and (state.nQuotes == 0) and (state.nMargin == 0):
            report_error(f"{state.referenceString} - Missing paragraph marker (\\p), margin (\\m) or quote (\\q) before verse text\n")

    missing = ""
    if state.verse < state.lastVerse and state.addError(state.lastReferenceString):
        report_error(f"{state.referenceString} - Verse out of order: after {state.lastReferenceString}\n")
        state.addError(state.referenceString)
    elif state.verse == state.lastVerse:
        report_error(f"{state.referenceString} - Duplicated verse\n")
    elif state.verse == state.lastVerse + 2 and not isOptional(state.referenceString):
        missing = " - Missing verse between this and: "
    elif state.verse > state.lastVerse + 2:
        missing = " - Missing verses between this and: "

    if missing:
        state.addError(state.lastReferenceString)
        if not error_log is None:  # see if already warned for missing verses
            gaps = False
            for i in range(state.lastVerse+1, state.verse):
                ref = f"{state.ID} {state.chapter}:{i}"
                ref_len = len(ref)
                verse_warning_found = False
                for error in error_log:
                    if error[:ref_len] == ref:
                        verse_warning_found = True
                        break
                if not verse_warning_found:
                    gaps = True
            if not gaps:
                return

        report_error(state.lastReferenceString + missing + state.referenceString + '\n')


def takeText(t):
    state = State()
    global lastToken
    if not state.textOkay() and not isTextCarryingToken(lastToken):
        if t[0] == '\\':
            report_error(f"{state.referenceString} - Nearby uncommon or invalid marker\n")
        else:
            # print "Missing verse marker before text: <" + t.encode('utf-8') + "> around " + state.reference
            # report_error("Missing verse marker or extra text around " + state.referenceString + ": <" + t[0:10] + '>.\n')
            report_error(f"{state.referenceString} - Missing verse marker or extra text nearby\n")
        if lastToken:
            report_error(f"{state.referenceString} - Preceding Token.type was '{lastToken.getType()}'\n")
        else:
            report_error(f"{state.referenceString} - No preceding Token\n")
    state.addText()


def takeUnknown(state, token):
    value = token.getValue()
    if (value == 'v') or (value == 'c'):
        return  # skip malformed chapter and verses - will be caught later
    elif value == 'p':
        report_error(f"{state.referenceString} - Orphan paragraph marker follows")
    else:
        report_error(f"{state.referenceString} - Unknown USFM token: '\\{value}'")


# Returns True if token is part of a footnote
def isFootnote(token):
    return token.isF_S() or token.isF_E() \
        or token.isFR() or token.isFR_E() \
        or token.isFT() or token.isFT_E() \
        or token.isFP() \
        or token.isFE_S() or token.isFE_E()

# Returns true if token is part of a cross reference.
def isCrossRef(token):
    return token.isX_S() or token.isX_E() \
        or token.isXO() \
        or token.isXT()


# Returns True if the specified reference immediately FOLLOWS a verse that does not appear in some manuscripts.
# Does not handle optional passages, such as John 7:53-8:11, or Mark 16:9-20.
def isOptional(ref):
#   return ref in { 'MAT 17:21', 'MAT 18:11', 'MAT 23:14', 'MRK 7:16', 'MRK 9:44', 'MRK 9:46', 'MRK 11:26', 'MRK 15:28', 'MRK 16:9', 'MRK 16:12', 'MRK 16:14', 'MRK 16:17', 'MRK 16:19', 'LUK 17:36', 'LUK 23:17', 'JHN 5:4', 'JHN 7:53', 'JHN 8:1', 'JHN 8:4', 'JHN 8:7', 'JHN 8:9', 'ACT 8:37', 'ACT 15:34', 'ACT 24:7', 'ACT 28:29', 'ROM 16:24' }
    return ref in { 'MAT 17:22', 'MAT 18:12', 'MAT 23:15', 'MRK 7:17', 'MRK 9:45', 'MRK 9:47', 'MRK 11:27', 'MRK 15:29', 'LUK 17:37', 'LUK 23:18', 'JHN 5:5', 'ACT 8:38', 'ACT 15:35', 'ACT 24:8', 'ACT 28:30', 'ROM 16:25' }

def isPoetry(token):
    return token.isQ() or token.isQ1() or token.isQA() or token.isSP()

def isIntro(token):
    return token.is_is1() or token.is_ip() or token.is_iot() or token.is_io1()

def isCharacterFormatting(token):
    # RJH added this 16May2019 -- doesn't contain all character format codes yet
    return token.isADDS() or token.isADDE() \
        or token.isNDS() or token.isNDE() \
        or token.isWJS() or token.isWJE() \
        or token.isBDS() or token.isBDE() \
        or token.isBDITS() or token.isBDITE() \
        or token.isSCS() or token.isSCE() \
        or token.isCAS() or token.isCAE() \
        or token.isVAS() or token.isVAE()

def isTextCarryingToken(token):
    """
    NOTE: RJH -- how can this work when it contains both newline markers
                    and character (e.g., footnote) markers???
            Also, does it check if they actually contain text?
    """
    return token.isB() or token.isM() or token.isD() or isFootnote(token) \
        or isCrossRef(token) or isPoetry(token) or isIntro(token) \
        or isCharacterFormatting(token) # RJH added this (for \wj fields, etc.)


def take(token):
    state = State()
    if isFootnote(token):
        state.addText()     # footnote suffices for verse text
    if state.needText() and not token.isTEXT() and not isTextCarryingToken(token):
        # print(f"EMPTY VERSE {state.referenceString}: {token}")
        report_error(f"{state.referenceString} - Empty verse\n")
    if token.isID():
        takeID(token.value)
    elif token.isIDE():
        takeIDE(token.value)
    elif token.isUSFM():
        takeUSFM(token.value)
    elif token.isH():
        takeH(token.value)
    elif token.isTOC1():
        takeTOC1(token.value)
    elif token.isTOC2():
        takeTOC2(token.value)
    elif token.isTOC3():
        takeTOC3(token.value)
    elif token.isMT() or token.isMT1():
        takeMT(token.value)
    elif token.isCL():
        takeCL(token.value)
    elif token.isC():
        verifyVerseCount()  # for the preceding chapter
        takeC(token.value)
    elif token.isP() \
    or token.isPI() or token.isPI1() or token.isPI2() \
    or token.isPC() or token.isNB():
        takeP()
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isQ() or token.isQ1() or token.isQ2() or token.isQ3():
        state.addQuote()
    elif token.isM() or token.isMI():
        state.addMargin()
    elif token.isUnknown():
        takeUnknown(state, token)
    global lastToken
    lastToken = token
# end of take(token) function


def verify_contents_quiet(unicodestring, filename, book_code, lang_code):
    """
    This is called by the USFM linter.
    """
    global error_log
    error_log = []  # enable error logging
    state = State()
    state.reset_all()  # clear out previous values
    state.set_book_code(book_code)
    state.setLanguageCode(lang_code)
    verifyChapterAndVerseMarkers(unicodestring, book_code)
    for token in parseUsfm.parseString(unicodestring):
        take(token)
    verifyNotEmpty(filename, book_code)
    verifyIdentification(book_code)
    verifyVerseCount()  # for last chapter
    verifyChapterCount()
    errors = error_log
    error_log = None  # turn error logging back off
    return errors, state.ID
# end of verify_contents_quiet function
