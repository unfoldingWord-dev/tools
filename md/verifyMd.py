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
# Reports files that have a UTF-8 Byye Order Mark (BOM)
# Reports missing title.md and sub-title.md files in tA.


# To-do -- check for other kinds of links in headings, not just TA links.
#          Check that tW files begin with H1 heading immediately followed by H2 heading.

# Globals
source_dir = r'C:\DCS\Nepali\work'
language_code = 'ne'
resource_type = 'tq'
ta_dir = r'C:\DCS\Kannada\kn_ta.STR'    # Target language tA, or English tM for WA
obstn_dir = r'C:\DCS\Russian\ru_obs-tn.STR'
en_tn_dir = r'C:\DCS\English\en_tn.md-orig'
en_tq_dir = r'C:\DCS\English\en_tq.v38'
tn_dir = r'C:\DCS\Spanish-es-419\es-419_tn.RPP'    # Markdown-style tN folder in target language, for note link validation
tw_dir = r'C:\DCS\Kannada\kn_tw.STR'

nChecked = 0
nChanged = 0
current_file = ""
issuesFile = None

suppress1 = False    # Suppress warnings about text before first heading
suppress2 = False    # Suppress warnings about blank headings
suppress3 = False    # Suppress warnings about item number not followed by period
suppress4 = False    # Suppress warnings about closed headings
suppress5 = False    # Suppress warnings about invalid relative links
suppress6 = False    # Suppress warnings about invalid OBS notes links
suppress7 = False    # Suppress warnings about file starting with blank line
suppress8 = False    # Suppress warnings about blank lines before, after, and within lists
suppress9 = False    # Suppress warnings about ASCII content
suppress10 = False   # Suppress warnings about heading levels
suppress11 = False    # Suppress warnings about unbalanced parentheses
suppress12 = False     # Suppress warnings about newlines at end of file
suppress13 = False     # Suppress warnings about mistmatched **
suppress14 = True     # Suppress "invalid note link" warnings
suppress15 = True     # Suppress punctuation warnings.
suppress16 = False     # Suppress warnings about empty files
suppress17 = (resource_type != 'tn')  # Suppress the missing intro.md file warning, which applies only to tN resources
suppress18 = False     # Suppress warnings about newline in title.md files
suppress19 = False     # Suppress "should be a header here" warnings
suppress20 = False      # Suppress "invalid TA page reference" warnings
suppress21 = False       # Suppress missing title/subtitle files warnings (applies to tA only)
suppress22 = True       # Suppress warnings about http links

if resource_type == "ta":
    suppress1 = True
    suppress7 = True
if language_code in {'ceb','en','es-419','ha','hr','id','nag','plt','pmy','pt-br','sw'}:    # ASCII content
    suppress9 = True

# Markdown line types
HEADING = 1
BLANKLINE = 2
TEXT = 3
LIST_ITEM = 4
ORDEREDLIST_ITEM = 5

import xml
import sys
import os
import io
import codecs
import re
import usfm_verses

listitem_re = re.compile(r'[ \t]*[\*\-][ \t]')
olistitem_re = re.compile(r'[ \t]*[0-9]+\. ')
badolistitem_re = re.compile(r'[ \t]*[0-9]+[\)]')
badheading_re = re.compile(r' +#')

class State:
    def setPath(self, path):
        State.path = path
        State.titlefile = path.endswith("title.md")
        State.linecount = 0
        State.headingcount = 0
        State.textcount = 0
        State.prevQ = ""
        State.currQ = ""
        State.prevheadinglevel = 0
        State.currheadinglevel = 0
        State.prevlinetype = None
        State.currlinetype = None
        State.linetype = []
        State.reported1 = False
        State.reported2 = False
        State.leftparens = 0
        State.rightparens = 0
        State.reported_parens_inline = False
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
            if resource_type == 'tq':
                State.prevQ = State.currQ
                State.currQ = line
        elif not line or len(line.strip()) == 0:
            State.currlinetype = BLANKLINE
        elif listitem_re.match(line):
            State.currlinetype = LIST_ITEM
            if State.prevlinetype in {HEADING,BLANKLINE}:
                State.textcount += 1
        elif olistitem_re.match(line): #  or badolistitem_re.match(line):
            State.currlinetype = ORDEREDLIST_ITEM
            if State.prevlinetype in {HEADING,BLANKLINE}:
                State.textcount += 1
        else:
            State.currlinetype = TEXT
            State.textcount += 1
            State.italicized = (line[0] == '_' and line[-1] == '_') #  or (line[0] == '*' and line[-1] == '*') asterisks don't pass the tx check
        State.linetype.append(State.currlinetype)
        if State.ascii and not line.isascii() and not suppress9:
            State.ascii = False

    def countParens(self, line):
        #if not re.search(r'[0-9]\)', line):   # right parens used in list items voids the paren matching logic for that line
            #State.leftparens += line.count("(")
            #State.rightparens += line.count(")")
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

