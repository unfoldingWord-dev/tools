# -*- coding: utf-8 -*-
# Python 3 script for verifying proper format of each row in a TSV tQ file.
# The Question and Response fields, line breaks are coded as <br>.
# A newline terminates the entire row.
# There may be more than one row (more than one Question/Response) for each verse.
# The script checks each row for the following:
#   Wrong number of columns, should be 7 per row.
#   Invalid Reference values.
#   Invalid ID values.
#   Missing value in these columns: Reference, ID, Question, Response
#   Response values.
#      Is blank.
#      ASCII content only (likely untranslated).
#      Unmatched parentheses and brackets.
#      Hash marks.
# A lot of these checks are done by tq_tsv2rc.py as well.
# Some of these conditions may be correctable with tq_tsv_cleanup.py.

# Globals
source_dir = r'C:\DCS\Telugu\TQ'
language_code = 'te'
#ta_dir = r'C:\DCS\English\en_tA.v13'    # English tA
ta_dir = r'C:\DCS\Marathi\mr_ta.STR'    # Use Target language tA if available
obs_dir = r'C:\DCS\Kannada\kn_obs\content'

suppress1 = False    # Suppress warnings about text before first heading and TA page references in headings
suppress2 = True    # Suppress warnings about questions and response being marked as headings or not
suppress6 = False    # Suppress warnings about invalid OBS links
suppress9 = False    # Suppress warnings about ASCII content in response.
suppress11 = False    # Suppress warnings about unbalanced parentheses
suppress12 = False    # Suppress warnings about markdown syntax in responses
suppress13 = False    # Suppress warnings about multiple lines in responses

if language_code in {'hr','id','nag','pmy','sw','en','es-419'}:    # Expect ASCII content with these languages
    suppress9 = True

nChecked = 0
rowno = 0
issuesfile = None

import sys
import os
import io
import re
import tsv
import usfm_verses

class State:        # State information about a single response (a single column 7 value)
    def setPath(self, path ):
        State.path = path
        State.bookid = None
        State.addRow(self, None)

    def setBookID(self, bookid):
        State.bookid = bookid

    def addRow(self, locator):
        State.locator = locator     # [ <reference>, <ID> ]
    
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
def reportError(msg):
    global rowno
    state = State()
    shortpath = shortname(state.path)
    locater = state.locator     # the first two columns of a row
    id = ""
    if locater:
        id = locater[1]
        if len(id) > 8:
            id = id[0:8] + "..."
    if locater and len(locater) > 1:
        issue = shortpath + ": " + locater[0] + " " + " ID=(" + id + "), row " + str(rowno) + ": " + msg + ".\n"
    else:
        issue = shortpath + ": row " + str(rowno) + ": " + msg + ".\n"
    sys.stderr.write(issue)
    issuesFile().write(issue)

def reportSuppression(msg):
    sys.stderr.write(msg + "\n")
    issuesFile().write(msg + "\n")

def reportSuppressions():
    reportSuppression("")
    if suppress1:
        reportSuppression("Warnings about text before question heading and TA page references in questions were suppressed")
    if suppress6:
        reportSuppression("Warnings about invalid OBS links were suppressed")
    if suppress9:
        reportSuppression("Warnings about ASCII content in column 9 were suppressed")
    if suppress11:
        reportSuppression("Warnings about unbalanced parentheses were suppressed")
    if suppress12:
        reportSuppression("Warnings about markdown syntax in responses were suppressed")
    if suppress13:
        reportSuppression("Warnings about multiple lines in responses were suppressed")

blankheading_re = re.compile(r'#+$')
heading_re = re.compile(r'#+[ \t]')
closedHeading_re = re.compile(r'#+[ \t].*#+[ \t]*$', re.UNICODE)
toobold_re = re.compile(r'#+[ \t]+[\*_]', re.UNICODE)        # unwanted formatting in headings

