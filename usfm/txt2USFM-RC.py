# -*- coding: utf-8 -*-
# This script converts text files from tStudio to USFM Resource Container format.
#    Parses manifest.json to get the book ID.
#    Outputs list of contributors gleaned from all manifest.json files.
#    Finds and parses title.txt to get the book title.
#    Populates the USFM headers.
#    Standardizes the names of .usfm files. For example 41-MAT.usfm and 42-MRK.usfm.
#    Converts multiple books at once.

# Global variables
target_dir = r'C:\DCS\Amo\work'
source_dir = r'C:\DCS\Amo\NT\amo_mat_text_reg'
mark_chunks = False     # Should be true for GL source text

import usfm_verses
import re
import operator
import io
import os

verseMarker_re = re.compile(r'[ \n\t]*\\v *([\d]{1,3})', re.UNICODE)
numbers_re =     re.compile(r'[ \n]([\d]{1,3})[ \n]', re.UNICODE)
numberstart_re = re.compile(r'([\d]{1,3})[ \n]', re.UNICODE)
chapMarker_re = re.compile(r'\\c *[\d]{1,3}', re.UNICODE)
contributors = []
projects = []

# Copies named file to XX-orig.txt.
# Calls ensureMarkers() to put in missing chapter and verse markers.
# @param verserange is a list of verse number strings that should exist in the file.
# On exit, the named file contains the improved chunk.
# On exit, XX-orig.txt contains the original chunk, if different.
def cleanupChunk(directory, filename, verserange):
    dot = filename.find('.')
    verse_start = filename[0:dot]
    path = directory + "/" + filename
    input = io.open(path, "tr", 1, encoding='utf-8-sig')
    text = input.read(-1)
    input.close()

    missing_chapter = ""
    if int(verse_start) == 1 and lacksChapter(text):
        missing_chapter = directory.lstrip('0')
    missing_verses = lackingVerses(text, verserange, numbers_re, directory, filename)
    missing_markers = lackingVerses(text, verserange, verseMarker_re, directory, filename)
    if missing_chapter or missing_verses or missing_markers:
        ext = filename[dot:]
        tmpPath = directory + "/" + verse_start + "-orig" + ext
        if os.access(tmpPath, os.F_OK):
            os.remove(tmpPath)
        os.rename(path, tmpPath)
        output = io.open(path, "tw", 1, encoding='utf-8', newline='\n')
        ensureMarkers(text, output, missing_chapter, verse_start, missing_verses, missing_markers)
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

# Searches for the expected verse numbers in the string
# Returns list of verse numbers (marked or unmarked) missing from the string
def lackingVerses(str, verserange, expr_re, directory, filename):
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
def ensureMarkers(text, output, missingChapter, verse_start, missingVerses, missingMarkers):
    # foundV = False
    # foundText = False
    # markerExpr = re.compile(r'\\\\[a-z0-9]+[ \n\t]+[\d]{0,3}')
    if missingChapter:
        output.write("\\c " + missingChapter + '\n')
    if not (missingVerses or missingMarkers):
        output.write(text)
    else:
        chap = chapMarker_re.search(text)
        if chap:
            output.write(text[0:chap.end()] + '\n')
            text = text[chap.end():]
        initialVerse = verseMarker_re.match(text)
        if not initialVerse:
            initialVerse = numberstart_re.match(text)
        if not initialVerse and missingVerses[0] == verse_start:
            verses = ""
            if len(missingVerses) == 1:
                verses = "\\v " + missingVerses[0] + "\n"
            else:
                verses += "\\v " + missingVerses[0] + "-" + missingVerses[-1] + " \n"
            text = verses + text      # insert initial verse marker
        number = numberMatch_re.match(text)          # matches orphaned number at beginning of the string
        if not number:
            number = untaggednumber_re.search(text)          # finds orphaned number anywhere in string
        while number:
            # verse = number.group(1)
            verse = number.group(1)[0:-1]
            if verse in missingMarkers:         # outputs \v then the number
                output.write(text[0:number.start(1)] + "\\v " + number.group(1))
            else:
                output.write(text[0:number.end()])  # leaves number as is
            text = text[number.end():]
            number = untaggednumber_re.search(text)
        output.write(text)

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
# Inserts chapter label if needed.
# May perform other first pass cleanup tasks.
# Returns single string containing newlines.
def combineLines(lines):
    section = ""
    for line in lines:
        line = line.replace("\t", " ")
        line = line.replace("   ", " ")
        line = line.replace("  ", " ")
        line = line.replace(" \\", "\n\\")
        line = line.strip()    # strip leading and trailing whitespace

        if line:    # disregard lines that reduced to nothing
            if not section:
                section = line
            else:
                if line[0] != '\\':
                    section = section + " " + line
                else:
                    section = section + "\n" + line
    return section