# Report unbalanced parentheses/brackets on a file-wide basis
def reportParens():
    state = State()
    if not suppress11 and state.reported_parens_inline and state.leftparens != state.rightparens:
        reportError("Parentheses are unbalanced (" + str(state.leftparens) + ":" + str(state.rightparens) + ")", False)
    if state.leftbrackets != state.rightbrackets:
        reportError("Left and right square brackets are unbalanced (" + str(state.leftbrackets) + ":" + str(state.rightbrackets) + ")", False)
    if state.leftcurly != state.rightcurly:
        reportError("Left and right curly braces are unbalanced (" + str(state.leftcurly) + ":" + str(state.rightcurly) + ")", False)
#    if state.underscores % 2 != 0:
#        reportError("Unmatched underscores", False)


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
            else:
                os.remove(path)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')

    return issuesFile

# Writes error message to stderr and to issues.txt.
def reportError(msg, report_lineno=True):
    state = State()
    issues = openIssuesFile()
    if msg[-1] != '\n':
        msg += '\n'
    if report_lineno and state.linecount > 0:
        try:
            sys.stderr.write(shortname(state.path) + " line " + str(state.linecount) + ": " + msg)
        except UnicodeEncodeError as e:
            sys.stderr.write(shortname(state.path) + " line " + str(state.linecount) + ": (Unicode...)\n")
        issues.write(shortname(state.path) + " line " + str(state.linecount) + ": " + msg)
    else:
        sys.stderr.write(shortname(state.path) +  ": " + msg)
        issues.write(shortname(state.path) + ": " + msg)
    state.reportedError()

def checkForBOM(path):
    with open(path, "rb") as file:
        beginning = file.read(4)
        # The order of these if-statements is important
        # otherwise UTF32 LE may be detected as UTF16 LE as well
        if beginning[0:3] == b'\xef\xbb\xbf':
            reportError("File has a BOM", False)

# Called only for tA articles.
# Verifies whether the file has any line endings (it should not).
# Verifies whether the file has non-ASCII content.
def verifyTitleFile(path):
    input = io.open(path, "rb")
    content = input.read()
    input.close()
    if not suppress18:
        if b'\n' in content:
            reportError("TA title and subtitle files should not have any line endings", False)
    if not suppress9:
        if content.isascii():
            reportError("No non-ASCII content", False)

# Reports empty file and returns True if file is empty.
def verifyNotEmpty(mdPath):
    empty = False
    if os.path.isfile(mdPath):
       statinfo = os.stat(mdPath)
       if statinfo.st_size < 7:
           empty = True
           if not suppress16:
               reportError("No content in file", False)
    return empty

blankheading_re = re.compile(r'#+$')
heading_re = re.compile(r'#+[ \t]')
multiHash_re = re.compile(r'#+[ \t].+#', re.UNICODE)
closedHeading_re = re.compile(r'#+[ \t].*#+[ \t]*$', re.UNICODE)
badclosedHeading_re = re.compile(r'#+[ \t].*[^# \t]#+[ \t]*$', re.UNICODE)  # closing hash without preceding space

