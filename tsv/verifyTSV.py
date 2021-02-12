# -*- coding: utf-8 -*-
# Python 3 script for verifying proper format of each row in a TSV tN file.
# In a TSV file, column 9 (OccurrenceNote) corresponds to a single tN file in markdown format.
# Within that field line breaks are coded as <br>, not newline characters.
# A newline terminates the entire row.
# The script checks each row for the following:
#   Wrong number of columns, should be 9 per row.
#   Non-sequential chapter numbers (non-sequential verse numbers are permitted).
#   Invalid verse number (0).
#   ASCII, non-ASCII in each column.
#   OccurrenceNote (column 9) values. Some of these conditions are correctable with tsv_cleanup.py.
#      ASCII content only.
#      Unmatched parentheses and brackets.
#      Missing space after hash mark(s).
#      Double quotes enclosing the OccurrenceNote field.
#      Leading spaces before markdown headers.
# A lot of these checks are done by tsv2rc.py as well.

# Globals
source_dir = r'C:\DCS\Marathi\TN\mr_tn_65-3JN.tsv'
language_code = 'mr'
source_language = 'en'         # The language that the notes are translated from, usually en
#ta_dir = r'C:\DCS\English\en_tA.v13'    # English tA
ta_dir = r'C:\DCS\Marathi\mr_ta.STR'    # Use Target language tA if available
#obs_dir = r'C:\DCS\English\en_obs\content'    # should end in 'content'
obs_dir = r'C:\DCS\Kannada\kn_obs\content'

suppress1 = False    # Suppress warnings about text before first heading and TA page references in headings
suppress2 = False    # Suppress warnings about blank headings
suppress3 = False    # Suppress warnings about markdown list syntax
suppress4 = False    # Suppress warnings about closed headings
suppress5 = True     # Suppress warnings about invalid passage links (don't know how to validate these with TSV)
suppress6 = False    # Suppress warnings about invalid OBS links
suppress7 = False    # Suppress warnings about file starting with blank line
suppress9 = False    # Suppress warnings about ASCII content in column 9
suppress10 = False   # Suppress warnings about heading levels
suppress11 = True    # Suppress warnings about unbalanced parentheses
suppress12 = False    # Suppress warnings about markdown syntax in 1-line notes
suppress13 = True    # Suppress warnings about multiple lines in non-intro notes
if language_code in {'hr','id','nag','pmy','sw','en'}:    # Expect ASCII content with these languages
    suppress9 = True

nChecked = 0
book = None
chapter = 0
rowno = 0
issuesfile = None

# Markdown line types
HEADING = 1
BLANKLINE = 2
TEXT = 3
LIST_ITEM = 4
ORDEREDLIST_ITEM = 5

import sys
import os
import io
import re
import tsv

listitem_re = re.compile(r'[ \t]*[\*\-][ \t]')
olistitem_re = re.compile(r'[ \t]*[0-9]+\. ')
badolistitem_re = re.compile(r'[ \t]*[0-9]+[\)]')
badheading_re = re.compile(r' +#')

class State:        # State information about a single note (a single column 9 value)
    def setPath(self, path ):
        State.path = path
        State.addRow(self, None)

    def addRow(self, locator):
