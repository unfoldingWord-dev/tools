# -*- coding: utf-8 -*-
# This script converts plain text files containing books of the Bible to usfm files.
# The text files must be prepared to meet these conditions:
#    Each file contains a single book of the Bible, and no extraneous text.
#    The file names match XXX.txt, where XXX is the 3-character book id.
#    UTF-8 encoding is required.
#    The first line of each file contains the book title, with no other characters.
#    Chapter and verse numbers are in Arabic numerals (0-9).
#    Input text file does not contain USFM markers.
# The script performs these operations:
#    Populates the USFM headers based on the text file name and first line.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once if there are multiple books.
#    Reports failure when chapter 1 is not found, and other errors.
# The script does not mark chunks. If that is desired. run usfm2rc.py later.

import configreader
import usfm_verses
import re
import operator
import io
import os
import sys
import json
from pathlib import Path

numberstart_re = re.compile(r'([\d]{1,3})[ \n]', re.UNICODE)
projects = []
issues_file = None

# Entities
ID = 1
TITLE = 2
CHAPTER = 3
VERSE = 4
TEXT = 5
EOF = 6

class State:
    ID = ""
    data = ""
    title = ""
    chapter = 0
    verse = 0
    reference = ""
    lastRef = ""
    lastEntity = None
    neednext = ID
    priority = ID
    usfm_file = None
    missing_chapters = []

    # Resets state data for a new book
    def addID(self, id):
        global target_dir
        State.ID = id
        State.data = ""
        State.title = ""
        State.chapter = 0
        State.verse = 0
        State.missing_chapters = []
        State.lastRef = State.reference + "0"
        State.lastEntity = ID
        State.neednext = {TITLE}
        State.priority = TITLE
        State.usfm_file = io.open(makeUsfmPath(id), "tw", encoding='utf-8', newline='\n')

    def addTitle(self, title, lineno):
        if len(State.data):
            State.data += ' '
        State.data += title
        State.title += title
        State.lastEntity = TITLE
        State.neednext = {CHAPTER, TITLE}
        if lineno > 7:
            State.neednext = {CHAPTER}
        State.priority = CHAPTER

    def addChapter(self, nchap):
        State.data = ""
        State.chapter = nchap
        State.verse = 0
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(nchap) + ":"
        State.lastEntity = CHAPTER
        State.neednext = {VERSE}
        State.priority = VERSE

    def missingChapter(self, nchap):
        State.missing_chapters.append(nchap)

    # Adds the line of text as is without touching any other state
    # Supports texts where chapter labels or section headings are tagged: \cl or \s
    def addMarkedLine(self, text):
        State.data += "\n" + text

    def addVerse(self, vstr):
        State.data = ""
        State.verse = int(vstr)
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + vstr
        State.lastEntity = VERSE
        State.neednext = {TEXT}
        State.priority = TEXT

    def addText(self, text):
        if len(State.data) > 0:
            State.data += ' '
        text = text.lstrip(". ")   # lose period after preceding verse number
        State.data += text.strip()  # lose other leading and trailing white space
        if State.lastEntity != TEXT:
            State.neednext = {VERSE, CHAPTER, TEXT}
            State.priority = whatsNext(State.ID, State.chapter, State.verse)
            State.lastEntity = VERSE

    # Called when the end of file is reached
    def addEOF(self):
        State.usfm_file.close()
        State.lastRef = State.reference
        State.lastEntity = EOF
        State.neednext = {ID}
        State.priority = ID
        if State.chapter == 0:
            State.title = ""
            State.lastref = State.ID + " 0"

# Determines whether a verse or a chapter is expected next.
# Based on the current book, chapter and verse as specified by the arguments.
# Not all languages and translation follow the same versification scheme, however.
# Returns VERSE, CHAPTER, or EOF
def whatsNext(book, chapter, verse):
    if verse < usfm_verses.verseCounts[book]['verses'][chapter-1]:
        next = VERSE
    elif chapter < usfm_verses.verseCounts[book]['chapters']:
        next = CHAPTER
    else:
        next = EOF
    return next

vv_re = re.compile(r'([0-9]+)-([0-9]+)')

# cstr is the entire chapter label, often just the chapter number.
def takeChapter(cstr, nchap):
    state = State()
    if State.lastEntity == TITLE:
        writeHeader(state.usfm_file, state.ID, state.data)
    elif state.data:
        state.usfm_file.write(re.sub(" +", " ", state.data) + "\n")
    state.usfm_file.write("\\c " + str(nchap) + "\n")
    if len(cstr) > len(str(nchap)):
        state.usfm_file.write("\\cl " + cstr + "\n")
    state.addChapter(nchap)