def take(line):
    global current_file
    state = State()
    state.countParens(line)
    state.addLine(line)
    if not line:
        if state.linecount == 1 and not suppress7:
            reportError("starts with blank line", False)
        return
    if "placeholder" in line:
        reportError("Line contains a placeholder.")
    if state.prevlinetype == HEADING and state.currlinetype != BLANKLINE:
        reportError("missing blank line after heading.")
    if state.currlinetype != HEADING and not state.titlefile:
        if state.headingcount == 0 and not suppress1 and not state.reported1:
            reportError("has text before first heading")
            state.report1()
        if resource_type == 'tq' and state.currQ == state.prevQ and state.currQ != "":
            reportError("Duplicate questions")
    if state.currlinetype == TEXT and not state.reported2 and not suppress19:
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
        elif multiHash_re.match(line):
            if closedHeading_re.match(line):
                if not suppress4:
                    reportError("closed heading")
                if badclosedHeading_re.match(line):
                    reportError("no space before closing hash mark")
            else:
                reportError("multiple hash groups on one line")
        elif not suppress2 and blankheading_re.match(line):
            reportError("blank heading")
        elif len(line) > 1 and not heading_re.match(line):
            reportError("missing space after hash symbol(s)")
        if not suppress10:
            if resource_type in {"tn", "tq"} and state.currheadinglevel > 1:
                if resource_type == 'tq' or current_file != "intro.md":
                    reportError("excessive heading level: " + "#" * state.currheadinglevel)
            elif resource_type not in {"ta","tw"} and state.currheadinglevel > 2:
                reportError("excessive heading level")
            elif resource_type == 'tw' and state.linecount > 1 and state.currheadinglevel == 1 and state.headingcount > 1:
                reportError("Incorrect tW file, must have only one H1 heading")
            elif state.currheadinglevel > state.prevheadinglevel + 1:
                if resource_type != "ta" or state.prevheadinglevel > 0:
                    reportError("heading level incremented by more than one level")

    if resource_type == 'tw' and state.linecount == 1 and (state.currlinetype != HEADING or state.currheadinglevel != 1):
        reportError("Incorrect tW file, must have H1 heading on line 1")
    # In a tW file, the third line must be an H2 heading
    if resource_type == 'tw' and state.linecount == 3 and (state.currlinetype != HEADING or state.currheadinglevel != 2):
        reportError("Incorrect tW file, must have H2 \"Definition\" heading on line 3")
    if resource_type == 'obs' and ".jpg" in line:
        if not line.startswith("![OBS Image]"):
            reportError("Incorrect alt text")
        if not line.endswith(".jpg)"):
            reportError("Extra character(s) after image link")

    # 8/19/21 - Blank lines are optional around lists on DCS, but WACS needs them
    if not suppress8:
        if state.currlinetype in {LIST_ITEM, ORDEREDLIST_ITEM}:
            if state.prevlinetype in { TEXT, HEADING }:
                reportError("need blank line before first list item")
            i = state.linecount - 1     # 0-based index
            if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == state.currlinetype:
                reportError("blank line between list items")
        elif state.currlinetype in {TEXT, HEADING}:
            if state.prevlinetype in {LIST_ITEM, ORDEREDLIST_ITEM}:
                reportError("need blank line after last list item")

    if state.currlinetype == ORDEREDLIST_ITEM:
#        if badolistitem_re.match(line) and not suppress3:
#            reportError("item number not followed by period")
        if olistitem_re.match(line):
            if state.prevlinetype in { TEXT, HEADING }:
                reportError("missing blank line before ordered list")
            i = state.linecount - 1
# At least in the English tA, there are numerous violations of this rule, and yet
# the lists render beautifully. I am commenting out this rule check, 1/29/19.
#            if i > 1 and state.linetype[i-1] == BLANKLINE and state.linetype[i-2] == ORDEREDLIST_ITEM:
#                reportError("invalid ordered list style")
    checkLineContents(line)

#toobold_re = re.compile(r'#+[ \t]+.*[\*_]', re.UNICODE)        # unwanted formatting in headings
unexpected_re = re.compile(r'\([^\)\[]*\]', re.UNICODE)         # ']' after left paren
unexpected2_re = re.compile(r'\[[^\]\(]*\)', re.UNICODE)         # ')' after left square bracket
unexpected3_re = re.compile(r'^[^\[]*\]', re.UNICODE)            # ']' before '['
unexpected4_re = re.compile(r'\[[^\]]*$', re.UNICODE)            # '[' without following ']'

