# -*- coding: utf-8 -*-
# This script converts text files from tStudio to USFM Resource Container format.
#    Parses manifest.json to get the book ID.
#    Outputs list of contributors gleaned from all manifest.json files.
#    Finds and parses title.txt to get the book title.
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once if there are multiple books.

# Global variables
source_dir = r'C:\DCS\Havu\REG'  # must be a folder
target_dir = r'C:\DCS\Havu\work'
language_code = "Havu"
mark_chunks = False   # Should be true for GL source text

import usfm_verses
import re
import operator
import io
import os

verseMarker_re = re.compile(r'[ \n\t]*\\v *([\d]{1,3})', re.UNICODE)
verseTags_re = re.compile(r'\\v +[^1-9]', re.UNICODE)
numbers_re = re.compile(r'[ \n]([\d]{1,3})[ \n]', re.UNICODE)
numberstart_re = re.compile(r'([\d]{1,3})[ \n]', re.UNICODE)
chapMarker_re = re.compile(r'\\c *[\d]{1,3}', re.UNICODE)
chaplabel_re = re.compile(r'\\cl', re.UNICODE)

contributors = []
projects = []

# Calls ensureMarkers() to put in missing chapter and verse markers.
# Inserts chapter title where appropriate.
# verserange is a list of verse number strings that should exist in the file.
# On exit, the named file contains the improved chunk.
# On exit, XX.txt-orig. contains the original chunk, if different.
def cleanupChunk(directory, filename, verserange):
    # dot = filename.find('.')
    # verse_start = filename[0:dot]
    vn_start = int(verserange[0])
    vn_end = int(verserange[-1])
    path = os.path.join(directory, filename)
    input = io.open(path, "tr", encoding='utf-8-sig')
    origtext = input.read()
    input.close()
    text = fixVerseMarkers(origtext)
    text = fixChapterMarkers(text)
    text = fixPunctuationSpacing(text)

    missing_chapter = ""
    if vn_start == 1 and lacksChapter(text):
        missing_chapter = directory.lstrip('0')
    missing_verses = lackingVerses(text, verserange, numbers_re)
    missing_markers = lackingVerses(text, verserange, verseMarker_re)
    if missing_chapter or missing_verses or missing_markers:
        if verseTags_re.search(text):
            if missing_verses:
                text = ensureNumbers(text, missing_verses)
                missing_verses = lackingVerses(text, verserange, numbers_re)
        text = ensureMarkers(text, missing_chapter, vn_start, vn_end, missing_verses, missing_markers)
    if language_code == "ior":
        text = fixInorMarkers(text, verserange)

    if text != origtext:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
        output = io.open(path, "tw", 1, encoding='utf-8', newline='\n')
        output.write(text)
        output.close()

# Returns True unchanged if there is no \c marker before the first verse marker.
# Returns False if \c marker precedes first verse marker.
def lacksChapter(text):
    verseMarker = verseMarker_re.search(text)
    if verseMarker:
        text = text[0:verseMarker.start()]
    return (not chapMarker_re.search(text))

# Searches for the expected verse numbers in the string using the specified expression.
# Returns list of verse numbers (marked or unmarked) missing from the string
def lackingVerses(str, verserange, expr_re):
    missing_verses = []
    numbers = expr_re.findall(str)
#    if len(numbers) < len(verserange):     # not enough verse numbers
    versenumbers_found = []
    for vn in numbers:
        if vn in verserange:
            versenumbers_found.append(vn)
    for verse in verserange:
        if not verse in versenumbers_found:
            missing_verses.append(verse)
    return missing_verses

