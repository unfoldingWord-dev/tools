# -*- coding: utf-8 -*-

# Script for verifying proper Markdown format and links. Should check the following:
# Remove empty .md files.
# Blank line before and after header lines.
# Single space after hash on header line.
# No closed headers.
# Standard format of ordered lists (lists whose items are arranged on separate lines)
#      blank lines before and after list
#      period not paren after the number
#      space after period
# References are properly formed: [[rc://*/ta/man/translate/figs-hyperbole]]
# References in headings (warning)
# References to tA entries are valid.
# No html code: <!-- -->, &nbsp;
# Counts open and closed parentheses, open and closed brackets. (not markdown-specific)
# Reports files that have purely ASCII content.

# To-do -- check for others kinds of links in headings, not just TA links.

# Globals
language_code = 'hr'
resource_type = 'tn'
#ta_dir = r'E:\DCS\English\en_tA'    # English tA
ta_dir = r'E:\DCS\Croatian\hr_tA'    # Target language tA
obs_dir = r'E:\DCS\Spanish\es_obs\content'    # should end in 'content'
tn_dir = r'E:\DCS\Croatian\hr_tn'    # Target language tN, needed if note links are to be checked
nChecked = 0
nChanged = 0
sourceDir = ""
current_file = ""
issuesFile = None

suppress1 = False    # Suppress warnings about text before first heading
suppress2 = False    # Suppress warnings about blank headings
suppress3 = False    # Suppress warnings about item number not followed by period
suppress4 = False    # Suppress warnings about closed headings
suppress5 = False    # Suppress warnings about invalid passage links
suppress6 = False    # Suppress warnings about invalid OBS links
suppress7 = False    # Suppress warnings about file starting with blank line
suppress8 = False    # Suppress warnings about invalid list style
suppress9 = False    # Suppress warnings about ASCII content
suppress10 = False   # Suppress warnings about heading levels
suppress11 = False    # Suppress warnings about unbalanced parentheses
suppress12 = False     # Suppress warnings about newlines at end of file
if resource_type == "ta":
    suppress1 = True
    suppress7 = True
    suppress8 = True
if language_code in {'hr','id','nag','pmy','sw'}:    # ASCII content
    suppress9 = True

# Markdown line types
HEADING = 1
BLANKLINE = 2
TEXT = 3
LIST_ITEM = 4
ORDEREDLIST_ITEM = 5

import sys
import os

# Set Path for files in support/
# rootdiroftools = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(rootdiroftools,'support'))

import io
import codecs
import re

listitem_re = re.compile(r'[ \t]*[\*\-][ \t]')
olistitem_re = re.compile(r'[ \t]*[0-9]+\. ')
badolistitem_re = re.compile(r'[ \t]*[0-9]+[\)]')
badheading_re = re.compile(r' +#')