def checkLineContents(line):
    if line.find('# #') != -1:
        reportError('heading syntax error')
    if line.startswith("% ") or line.startswith("%​ "):  # invisible character in second comparison
        reportError("% used to mark text")
    pos = line.find('&')
    if "<!--" in line or "o:p" in line or (pos >= 0 and line.find(';') > pos):
        reportError("html code")
    #if toobold_re.match(line):
        #if resource_type != "tn" or current_file != "intro.md":
            #reportError("extra formatting in heading")
    if '**' in line:
        if not suppress13 and line.count("**") % 2 == 1:
            reportError("Line seems to have mismatched '**'")
        if line.find("** ") == line.find("**"):      # the first ** is followed by a space
            reportError("Incorrect markdown syntax, space after double asterisk '**'")
        if '****' in line:
            reportError("Line contains quadruple asterisks, ****")
        #elif '***' in line:
            #reportError("Line contains triple asterisks, ***")
        #if "**_" in line:
            #reportError("Line contains **_")
        #if "_**" in line:
            #reportError("Line contains _**")
    if not suppress13 and line.count("__") % 2 == 1:
        reportError("Line seems to have mismatched '__'")
    #if "___" in line:
        #reportError("Triple underscore")
    if unexpected_re.search(line):
        reportError("found ']' after left paren")
    if unexpected2_re.search(line):
        reportError("found ')' after left square bracket")
    if unexpected3_re.search(line):
        reportError("found ']' without preceding '['")
    if unexpected4_re.search(line):
        reportError("found '[' without following ']'")
    if '[[[' in line or '[[[' in line or '(((' in line or ')))' in line:
        reportError("Extra parens or brackets")
    if line.count("[") != line.count("]"):
        reportError("Unbalanced brackets within this line: " + str(line.count("[")) + ":" + str(line.count("]")))
    if not suppress11:
        nRight = reportParensInLine(line, count_numbered=False)

rclink2_re = re.compile(r'rc:[a-z0-9\-\.\*/]+(.*?)[\)\]]')

# Reports an error if the line contains any corrupted RC links (containing non-ASCII characters).
def checkTranslatedLinks(line):
    links = re.finditer(rclink2_re, line)
    for link in links:
        if not link.group(1).isascii():
            reportError("Has corrupted rc link")
        if link.group(0).startswith("rc://*/ta") and not link.group(0).startswith("rc://*/ta/man/"):
            reportError("ta link must start with ta/man in order to render")

unbracketed_re = re.compile(r'[^\[][^\[][^\[]rc\://')
altbracketed_re = re.compile(r'.\] *\( *rc\://.*\)')

# Reports an error if the text (one line from a file) contains an RC link that is not bracketed
def checkUnbracketedLinks(text):
    unbracketed = False
    found = unbracketed_re.search(text)
    if found:
        altfound = altbracketed_re.match(text[found.start():])
        if not altfound:
            unbracketed = True
            reportError("Unbracketed RC link")

# Looks for underscores in TA links.
# Looks for :en: and rc://en in the line
def checkUnconvertedLinks(line):
    if ("figs_" in line or "translate_" in line or "guidelines_" in line or "writing_" in line) and not "ufw.io" in line:
        reportError("Underscore in tA reference")
    elif  " figs-" in line or " translate-" in line or " guidelines-" in line or " writing-" in line:
        reportError("Malformed tA reference")
    if language_code != 'en':
        if line.find(':en:') >= 0 or line.find('rc://en/') >= 0:
            reportError("Unconverted language code")


tapage_re = re.compile(r'\[\[.*?/ta/man/(.*?)]](.*)', flags=re.UNICODE)
talink_re = re.compile(r'(\(rc://[\*\w\-]+/ta/man/)(.+?/.+?)(\).*)', flags=re.UNICODE)
obsJpg_re = re.compile(r'https://cdn.door43.org/obs/jpg/360px/obs-en-[0-9]+\-[0-9]+\.jpg$', re.UNICODE)

# Parse tA manual page names from the line.
# Verifies the existence of the referenced page.
def checkTALinks(line):
    found = False
    page = tapage_re.search(line)           # [[../ta/man/...]]
    while page:
        found = True
        if line and line[0] == '#' and not current_file.endswith("intro.md"):
            reportError("tA page reference in heading")
        manpage = page.group(1)
        path = os.path.join(ta_dir, manpage)
        if not os.path.isdir(path) and not suppress20:
            reportError("invalid tA page reference: " + manpage)
        page = tapage_re.search(page.group(2))

    if not found:
        link = talink_re.search(line)       # (rc://.../ta/man/...
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

