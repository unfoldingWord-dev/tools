# -*- coding: utf-8 -*-
# This module converts a single json file or individual lines to .md format.
#    Ensures correct syntax, with blank lines before and after lists, etc.
#    Fixes links of this form [[:en:ta...]]
#    Converts leading dash to asterisk (json2md() only, needed for Brazilian Portuguese)
#    Removes leading spaces from headers and text lines.
# Import and use either of two external functions:
#    json2md()
#    md2md()

# Global variables
g_langcode = u''
g_mdPath = ''
pages = []
g_multilist = False     # Support multi-level lists. By default, spaces before asterisk are removed.

import re
import io
import os
import sys
import json
import codecs

listitem_re = re.compile(r'[ \t]*[\*\-][ \t]')
olistitem_re = re.compile(r'[ \t]*[0-9]+\. ')
badolistitem_re = re.compile(r'[ \t]*[0-9]+[\) ]')

# Markdown line types
HEADING = 1
BLANKLINE = 2
TEXT = 3
LIST_ITEM = 4
ORDEREDLIST_ITEM = 5

class State:
    prevlinetype = None
    currlinetype = None
    
    def newFile(self):
        State.prevlinetype = None
        State.currlinetype = None

    def addLine(self, line):
        State.prevlinetype = State.currlinetype
        if not line or len(line.strip()) == 0:
            State.currlinetype = BLANKLINE
        elif line and line[0] == u'#':
            State.currlinetype = HEADING
        elif listitem_re.match(line):
            State.currlinetype = LIST_ITEM
        elif olistitem_re.match(line) or badolistitem_re.match(line):
            State.currlinetype = ORDEREDLIST_ITEM
        else:
            State.currlinetype = TEXT
        # sys.stdout.write(str(State.linecount) + ": line length: " + str(len(line)) + ". headingcount is " + str(State.headingcount) + "\n")

# Converts a tStudio-generated .txt file with a list of title/body pairs, to .md.
# The caller guarantees that inputPath is a readable file.
def json2md(inputPath, mdPath, langcode, shortname):
    global g_langcode
    global g_mdPath
    g_langcode = langcode
    g_mdPath = mdPath
    convertJson(inputPath, mdPath, shortname)

    if os.path.isfile(mdPath):
        statinfo = os.stat(mdPath)
        if statinfo.st_size == 0:
            sys.stderr.write("Removed empty: " + shortname(mdPath) + "\n")
            sys.stderr.flush()
            os.remove(mdPath)

def convertJson(inputPath, mdPath, shortname):
    notes = []
    enc = detect_by_bom(inputPath, default="utf-8")
    f = io.open(inputPath, "tr", 1, encoding=enc)
    try:
        notes = json.load(f)
    except ValueError as e:
        sys.stderr.write("Not valid JSON: " + shortname(inputPath) + '\n')
        sys.stderr.flush()
    f.close()

    if len(notes) > 0:
        nIn = 0   # used in error messages below
        nOut = 0
    
        # Open output .md file for writing.
        mdFile = io.open(mdPath, "tw", buffering=1, encoding='utf-8', newline='\n')
        for note in notes:
            nIn += 1
            if keepNote(note):
                titlestr = unicode(note['title']).strip()
                titlestr = titlestr.replace(u"#", u"%")
                title = normalizeTitle(titlestr)
                bodystr = unicode(note['body']).strip()
                body = bodystr.replace(u'●', u'*')     # this stmt doesn't work in normalize() function!?
                body = body.replace(u'•', u'*')     # this stmt doesn't work in normalize() function!?
                body = body.replace(u"#", u"%")
                body = normalize(body)
                if nOut > 0:
                    mdFile.write(u'\n')
                mdFile.write(u'# ' + title + u'\n\n')
                mdFile.write(body + u'\n')
                nOut += 1
                if abs(len(title) - len(titlestr)) > 12 or len(body) - len(bodystr) > 16 or len(body) - len(bodystr) < -50:
                    sys.stderr.write("Manually check conversion of note " + str(nIn) + " in " + shortname(inputPath) + ".\n")
                    sys.stderr.write("  Length difference of title: " + str(len(title) - len(titlestr)) + "\n")
                    sys.stderr.write("  Length difference of body: " + str(len(body) - len(bodystr)) + "\n")
                    sys.stderr.flush()
            # else:
                # sys.stderr.write("Discarded note " + str(n) + " in: " + shortname(inputPath) + '\n')
                # sys.stderr.flush()
        mdFile.close()