numberMatch_re = re.compile(r'[ \n\t]*([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)
untaggednumber_re =     re.compile(r'[^v][ \n]([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)

# Writes chapter marker at beginning of file if needed.
# Write initial verse marker and number at beginning of file if needed.
# Finds orphaned verse numbers and inserts \v before them.
# missingVerses is a list of verse numbers (in string format) not found in the string
# missingMarkers is a list of verse markers (e.g. "\v 1") not found in the string
# Returns corrected string.
def ensureMarkers(text, missingChapter, vn_start, vn_end, missingVerses, missingMarkers):
    goodstr = ""
    if missingChapter:
        goodstr = "\\c " + missingChapter + '\n'
    if not (missingVerses or missingMarkers):
        goodstr += text
    else:
        chap = chapMarker_re.search(text)
        if chap:
            goodstr += text[0:chap.end()] + '\n'
            text = text[chap.end():]

        verseAtStart = numberstart_re.match(text)
        if (missingVerses or missingMarkers) and not verseAtStart:
            verseAtStart = verseMarker_re.match(text)
        if not verseAtStart:
            startVV = missingStartVV(vn_start, vn_end, text)
            text = startVV + text      # insert initial verse marker
        number = numberMatch_re.match(text)          # matches orphaned number at beginning of the string
        if not number:
            number = untaggednumber_re.search(text)          # finds orphaned number anywhere in string
        while number:
            # verse = number.group(1)
            verse = number.group(1)[0:-1]
            if verse in missingMarkers:         # outputs \v then the number
                goodstr += text[0:number.start(1)] + "\\v " + number.group(1)
            else:
                goodstr += text[0:number.end()]   # leave untagged number as is and move on
            text = text[number.end():]
            number = untaggednumber_re.search(text)
        goodstr += text
    return goodstr

# Generates a string like "\v 1"  or "\v 1-3" which should be prepended to the specified text
# start_vn is the starting verse number
def missingStartVV(vn_start, vn_end, text):
    firstVerseFound = verseMarker_re.search(text)
    if firstVerseFound:
        firstVerseNumberFound = int(firstVerseFound.group(1))
    else:
        firstVerseNumberFound = 999
    vn = vn_start
    while vn < firstVerseNumberFound - 1 and vn < vn_end:
        vn += 1
    if vn_start == vn:
        startVV = "\\v " + str(vn_start) + " "
    else:
        startVV = "\\v " + str(vn_start) + "-" + str(vn) + " "
    return startVV

def ensureNumbers(text, missingVerses):
    missi = 0
    while missi < len(missingVerses):
        versetag = verseTags_re.search(text)
        if versetag:
            text = text[0:versetag.end()-1] + missingVerses[missi] + " " + text[versetag.end()-1:]
        missi += 1
    return text

sub0_re = re.compile(r'/v +[1-9]', re.UNICODE)      # slash v
sub0b_re = re.compile(r'\\\\v +[1-9]', re.UNICODE)  # double backslash v
sub1_re = re.compile(r'[^\n ]\\v ', re.UNICODE)     # no space before \v
sub2_re = re.compile(r'[\n \.,"\'?!]\\ *v[1-9]', re.UNICODE)   # no space before verse number, possible space betw \ and v
sub2m_re = re.compile(r'\\ *v[1-9]', re.UNICODE)       # no space before verse number, possible space betw \ and v  -- match
sub3_re = re.compile(r'\\v +[0-9\-]+[^0-9\-\n ]', re.UNICODE)       # no space after verse number
sub4_re = re.compile(r'(\\v +[0-9\-]+ +)\\v +[^1-9]', re.UNICODE)   # \v 10 \v The...
sub5_re = re.compile(r'\\v( +\\v +[0-9\-]+ +)', re.UNICODE)         # \v \v 10
sub6_re = re.compile(r'[\n ]\\ v [1-9]', re.UNICODE)           # space betw \ and v
sub6m_re = re.compile(r'\\ v [1-9]', re.UNICODE)               # space betw \ and v -- match
sub7_re = re.compile(r'[\n ]v [1-9]', re.UNICODE)              # missing backslash
sub8_re = re.compile(r'(.)([\n ]*\\v [1-9]+) ?([\.\,\:;]) ', re.UNICODE)   # Punctuation after verse marker
sub9_re = re.compile(r'(\\v [1-9]+) ?([\.\,\:;]) ', re.UNICODE)

# Fixes malformed verse markers
def fixVerseMarkers(text):
    found = sub0_re.search(text)
    while found:
        text = text[0:found.start()] + "\\" + text[found.start()+1:]
        found = sub0_re.search(text, found.start()+3)

    found = sub0b_re.search(text)
    while found:
        text = text[0:found.start()] + text[found.start()+1:]
        found = sub0b_re.search(text, found.start()+3)

    found = sub1_re.search(text)
    while found:
        text = text[0:found.start()+1] + "\n" + text[found.end()-3:]
        found = sub1_re.search(text, found.start()+3)

    if found := sub2m_re.match(text):
        text = '\\v ' + text[found.end()-1:]
    found = sub2_re.search(text)
    while found:
        text = text[0:found.start()+1] + '\n\\v ' + text[found.end()-1:]
        found = sub2_re.search(text, found.end()+1)

    found = sub3_re.search(text)
    while found:
        text = text[0:found.end()-1] + " " + text[found.end()-1:]
        found = sub3_re.search(text, found.end()+1)

    found = sub4_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end()-1:]
        found = sub4_re.search(text)

    found = sub5_re.search(text)
    while found:
        text = text[0:found.start()] + found.group(1) + text[found.end():]
        found = sub5_re.search(text)

    if found := sub6m_re.match(text):
        text = "\\v " + text[found.end()-1:]
    found = sub6_re.search(text)
    while found:
        text = text[0:found.start()] + "\n\\v " + text[found.end()-1:]
        found = sub6_re.search(text)

    found = sub7_re.search(text)
    while found:
        text = text[0:found.start()] + "\n\\v " + text[found.end()-1:]
        found = sub7_re.search(text)

    found = sub8_re.search(text)
    while found:
        if found.group(3) != found.group(1):
            text = text[0:found.start()+1] + found.group(3) + found.group(2) + text[found.end()-1:]
        else:
            text = text[0:found.start()+1] + found.group(2) + text[found.end()-1:]
        found = sub8_re.search(text)

    if found := sub9_re.match(text):
        text = found.group(1) + text[found.end()-1:]

    return text

# Does a first pass on a list of lines to eliminate unwanted line breaks,
# tabs, and extra whitespace. Places most markers at the beginning of lines.
# Returns single string containing newlines.
def combineLines(lines):
    section = ""
    for line in lines:
        line = line.replace("\t", " ")
        line = line.replace("   ", " ")
        line = line.replace("  ", " ")
        line = line.replace(" \\", "\n\\")
        line = line.strip()    # strip leading and trailing whitespace

        if line:    # discard lines that reduced to nothing
            if not section:
                section = line
            else:
                if line[0] == '\\' or line.startswith("==") or line.startswith(">>"):
                    section = section + "\n" + line
                else:
                    section = section + " " + line
    return section

cvExpr = re.compile(r'\\[cv] [0-9]+')
chapter_re = re.compile(r'\n\\c +[0-9]+[ \n]*', re.UNICODE)
# labeledChapter_re = re.compile(r'(\\c +[\d]{1,3}) +(.+?)$', re.UNICODE+re.MULTILINE)

# Adds section marker, chapter label, and paragraph marker as needed.
# Returns modified section.
def augmentChapter(section, chapterTitle):
    if mark_chunks:
        # section = addSectionMarker(section)
        if marker := cvExpr.search(section):
            section = section[0:marker.start()] + '\\s5\n' + section[marker.start():]

#    chap = labeledChapter_re.search(section)
#    if chap:
#        section = section[:chap.start()] + chap.group(1) + "\n\\cl " + chap.group(2) + "\n\\p" + section[chap.end():]
#    else:
    chap = chapter_re.search(section)
    if chap:
        if chapterTitle:
            clpstr = "\n\\cl " + chapterTitle + "\n\\p\n"
        else:
            clpstr = "\n\\p\n"
        section = section[:chap.end()].rstrip() + clpstr + section[chap.end():].lstrip()
    return section

spacedot_re = re.compile(r'[^0-9] [\.\?!;\:,][^\.]')    # space before clause-ending punctuation
jammed = re.compile(r'[\.\?!;:,)][\w]', re.UNICODE)     # no space between clause-ending punctuation and next word -- but \w matches digits also

# Removes extraneous space before clause ending punctuation and adds space after
# sentence/clause end if needed.
def fixPunctuationSpacing(section):
    # First remove space before most punctuation
    found = spacedot_re.search(section)
    while found:
        section = section[0:found.start()+1] + section[found.end()-2:]
        found = spacedot_re.search(section)

    # Then add space between clause-ending punctuation and next word.
    match = jammed.search(section, 0)
    while match:
        if section[match.end()-1] not in "0123456789":
            section = section[:match.start()+1] + ' ' + section[match.end()-1:]
        match = jammed.search(section, match.end())
    return section

# Inserts space between \c and the chapter number if needed
def fixChapterMarkers(section):
    pos = 0
    match = re.search('\\\\c[0-9]', section, 0)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end()
        match = re.search('\\\\c[0-9]', section, pos)
    return section

stripcv_re = re.compile(r'\s*\\([cv])\s*\d+\s*', re.UNICODE)

# Returns the string with \v markers removed at beginning of chunk.
def stripInitialMarkers(text):
    saveChapterMarker = ""
    marker = stripcv_re.match(text)
    while marker:
        text = text[marker.end():]
        marker = stripcv_re.match(text)
    return text

# Returns True if the string contains all the verse numbers in verserange and there are no \v tags
def fitsInorPattern(str, verserange):
    fits = not ("\\v" in str)
    if fits:
        for v in verserange:
            if not v in str:
                fits = False
                break
    return fits

# This method is only called for the Inor language.
# Fixes very common error in Inor translations where the verse markers are listed at the beginning of the
# chunk but are empty, immediately followed by the first verse, followed by the next verse number and
# verse, followed by the next verse number and verse, and so on.
def fixInorMarkers(text, verserange):
    saveChapterMarker = ""
    if c := chapMarker_re.search(text):
        saveChapterMarker = text[c.start():c.end()]
    str = stripInitialMarkers(text)
    if not str.startswith(verserange[0]):
        str = verserange[0] + " " + str
    if fitsInorPattern(str, verserange):
        for v in verserange:
            pos = str.find(v)
            if pos == 0:
                str = "\\v " + str[pos:]
            else:
                str = str[0:pos] + "\n\\v " + str[pos:]
        if saveChapterMarker:
            str = saveChapterMarker + "\n" + str

        # Ensure space after verse markers
        found = sub3_re.search(str)
        while found:
            pos = found.end()-1
            if str[pos] == '.':
                pos += 1
            str = str[0:found.end()-1] + " " + str[pos:]
            found = sub3_re.search(str, pos+1)
    else:
        str = text
    return str

# Reads all the lines from the specified file and converts the text to a single
# USFM section by adding chapter label, section marker, and paragraph marker where needed.
# Starts each usfm marker on a new line.
# Fixes white space, such as converting tabs to spaces and removing trailing spaces.
def convertFile(txtPath, chapterTitle):
    input = io.open(txtPath, "tr", 1, encoding='utf-8-sig')
    lines = input.readlines()
    input.close()
    section = "\n" + combineLines(lines)    # fixes white space
    section = augmentChapter(section, chapterTitle)
    # section = fixPunctuationSpacing(section)
    # section = fixChapterMarkers(section)
    return section

# Returns True if the specified directory is one with text files to be converted
def isChapter(dirname):
    isChap = False
    if dirname != '00' and re.match(r'\d{2,3}$', dirname):
        isChap = True
    return isChap

# Returns True if the specified path looks like a collection of chapter folders
def isBookFolder(path):
    chapterPath = os.path.join(path, '01')
    return os.path.isdir(chapterPath)

import sys
import json

def parseManifest(path):
    bookId = ""
    try:
        jsonFile = io.open(path, "tr", encoding='utf-8-sig')
    except IOError as e:
        sys.stderr.write("   Can't open: " + path + "!\n")
        sys.stderr.flush()
    else:
        global contributors
        try:
            manifest = json.load(jsonFile)
        except ValueError as e:
            sys.stderr.write("   Can't parse: " + path + ".\n")
            sys.stderr.flush()
        else:
            bookId = manifest['project']['id']
            contributors += [x.title() for x in manifest['translators']]

        jsonFile.close()
    return bookId.upper()

# Parses all manifest.json files in the current folder.
# If more than one manifest.json, their names vary.
# Return upper case bookId, or empty string if failed to retrieve.
# Also parses translator names out of the manifest, adds to global contributors list.
def getBookId(folder):
    bookId = None
    for file in os.listdir(folder):
        if file.find("manifest") >= 0 and file.find(".json") >= 8:
            path = os.path.join(folder, file)
            if os.path.isfile(path):
                bookId = parseManifest(path)
    if not bookId:
        matchstr = language_code + "_([a-zA-Z1-3][a-zA-Z][a-zA-Z])_"
        if okname := re.match(matchstr, os.path.basename(folder)):
            bookId = okname.group(1).upper()
    return bookId

# Locates title.txt in either the front folder or 00 folder.
# Extracts the first line of that file as the book title.
def getBookTitle():
    bookTitle = ""
    path = os.path.join("front", "title.txt")
    if not os.path.isfile(path):
        path = os.path.join("00", "title.txt")
    if os.path.isfile(path):
        f = io.open(path, "tr", 1, encoding='utf-8-sig')
        bookTitle = f.readline().strip()
        f.close()
    else:
        sys.stderr.write("   Can't open " + path + "!\n")
    return bookTitle

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    testament = 'nt'
    if usfm_verses.verseCounts[bookId]['sort'] < 40:
        testament = 'ot'
    project = { "title": bookTitle, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + makeUsfmFilename(bookId), "category": "[ 'bible-" + testament + "' ]" }
    projects.append(project)

def dumpProjects():
    projects.sort(key=operator.itemgetter('sort'))

    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
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

def convertFolder(folder):
    if not folder:
        folder = os.getcwd()
    try:
        os.chdir(folder)
    except IOError as e:
        sys.stderr.write("Invalid folder: " + folder + "\n")
        return
    except WindowsError as e:
        sys.stderr.write("Invalid folder: " + folder + "\n")
        return
    else:
        sys.stdout.write("Converting: " + shortname(folder) + "\n")
        sys.stdout.flush()
        bookId = getBookId(folder)
        bookTitle = getBookTitle()
        if bookId and bookTitle:
            convertBook(folder, bookId, bookTitle)   # converts the pieces in the current folder
            appendToProjects(bookId, bookTitle)
            # sys.stdout.write("\n")
            # sys.stdout.flush()
        else:
            if not bookId:
                sys.stderr.write("Unable to determine book ID in " + folder + "\n")
            if not bookTitle:
                sys.stderr.write("Unable to determine book title in " + folder + "\n")

# Returns file name for usfm file in current folder
def makeUsfmFilename(bookId):
    # loadVerseCounts()

    if len(usfm_verses.verseCounts) > 0:
        num = usfm_verses.verseCounts[bookId]['usfm_number']
        filename = num + '-' + bookId + '.usfm'
    else:
        pathComponents = os.path.split(os.getcwd())   # old method
        filename = pathComponents[-1] + ".usfm"
    return filename

# Returns path of temporary manifest file block listing projects converted
def makeManifestPath():
    return os.path.join(target_dir, "projects.yaml")

def writeHeader(usfmfile, bookId, bookTitle):
    usfmfile.write("\\id " + bookId + "\n\\ide UTF-8")
    usfmfile.write("\n\\h " + bookTitle)
    usfmfile.write("\n\\toc1 " + bookTitle)
    usfmfile.write("\n\\toc2 " + bookTitle)
    usfmfile.write("\n\\toc3 " + bookId.lower())
    usfmfile.write("\n\\mt " + bookTitle + "\n")

# Eliminates duplicates from contributors list and sorts it.
# Outputs list to contributors.txt.
def dumpContributors():
    global contributors
    contribs = list(set(contributors))
    contribs.sort()
    path = os.path.join(target_dir, "contributors.txt")
    f = io.open(path, 'tw', encoding='utf-8', newline='\n')
    for name in contribs:
        if name:
            f.write('    - "' + name + '"\n')
    f.close()

# This method returns a list of chapter folders in the specified directory.
# This list is returned in numeric order.
def listChapters(bookdir):
    list = []
    for directory in os.listdir(bookdir):
        if isChapter(directory):
            list.append(directory)
    if len(list) > 99:
        list.sort(key=int)
    return list

# This method lists the chunk names (just the digits, without the .txt extension)
# in the specified folder.
# The list is returned in numeric order.
def listChunks(chap):
    list = []
    longest = 0
    for filename in os.listdir(chap):
        chunky = re.match(r'(\d{2,3})\.txt$', filename)
        if chunky and filename != '00.txt':
            chunk = chunky.group(1)
            list.append(chunk)
            if len(chunk) > longest:
                longest = len(chunk)
    if longest > 2:
        list.sort(key=int)
    return list

# Compiles a list of verse number strings that should be in the specified chunk
def makeVerseRange(chunks, i, bookId, chapter):
    verserange = [ chunks[i].lstrip('0') ]
    if i+1 < len(chunks):
        limit = int(chunks[i+1])
    else:           # last chunk
        limit = usfm_verses.verseCounts[bookId]['verses'][chapter-1] + 1
    v = int(chunks[i]) + 1
    while v < limit:
        verserange.append(str(v))
        v += 1
    return verserange

# Tries to find front/title.txt or 00/title.txt.
# Returns the content of that file if it exists, or an empty string.
def getChapterTitle(folder, chap):
    title = ""
    chapterPath = os.path.join(folder, chap)
    path = os.path.join( os.path.join(folder, chap), "title.txt")
    if os.path.isfile(path):
        titlefile = io.open(path, 'tr', encoding='utf-8-sig')
        title = titlefile.read()
        titlefile.close()
    return title

# This method is called to convert the chapters in the current folder to USFM
def convertBook(folder, bookId, bookTitle):
    chapters = listChapters(folder)
    # Open output USFM file for writing.
    usfmPath = os.path.join(target_dir, makeUsfmFilename(bookId))
    usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
    writeHeader(usfmFile, bookId, bookTitle)

    for chap in chapters:
        chapterTitle = getChapterTitle(folder, chap)
        chunks = listChunks(chap)
        i = 0
        while i < len(chunks):
            filename = chunks[i] + ".txt"
            txtPath = os.path.join(chap, filename)
            cleanupChunk(chap, filename, makeVerseRange(chunks, i, bookId, int(chap)))
            section = convertFile(txtPath, chapterTitle) + '\n'
            usfmFile.write(section)
            i += 1
        # Process misnamed 00.txt file last, if it exists
        # if os.access(chap + "/00.txt", os.F_OK):
        #     section = convertFile(chap, "00.txt") + u'\n'
        #     usfmFile.write(section)
    # Wrap up
    usfmFile.close()

# Converts the book or books contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if isBookFolder(dir):
        convertFolder(dir)
    else:       # presumed to be a folder containing multiple books
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if isBookFolder(folder):
                convertFolder(folder)
    dumpContributors()
    dumpProjects()

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convert(source_dir)
        print("\nDone.")
    else:
        print("Not a valid folder: " + source_dir + '\n')