rclink_re = re.compile(r'[^s]rc:*[\\/]+([ \w\-\*]*?)[\\/]', re.UNICODE)
rcgoodlink_re = re.compile(r'rc://[\w\-\*]+/t', re.UNICODE)

# Parse tA links, note links, OBS links and passage links to verify existence of referenced .md file.
def checkMdLinks(line, fullpath):
    checkUnconvertedLinks(line)
    checkUnbracketedLinks(line)
    checkTranslatedLinks(line)
    text = line
    rclink = rclink_re.search(text)
    while rclink:
        if not rcgoodlink_re.match(text[rclink.start()+1:rclink.end()+1]):
            reportError("malformed link: " + text[rclink.start():rclink.end()+1] + "...")
        text = text[rclink.end()+1:]
        rclink = rclink_re.search(text)
    foundTA = checkTALinks(line)
    foundOBS = checkOBSLinks(line)
    foundTW = checkTWLinks(line)
    if not foundOBS:        # because note links match OBS links
        foundTN = checkTNLinks(line)
    if not suppress5:
        checkPassageLinks(line, fullpath)
    checkReversedLinks(line)

twlink_re = re.compile(r'(\(rc://[\*\w\-]+/tw/dict/bible/)(.+?)/(.+?)(\).*)', flags=re.UNICODE)      # matches rc://en/tw/dict/bible/.../...)  or rc://*/tw/dict/bible/.../...)

def checkTWLinks(line):
    found = False
    tw = twlink_re.search(line)     # (rc://.../tw/dict/bible/...
    while tw:
        found = True
        path = os.path.join(tw_dir, tw.group(2))
        path = os.path.join(path, tw.group(3)) + ".md"
        if not os.path.isfile(path):
            reportError("invalid tW link: " + tw.group(2) + "/" + tw.group(3))
        tw = twlink_re.search(tw.group(4))
    return found

obslink_re = re.compile(r'(rc://)([\*\w\-]+)(/tn/help/obs/)(\d+)/(\d+)(.*)', flags=re.UNICODE)

# Returns True if any OBS links were found and checked.
def checkOBSLinks(line):
    found = False
    link = obslink_re.search(line)      # rc://.../tn/help/obs
    while link:
        found = True
        if link.group(2) != "*" and link.group(2) != language_code:
            reportError("invalid language code in OBS notes link")
        elif not suppress6:
            obsPath = os.path.join(obstn_dir, link.group(4))
            obsPath = os.path.join(obsPath, link.group(5) + ".md")
            if not os.path.isfile(obsPath):
                reportError("invalid OBS notes link: " + link.group(1) + link.group(2) + link.group(3) + link.group(4) + '/' + link.group(5))
        link = obslink_re.search(link.group(6))
    return found

notelink_re = re.compile(r'(rc://)([ \*\w\-]+)(/tn/help/)(\w\w\w/\d+)/(\d+)(.*)', flags=re.UNICODE)

# Returns True if any notes links were found.
# Note links currently are not rendered on live site as links.
def checkTNLinks(line):
    found = False
    notelink = notelink_re.search(line)     # rc://.../tn/help/...
    while notelink:
        found = True
        if language_code == 'en':
            if notelink.group(2) != 'en':
                reportError("Probably need 'en' in note link in place of '" + notelink.group(2) + "'")
        elif notelink.group(2) != "*":
            reportError("need wildcard * in note link: " + notelink.group(2))
        if not suppress14:
#            chunkmd = notelink.group(5) + ".md"
            notePath = os.path.join(tn_dir, notelink.group(4))
            notePath = os.path.join(notePath, notelink.group(5) + ".md")
            notePath = os.path.normcase(notePath)
            if not os.path.isfile(notePath):
                reportError("invalid note link: " + notelink.group(1) + notelink.group(2) + notelink.group(3) + notelink.group(4) + "/" + notelink.group(5))
        notelink = notelink_re.search(notelink.group(6))

    return found

def checkOBSTNLink(link):
    story = link[0: link.find("/")]
    paragraph = link[link.find("/")+1:]
    if story.isdigit() and paragraph.isdigit():     # otherwise it's not a story link
        referencedPath = os.path.join( os.path.join(obstn_dir, story), paragraph + ".md")
        if not os.path.isfile(referencedPath):
            reportError("invalid OBS story link: " + link)

passagelink_re = re.compile(r'] *\(([^\)]*?)\)(.*)', flags=re.UNICODE)  # ](some-kind-of-link)...