#        State.key = key             # "<ID>.<verse>.<chapter>"  only needed if referencing English notes
        State.locator = locator     # [ <book>, <chapter>, <verse>, <ID> ]
        State.md_lineno = 0
        State.headingcount = 0
        State.textcount = 0
        State.prevheadinglevel = 0
        State.currheadinglevel = 0
        State.prevlinetype = None
        State.currlinetype = None
        State.linetype = []
        State.reported1 = False
        State.reported2 = False
        State.leftparens = 0
        State.rightparens = 0
        State.leftbrackets = 0
        State.rightbrackets = 0
        State.leftcurly = 0
        State.rightcurly = 0
        State.underscores = 0
        State.ascii = True      # In column 9 only
        State.nerrors = 0
    
    def addSimpleNote(self, note):
        State.addLine(self, note)
        State.md_lineno = 0
    
    def addLine(self, line):
        State.prevlinetype = State.currlinetype
        State.md_lineno += 1
        if line and (line[0] == '#' or badheading_re.match(line)):
            State.currlinetype = HEADING
            State.headingcount += 1
            State.prevheadinglevel = State.currheadinglevel
            State.currheadinglevel = line.count('#', 0, 5)
            State.reported2 = False
        elif not line or len(line.strip()) == 0:
            State.currlinetype = BLANKLINE
        elif listitem_re.match(line):
            State.currlinetype = LIST_ITEM
            if State.prevlinetype in {HEADING,BLANKLINE}:
                State.textcount += 1
        elif olistitem_re.match(line) or badolistitem_re.match(line):
            State.currlinetype = ORDEREDLIST_ITEM
            if State.prevlinetype in {HEADING,BLANKLINE}:
                State.textcount += 1
        else:
            State.currlinetype = TEXT
            State.textcount += 1
        State.linetype.append(State.currlinetype)
        if State.ascii and not line.isascii():
            State.ascii = False
    
    # Resets markdown line number to indicate end of line by line checking
    def closeNote(self):
        State.md_lineno = 0     # impacts error message format

    def countParens(self, line):
        if not re.search(r'[0-9]\)', line):   # right parens used in list items voids the paren matching logic for that line
            State.leftparens += line.count("(")
            State.rightparens += line.count(")")
        State.leftbrackets += line.count("[")
        State.rightbrackets += line.count("]")
        State.leftcurly += line.count("{")
        State.rightcurly += line.count("}")
        State.underscores += line.count('_')
        
    def reportedError(self):
        State.nerrors += 1

    def report1(self):
        State.reported1 = True
    def report2(self, report=True):
        State.reported2 = report

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
# locater is the first four columns of a row
def reportError(msg):
    global rowno
    state = State()
    shortpath = shortname(state.path)
    locater = state.locator     # the first four columns of a row
    id = ""
    if locater:
        id = locater[3]
        if len(id) > 8:
            id = id[0:8] + "..."
    if locater and len(locater) > 3:
        if state.md_lineno > 0:
            issue = shortpath + ": " + locater[0] + " " + locater[1] + ":" + locater[2] + " ID=(" + id + "), row " + str(rowno) + "." + str(state.md_lineno) + ": " + msg + ".\n"
        else:
            issue = shortpath + ": " + locater[0] + " " + locater[1] + ":" + locater[2] + " ID=(" + id + "), row " + str(rowno) + ": " + msg + ".\n"
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
        reportSuppression("Warnings about text before first heading and TA page references in headings were suppressed")
    if suppress2:
        reportSuppression("Warnings about blank headings were suppressed")
    if suppress3:
        reportSuppression("Warnings about markdown list syntax were suppressed")
    if suppress4:
        reportSuppression("Warnings about closed headings were suppressed")
    if suppress6:
        reportSuppression("Warnings about invalid OBS links were suppressed")
    if suppress7:
        reportSuppression("Warnings about file starting with blank line were suppressed")
    if suppress9:
        reportSuppression("Warnings about ASCII content in column 9 were suppressed")
    if suppress10:
        reportSuppression("Warnings about heading levels were suppressed")
    if suppress11:
        reportSuppression("Warnings about unbalanced parentheses were suppressed")
    if suppress12:
        reportSuppression("Warnings about markdown syntax in 1-line notes were suppressed")
    if suppress13:
        reportSuppression("Warnings about multiple lines in non-intro notes were suppressed")

# This function, instead of take(), checks most notes.
# Most notes consist of a single line with no headings or lists.
def checkSimpleNote(note):
    state = State()
    state.countParens(note)
    state.addSimpleNote(note)
    if state.currlinetype in {HEADING, LIST_ITEM, ORDEREDLIST_ITEM} and not suppress12:
        reportError("Simple (1-line) note contains markdown syntax")
    elif state.currlinetype == BLANKLINE:
        reportError("Blank note")
    if note.find("<!--") != -1 or note.find("&nbsp;") != -1 or note.find("<b>") != -1:
        reportError("html code")