blankheading_re = re.compile(r'\#[# \t]*$', re.UNICODE)
forgothash_re = re.compile(r'\w.*\?$', re.UNICODE)      # starts with word, ends with question mark

def md2md(inputPath, mdPath, langcode, shortname):
    global g_langcode
    global g_mdPath
    g_langcode = langcode
    g_mdPath = mdPath

    enc = detect_by_bom(inputPath, default="utf-8")
    input = io.open(inputPath, "tr", 1, encoding=enc)
    lines = input.readlines(-1)
    input.close

    if len(lines) > 0:
        state = State()
        state.newFile()
        nIn = 0
        nOut = 0
        # Open output .md file for writing.
        mdFile = io.open(mdPath, "tw", buffering=1, encoding='utf-8', newline='\n')
        for line in lines:
            nIn += 1
            line = line.rstrip()
            if blankheading_re.match(line):
                line = u""
                sys.stderr.write("Removed empty heading: " + shortname(mdPath) + " at line: " + str(nIn) + ". Must check manually.\n")
#             if len(line) > 0:
#                 if not hash:       # Find the first character in the file, should be a hash mark
#                     hash = line[0]
#                 if hash == u'*':    # The user used * instead of # to mark headings
#                     line = re.sub(r'^[ \t]*\*', u'#', line)
#                 elif nOut == 1 and hash != u'#':
#                     sys.stderr.write("File does not begin with heading: "  + shortname(mdPath) + "\n")                    
            if nIn == 1 and forgothash_re.match(line):
                line = u"# " + line
            if len(line.strip()) == 0:
                if nOut == 0:     # skip blank lines at top of input file
                    sys.stderr.write("Removing blank line at top of file: " + shortname(mdPath) + "\n")
                elif state.currlinetype == BLANKLINE:
                    sys.stderr.write("Conslidating blank lines in: " + shortname(mdPath) + "\n")
            else:
                convertLine(line, nIn, mdFile, inputPath, shortname)
                nOut += 1
        mdFile.close()
        statinfo = os.stat(mdPath)
        if statinfo.st_size == 0:
            sys.stderr.write("Removed empty: " + shortname(mdPath) + "\n")
            os.remove(mdPath)

hashes_re = re.compile(r'(#+)', re.UNICODE)
nospace = r'([^ \t].*)'
closedheading_re = re.compile(r'(#+[ \t]+.*?)#+\s*$', re.UNICODE)

# Fix poorly formed header lines
def fixHeadings(line):
    line = re.sub(r'#+[\s][\s]+', u'# ', line, count=1, flags=re.UNICODE)     # remove extra spaces/tabs after hash mark
    line = re.sub(r'\*+[\s][\s]+', u'* ', line, count=1, flags=re.UNICODE)    # remove extra spaces/tabs after asterisk
    
    # ensure space after hash(es)
    hashes = hashes_re.match(line)
    if hashes:
        strHashes = hashes.group(1)
        pattern = strHashes + nospace
        jam = re.match(pattern, line)
        if jam:
            line = strHashes + u" " + jam.group(1)
        line = uncloseHeading(line)
    return line

def fixBullets(line):
    line = line.replace(u'\x2E', u'*')
    line = line.replace(u'\xE2\x80\xA2', u'*')
    return line

# Changes heading style from opened to closed, by removing closing hash marks
def uncloseHeading(line):
    closed = closedheading_re.match(line)
    if closed:
        line = closed.group(1)
    return line