class State:
    def setPath(self, path):
        State.path = path
        State.linecount = 0
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
        State.ascii = True
        State.nerrors = 0

    def addLine(self, line):
        State.prevlinetype = State.currlinetype
        State.linecount += 1
        State.italicized = False
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
            State.italicized = (line[0] == '_' and line[-1] == '_')
        State.linetype.append(State.currlinetype)
        if State.ascii and not line.isascii() and not suppress9:
            State.ascii = False
        # sys.stdout.write(str(State.linecount) + ": line length: " + str(len(line)) + ". headingcount is " + str(State.headingcount) + "\n")
    
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
        reportError("Parentheses are unbalanced", False)
    if state.leftbrackets != state.rightbrackets:
        reportError("Left and right square brackets are unbalanced", False)
    if state.leftcurly != state.rightcurly:
        reportError("Left and right curly braces are unbalanced", False)
    if state.underscores % 2 != 0:
        reportError("Unmatched underscores", False)
    

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global sourceDir
        path = os.path.join(sourceDir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(sourceDir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
            else:
                os.remove(path)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
        
    return issuesFile

# Writes error message to stderr and to issues.txt.
def reportError(msg, report_lineno=True):
    state = State()
    issues = openIssuesFile()       

    if report_lineno:
        try:
            sys.stderr.write(shortname(state.path) + " line " + str(state.linecount) + ": " + msg + ".\n")
        except UnicodeEncodeError as e:
            sys.stderr.write(shortname(state.path) + " line " + str(state.linecount) + ": (Unicode...)\n")
        issues.write(shortname(state.path) + " line " + str(state.linecount) + ": " + msg + ".\n")
    else:
        sys.stderr.write(shortname(state.path) +  ": " + msg + ".\n")
        issues.write(shortname(state.path) + ": " + msg + ".\n")
    state.reportedError()

 
# Reports empty file and returns True if file is empty.
def verifyNotEmpty(mdPath):
    empty = False
    if os.path.isfile(mdPath):
       statinfo = os.stat(mdPath)
       if statinfo.st_size == 0:
           empty = True 
           reportError("Empty file", False)
    return empty

blankheading_re = re.compile(r'#+$')
heading_re = re.compile(r'#+[ \t]')
closedHeading_re = re.compile(r'#+[ \t].*#+[ \t]*$', re.UNICODE)
badclosedHeading_re = re.compile(r'#+[ \t].*[^# \t]#+[ \t]*$', re.UNICODE)  # closing hash without preceding space
toobold_re = re.compile(r'#+[ \t]+[\*_]', re.UNICODE)        # unwanted formatting in headings

def take(line):
    global current_file
    state = State()
    state.countParens(line)
    state.addLine(line)
    if not line:
        if state.linecount == 1 and not suppress7:
            reportError("starts with blank line")
        return
    if state.prevlinetype == HEADING and state.currlinetype != BLANKLINE:
        reportError("missing blank line after heading.")
    if state.currlinetype != HEADING:
        if state.headingcount == 0 and not suppress1 and not state.reported1:
            reportError("has text before first heading")
            state.report1()
    if state.currlinetype == TEXT and not state.reported2:
        if state.linecount >= 5 and state.prevlinetype == BLANKLINE and state.linetype[state.linecount-3] in {TEXT,LIST_ITEM,ORDEREDLIST_ITEM}:
            if resource_type in {"tn", "tq", "obs-tn", "obs-tq"}:
                if current_file != "intro.md" or resource_type != "tn":
                    reportError("should be a header here, or there is some other formatting problem")
                    state.report2()
    if state.currlinetype == HEADING:
        if state.linecount > 1 and state.prevlinetype != BLANKLINE:
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
            if resource_type in {"tn", "tq"} and state.currheadinglevel > 1:
                if resource_type == 'tq' or current_file != "intro.md":
                    reportError("excessive heading level: " + "#" * state.currheadinglevel)
            elif resource_type != "ta" and state.currheadinglevel > 2:
                reportError("excessive heading level")
            elif state.currheadinglevel > state.prevheadinglevel + 1:
                if resource_type != "ta" or state.prevheadinglevel > 0:
                    reportError("heading level incremented by more than one level")
    if state.currlinetype == LIST_ITEM:
        if state.prevlinetype in { TEXT, HEADING }:
            reportError("invalid list syntax")
        i = state.linecount - 1
        if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == LIST_ITEM and not suppress8:
            reportError("invalid list style")
    if state.currlinetype == ORDEREDLIST_ITEM:
        if badolistitem_re.match(line) and not suppress3:
            reportError("item number not followed by period")
        if olistitem_re.match(line):
            if state.prevlinetype in { TEXT, HEADING }:
                reportError("missing blank line before ordered list")
            i = state.linecount - 1
# At least in the English tA, there are numerous violations of this rule, and yet
# the lists render beautifully. I am commenting out this rule check, 1/29/19.
#            if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == ORDEREDLIST_ITEM:
#                reportError("invalid ordered list style")
    if line.find('# #') != -1:
        reportError('probable heading syntax error')
    if len(line) > 2 and line[0:2] == '% ':
        reportError("% used to mark a heading")
    if line.find("<!--") != -1 or line.find("&nbsp;") != -1 or line.find("o:p") != -1:
        reportError("html code")
    if toobold_re.match(line):
        if resource_type != "tn" or current_file != "intro.md":
            reportError("Extra formatting in heading")
    

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
notelink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/)(\w\w\w/\d+/\d+)(.*)', flags=re.UNICODE)
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
        if line and line[0] == '#':
            reportError("tA page reference in heading")
        manpage = page.group(1)
        path = os.path.join(ta_dir, manpage)
        if not os.path.isdir(path):
            reportError("invalid tA page reference")
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


# Parse tA links, note links, OBS links and passage links to verify existence of referenced .md file.
def checkMdLinks(line, fullpath):
    checkUnconvertedLinks(line)
    foundTA = checkTALinks(line)
    foundOBS = checkOBSLinks(line)
    if not foundOBS:        # because note links match OBS links
        foundTN = checkNoteLinks(line)
    if not foundTA and not foundOBS and not foundTN:    # because passagelink_re could match any of these
        if not suppress5:
            checkPassageLinks(line, fullpath)
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
def checkNoteLinks(line):
    found = False
    notelink = notelink_re.search(line)
    while notelink:
        found = True
        if notelink.group(2) != language_code:
            reportError("invalid language code in note link")
        else:
            notePath = os.path.join(tn_dir, notelink.group(4)) + ".md"
            notePath = os.path.normcase(notePath)
            if not os.path.isfile(notePath):
                reportError("invalid note link: " + notelink.group(1) + notelink.group(2) + notelink.group(3) + notelink.group(4))
        notelink = notelink_re.search(notelink.group(5))

    if notelink:
        found = True
    return found

# If there is a match to passageLink_re, passage.group(1) is the URL or other text between
# the parentheses,
# and passage.group(2) is everything after the right paren to the end of line.
def checkPassageLinks(line, fullpath):
    global resource_type
    passage = passagelink_re.search(line)
    while passage:
        referent = passage.group(1)
        if resource_type == 'obs-tn':
            contentDir = os.path.dirname( os.path.dirname(fullpath))
            story = referent[0: referent.find("/")]
            paragraph = referent[referent.find("/")+1:]
            if story.isdigit() and paragraph.isdigit():     # otherwise it's not a story link
                referencedPath = os.path.join( os.path.join(contentDir, story), paragraph + ".md")
                if not os.path.isfile(referencedPath):
                    reportError("invalid OBS story link: " + referent)
#                    reported = True
        elif not (resource_type == 'obs' and obsJpg_re.match(referent)):
            referencedPath = os.path.join( os.path.dirname(fullpath), referent )
            if not suppress5 and not os.path.isfile(referencedPath):
                reportError("invalid passage link: " + referent)
#                reported = True
        passage = passagelink_re.search(passage.group(2))

def checkReversedLinks(line):
    if reversedlink_re.search(line):
        reportError("Reversed link syntax")

#prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
#    if prefix_re.match(longpath):
#        shortname = "..." + longpath[6:]
    if sourceDir in longpath:
        shortname = longpath[len(sourceDir)+1:]
    return shortname

storyfile_re = re.compile(r'[0-9][0-9]\.md$')

# Markdown file verification
def verifyFile(path):
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines(-1)
    if not suppress12:          # newlines at end of file
        input.seek(0, io.SEEK_SET)      # rewind to beginning of file
        gulp = input.read()
    input.close()

    state = State()
    state.setPath(path)
    empty = verifyNotEmpty(path)
    if not empty:
        for line in lines:
            line = line.rstrip()
            take( line )
            checkMdLinks(line, path)
        reportParens()
        if resource_type == 'obs' and not state.italicized and storyfile_re.search(path):
            reportError("Last line is not italicized")
        if state.ascii and not suppress9:
            reportError("No non-ASCII content", False)
        if state.headingcount > state.textcount:
            if resource_type in {"tn", "obs-tn"} and not "intro.md" in path:
                reportError("At least one note heading is not followed by a note", False)
            elif resource_type in {"tq", "obs-tq"}:
                reportError("At least one question heading does not have a corresponding answer", False)
        if not suppress12:
            if state.currlinetype == BLANKLINE:
                reportError("Multiple newlines at end of file", False)
            if gulp[-1] != '\n':
                reportError("No ending newline", False)
    sys.stderr.flush()

    global nChecked
    nChecked += 1
    global nChanged
    if state.nerrors > 0:
#        sys.stdout.write(shortname(path) + u'\n')
        nChanged += 1

# Returns True if the specified file should be verified as a markdown document.
def verifiable(path, fname):
    v = False
    if os.path.isfile(path) and fname[-3:].lower() == '.md':
        if resource_type == "ta":
            v = (fname == "01.md")
        elif resource_type == "obs":
            v = (fname != "intro.md")
        else:
            v = True
    if fname in {"LICENSE.md", "README.md"}:
        v = False
    return v
    
def verifyDir(dirpath):
    global current_file
    sys.stdout.flush()
    for f in os.listdir(dirpath):
        path = os.path.join(dirpath, f)
        if os.path.isdir(path) and path[-4:] != ".git":
            # It's a directory, recurse into it
            verifyDir(path)
        elif verifiable(path, f):
            current_file = f
            verifyFile(path)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        source = r'E:\DCS\Croatian\hr_tn\2sa'
    else:
        source = sys.argv[1]

    if resource_type == "ta":
        sys.stdout.write("Checking only files named 01.md.\n\n")
        sys.stdout.flush()

    if os.path.isdir(source):
        sourceDir = source
        verifyDir(sourceDir)
    elif os.path.isfile(source):
        sourceDir = os.path.dirname(source)
        verifyFile(source)
    else:
        sys.stderr.write("File not found: " + source + '\n') 

    if issuesFile:
        issuesFile.close()
    print("Done. Checked " + str(nChecked) + " files. " + str(nChanged) + " failed.\n")