# If there is a match to passageLink_re, passage.group(1) is the URL or other text between
# the parentheses,
# and passage.group(2) is everything after the right paren to the end of line.
def checkPassageLinks(line, fullpath):
    global resource_type
    passage = passagelink_re.search(line)
    while passage:
        link = passage.group(1).strip()
        if resource_type in {'obs-tn','obs-tq','obs-sn','obs-sq'}:
            checkOBSTNLink(link)
        elif not "/ta/" in link and not '/tn/' in link and not '/tw/' in link and not (resource_type == 'obs' and obsJpg_re.match(link)):
            # i.e. we are dealing with a relative path to a resource of the same type
            if not link.isascii():
                reportError("Non-ascii link")
            elif not link.startswith("http") and not suppress5:
                checkRelativeLink(link, fullpath)
            elif not suppress22:
                reportError("http link: " + link)
        passage = passagelink_re.search(passage.group(2))

def checkRelativeLink(link, currpath):
    current_dir = os.path.dirname(currpath)
    if resource_type == 'tw':
        folder = os.path.join(tw_dir, os.path.basename(current_dir))
    elif resource_type == 'ta':
        category_dir = os.path.basename( os.path.dirname(current_dir))
        folder = os.path.join(ta_dir, category_dir)
        folder = os.path.join(folder, os.path.basename(current_dir))
    else:
        folder = current_dir
    referencedPath = os.path.join(folder, link)
    if not os.path.isfile(referencedPath):
        reportError("invalid relative link: " + link)

reversedlink_re = re.compile(r'\(.*\) *\[.*\]', flags=re.UNICODE)

def checkReversedLinks(line):
    if reversedlink_re.search(line):
        reportError("Reversed link syntax")

paren_re = re.compile(r'[0-9১-৩]+\)', flags=re.UNICODE)   # Right parens after a number. May match too much.
parens_re = re.compile(r'\([0-9১-৩]+\)', flags=re.UNICODE)   # Number in parentheses.

def reportParensInLine(line, count_numbered=False):
    right = line.count(")")
    rightX = right
    left = line.count("(")
    if right > left and not count_numbered:    # eliminate miscounts from parenthesized ordered list in the line
        numbered_parens = len( paren_re.findall(line) )
        parenthesized_numbers = len( parens_re.findall(line) )
        rightX -= (numbered_parens - parenthesized_numbers)
    if left != rightX:
        reportError("Unbalanced parens within this line: " + str(left) + ":" + str(right))
        State().reported_parens_inline = True

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath and source_dir != longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

punctuation_re = re.compile(r'([\?!;\:,][^ \n\)\]\'"’”»›\*]_)', re.UNICODE)
spacey_re = re.compile(r'[\s]([\.\?!;\:,\)’”»›])', re.UNICODE)
spacey2_re = re.compile(r'[\s]([\(\'"])[\s]', re.UNICODE)

def reportPunctuation(text):
    global lastToken
    state = State()
    if bad := punctuation_re.search(text):
        three = text[bad.start():bad.end()+1]
        if three != '...' and three != '../' and three != '://':
            if not (bad.group(1)[0] in ',.:' and bad.group(1)[1] in "0123456789"):   # it's a number or verse reference
                reportError("Bad punctuation: " + bad.group(1))
    if bad := spacey_re.search(text):
        three = text[bad.start()+1:bad.start()+4]
        if three != '...' and three[0:2] != '![':
            reportError("Space before phrase ending mark: " + bad.group(1))
    if bad := spacey2_re.search(text):
        reportError("Free floating mark: " + bad.group(1))
    if "''" in text:
        reportError("Repeated quotes")

storyfile_re = re.compile(r'[0-9][0-9]\.md$')