# Converts a line of markdown to a properly formatted line of markdown.
def convertLine(line, nIn, mdFile, path, shortname):
    line = fixHeadings(line)
    # line = fixBullets(line)
    origlen = len(line)
    line = normalize(line)
    needblank = False
    
    state = State()
    state.addLine(line)
    if state.currlinetype == HEADING:
        if state.prevlinetype and state.prevlinetype != BLANKLINE:
            needblank = True
    elif state.currlinetype == LIST_ITEM:
        if state.prevlinetype != LIST_ITEM and state.prevlinetype != BLANKLINE:
            needblank = True
    elif state.currlinetype == ORDEREDLIST_ITEM:
        if state.prevlinetype != ORDEREDLIST_ITEM and state.prevlinetype != BLANKLINE:
            needblank = True
    elif state.currlinetype == TEXT:
        line = line.lstrip()
        if state.prevlinetype in (HEADING, LIST_ITEM, ORDEREDLIST_ITEM):
            needblank = True

    if needblank:
        mdFile.write(u'\n')
    mdFile.write(line + u'\n')
    
    if len(line) - origlen > 15 or len(line) - origlen < -25:
        sys.stderr.write("Manually check conversion of line " + str(nIn) + " in " + shortname(path) + ".\n")
        sys.stderr.write("  Length difference: " + str(len(line) - origlen) + "\n")

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


# Returns a boolean value indicating whether the specified note should be converted.
def keepNote(note):
    keep = len(note) > 0 and (note['title'] or note['body'])
    if note['title'].strip() == "" and note['body'].strip() == "":
        keep = False
    
    # I deleted notes containing "bible:questions" from the Vietnamese collection.
    # if keep and note['title'].find(u"bible:questions") > 0 and note['body'].find(u"bible:questions") > 0:
    #     keep = False
    return keep

#
enurl_re = re.compile(r'(.*rc://)en(/.*)', re.UNICODE)  # a URL referencing an English language file

# NOTE: These patterns are very touchy. When changing, be sure to test on a large body of test cases.
#
bad9_re = re.compile(r'(.*[^\s(])\[\[:en:(.*)', re.UNICODE+re.DOTALL)         # missing space before left brackets
bad8_re = re.compile(r'(.*[^\[])\[?:en:(.*\].*)', flags=re.UNICODE+re.DOTALL)      # single/missing left bracket
bad0_re = re.compile(r'(.*\[\[:en:[^\n\]]*)]? *$', flags=re.UNICODE+re.DOTALL)    # single right bracket at end of string
bad1_re = re.compile(r'(.*\[\[:en:[^\n\]]*)]([^\]].*)', flags=re.UNICODE+re.DOTALL)  # single right bracket
bad2_re = re.compile(r'(.*\[\[:en:[^\n\]]*)([\n\)].*)', flags=re.UNICODE+re.DOTALL)  # no right bracket before right paren or newline
bad4_re = re.compile(r'(.*)]](\w.*)', flags=re.UNICODE)         # no space after right brackets
link_re = re.compile(r'(.*)(\[\[:en:[^\n\]]*\]\])(.*)', flags=re.UNICODE+re.DOTALL)     # matches a full link
# list0_re = re.compile(r'(.*\n)\*([^ ].*)', flags=re.UNICODE+re.DOTALL)      # no space after asterisk
list1_re = re.compile(r'^([^\*]*[^\n])\n\* (.*)', flags=re.UNICODE+re.DOTALL)        # no blank line before ordered list
list2_re = re.compile(r'(.*\* [^\n]*)\n([^\n\*].*)', flags=re.UNICODE+re.DOTALL)      # no blank line after ordered list
list3_re = re.compile(r'^\*([^ \*].*)', flags=re.UNICODE+re.DOTALL)      # no space after single asterisk at beginning of string

