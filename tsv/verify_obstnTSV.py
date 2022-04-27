# -*- coding: utf-8 -*-
# To verify proper format of each row in a TSV OBS-tN file.
# Column descriptions:
#   1. "Reference" -- story:paragraph  e.g. 1:2 is the second paragraph in story 1.
#   2. "ID" -- unique 4-character ID
#   3. "Tags" (ignored) -- is "title" for paragraph 0 and blank for other paragraphs
#   4. "SupportReference" -- should match an RC link the note (last column) but without the square brackets
#   5. "Quote" -- note title, becomes an H1 heading in a markdown file
#   6. "Occurrence" (ignored) -- always 1
#   7. "Note" -- note text
# The script checks each row for the following:
#   Wrong number of columns, should be 7 per row.
#   Non-sequential story numbers
#   Non-sequential paragraph numbers within each story
#   Invalid story number (must be 1-50).
#   ASCII, non-ASCII in note title and note
#   SupportReference value does not match any TA articles referenced in note.
#   Note (column 7) values. Some of these conditions are correctable with tsv_cleanup.py.
#      Blank note.
#      ASCII content only (likely untranslated).
#      Unmatched parentheses and brackets.
#      Hash marks.

# Globals
source_dir = r'C:\DCS\Spanish-es-419\OBSTN'
language_code = 'es-419'
ta_dir = r'C:\DCS\English\en_ta.v24'    # Use Target language tA if available
obs_dir = r'C:\DCS\Spanish-es-419\es-419_obs.STR\content'

suppress6 = False    # Suppress warnings about invalid OBS links
suppress9 = False    # Suppress warnings about ASCII content.
suppress11 = False    # Suppress warnings about unbalanced parentheses
suppress12 = False    # Suppress warnings about markdown syntax in notes
suppress14 = True    # Suppress warnings about mismatched TA page references (Only report total number)
suppress15 = False    # Suppress warnings each and every blank note (Only report number of blank notes.)

if language_code in {'hr','id','nag','pmy','sw','en','es-419'}:    # Expect ASCII content with these languages
    suppress9 = True

nChecked = 0
rowno = 0
issuesfile = None

import sys
import os
import io
import tsv
import re
refcheck_re = re.compile(r'([0-9]+):([0-9]+) *$')

class State:        # State information about a single note (a single column 9 value)
    def setPath(self, path ):
        State.path = path
        State.id = "ID"
        State.story = 1
        State.paragraph = 0
        State.addRow(self, None)
        State.nBlanks = 0
        State.nMismatched = 0
        State.allrefs = set()

    def addRow(self, locator):
        State.prevstory = State.story
        State.prevparagraph = State.paragraph
        if locator:
            State.locator = locator
            if ref := refcheck_re.match(locator[0].strip()):
                State.story = int(ref.group(1))
                State.paragraph = int(ref.group(2))
            State.id = locator[1]
        State.leftparens = 0
        State.rightparens = 0
        State.leftbrackets = 0
        State.rightbrackets = 0
        State.leftcurly = 0
        State.rightcurly = 0
        State.underscores = 0

    def countParens(self, line):
        if not re.search(r'[0-9]\)', line):   # right parens used in list items voids the paren matching logic for that line
            State.leftparens += line.count("(")
            State.rightparens += line.count(")")
        State.leftbrackets += line.count("[")
        State.rightbrackets += line.count("]")
        State.leftcurly += line.count("{")
        State.rightcurly += line.count("}")
        State.underscores += line.count('_')

    def incrementBlanks(self):
        State.nBlanks += 1
    def incrementMismatched(self):
        State.nMismatched += 1