vrange_re = re.compile(r'([0-9])+-([0-9]+)')

# vstr contains only the verse number, or a verse number range
def takeVerse(vstr):
    state = State()
    if state.data:
        state.usfm_file.write(re.sub(" +", " ", state.data) + "\n")
    if state.verse == 0:
        state.usfm_file.write("\\p\n")
    state.usfm_file.write("\\v " + vstr + " ")
    if range := vrange_re.search(vstr):
        state.addVerse(range.group(1))
        state.addVerse(range.group(2))
    else:
        state.addVerse(vstr)

def takeLine(line, lineno):
    state = State()
    if line.startswith(r'\cl ') or line.startswith(r'\s '):
        state.addMarkedLine(line)
    else:
        take(line, lineno)

# Handles the next bit of text, which may be a line or part of a line.
# Uses recursion to handle complex lines.
def take(s, lineno):
    state = State()
    if state.priority == EOF:
        state.priority = TEXT
    if state.priority == TITLE:
        state.addTitle(s, lineno)
    elif state.priority == CHAPTER:
        if hasnumber(s, state.chapter+1) >= 0 and len(s) < 25:    # may have to allow longer s
            takeChapter(s, state.chapter+1)
        elif TITLE in state.neednext:   # haven't reached chapter 1 yet
            state.addTitle(s, lineno)
        elif VERSE in state.neednext:
            (pretext, vv, remainder) = getvv(s, state.verse+1)
            if vv:
                if pretext:
                    take(pretext, lineno)
                takeVerse(vv)
                if remainder:
                    take(remainder, lineno)
            elif TEXT in state.neednext:
                state.addText(s)
        elif TEXT in state.neednext:
            state.addText(s)
        else:
            state.missingChapter(state.chapter+1)
    elif state.priority == VERSE:
        (pretext, vv, remainder) = getvv(s, state.verse+1)
        if not vv and state.verse+1 < usfm_verses.verseCounts[state.ID]['verses'][state.chapter-1]:
            (pretext, vv, remainder) = getvv(s, state.verse+2)
            missingVerse = f"{state.ID} {state.chapter}:{state.verse+1}"
            if vv:
                reportError(f"Skipping {missingVerse}.")
        if vv:
            if pretext:
                take(pretext, lineno)
            takeVerse(vv)
            if remainder:
                take(remainder, lineno)
        elif CHAPTER in state.neednext and hasnumber(s, state.chapter+1) >= 0:
            takeChapter(s, state.chapter+1)
        elif TEXT in state.neednext:
            state.addText(s)
        else:
            reportError("Expected verse not found. (" + state.reference + str(state.verse+1) + ", line " + str(lineno) + ")")
            if state.chapter > 0 and state.verse == 0:
                reportError(f"Is {state.ID} {state.chapter-1}:{state.chapter} missing?")
    elif state.priority == TEXT:
        (pretext, vv, remainder) = getvv(s, state.verse+1)
        if not vv and state.verse+1 < usfm_verses.verseCounts[state.ID]['verses'][state.chapter-1]:
            (pretext, vv, remainder) = getvv(s, state.verse+2)
            missingVerse = f"{state.ID} {state.chapter}:{state.verse+1}"
            if vv:
                reportError(f"Skipping {missingVerse}.")
        if vv:
            if pretext:
                state.addText(pretext)
            takeVerse(vv)
            if remainder:
                take(remainder, lineno)
        else:
            state.addText(s)
    else:
        reportError("Internal error at line " + str(lineno) + " in the text.")

# Extracts specified verse number or verse range beginning with that number.
# Return a (pretext, vv, remainder) tuple.
# If the specified verse is not found, returns ("","","")
def getvv(s, n):
    pos = hasnumber(s, n)
    if pos < 0:
        pretext = ""
        vv = ""
        remainder = ""
    else:
        pretext = s[0:pos]
        range = vrange_re.match(s[pos:])
        if range:
            vv = s[pos:range.end()]
        else:
            vv = str(n)
        if len(s) > pos + len(vv):
            remainder = s[pos + len(vv):]
        else:
            remainder = ""
    return (pretext, vv, remainder)


# Searches for the specified number in the string.
# Returns the position of the specified number in the string, or -1
def hasnumber(s, n):
    s = isolateNumbers(s)
    nstr = str(n)
    if s == nstr or s.startswith(nstr + " "):
        pos = 0
    elif s.endswith(" " + nstr):
        pos = len(s) - len(nstr)
    else:
        pos = s.find(" " + nstr + " ")
        if pos >= 0:
            pos += 1
    return pos