# This function is used by both md2md() and json2md().
# Cleans up the string destined for markdown file.
# Converts improper links [[:en:ta...]] to the current format.
# Converts &nbsp; to space character
# Returns fixed string.
def normalize(ustr):
    # Poorly formed links
    str = ustr.replace(u"[en:", u"[:en:")
    str = str.replace(u"[ en:", u"[:en:")
    str = str.replace(u"[: en:", u"[:en:")
    str = str.replace(u"]]]]", u"]]")
    str = str.replace(u"]]]", u"]]")
    str = str.replace(u"[[[[", u"[[")
    str = str.replace(u"[[[", u"[[")
    str = str.replace(u"\t", u" ")
    str = re.sub(r'\] *\(', u'](', str)
    str = re.sub(r'\n *-', u'\n*', str)
    str = re.sub(r'&nbsp;', u' ', str, count=0)
    
    if not g_multilist:
        str = re.sub(r'    *', u'  ', str)   # reduce runs of 3 or more spaces
        str = re.sub(r'\n +\*', u'\n*', str)     # removes spaces before asterisk, although they are required in multi-level lists (uncommon)
    
    str = re.sub(r'\n +\#', u'\n#', str)       # removes spaces before hash marks (new 5/30/19)
    str = re.sub(r'\n\*  +', u'\n* ', str)     # removes excess spaces after asterisk
    str = re.sub(r':\n\* ', u':\n\n* ', str)   # adds blank line at start of list

    # Left brackets
    str = re.sub(r'^\[?:?en:', u'[[:en:', str)   # fix missing bracket at beginning of string
    bad = bad8_re.match(str)
    while bad:
        str = bad.group(1) + u"[[:en:" + bad.group(2)
        bad = bad8_re.match(str)
    bad = bad9_re.match(str)
    while bad:
        str = bad.group(1) + u" [[:en:" + bad.group(2)
        bad = bad9_re.match(str)

    # Right brackets
    bad = bad0_re.match(str)
    if bad:
        str = bad.group(1) + u"]]"
    bad = bad1_re.match(str)
    while bad:
        str = bad.group(1) + u"]]" + bad.group(2)
        bad = bad1_re.match(str)
    bad = bad2_re.match(str)
    while bad:
        str = bad.group(1) + u"]]" + bad.group(2)
        bad = bad2_re.match(str)
    bad = bad4_re.match(str)
    while bad:
        str = bad.group(1) + u"]] " + bad.group(2)
        bad = bad4_re.match(str)

    # Unordered lists
#    bad = list0_re.match(str)      Commented out because *italics* is valid
#    while bad:
#        str = bad.group(1) + u'* ' + bad.group(2)
#        bad = list0_re.match(str)
    bad = list1_re.match(str)
    while bad:
        str = bad.group(1) + u'\n\n* ' + bad.group(2)
        bad = list1_re.match(str)
    bad = list2_re.match(str)
    while bad:
        str = bad.group(1) + u'\n\n' + bad.group(2)
        bad = list2_re.match(str)
    bad = list3_re.match(str)   # no space after asterisk at beginning of string
    if bad:
        str = u'* ' + bad.group(1)

    if g_langcode != "en":
        url = enurl_re.match(str)
        while url:
            str = url.group(1) + u"*" + url.group(2)
            url = enurl_re.match(str)

    # Fix what's inside the note links and tA links
    link = link_re.match(str)
    while link:
        linkstr = normalizeLink(link.group(2))      # group(2) is a full link [[:en:...]]
        # sys.stdout.write("linkstr: " + linkstr + '. link.group(1)[-1:]: ' + link.group(1)[-1:] + '.\n')
        str = link.group(1) + linkstr + link.group(3)
        link = link_re.match(str)
        
    str = fixBadRelativePath(str)
    return str

def normalizeLink(linkstr):
    lastpart = linkstr[5:-2]      # Strip [[:en, leaving  :ta:....  or  :bible:....
    lastpart = lastpart.replace(u'\n', u'')
    if lastpart.find(u"bible:notes") > 0:
        linkstr = normalizeNoteLink(lastpart)
    else:
        linkstr = normalizeTaLink(lastpart)
    return linkstr
    
fulllink_re = re.compile(r'.*:(\w\w\w):(\d+):(\d+)\|(.+)', flags=re.UNICODE)
partlink_re = re.compile(r'.*:(\w\w\w):(\d+):(\d+)', flags=re.UNICODE)

# Converts an old style notes link to the current format. Examples:
#   :bible:notes:1jn:02:04|2:5-6  --->  [1JN 2:5-6](../02/04.md)
#   :bible:notes:mat:17:01|17:1-8 --->  [MAT 17:1-8](../../mat/17/01.md)
#   :bible:notes:1ch:06:33|1 Chronicles 6:33  --->  [1 Chronicles 6:33](../06/33.md)
def normalizeNoteLink(lastpart):
    full = fulllink_re.match(lastpart)
    if not full:
        ref = full      # ref is referenced below, need to assign it here
        part = partlink_re.match(lastpart)
        if part:
            ref = part
            readable = buildBriefRef(part.group(1), part.group(2), part.group(3))
    else:
        ref = full
        readable = buildReadableRef(full.group(1), full.group(4))
    if ref:
        linkstr = readable + buildFileRef(ref.group(1), ref.group(2), ref.group(3))
    else:
        linkstr = u"[linkerror" + lastpart + u"]"    # revert to old style link, to be dealt with manually
    return linkstr        