def reportParens():
    state = State()
    if not suppress11 and state.leftparens != state.rightparens:
        reportError("Parentheses are unbalanced (" + str(state.leftparens) + ":" + str(state.rightparens) + ")")
    if state.leftbrackets != state.rightbrackets:
        reportError("Left and right square brackets are unbalanced (" + str(state.leftbrackets) + ":" + str(state.rightbrackets) + ")")
    if state.leftcurly != state.rightcurly:
        reportError("Left and right curly braces are unbalanced (" + str(state.leftcurly) + ":" + str(state.rightcurly) + ")")
    if state.underscores % 2 != 0:
        reportError("Unmatched underscores")

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def issuesFile():
    global issuesfile
    if not issuesfile:
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(source_dir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
            else:
                os.remove(path)
        issuesfile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesfile

# Writes error message to stderr and to issues.txt.
# locater is the first two columns of a row
def reportError(msg, reportlocation = True):
    global rowno
    state = State()
    shortpath = shortname(state.path)
    if reportlocation:
        issue = f"{shortpath}: {state.story}:{state.paragraph} ID=({state.id}), row {rowno}: {msg}.\n"
    else:
        issue = f"{shortpath}: {msg}.\n"
    sys.stderr.write(issue)
    issuesFile().write(issue)

def reportSuppression(msg):
    if not msg:
        str = "\n"
    else:
        str = f"Warnings about {msg} were suppressed.\n"
    sys.stderr.write(str)
    issuesFile().write(str)

def reportSuppressions():
    reportSuppression("")
    if suppress6:
        reportSuppression("invalid OBS links")
    if suppress9:
        reportSuppression("ASCII content")
    if suppress11:
        reportSuppression("unbalanced parentheses")
    if suppress12:
        reportSuppression("markdown syntax in notes")
    # if suppress14:
        # reportSuppression("mismatched SupportReference and TA page references")

# Collect a list of all story:paragraph references
def preprocess(data):
    state = State()
    for row in data:
        str = row[0].strip()
        if refcheck_re.match(str):
            state.allrefs.add(str)

# Looks for :en: and rc://en in the line
def checkUnconvertedLinks(line):
    if line.find('figs_') >= 0:
        reportError("Underscore in tA reference")
    if language_code != 'en':
        if line.find(':en:') >= 0 or line.find('rc://en/') >= 0:
            reportError("Unconverted language code")


tapage_re = re.compile(r'\[\[.*?/ta/man/(.*?)]](.*)', flags=re.UNICODE)
talink_re = re.compile(r'(\(rc://[\*\w\-]+/ta/man/)(.+?/.+?)(\).*)', flags=re.UNICODE)
obsJpg_re = re.compile(r'https://cdn.door43.org/obs/jpg/360px/obs-en-[0-9]+\-[0-9]+\.jpg$', re.UNICODE)

# Parse tA manual page names from the line.
# Verifies the existence of the referenced page.
def checkTALinks(line, where):
    found = False
    page = tapage_re.search(line)
    while page:
        found = True
        manpage = page.group(1)
        path = os.path.join(ta_dir, manpage)
        if not os.path.isdir(path):
            reportError(f"invalid tA page in {where}: {manpage}")
        page = tapage_re.search(page.group(2))

    if not found:
        link = talink_re.search(line)
        while link:
            found = True
            manpage = link.group(2)
            manpage = manpage.replace('_', '-')
            path = os.path.join(ta_dir, manpage)
            if path[-3:].lower() == '.md':
                path = path[:-3]
            if not os.path.isdir(path):
                reportError("invalid tA link: " + manpage)
            link = talink_re.search(link.group(3))
    return found

# Verify tA links, note links, OBS links and passage links.
def checkLinks(line):
    checkUnconvertedLinks(line)
    foundTA = checkTALinks(line, "Note")
    foundOBS = checkOBSLinks(line)
#    if not foundOBS:        # because note links match OBS links
#        foundTN = checkNoteLinks(line)
    # if not foundTA and not foundOBS:  # and not foundTN:    # because passagelink_re could match any of these
    checkInternalLinks(line)
    checkReversedLinks(line)

obslink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/obs/)(\d+)(/\d+)(.*)', flags=re.UNICODE)

# Returns True if any OBS links were found and checked.
def checkOBSLinks(line):
    found = False
    link = obslink_re.search(line)
    while link:
        found = True
        if link.group(2) != language_code:
            reportError("invalid language code in OBS link")
        elif not suppress6:
            obsPath = os.path.join(obs_dir, link.group(4)) + ".md"
            if not os.path.isfile(obsPath):
                reportError("invalid OBS link: " + link.group(1) + link.group(2) + link.group(3) + link.group(4) + link.group(5))
        link = obslink_re.search(link.group(6))
    return found

# notelink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/)(\w\w\w/\d+/\d+)(.*)', flags=re.UNICODE)

# Returns True if any notes links were found.
# Note links currently are not rendered on live site as links.
#def checkNoteLinks(line):
#    found = False
#    notelink = notelink_re.search(line)
#    while notelink:
#        found = True
#        if notelink.group(2) != language_code:
#            reportError("invalid language code in note link")
#        else:
#            notePath = os.path.join(tn_dir, notelink.group(4)) + ".md"
#            notePath = os.path.normcase(notePath)
#            if not os.path.isfile(notePath):
#                reportError("invalid note link: " + notelink.group(1) + notelink.group(2) + notelink.group(3) + notelink.group(4))
#        notelink = notelink_re.search(notelink.group(5))
#
#    if notelink:
#        found = True
#    return found

# passagelink_re = re.compile(r'] ?\(([^\)]*?)\)(.*)', flags=re.UNICODE)    # [ref](link)
internallink_re = re.compile(r'] ?\(([^\)/]+)/([^\)]+)\)(.*)', flags=re.UNICODE)    # [ref](story/pp)

# Internal links point to another note in the same OBS-tN file.
# If there is a match to internallink_re, group(1) is the URL or other text between parens
# and passage.group(2) is everything after the right paren to the end of line.
def checkInternalLinks(line):
    state = State()
    link = internallink_re.search(line)
    while link:
        referent = f"{link.group(1).lstrip('0')}:{link.group(2).lstrip('0')}"
        if not referent in state.allrefs:
            reportError("invalid internal link: " + referent)
        link = internallink_re.search(link.group(3))