# Looks for :en: and rc://en in the line
def checkUnconvertedLinks(line):
    if line.find('figs_') >= 0:
        reportError("Underscore in tA reference")
    if language_code != 'en':
        if line.find(':en:') >= 0 or line.find('rc://en/') >= 0:
            reportError("Unconverted language code")


tapage_re = re.compile(r'\[\[.*?/ta/man/(.*?)]](.*)', flags=re.UNICODE)
talink_re = re.compile(r'(\(rc://[\*\w\-]+/ta/man/)(.+?/.+?)(\).*)', flags=re.UNICODE)
obslink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/obs/)(\d+)(/\d+)(.*)', flags=re.UNICODE)
# responselink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/)(\w\w\w/\d+/\d+)(.*)', flags=re.UNICODE)
obsJpg_re = re.compile(r'https://cdn.door43.org/obs/jpg/360px/obs-en-[0-9]+\-[0-9]+\.jpg$', re.UNICODE)
reversedlink_re = re.compile(r'\(.*\) *\[.*\]', flags=re.UNICODE)

# Parse tA manual page names from the link.
# Verifies the existence of the referenced page.
def checkTALinks(line):
    found = False
    page = tapage_re.search(line)
    while page:
        found = True
        if line and line[0] == '#' and not suppress1:
            reportError("tA page reference in heading")
        manpage = page.group(1)
        path = os.path.join(ta_dir, manpage)
        if not os.path.isdir(path):
            reportError("invalid tA page reference: " + manpage)
        page = tapage_re.search(page.group(2))

    if not found:
        link = talink_re.search(line)
        while link:
            found = True
            if line and line[0] == '#':
                reportError("tA link in heading")
            manpage = link.group(2)
            manpage = manpage.replace('_', '-')
            path = os.path.join(ta_dir, manpage)
            if path[-3:].lower() == '.md':
                path = path[:-3]
            if not os.path.isdir(path):
                reportError("invalid tA link: " + manpage)
            link = talink_re.search(link.group(3))
    return found          

# Verify tA links, response links, OBS links and passage links.
def checkLinks(line):
    checkUnconvertedLinks(line)
    foundTA = checkTALinks(line)
    foundOBS = checkOBSLinks(line)
    if not foundTA and not foundOBS:  # and not foundTN:    # because passagelink_re could match any of these
        checkPassageLinks(line)
    checkReversedLinks(line)

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

passagelink_re = re.compile(r']\(([^\)]*?)\)(.*)', flags=re.UNICODE)

# If there is a match to passageLink_re, passage.group(1) is the URL or other text between
# the parentheses,
# and passage.group(2) is everything after the right paren to the end of line.
def checkPassageLinks(line):
    state = State()
    passage = passagelink_re.search(line)
    while passage:
        referent = passage.group(1)
        referencedPath = os.path.join( os.path.dirname(state.path), referent )
        if not suppress5 and not os.path.isfile(referencedPath):
            reportError("invalid passage link: " + referent)
        passage = passagelink_re.search(passage.group(2))

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

# Verifies a question or response string
def verifyQR(str, type):
    if "<table" in str or "<span" in str or "nbsp" in str:
        reportError("HTML code in response")
    elif "<br>" in str and not suppress13:
        reportError("Multiple lines in " + type)
    if not re.search(r'[0-9]\)', str):   # right parens used in list items voids the paren matching logic for that line
        if str.count("(") != str.count(")"):
            reportError("Unmatched parens in " + type)
    if str.count("[") != str.count("]"):
        reportError("Unmatched square brackets in " + type)
    if str.count("{") != str.count("}"):
        reportError("Unmatched curly braces in " + type)
    if str.count("__") % 2 != 0:
        reportError("Unmatched double underscores in " + type)
    elif str.count('_') % 2 != 0:
        reportError("Unmatched underscores in " + type)
    if unexpected_re.search(str):
        reportError("found ']' after left paren in " + type)
    if unexpected2_re.search(str):
        reportError("found ')' after left square bracket in " + type)
    if "<!--" in str or "&nbsp"in str:
        reportError("html code in " + type)
    if len(str.strip()) == 0:
        reportError(type + " is empty")
    elif len(str.strip()) < 4:
        reportError(type + " appears to be truncated")
    elif str.isascii() and not suppress9:
        reportError("No non-ASCII content in " + type)