# Builds the most readable verse reference possible from the specified parameters, in square brackets.
def buildBriefRef(bookId, chapter, verse):
    while chapter[0] == '0':
        chapter = chapter[1:]
    while verse[0] == '0':
        verse = verse[1:]
    return u'[' + bookId.upper() + u' ' + chapter + u':' + verse + u']'

readable_re = re.compile(r'(.*) (\d+:\d+[-\d]*)', flags=re.UNICODE)
# Builds the most readable verse reference possible from the specified parameters, in square brackets.
# reference may be just chapter and verse(s), or it may have a book name on the front.
def buildReadableRef(bookId, reference):
    # sys.stdout.write("buildReadableRef(" + bookId + ", " + reference + ")\n")
    ref = readable_re.match(reference)
    if ref:
        str = u'[' + ref.group(1) + u' ' + ref.group(2) + u']'
    else:
        str = u'[' + bookId.upper() + u' ' + reference + u']'
    return str

# Builds a relative path to the referent .md file, in parentheses. 
def buildFileRef(bookId, chapter, chunk):
    global g_mdPath
    chapter = leadZeros(bookId, chapter)
    chunk = leadZeros(bookId, chunk)
    partialpath1 = '/' + bookId.lower() + '/' + chapter + '/'
    partialpath2 = '\\' + bookId.lower() + '\\' + chapter + '\\'
    if g_mdPath.find(partialpath1) > 0 or g_mdPath.find(partialpath2) > 0:    # same book and chapter
        str = u'(./' + chunk + u'.md)'
    else:
        partialpath1 = '/' + bookId.lower() + '/'
        partialpath2 = '\\' + bookId.lower() + '\\'
        if g_mdPath.find(partialpath1) > 0 or g_mdPath.find(partialpath2) > 0:     # same book
            str = u'(../' + chapter + u'/' + chunk + u'.md)'
        else:
            str = u'(../../' + bookId.lower() + u'/' + chapter + u'/' + chunk + u'.md)'
    return str

# Adds the appropriate number of leading 0s to the name
def leadZeros(bookId, name):
    if len(name) == 1:
        name = '0' + name
    if bookId.lower() == 'psa' and len(name) == 2:
        name = '0' + name
    return name

# Updates :en:ta links to current format.
# Changes any colons in the links to slashes, underscores to dashes.
# Eliminates spaces.
# Changes /vol1/ or /vol2/ to /man/
# Fixes language code.
def normalizeTaLink(lastpart):
    lastpart = lastpart.lower()
    lastpart = lastpart.replace(u' ', u'')
    lastpart = lastpart.replace(u':', u'/')
    lastpart = lastpart.replace(u'_', u'-')
    lastpart = lastpart.replace(u'/vol1/', u'/man/')
    lastpart = lastpart.replace(u'/vol2/', u'/man/')
    lastpart = re.sub(r'\|[^\]]*', u'', lastpart, flags=re.UNICODE)

    goodlink = u"[[rc://" + u"*" + lastpart + u"]]"
    return goodlink

badbita_re = re.compile(r'(.*\()(bita-.*?)(\).*)', flags=re.UNICODE+re.DOTALL)     # matches a bad relative path in tA link to bita parts
badfigs_re = re.compile(r'(.*\()(figs-.*?)(\).*)', flags=re.UNICODE+re.DOTALL)     # matches a bad relative path in tA link to figs articles

# This is a fix for some specific bad links found in English tA and most translations thereof.
# Was tired of fixing them manually.
def fixBadRelativePath(str):
    bad = badbita_re.match(str)
    while bad:
        str = bad.group(1) + u"../" + bad.group(2) + u"/01.md" + bad.group(3)
        bad = badbita_re.match(str)
    bad = badfigs_re.match(str)
    while bad:
        str = bad.group(1) + u"../" + bad.group(2) + u"/01.md" + bad.group(3)
        bad = badfigs_re.match(str)
    return str


# Returns the specified title with newlines removed
def normalizeTitle(titlestr):
    if not titlestr:
        titlestr = u"X"     # null titles cause warnings
    titlestr = titlestr.replace(u'\n', u' ')
    titlestr = titlestr.replace(u'\r', u' ')
    return normalize(titlestr)