blankheading_re = re.compile(r'#+$')
heading_re = re.compile(r'#+[ \t]')
closedHeading_re = re.compile(r'#+[ \t].*#+[ \t]*$', re.UNICODE)
badclosedHeading_re = re.compile(r'#+[ \t].*[^# \t]#+[ \t]*$', re.UNICODE)  # closing hash without preceding space
toobold_re = re.compile(r'#+[ \t]+[\*_]', re.UNICODE)        # unwanted formatting in headings
headjam_re = re.compile(r'#[^# ]', re.UNICODE)          # no space after hash mark

def take(line):
    state = State()
    state.countParens(line)
    state.addLine(line)
    if not line:
        if state.md_lineno == 1 and not suppress7:
            reportError("starts with blank line")
        return
#    if state.prevlinetype == HEADING and state.currlinetype != BLANKLINE and state.currlinetype != HEADING:
#        reportError("missing line break after heading")
    if state.currlinetype != HEADING:
        if state.headingcount == 0 and not suppress1 and not state.reported1:
            reportError("has text before first heading")
            state.report1()
#    if state.currlinetype == TEXT and not state.reported2:
#        if state.md_lineno >= 5 and state.prevlinetype == BLANKLINE and state.linetype[state.md_lineno-3] in {TEXT,LIST_ITEM,ORDEREDLIST_ITEM}:
#            reportError("should be a header here, or there is some other formatting problem")
#            state.report2()
    if state.currlinetype == HEADING:
        if state.md_lineno > 1 and state.prevlinetype != BLANKLINE and state.prevlinetype != HEADING:
            reportError("missing blank line before heading")
        if badheading_re.match(line):
            reportError("space(s) before heading")
        elif closedHeading_re.match(line):
            if not suppress4:
                reportError("closed heading")
            if badclosedHeading_re.match(line):
                reportError("no space before closing hash mark")
        elif not suppress2 and blankheading_re.match(line):
            reportError("blank heading")
        elif len(line) > 1 and not heading_re.match(line):
            reportError("missing space after hash symbol(s)")
        if not suppress10:
            if state.currheadinglevel > state.prevheadinglevel + 1:
                if state.prevheadinglevel > 0:
                    reportError("heading level incremented by more than one level")
    if state.currlinetype == LIST_ITEM and not suppress3:
        if state.prevlinetype in { TEXT, HEADING }:
            reportError("invalid list syntax")
        i = state.md_lineno - 1
        if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == LIST_ITEM:
            reportError("invalid list style")
    if state.currlinetype == ORDEREDLIST_ITEM and not suppress3:
        if badolistitem_re.match(line):
            reportError("item number not followed by period")
        if olistitem_re.match(line):
            if state.prevlinetype in { TEXT, HEADING }:
                reportError("missing blank line before ordered list")
            i = state.md_lineno - 1
            if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == ORDEREDLIST_ITEM:
                reportError("invalid ordered list style")
    if line.find('# #') != -1:
        reportError('Heading syntax error: # #')
    if headjam_re.search(line):
        reportError("Missing space after hash mark(s)")
    if len(line) > 2 and line[0:2] == '% ':
        reportError("% used to mark a heading")
    if line.find("<!--") != -1 or line.find("&nbsp;") != -1 or line.find("o:p") != -1:
        reportError("html code")

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
# notelink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/)(\w\w\w/\d+/\d+)(.*)', flags=re.UNICODE)
passagelink_re = re.compile(r']\(([^\)]*?)\)(.*)', flags=re.UNICODE)
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

# Verify tA links, note links, OBS links and passage links.
def checkLinks(line):
    checkUnconvertedLinks(line)
    foundTA = checkTALinks(line)
    foundOBS = checkOBSLinks(line)
#    if not foundOBS:        # because note links match OBS links
#        foundTN = checkNoteLinks(line)
    if not foundTA and not foundOBS:  # and not foundTN:    # because passagelink_re could match any of these
        if not suppress5:
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

