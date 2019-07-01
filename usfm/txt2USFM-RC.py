# coding: latin-1
#### ###### -*- coding: utf-8 -*-

# This script converts text files from tStudio to USFM Resource Container format.
#    Parses manifest.json to get the book ID.
#    Outputs list of contributors gleaned from all manifest.json files.
#    Finds and parses title.txt to get the book title.
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once.

# Global variables
contributors = []
target_dir = r'C:\DCS\Spanish\es-419_ulb'

import usfm_verses
import re

verseMarker_re = re.compile(r'[ \n\t]*\\v *[\d]', re.UNICODE)
chapMarker_re = re.compile(r'\\c *[\d]{1,3}', re.UNICODE)

# Copies named file to XX-orig.txt.
# Calls ensureMarkers() to put in missing chapter and verse markers.
# @param verserange is a set of verse number strings that should exist in the file.
# On exit, the named file contains the improved chunk.
# On exit, XX-orig.txt contains the original chunk, if different.
def cleanupChunk(directory, filename, verserange):
    dot = filename.find('.')
    verse = filename[0:dot]
    path = directory + "/" + filename
    input = io.open(path, "tr", 1, encoding='utf-8')
    text = input.read(-1)
    input.close()

    chapter = u""
    if int(verse) == 1 and lacksChapter(text):
        chapter = directory.lstrip('0')
    if len(verseMarker_re.findall(text)) >= len(verserange):     # there are enough verse markers
        verserange = {}
    # lacking = lacksMarkers(input, chapter.lstrip('0'), verse.lstrip('0'))  # returns (lacksC, lacksV) pair
    # input.seek(0)
    # changed = ensureFirstMarkers(input, output, lacking[0], lacking[1])
    if chapter or verserange:
        ext = filename[dot:]
        tmpPath = directory + "/" + verse + "-orig" + ext
        if os.access(tmpPath, os.F_OK):
            os.remove(tmpPath)
        os.rename(path, tmpPath)
        output = io.open(path, "tw", 1, encoding='utf-8', newline='\n')
        ensureMarkers(text, output, chapter, int(verse), verserange)
        output.close()
    # if not changed:
        # # Restore the original file
        # os.remove(path)
        # os.rename(tmpPath, path)

# Returns True unchanged if there is no \c marker before the first verse marker.
# Returns False if \c marker precedes first verse marker.
def lacksChapter(text):
    verseMarker = verseMarker_re.search(text)
    if verseMarker:
        text = text[0:verseMarker.start()]
    return (not chapMarker_re.search(text))