# Markdown file verification
def verifyFile(path):
    global current_file
    current_file = os.path.basename(path)
    input = io.open(path, "tr", buffering=1, encoding="utf-8-sig")
    lines = input.readlines(-1)
    if not suppress12:          # newlines at end of file
        input.seek(0, io.SEEK_SET)      # rewind to beginning of file
        gulp = input.read()
    input.close()

    state = State()
    state.setPath(path)
    checkForBOM(path)
    empty = verifyNotEmpty(path)
    if not empty:
        for line in lines:
            line = line.rstrip()
            take( line )
            if line:
                checkMdLinks(line, path)
        reportParens()
        if resource_type == 'obs' and not state.italicized and storyfile_re.search(path):
            reportError("Last line is not italicized correctly")
        if state.ascii and not suppress9:
            reportError("No non-ASCII content", False)
        if state.headingcount > state.textcount:
            if resource_type in {"tn", "obs-tn", "obs-sn"} and not "intro.md" in path:
                reportError("At least one note heading is not followed by a note", False)
            elif resource_type in {"tq", "obs-tq", "obs-sq"}:
                reportError("At least one question heading does not have a corresponding answer", False)
        if not suppress12:
            if state.currlinetype == BLANKLINE and len(lines) > 1:
                reportError("Multiple newlines at end of file", False)
            if gulp[-1] != '\n' and not state.titlefile:
                reportError("No ending newline", False)
        if not suppress15:
            reportPunctuation(gulp)
    sys.stderr.flush()

    global nChecked
    nChecked += 1
    global nChanged
    if state.nerrors > 0:
#        sys.stdout.write(shortname(path) + u'\n')
        nChanged += 1

# Returns True if the specified file should be verified as a markdown document.
#   Means file extension is .md
def verifiable(path, fname):
    v = (os.path.isfile(path) and fname[-3:].lower() == '.md')
    if v:
        if resource_type == "ta":
            v = (fname == "01.md")
        elif resource_type == "obs":
            v = (fname != "intro.md")
    if fname in {"LICENSE.md", "README.md"}:
        v = False
    return v

def verifyFrontFolder(path):
    files = os.listdir(path)
    for fname in files:      # find the highest numbered verse
        fpath = os.path.join(path, fname)
        if verifiable(fpath, fname):
            verifyFile(fpath)

# Used for tn and tq projects only.
def verifyChapter(path, chapter, book):
    state = State()
    state.setPath(path)
    if resource_type == 'tn' and not suppress17:
        intropath = os.path.join(path, "intro.md")
        if not os.path.isfile(intropath):
            reportError("Chapter is missing an intro.md file: " + shortname(path))

    if resource_type == 'tn':
        enpath = os.path.join(en_tn_dir, book)
    else:   # resource_type is 'tq'
        enpath = os.path.join(en_tq_dir, book)
    if verifyChapterName(book.upper(), path, chapter):
        nverses = usfm_verses.verseCounts[book.upper()]['verses'][int(chapter)-1]
        files = os.listdir(path)
        enpath = os.path.join(enpath, chapter)
        if book == 'psa' and len(chapter) == 3 and chapter[0] == '0' and not os.path.isdir(enpath):
            enpath = os.path.join( os.path.join(en_tq_dir, book), chapter[1:])

        path01 = os.path.join(path, "01.md")
        path01en = os.path.join(enpath, "01.md")
        if book == "psa":
            path01 = os.path.join(path, "001.md")
            path01en = os.path.join(path, "001.md")
        en_files = os.listdir(enpath)
        reportedMissing = False
        if not os.path.isfile(path01) and os.path.isfile(path01en) and os.stat(path01en).st_size > 4:
            reportError("Missing file(s) in: " + shortname(path))
            reportedMissing = True
        elif len(files) * 4 < len(en_files):
            reportError("Missing some files in: " + shortname(path))
            reportedMissing = True
        elif len(files) > nverses + 1:
            reportError("Too many files in: " + shortname(path))
#        else:
        topverse = 0
        for fname in files:
            fpath = os.path.join(path, fname)
            if verifiable(fpath, fname):
                pair = os.path.splitext(fname)
                if pair[0].isdigit():
                    verseno = int(pair[0])
                    if verseno > topverse:          # find the highest numbered verse
                        topverse = verseno
                verifyFile(fpath)
            verifyFilename(path, fname)
        if not reportedMissing and topverse + 5 < nverses and len(files) * 3 < len(en_files):
            state.setPath(path)
            reportError("Likely missing some files in: " + shortname(path))