# Column 9 (OccurrenceNote) verification
def verifyNote(note, verse):
    state = State()

    lines = note.split("<br>")
    if len(lines) > 1:
        if verse != "intro" and not suppress13:
            reportError("Multiple lines in non-intro note")
        for line in lines:
            line = line.rstrip()
            take(line)
            checkLinks(line)
    if len(lines) <= 1 and verse != "intro":       # 1-line  note
        checkSimpleNote(note)
        checkLinks(note)
    state.closeNote()
    reportParens()
    if state.ascii and not suppress9:
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
def checkHeader(row):
    checkColHeader(row[0], "Book", 1)
    checkColHeader(row[1], "Chapter", 2)
    checkColHeader(row[2], "Verse", 3)
    checkColHeader(row[3], "ID", 4)
    checkColHeader(row[4], "SupportReference", 5)
    checkColHeader(row[5], "OrigQuote", 6)
    checkColHeader(row[6], "Occurrence", 7)
    checkColHeader(row[7], "GLQuote", 8)
    checkColHeader(row[8], "OccurrenceNote", 9)

def verifyGLQuote(quote, verse):
    if verse == "intro":
        if len(quote) != 0:
            reportError("Unexpected (non-empty) value in GLQuote column of intro note")
    else:
        if len(quote) > 0 and source_language not in {'en'}:
            if quote.isascii():
                reportError("ASCII GLQuote (column 8)")

idcheck_re = re.compile(r'[^0-9a-z]')

# Checks the specified non-header row values.
# The row must have 9 columns or this function will fail.
def checkRow(row):
    global book
    global chapter

    if not book:
        book = row[0]
    if row[0] != book:
        reportError("Bad book name (" + row[0] + ")")

    # Establish chapter number
    if row[1] != 'front':
        try:
            c = int(row[1])
            if c == chapter + 1:
                chapter = c
            elif c != chapter:
                reportError("Non-sequential chapter number")
        except ValueError as e:
            c = 0
            reportError("Non-numeric chapter number")
    # Establish verse
    if row[2] == 'intro':
        verse = 0
    else:
        try:
#           Based on 10/29/19 discussion on Zulip, the verse order in TSV file is not important.
            verse = int(row[2])
            if verse < 1 or verse > 176:
                reportError("Invalid verse number (" + str(verse) + "). Probably should be \"intro\"")
        except ValueError as e:
            reportError("Non-numeric verse number")

    if len(row[3]) != 4 or idcheck_re.search(row[3]):
        reportError("Invalid ID")

    if not row[4].isascii():
        reportError("Non-ascii SupportReference value (column 5)")
    if len(row[5].strip()) > 0 and row[5].isascii():
        reportError("Invalid (ASCII) OrigQuote (column 6)")
    if row[6] not in {'0', '1', '2'}:
        reportError("Invalid Occurrence value (should be a small number): " + row[6])
    verifyGLQuote(row[7].strip(), row[2])
    verifyNote(row[8], row[2])


# Processes the rows in a single TSV file.
def verifyFile(path):
    global book
    global chapter
    global rowno
    state = State()
    state.setPath(path)

    rowno = 0
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows).
    heading = True
    for row in data:
        rowno += 1
        nColumns = len(row)
        if nColumns > 3:
#            try:
#                verse = int(row[2])
#            except ValueError as e:
#                verse = 0
#            key = tsv.make_key(row, [3,2,1])
            if nColumns == 9:
                if rowno == 1:
                    checkHeader(row)
                    state.addRow(row[0:4])
                    book = None
                    chapter = 0
#                    verse = 0
                else:
                    state.addRow(row[0:4])
                    checkRow(row)
            else:
                try:
                    if len(row[0]) == 3 and int(row[1]) > 0 and int(row[2]) > 0 and len(row[3]) == 4:
                        state.addRow(row[0:4])
                except ValueError as e:
                    verse = 0
                reportError("Wrong number of columns (" + str(nColumns) + ")")
        else:
#            key = row[0][0:3] + "..."
            state.addRow(None)
            reportError("Wrong number of columns (" + str(nColumns) + ")")

def verifyDir(dirpath):
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path) and path[-4:] != ".git":
            # It's a directory, recurse into it
            verifyDir(path)
        elif os.path.isfile(path) and f[-4:].lower() == '.tsv':
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
