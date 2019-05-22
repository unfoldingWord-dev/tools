# -*- coding: utf-8 -*-
# This script attempts to convert tN files exported from V-MAST into .txt files that
# tS can import.
# In general, the input files contain a series of notes, of which the note title begins
# with hash marks and the body does not. There must be a blank line between each title
# and body. There must be a blank line between each note body and the title of the next
# note. There must be a blank line between the file heading and the first title.
# Each note title is on a single line and each note body is on a single line.
# These input complications must be handled:
#   Some files have a heading line, which should be discarded.
#   Some files have multiple heading lines, which should be discarded.
#   The file heading may or may not begin with hash symbols.
#   There are blank title lines for which a question mark will be substituted.
#   There may be a blank note body, which would not invalidate the entire note.
#   If both the title and body are blank, the note will be discarded.

####### This script has not been finished. Started work on it 11/20/18.

# Global variables
resource_type = 'tn'
language_code = u'id'
target_dir = r'C:\DCS\Indonesian\TN'
max_changes = 1

import re
import io
import os
import sys
import shutil
import codecs
import json
#import usfm_verses


def makeChapterDir(bookdir, chap):
    path = os.path.join(target_dir, bookdir.lower())
    if not os.path.isdir(path):
        os.mkdir(path)

    path = os.path.join(path, chap)
    if not os.path.isdir(path):
        os.mkdir(path)
        
    return path

# Returns True if the specified file name matches a pattern that indicates
# the file contains text to be converted.
def isChunk(filename):
    isSect = False
    if re.match('\d\d\d?\.md$', filename):     # or filename == "intro.md":
        isSect = True
    return isSect

# Returns True if the specified directory is one with files to be converted
# Note that this function excludes "front" folders for the time being.
def isChapter(dirname):
    isChap = False
    if re.match('\d\d\d?$', dirname):
        isChap = True
    return isChap

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname


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

# Returns a list of Python dictionary objects.
# Each object maps a string to "title" and another string to "body".
# Any file heading, if present, is stripped out.
# Markdown hash markers identify the titles, but the hashes are removed.
def parseNotes(alllines):
    for line in alllines:
        if line[0] == u'#':
            if note:
                notes.append(note)  # capture preceding note
            note = line     # first line of new note
        else:
            note += line
    if note > 0:      # capture last note at EOF
        notes.append(note)
    return notes

# Writes out all the notes in verse-specific files
def writeChapter(notekeeper):
    # print notekeeper.verseDict.keys()
    # print notekeeper.verseDict.values()
    
    chapDir = makeChapterDir(notekeeper.book, notekeeper.chapter)
    for verse in notekeeper.verseDict.keys():
        versePath = os.path.join(chapDir, ("%02d" % verse) + ".md")
        verseFile = io.open(versePath, "tw", buffering=1, encoding='utf-8', newline='\n')
        addline = False
        for note in notekeeper.verseDict[verse]:
            if addline and note[0] != u'\n':
                verseFile.write(u'\n')
            verseFile.write( note )
            addline = (note[-2:] != u'\n\n')
        verseFile.close()

    statinfo = os.stat(versePath)
    if statinfo.st_size == 0:
        sys.stderr.write("Removed: " + shortname(versePath) + "\n")
        os.remove(versePath)

# Returns a shorter list of lines with file heading and blank lines between 
# title and body removed.
def simplify_lines(alllines, path):
    return alllines
    
# Returns False if the lines in the file are not parseable.
# Reports errors.
def validate_lines(alllines, path):
    valid = True
    if len(alllines) < 3:
        sys.stderr.write("Not enough lines in file: " + path + '\n')
        valid = False
    count = 1
    titleline = 0
    bodyline = 0
    for line in alllines:
        if count % 2 == 0 and len(line.strip()) > 0:
            sys.stderr.write("Line " + str(count) + " should be blank. " + path + "\n")
            valid = False
        if count % 2 == 1:
            if len(line.strip()) == 0:
                sys.stderr.write("Line " + str(count) + " should be nonblank: " + path + "\n")
                valid = False
            elif line[0] == u'#':
                if count > 3 and bodyline > 0 and count == titleline + 2:
                    sys.stderr.write("Consecutive titles at line " + str(count) + ": " + path + ".\n")
                    valid = False
                titleline = count
            else:       # line does not start with a hash
                if titleline > 0 and count > 2:
                    bodyline = count
                if count > 2 and count != titleline + 2:
                    sys.stderr.write("Consecutive body lines at line " + str(count) + ": " + path + ".\n")
                    valid = False
        count += 1
    if bodyline == 0:
        sys.stderr.write("No body lines in: " + path + ".\n")
        valid = False
    if titleline == 0:
        sys.stderr.write("No title lines in: " + path + ".\n")
        valid = False
    if not valid:
        sys.stderr.flush()
        sys.stdout.write("Invalid contents: " + path + '\n')
    return valid
        

# Converts notes in fullpath to corresponding json .txt files.
def convertFile(chap, fname, fullpath):
    global nProcessed
    global nBadFiles
    # Read input file
    if os.access(fullpath, os.F_OK):
        enc = detect_by_bom(fullpath, default="utf-8")
        if enc != "utf-8":
            sys.stderr.write("Warning: UTF-8 not detected: " + shortname(fullpath) + "\n")
        input = io.open(fullpath, "tr", 1, encoding=enc)
        lines = input.readlines(-1)
        input.close()
        if validate_lines(lines, shortname(fullpath)):
            lines = simplify_lines(lines, shortname(fullpath))
        else:
            nBadFiles += 1
        nProcessed += 1

# This function is called to convert the .md files in the specified chapter folder
def convertChapter(bookdir, chapdir, fullpath):
    for fname in os.listdir(fullpath):
        if isChunk(fname):
            convertFile(chapdir, fname, os.path.join(fullpath, fname))
        if nProcessed > max_changes:
            break

# Determines if the specified path is a book folder, and processes it if so.
# Return False if it is not a book.
def convertBook(path):
    isbook = False
    bookfolder = os.path.split(path)[1]
#    sys.stdout.write("Converting: " + shortname(path) + "\n")
#    sys.stdout.flush()
    for dir in os.listdir(path):
        if isChapter(dir):
            isbook = True
            # sys.stdout.write( " " + dir )
            convertChapter(bookfolder, dir, os.path.join(path, dir))
        if nProcessed > max_changes:
            break
    return isbook
 
# Converts the book or books contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if not convertBook(dir):
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if os.path.isdir(folder):
                convertBook(folder)
            if nProcessed > max_changes:
                break


# Processes each directory and its files one at a time
if __name__ == "__main__":
    nProcessed = 0
    nBadFiles = 0

    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convert(r'C:\DCS\Indonesian\id_tn')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print "\nDone. Processed ", nProcessed, "files, and " + str(nBadFiles) + " were bad."