def verifyQuestion(question):
    if question.startswith("# ") and not suppress2:
        reportError("Question is marked as a heading")
    if question.count('#') > 1:
        reportError('Multiple # hash marks in Question')
    verifyQR(question[2:], "Question")

# Column 7 (Response) verification
def verifyResponse(response):
    if "#" in response:
        reportError("Hash mark found in Response")
    verifyQR(response, "Response")
    checkLinks(response)

def checkColHeader(value, expected, col):
    if value != expected:
        reportError("Invalid column " + str(col) + " header: \"" + value + "\"")

# Reports an error if there is anything wrong with the first row in the TSV file.
# That row contains nothing but column headings.
def checkHeader(row):
    checkColHeader(row[0], "Reference", 1)
    checkColHeader(row[1], "ID", 2)
    checkColHeader(row[2], "Tags", 3)
    checkColHeader(row[3], "Quote", 4)
    checkColHeader(row[4], "Occurrence", 5)
    checkColHeader(row[5], "Question", 6)
    checkColHeader(row[6], "Response", 7)

refcheck_re = re.compile(r'([0-9]+):([0-9]+) *$')
idcheck_re = re.compile(r'[^0-9a-z]')

# Checks the specified non-header row values.
# The row must have 9 columns or this function will fail.
def checkRow(row):
    chapter = None
    verse = None
    state = State()

    ref = refcheck_re.match(row[0])
    if ref:
        chapter = ref.group(1)
        verse = ref.group(2)
        if int(chapter) < 1 or int(chapter) > usfm_verses.verseCounts[state.bookid]['chapters']:
            reportError("Invalid chapter number in Reference: " + chapter)
        elif int(verse) < 0 or int(verse) > usfm_verses.verseCounts[state.bookid]['verses'][int(chapter)-1]:
            reportError("Invalid verse number in Reference: " + verse)
    if len(row[1]) != 4 or idcheck_re.search(row[1]):
        reportError("Invalid ID")
    question = row[5]
    if question.startswith("\\#"):
        question = question[1:]
    verifyQuestion(question)
    verifyResponse(row[6])

filename_re = re.compile(r'tq_([123A-Za-z][A-Za-z][A-Za-z]).tsv')

def verifyBookID(filename):
    fname = filename_re.match(filename)
    if fname:
        bookid = fname.group(1).upper()
        if bookid in usfm_verses.verseCounts.keys():
            State().setBookID(bookid)
        else:
            reportError("Invalid file name; book ID appears to be " + bookid)
    else:
        reportError("Invalid TSV file name")

# Processes the rows in a single TSV file.
def verifyFile(path, filename):
    state = State()
    state.setPath(path)
    verifyBookID(filename)
    if state.bookid:
        verifyRows(path)
    else:
        reportError("No more checks done on this file")

def verifyRows(path):
    global rowno
    rowno = 0
    state = State()
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows).
    for row in data:
        rowno += 1
        nColumns = len(row)
        if nColumns > 1:
            if nColumns == 7:
                if rowno == 1:
                    checkHeader(row)
                    state.addRow(row[0:2])
                else:
                    if state.locator and state.locator[1] == row[1]:
                        reportError("duplicate ID: " + row[1])
                    state.addRow(row[0:2])
                    checkRow(row)
            else:
                reportError("Wrong number of columns (" + str(nColumns) + ")")
        else:
            state.addRow(None)
            reportError("Wrong number of columns (" + str(nColumns) + ")")
    
def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path) and f[0] != ".":
            # It's a directory, recurse into it
            verifyDir(path)
        elif os.path.isfile(path) and f.endswith('.tsv'):
            verifyFile(path, f)
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