numberMatch_re = re.compile(r'[ \n\t]*([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)
number_re =     re.compile(r'[^v][ \n]([\d]{1,3}[ \n])', re.UNICODE+re.DOTALL)

# Writes chapter marker at beginning of file if needed.
# Write initial verse marker and number at beginning of file if needed.
# Finds orphaned verse numbers and inserts \v before them.
def ensureMarkers(text, output, missingChapter, firstverse, verserange):
    # foundV = False
    # foundText = False
    # markerExpr = re.compile(r'\\\\[a-z0-9]+[ \n\t]+[\d]{0,3}')
    if missingChapter:
        output.write(u"\\c " + missingChapter + '\n')
    if not verserange:
        output.write(text)
    else:
        chap = chapMarker_re.search(text)
        if chap:
            output.write(text[0:chap.end()])
            text = text[chap.end():]
        initialVerse = verseMarker_re.match(text)
        if not initialVerse:
            text = u"\\v " + str(firstverse) + u" " + text      # insert initial verse marker
        number = numberMatch_re.match(text)
        if not number:
            number = number_re.search(text)
        while number:
            # verse = number.group(1)
            verse = number.group(1)[0:-1]
            if verse in verserange:
                output.write(text[0:number.start(1)] + u"\\v " + number.group(1))
            else:
                output.write(text[0:number.end()])
            text = text[number.end():]
            number = number_re.search(text)
        output.write(text)


# Looks for \c marker missing before wantChapter, and/or \v missing before wantVerse
# @param input is a file handle
# @param wantChapter is chapter number expected, or "" if not at the beginning of chapter
# @parma wantVerse is always the first verse expected in the file
# This function returns a pair where the first item is the missing chapter, or "", and the
# second item is the missing verse, or "".
""" def lacksMarkers(input, wantChapter, wantVerse):
    foundV = False
    foundText = False
    markerExpr = re.compile(r'\\\\[a-z0-9]+[ \n\t]+[\d]{0,3}')

    line = input.readline()
    while line and not foundV and not foundText:
        s = line.lstrip()
        match = markerExpr.search(s)
        while match and not foundV:
            # Peel off and output leading USF markers
            marker = s[match.start():match.end()]
            # print "WRITING MARKER: <" + marker + ">"
            if marker[0:2] == "\\c" and not foundV:
                wantChapter = ""
            elif marker[0:2] == "\\v" and not foundText:
                foundV = True
                wantVerse = ""
            s = s[match.end():].lstrip()    # s has everything after the marker
            # print "S AFTER STRIPPING PREV MATCH: <" + s + ">"
            match = markerExpr.match(s)

        # At this point, S contains the remainder of the input on the current line
            
        if len(s) > 1 and not foundV:
            # At this point we have a non-empty string with no leading markers
            foundText = True
        else:
            # The line was blank or had markers only
            line = input.readline()
    return (wantChapter, wantVerse)
 """

# Many input files are missing the first verse marker.
# This function prepends a verse marker if missing. The verse number is based on the file name.
# Since all 01.txt input files start a new chapter, they should all start with a chapter marker.
# This method makes it so.
# Returns True if any missing markers were corrected.
""" def ensureFirstMarkers(input, output, missingChapter, missingVerse):
    foundV = False
    changes = (missingChapter or missingVerse)
    markerExpr = re.compile(r'\\\\[a-z0-9]+[ \n\t]+[\d]{0,3}')

    line = input.readline()
    while line and (missingChapter or missingVerse):
        s = line.lstrip()
        match = markerExpr.match(s)
        while match and not foundV:
            # Peel off and output leading USF markers
            marker = s[match.start():match.end()]
            # print "WRITING MARKER: <" + marker + ">"
            if marker[0:2] == "\\v" and missingChapter:
                output.write(u"\\c " + missingChapter + u"\n")
                missingChapter = ""
                missingVerse = ""
                foundV = True
            output.write(marker + u'\n')
            s = s[match.end():].lstrip()    # s has everything after the marker
            # print "S AFTER STRIPPING PREV MATCH: <" + s + ">"
            match = markerExpr.match(s)

        # At this point the output file contains everything up to where a verse marker
        # or text is found.
        # S contains everything in the current line not yet written to the output file.
            
        if len(s) > 1:    # Found text before verse marker appeared, or verse marker was found
            if missingChapter:
                output.write(u"\\c " + missingChapter + u"\n")
                missingChapter = ""
            if missingVerse:
                output.write(u"\\v " + missingVerse + u"\n")
                missingVerse = ""
            output.write(s + u"\n")
        line = input.readline()

    if missingChapter:
        output.write(u"\\c " + missingChapter + u"\n")
        missingChapter = ""
    if missingVerse:
        output.write(u"\\v " + missingVerse + u"\n")
        missingVerse = ""
    while line:
        output.write(line)
        line = input.readline()
    return changes
 """
# Restores files that were renamed to XX-orig.txt by cleanupCheck().
# Renames fixed XX.txt file to XX-fixed.txt.
def restoreOrigFile(directory, filename):
    dot = filename.find('.')
    verse = filename[0:dot]
    ext = filename[dot:]
    path = directory + "/" + filename
    tmpPath = directory + "/" + verse + "-orig" + ext
    if os.access(tmpPath, os.F_OK):
        fixPath = directory + "/" + verse + "-fixed" + ext
        if os.access(fixPath, os.F_OK):
            os.remove(fixPath)
        os.rename(path, fixPath)
        os.rename(tmpPath, path)


# Does a first pass on a list of lines to eliminate unwanted line breaks,
# tabs, and extra whitespace. Places most markers at the beginning of lines.
# May perform other first pass cleanup tasks.
def combineLines(lines):
    section = ""
    for line in lines:
        line = line.strip(" \t\r\n")    # strip leading and trailing whitespace
        line = line.replace("\t", " ")
        line = line.replace("   ", " ")
        line = line.replace("  ", " ")
        line = line.replace(" \\c", "\n\\c")
        line = line.replace(" \\p", "\n\\p")
        line = line.replace(" \\s", "\n\\s")
        line = line.replace("\\v", "\n\\v")
        # line = line.replace(" \\v", "\n\\v")
        line = line.strip(" \t\r\n")    # strip trailing spaces

        if line:    # disregard lines that reduced to nothing
            if len(section) == 0:
                section = line
            else:
                if line[0] != '\\':
                    section = section + " " + line
                else:
                    section = section + "\n" + line
    return section

cvExpr = re.compile(u'\\\\[cv] [0-9]+')

# Prepends an s5 marker before the first chapter or verse marker.
def addSectionMarker(section):
    marker = cvExpr.search(section)
    if marker:
        newsection = section[0:marker.start()] + u'\\s5\n' + section[marker.start():]
    else:
        newsection = section    # this should rarely occur
    return newsection

# Adds a paragraph marker after each chapter marker
# Where a chapter does not start a new paragraph (like John 8), manually
# replace the paragraph marker with \nb.
def addParagraphMarker(section):
    tokenlist = re.split('(\\\\c [0-9]+)', section)
    marked = ""
    for token in tokenlist:
        if re.match('\\\\c [0-9]+', token):
            token = token + "\n\\p"   # add paragraph mark after each chapter marker
        marked = marked + token
    return marked

# Removes extraneous space before clause ending punctuation and adds space after
# sentence/clause end if needed.
def fixPunctuationSpacing(section):
    # First remove space before most punctuation
    section = section.replace(" .", ".")
    section = section.replace(" ;", ";")
    section = section.replace(" :", ":")
    section = section.replace(" ,", ",")
    section = section.replace(" ?", "?")
    section = section.replace(" !", "!")
    section = section.replace(" )", ")")
    section = section.replace(u" �", u"�")
    section = section.replace(u" �", u"�")

    # Then add space after punctuation where needed
    jammed = re.compile(u"[.?!;:,)][^ .?!;:,)'����\"]")
    match = jammed.search(section, 0)
    while match:
        if match.end() < len(section) and section[match.end()-1] != '\n':
            section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end() - 1
        match = jammed.search(section, pos)
    return section
    
# Inserts space between \c and the chapter number if needed
def fixChapterMarkers(section):
    pos = 0
    match = re.search(u'\\\\c[0-9]', section, 0)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end()
        match = re.search(u'\\\\c[0-9]', section, pos)
    return section
    
# Fixes the format of verse markers in the section
# All verse markers in the incoming string should already be at the beginning of a line.
# Converts "\v 10 10" or "\v10 10" or "\v10" to "\v 10"
def fixVerseMarkers(section):
    # Ensure space after each \v
    jammed = re.compile(u'\\\\v[0-9]')
    match = jammed.search(section, 0)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end()
        match = jammed.search(section, pos)
    # print "A. section length is " + str(len(section))

    # Take care of repeated verse numbers
    tokenlist = re.split('(\\\\v [0-9]+ [0-9]+)', section)
    section = ""
    repeatedVerseNumber = re.compile(u'\\\\v [0-9]+ [0-9]+')
    for token in tokenlist:
        if repeatedVerseNumber.match(token):
            parts = re.split(' ', token)
            verse = parts[1]
            if parts[2] == verse:
                token = "\\v " + verse
        section = section + token
    # print "B. section length is " + str(len(section))

    # Ensure space after verse number
    jammed = re.compile(u'\\\\v [0-9]+[^ \n-0123456789]')
    match = jammed.search(section)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        match = jammed.search(section)
    # print "C. section length is " + str(len(section))

    # Eliminate duplicate verse markers
    vm = re.compile(u'(\\\\v [0-9]+)')
    tokenlist = re.split(vm, section)
    section = ""
    lastVerseMarker = ""
    for token in tokenlist:
        if vm.match(token):
            if token != lastVerseMarker:
                lastVerseMarker = token
                section = section + token
            # else:
                # sys.stdout.write("\nREMOVED DUPLICATE VERSE MARKER: " + token + '\n')
        else:
            section = section + token
    
    # print "D. section length is " + str(len(section))
    return section
    
import io
import os

# Accepts a directory, and single file name which contains one chunk.
# Reads all the lines from that file and converts the text to a single
# USFM section.
def convertFile(txtPath):
    input = io.open(txtPath, "tr", 1, encoding='utf-8')
    lines = input.readlines()
    input.close()
    section = u"\n" + combineLines(lines)
    section = addSectionMarker(section)
    section = addParagraphMarker(section)
    # Most texts already have paragraph markers after chapter markers
    section = fixPunctuationSpacing(section)
    section = fixChapterMarkers(section)
    section = fixVerseMarkers(section)
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
        f = open(path, 'r')
    except IOError as e:
        sys.stderr.write("   Can't open: " + path + "!\n")
        sys.stderr.flush()
    else:
        global contributors
        try:
            manifest = json.load(f)
        except ValueError as e:
            sys.stderr.write("   Can't parse: " + path + ".\n")
            sys.stderr.flush()
        else:
            bookId = manifest['project']['id']
            contributors += manifest['translators']
        f.close()
    return bookId.upper()

# Parses all *manifest.json files in the current folder.
# If more than one manifest.json, their names vary.
# Return upper case bookId, or empty string if failed to retrieve.
# Also parses translator names out of the manifest, adds to global contributors list.
def getBookId(folder):
    bookId = ""
    for file in os.listdir(folder):
        if file.find("manifest") >= 0 and file.find(".json") >= 8:
            path = os.path.join(folder, file)
            if os.path.isfile(path):
                bookId = parseManifest(path)
    return bookId

# Locates title.txt in either the front folder or 00 folder.
# Extracts the first line of that file as the book title.
def getBookTitle():
    bookTitle = ""
    path = os.path.join("front", "title.txt")
    if not os.path.isfile(path):
        path = os.path.join("00", "title.txt")
    if os.path.isfile(path):
        f = io.open(path, "tr", 1, encoding='utf-8')
        bookTitle = f.readline()
        f.close()
    else:
        sys.stderr.write("   Can't open " + path + "!\n")
    return bookTitle 

def appendToManifest(bookId, bookTitle):
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    manifest.write(u"  -\n")
    manifest.write(u"    title: '" + bookTitle + u" '\n")
    manifest.write(u"    versification: ufw\n")
    manifest.write(u"    identifier: '" + bookId.lower() + u"'\n")
    manifest.write(u"    sort: " + str(usfm_verses.verseCounts[bookId]['sort']) + u"\n")
    manifest.write(u"    path: ./" + makeUsfmFilename(bookId) + u"\n")
    testament = u'nt'
    if usfm_verses.verseCounts[bookId]['sort'] < 40:
        testament = u'ot'
    manifest.write(u"    categories: [ 'bible-" + testament + u"' ]\n")
    manifest.close()

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
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
            convertBook(bookId, bookTitle)   # converts the pieces in the current folder
            appendToManifest(bookId, bookTitle)
            # sys.stdout.write("\n")
            # sys.stdout.flush()
 
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
    usfmfile.write(u"\\id " + bookId + u"\n\\ide UTF-8")
    usfmfile.write(u"\n\\h " + bookTitle)
    usfmfile.write(u"\n\\toc1 " + bookTitle)
    usfmfile.write(u"\n\\toc2 " + bookTitle)
    usfmfile.write(u"\n\\toc3 " + bookId.lower())
    usfmfile.write(u"\n\\mt " + bookTitle + u"\n")

# Eliminates duplicates from contributors list and sorts the list.
# Outputs list to contributors.txt.
def dumpContributors():
    global contributors
    contribs = list(set(contributors))
    contribs.sort()
    path = os.path.join(target_dir, "contributors.txt")
    f = io.open(path, 'tw', encoding='utf-8', newline='\n')
    for name in contribs:
        if name:
            f.write(u'    - "' + name + u'"\n')
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
    verserange = { chunks[i].lstrip('0') }
    if i+1 < len(chunks):
        limit = int(chunks[i+1])
    else:           # last chunk
        limit = usfm_verses.verseCounts[bookId]['verses'][chapter-1] + 1
    v = int(chunks[i]) + 1
    while v < limit:
        verserange.add(str(v))
        v += 1
    return verserange

# This method is called to convert the chapters in the *current folder* to USFM
def convertBook(bookId, bookTitle):
    chapters = listChapters(os.getcwd())
    # Open output USFM file for writing.
    usfmPath = os.path.join(target_dir, makeUsfmFilename(bookId))
    usfmFile = io.open(usfmPath, "tw", buffering=1, encoding='utf-8', newline='\n')
    writeHeader(usfmFile, bookId, bookTitle)

    for chap in chapters:
        chunks = listChunks(chap)
        i = 0
        while i < len(chunks):
            filename = chunks[i] + ".txt"
            txtPath = os.path.join(chap, filename)
            cleanupChunk(chap, filename, makeVerseRange(chunks, i, bookId, int(chap)))
            section = convertFile(txtPath) + u'\n'
            usfmFile.write(section)
            restoreOrigFile(chap, filename)
            i += 1
        # Process misnamed 00.txt file last, if it exists
        # if os.access(chap + "/00.txt", os.F_OK):
        #     section = convertFile(chap, "00.txt") + u'\n'
        #     usfmFile.write(section)
    # Wrap up
    usfmFile.close()
    # print "\nFINISHED: " + usfmPath

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

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convert(r'C:\DCS\Spanish\NT\es-419_1pe_text_lvl3_ulb')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print "\nDone."