def verifyChapterName(book, path, chapter):
    ok = True
    if not chapter.isdigit():
        reportError("Invalid chapter folder name: " + chapter)
        ok = False
    else:
        nchap = int(chapter)
        bookchapters = usfm_verses.verseCounts[book.upper()]['chapters']
        if nchap < 1 or nchap > bookchapters:
            reportError("Invalid chapter number: " + chapter)
            ok = False
        if "psa" in path or "PSA" in path:
            if len(chapter) not in {2,3}:
                reportError("Chapter folders in Psalms need 2 or 3 digits: " + chapter)
                ok = False
        else:
            if len(chapter) != 2:
                reportError("Chapter folders must have 2 digits: " + chapter)
                ok = False
    return ok

# Counts chapter folders and reports if there are too few or too many.
# Used for tn and tq projects only.
def verifyBook(path, book):
    sys.stdout.write("Checking " + book + "\n")
    sys.stdout.flush()
    nchapters = usfm_verses.verseCounts[book.upper()]['chapters']
    nchapters_found = 0
    entries = os.listdir(path)
    for entry in entries:
        subpath = os.path.join(path, entry)
        if os.path.isdir(subpath):
            if entry != "front":
                nchapters_found += 1
                verifyChapter(subpath, entry, book)
            else:
                verifyFrontFolder(os.path.join(path, entry))
        elif verifiable(subpath, entry):
            verifyFile(subpath)
    state = State()
    state.setPath(path)
    if nchapters_found < nchapters:
        reportError("There are only " + str(nchapters_found) + " chapter folders in: " + shortname(path) + ". Need " + str(nchapters) + " chapters.")
    elif nchapters_found > nchapters:
        reportError("Extraneous chapter folder(s) in: " + shortname(path))

fname2_re = re.compile(r'[0-8][0-9]\.md$')
fname3_re = re.compile(r'[0-1][0-9][0-9]\.md$')

def verifyFilename(path, fname):
    skip = (resource_type == 'tq' and "psa" in path and "119" in path)  # Psalm 119 in tQ has some 2-digit and some 3-digit verse numbers, and some in the 90s
    fname_re = fname2_re
    if resource_type == 'tn' and "psa" in path:
        fname_re = fname3_re
    if not skip and not fname_re.match(fname) and not fname == "intro.md" and not fname.endswith(".md.orig"):
        path = os.path.join(path, fname)
        reportError("Invalid file name: " + path, False)

# Used only for tA bottom level folders
def verify_ta_article(dirpath):
    state = State()
    state.setPath(dirpath)
    path = os.path.join(dirpath, "01.md")
    if os.path.isfile(path):
        verifyFile(path)
    else:
        reportError("Missing 01.md file in: " + shortname(dirpath), False)

    for path in [os.path.join(dirpath, "title.md"), os.path.join(dirpath, "sub-title.md")]:
        state.setPath(path)
        if not os.path.isfile(path):
            if not suppress21:
                reportError("Missing file", False)
        else:
            checkForBOM(path)
            verifyTitleFile(path)
    if len(os.listdir(dirpath)) > 3:
        reportError("Extraneous file(s) in: " + shortname(dirpath), False)

def verifyDir(dirpath):
    state = State()
    state.setPath(dirpath)
    f = os.path.basename(dirpath)
    if resource_type in {'tq','tn'} and dirpath != source_dir and f.upper() not in usfm_verses.verseCounts and f.lower() != "content":
        reportError("Invalid book folder: " + f)
    elif resource_type in {'tq','tn'} and f.upper() in usfm_verses.verseCounts:      # it's a book folder
        verifyBook(dirpath, f)
    else:
        for f in os.listdir(dirpath):
            path = os.path.join(dirpath, f)
            if os.path.isdir(path):
                if f[0] != '.':
                    verifyDir(path)
            elif resource_type == "ta":
                if f in {"01.md", "title.md", "sub-title.md"}:
                    verify_ta_article(dirpath)
                    break
            elif resource_type in {"tn","tw","obs","obs-tn","obs-tq","obs-sn","obs-sq"} and verifiable(path, f):
                verifyFile(path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if not tw_dir.endswith("bible"):
        tw_dir = os.path.join(tw_dir, "bible")
    if not obstn_dir.endswith("content"):
        obstn_dir = os.path.join(obstn_dir, "content")

    if os.path.isdir(source_dir):
        verifyDir(source_dir)
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        verifyFile(path)
    else:
        sys.stderr.write("Path not found: " + source_dir + '\n')

    if issuesFile:
        issuesFile.close()
    print("Done. Checked " + str(nChecked) + " files. " + str(nChanged) + " failed.\n")