cvExpr = re.compile(r'\\[cv] [0-9]+')

# Prepends an s5 marker before the first chapter or verse marker.
def addSectionMarker(section):
    marker = cvExpr.search(section)
    if marker:
        newsection = section[0:marker.start()] + '\\s5\n' + section[marker.start():]
    else:
        newsection = section    # this should rarely occur
    return newsection

# labeledChapter_re = re.compile(r'(\\c +[\d]{1,3}) +(.+?)$', re.UNICODE+re.MULTILINE)
chapter_re = re.compile(r'\n\\c +[0-9]+[ \n]*', re.UNICODE)

# Prepends section marker if needed.
# Append chapter label if needed
# Appends paragraph marker if needed.
# Returns modified section.
def augmentChapter(section):
    if mark_chunks:
        section = addSectionMarker(section)
#    chap = labeledChapter_re.search(section)
#    if chap:
#        section = section[:chap.start()] + chap.group(1) + "\n\\cl " + chap.group(2) + "\n\\p" + section[chap.end():]
#    else:
    chap = chapter_re.match(section)
    if chap:
        section = section[:chap.end()].rstrip() + "\n\\p\n" + section[chap.end():].lstrip()
    return section          

spacedot_re = re.compile(r'[^0-9] \.')
commadot_re = re.compile(r'[^0-9] ,')

# Removes extraneous space before clause ending punctuation and adds space after
# sentence/clause end if needed.
def fixPunctuationSpacing(section):
    # First remove space before most punctuation
    section = spacedot_re.sub(". ", section)
    section = commadot_re.sub(", ", section)
#    section = section.replace(" .", ".")
#    section = section.replace(" ,", ",")
    section = section.replace(" ;", ";")
    section = section.replace(" :", ":")
    section = section.replace(" ?", "?")
    section = section.replace(" !", "!")
    section = section.replace(" )", ")")
    section = section.replace(" �", "�")
    section = section.replace(" �", "�")

    # Then add space after punctuation where needed
    jammed = re.compile("[.?!;:,)][^ .?!;:,)'�\"]")
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
    match = re.search('\\\\c[0-9]', section, 0)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end()
        match = re.search('\\\\c[0-9]', section, pos)
    return section
    
# Fixes the format of verse markers in the section
# All verse markers in the incoming string should already be at the beginning of a line.
# Converts "\v 10 10" or "\v10 10" or "\v10" to "\v 10"
def fixVerseMarkers(section):
    # Ensure space after each \v
    jammed = re.compile('\\\\v[0-9]')
    match = jammed.search(section, 0)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        pos = match.end()
        match = jammed.search(section, pos)
    # print "A. section length is " + str(len(section))

    # Take care of repeated verse numbers
    tokenlist = re.split('(\\\\v [0-9]+ [0-9]+)', section)
    section = ""
    repeatedVerseNumber = re.compile('\\\\v [0-9]+ [0-9]+')
    for token in tokenlist:
        if repeatedVerseNumber.match(token):
            parts = re.split(' ', token)
            verse = parts[1]
            if parts[2] == verse:
                token = "\\v " + verse
        section = section + token
    # print "B. section length is " + str(len(section))

    # Ensure space after verse number
    jammed = re.compile('\\\\v [0-9]+[^ \n-0123456789]')
    match = jammed.search(section)
    while match:
        section = section[:match.end()-1] + ' ' + section[match.end()-1:]
        match = jammed.search(section)
    # print "C. section length is " + str(len(section))

    # Eliminate duplicate verse markers
    vm = re.compile('(\\\\v [0-9]+)')
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
    
# Reads all the lines from the specified file and converts the text to a single
# USFM section.
def convertFile(txtPath):
    input = io.open(txtPath, "tr", 1, encoding='utf-8-sig')
    lines = input.readlines()
    input.close()
    section = "\n" + combineLines(lines)    # fixes white space
    section = augmentChapter(section)
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
        f = io.open(path, "tr", 1, encoding='utf-8-sig')
        bookTitle = f.readline()
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
    global projectts
    projects.sort(key=operator.itemgetter('sort'))

    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
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
            convertBook(bookId, bookTitle)   # converts the pieces in the current folder
            appendToProjects(bookId, bookTitle)
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
    usfmfile.write("\\id " + bookId + "\n\\ide UTF-8")
    usfmfile.write("\n\\h " + bookTitle)
    usfmfile.write("\n\\toc1 " + bookTitle)
    usfmfile.write("\n\\toc2 " + bookTitle)
    usfmfile.write("\n\\toc3 " + bookId.lower())
    usfmfile.write("\n\\mt " + bookTitle + "\n")

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
            section = convertFile(txtPath) + '\n'
            usfmFile.write(section)
            restoreOrigFile(chap, filename)
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