# Returns a string with all non-numeric characters changed to a space,
def isolateNumbers(s):
    t = ""
    for i in range(0,len(s)):
        if s[i] in "0123456789,.":
            t += s[i]
        else:
            t += ' '
    return t

# Writes error message to stderr and to issues.txt.
def reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        sys.stderr.write(State().reference + ": (Unicode...)\n")
    openIssuesFile().write(msg + "\n")

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns file pointer.
def openIssuesFile():
    global issues_file
    if not issues_file:
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(source_dir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issues_file = io.open(path, "tw", buffering=2048, encoding='utf-8', newline='\n')
    return issues_file

# idfield_re = re.compile(r'\\id ([\w][\w][\w])', re.UNICODE)

# Parses the book id from the file name.
# Return upper case bookId, or empty string on failure.
def getBookId(filename):
    bookId = None
    (id, ext) = os.path.splitext(filename)
    if ext == ".txt" and len(id) == 3 and id.upper() in usfm_verses.verseCounts:
        bookId = id.upper()
    else:
        reportError(f"Cannot identify book from file name: {filename}. Use XXX.txt where XXX is book ID.")
    return bookId

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    testament = 'nt'
    if usfm_verses.verseCounts[bookId]['sort'] < 40:
        testament = 'ot'
    project = { "title": bookTitle, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + makeUsfmFilename(bookId), "category": "[ 'bible-" + testament + "' ]" }
    projects.append(project)

# Writes list of projects converted to the specified file.
# The resulting file can be used as the projects section of manifest.yaml.
def dumpProjects(path):
    projects.sort(key=operator.itemgetter('sort'))

    manifest = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    manifest.write("projects:\n")
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    versification: ufw\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: " + p['category'] + "\n")
    manifest.close()

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Generates name for usfm file
def makeUsfmPath(bookId):
    global target_dir
    return os.path.join(target_dir, makeUsfmFilename(bookId))

    # Generates name for usfm file
def makeUsfmFilename(bookId):
    num = usfm_verses.verseCounts[bookId]['usfm_number']
    return num + '-' + bookId + '.usfm'

def writeHeader(usfmfile, bookId, bookTitle):
    usfmfile.write("\\id " + bookId + "\n\\ide UTF-8")
    usfmfile.write("\n\\h " + bookTitle)
    usfmfile.write("\n\\toc1 " + bookTitle)
    usfmfile.write("\n\\toc2 " + bookTitle)
    usfmfile.write("\n\\toc3 " + bookId.lower())
    usfmfile.write("\n\\mt1 " + bookTitle + "\n\n")

# This method is called to convert the specified file to usfm.
# Returns the book title.
def convertBook(path, bookId):
    sys.stdout.write("Converting: " + shortname(path) + "\n")
    sys.stdout.flush()
    state = State()
    state.addID(bookId)

    with io.open(path, "tr", 1, encoding='utf-8-sig') as input:
        lines = input.readlines()
    lineno = 0
    for line in lines:
        lineno += 1
        line = line.strip()
        if len(line) > 0:
            takeLine(line, lineno)
    if state.data and state.chapter > 0:
        state.usfm_file.write(re.sub(" +", " ", state.data) + '\n')
    state.addEOF()
    if state.missing_chapters:
        reportError("Chapter number " + str(state.chapter+1) + " not found in " + shortname(path))
    return state.title

def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path) and entry[0] != '.':
            convertFolder(path)
        elif os.path.isfile(path) and entry.endswith(".txt") and not entry.startswith("issues"):
            bookId = getBookId(entry)
            if bookId:
                title = convertBook(path, bookId)
            if bookId and title:
                appendToProjects(bookId, title)
            else:
                if not bookId:
                    reportError("Unable to identify " + shortname(path) + " as a Bible book.")
                elif not title:
                    reportError("Invalid file: " + shortname(path))

# Processes each directory and its files one at a time
if __name__ == "__main__":
    config = configreader.get_config(sys.argv, 'plaintext2usfm')
    if config:
        source_dir = config['source_dir']
        file = config['file']
        target_dir = config['target_dir']
        Path(target_dir).mkdir(exist_ok=True)

        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                bookId = getBookId(file)
                if bookId:
                    title = convertBook(path, bookId)
                if not title:
                    reportError(f"Invalid file, cannot convert: {path}")
            else:
                reportError(f"No such file: {path}")
        else:
            convertFolder(source_dir)
            if projects:
                dumpProjects( os.path.join(target_dir, "projects.yaml") )

        print("\nDone.")