reversedlink_re = re.compile(r'\(.*\) *\[.*\]', flags=re.UNICODE)

def checkReversedLinks(line):
    if reversedlink_re.search(line):
        reportError("Reversed link syntax")

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

unexpected_re = re.compile(r'\([^\)\[]*\]', re.UNICODE)         # ']' after left paren
unexpected2_re = re.compile(r'\[[^\]\(]*\)', re.UNICODE)         # ')' after left square bracket

# Column 7 (Note) verification
def verifyNote(note, id):
    state = State()

    if len(note) == 0:
        state.incrementBlanks()
        if not suppress15:
            reportError("blank note")
    state.countParens(note)
    if note.find("<!--") != -1 or note.find("&nbsp;") != -1 or note.find("<b>") != -1 or note.find("<span") != -1:
        reportError("html code in note")
    if "#" in note:
        reportError('hash symbol in note')
    checkLinks(note)
    reportParens()
    if len(note) > 0 and note.isascii() and not suppress9:
        reportError("No non-ASCII content in note")
    if unexpected_re.search(note):
        reportError("found ']' after left paren")
    if unexpected2_re.search(note):
        reportError("found ')' after left square bracket")

def checkColHeader(value, expected, col):
    if value != expected:
        reportError("Invalid column " + str(col) + " header: \"" + value + "\"")

# Reports an error if there is anything wrong with the first row in the TSV file.
# That row contains nothing but column headings.
def checkHeaderRow(row):
    checkColHeader(row[0], "Reference", 1)
    checkColHeader(row[1], "ID", 2)
    checkColHeader(row[2], "Tags", 3)
    checkColHeader(row[3], "SupportReference", 4)
    checkColHeader(row[4], "Quote", 5)
    checkColHeader(row[5], "Occurrence", 6)
    checkColHeader(row[6], "Note", 7)

idcheck_re = re.compile(r'[^0-9a-z]')

# Checks the specified non-header row values.
# The row must have 7 columns or this function will fail.
def checkRow(row):
    state = State()

    # Check Reference column
    if not refcheck_re.search(row[0]):
        reportError("Invalid Reference value: " + row[0])
    if state.story < 1 or state.story < state.prevstory or state.story > 50:
        reportError("Invalid story number in Reference column: " + row[0])
    if state.story == state.prevstory and state.paragraph < state.prevparagraph:
        reportError("Invalid paragraph number in Reference column: " + row[0])

    # Check ID
    if len(row[1]) != 4 or idcheck_re.search(row[1]):
        reportError("Invalid ID: " + row[1])

    # Check SupportReference
    if row[3]:
        if not row[3].isascii():
            reportError("Non-ascii SupportReference value (column 4)")
        else:
            checkTALinks(row[3], "SupportReference")
            if not row[3] in row[6]:
                if not suppress14:
                    reportError("SupportReference value does not match any tA articles mentioned in note")
                state.incrementMismatched()

    # Check Quote column
    notetitle = row[4].strip()
    if len(notetitle) == 0:
        state.incrementBlanks()
        if not suppress15:
            reportError("Blank quote (column 5)")
    elif notetitle.isascii() and not suppress9:
        reportError("Invalid (ASCII) Quote (column 5)")
    # Check note itself
    verifyNote(row[6].strip(), row[1])

# Processes the rows in a single TSV file.
def verifyFile(path):
    global story
    global paragraph
    global rowno
    state = State()
    state.setPath(path)

    rowno = 0
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows).
    preprocess(data)
    for row in data:
        rowno += 1
        nColumns = len(row)
        if nColumns > 1:
            if nColumns == 7:
                if rowno == 1:
                    checkHeaderRow(row)
                    state.addRow(row[0:2])
                    story = 1
                    paragraph = 0
                else:
                    if row[0:2] == state.locator:
                        reportError("duplicate ID: " + row[1])
                    state.addRow(row[0:2])
                    checkRow(row)
            else:
                reportError(f"Wrong number of columns ({nColumns})")
                if refcheck_re.match(row[0]) and len(row[1]) == 4 and not idcheck_re.search(row[1]):
                    state.addRow(row[0:2])
        else:
            state.addRow(None)
            reportError(f"Wrong number of columns ({nColumns})")
    if state.nBlanks > 0:
        reportError("has " + str(state.nBlanks) + " blank notes or quotes", False)
    if state.nMismatched > 0:
        reportError(str(state.nMismatched) + " SupportReference values are not matched by TA articles in the Note", False)

def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path) and path[0] != ".":
            verifyDir(path)
        elif os.path.isfile(path) and f.endswith(".tsv"):
            verifyFile(path)
            sys.stdout.flush()
            global nChecked
            nChecked += 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        verifyDir(source_dir)
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        verifyFile(path)
        nChecked = 1
    else:
        sys.stderr.write("Folder not found: " + source_dir + '\n')

    print("Done. Checked " + str(nChecked) + " files.\n")
    if issuesfile:
        reportSuppressions()
        issuesfile.close()
    else:
        print("No issues found.")
