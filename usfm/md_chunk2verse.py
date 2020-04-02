# -*- coding: utf-8 -*-
# This script splits a repository of tN or tQ chunk-specific markdown files
# into a corresponding collection of verse-specific markdown files, based on the
# information contained in passage links, e.g. [17:3], in the chunk-specific files.
#    Parses the passage links, even when not perfectly formed.
#    Copies notes to the appropriate, verse-specific file(s) in target location.
#    Handles range of verses by duplicating notes into verse-specific files.
#    Converts multiple books at once.
# This script will usually be used to post-process the data after tntq_md2md.py is run,
# but don't run it unnecessarily. Ensure that the repository in question actually uses
# passage links. Some repositories may have a few parenthetical verse references that
# match the link_re pattern but are not passage links. The following grep will find
# passage links and false passage links demarked by parentheses.
#            grep -E '\([0-9]+:[0-9]+\)' */*/*.md > passagelinks.txt
#            grep -E '\[[0-9]+:[0-9]+\]' */*/*.md >> passagelinks.txt

# Global variables
resource_type = 'tq'
language_code = 'fr'
target_dir = r'C:\DCS\French\fr_tq'
max_changes = 1800

import re
import io
import os
import sys
import shutil
import codecs
import json
import usfm_verses

# Writer temporarily stores the notes for a single chapter.
# It is important that the NoteKeeper is one per chapter because multiple
# chunks can have notes linked to the same verse.
# Each note is associated to one or more verses in the chapter.
class NoteKeeper:
#     
    def __init__(self, bookdir, chap):
        self.book = bookdir
        self.chapter = chap
        self.baseverse = 1
        self.verseDict = {}
    
    def addChunk(self, fname):
        self.baseverse = int(fname[0:-3])

    # Adds a note to the default verse
    def addNoteDefault(self, note):
        if self.baseverse == 0:
            sys.stdout.write("baseverse 0\n")
        self.addNote(note, [self.baseverse])
    
    # Adds a note to the specified verses    
    def addNote(self, note, verses):
        for verse in verses:
            # sys.stdout.write("Verse: " + str(verse) + "\n")
            if verse in self.verseDict:
                self.verseDict[verse].append(note)
            else:
                if verse == 0:
                    sys.stdout.write("verse 0\n")
                self.verseDict[verse] = [ note ]

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
    if re.match('\d\d\d?\.md$', filename):
        isSect = True
    return isSect

# Returns True if the specified directory is one with files to be converted
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

link_re = re.compile(r'(.+)[\[\(] *(\d+) *: *([\d,-]+) *[\]\)](.*)', re.UNICODE+re.DOTALL)
range_re = re.compile(r'([0-9]+)-([0-9]+)')
list3_re = re.compile(r'([0-9]+),([0-9]+),([0-9]+)')
list2_re = re.compile(r'([0-9]+),([0-9]+)')

# Parses str to see if there are any valid passsage links.
# Returns list of verse numbers indicated in the links, if any.
# Also returns the string minus any passage links.
def linkedVerses(ustr, chap, path):
    # ustr = unicode(str).strip()
    if chap[0] == '0':
        chap = chap[1:]
    verses = []

    link = link_re.match(ustr)
    while link:
        ustr = link.group(1) + ' ' + link.group(4)
        if link.group(2) == chap:   # must be a valid link
            vv = link.group(3)      # the verse(s)
            range = range_re.match(vv)
            if not range:
                list3 = list3_re.match(vv)
                if not list3:
                    list2 = list2_re.match(vv)
            if range:
                vn = int(range.group(1))
                vnEnd = int(range.group(2))
                while vn <= vnEnd:
                    verses.append(vn)
                    vn += 1
            elif list3:
                verses.append( int(list3.group(1)) )
                verses.append( int(list3.group(2)) )
                verses.append( int(list3.group(3)) )
            elif list2:
                verses.append( int(list2.group(1)) )
                verses.append( int(list2.group(2)) )
            else:
                verses.append( int(vv) )
        else:
            # sys.stderr.write("Invalid link in " + shortname(path) + " removed: " + link.group(2) + ':' + link.group(3) + '\n')
            sys.stderr.write("Invalid link in " + shortname(path) + " removed\n")
        link = link_re.match(ustr)  # find another link in the same string

    return verses, ustr

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

# Returns a list of strings, each of which comprises a note.
# A note string begins with a hash symbol, and contains multiple newlines (typically).
def parseNotes(alllines):
    note = ""
    notes = []
    for line in alllines:
        if line[0] == '#':
            if note:
                notes.append(note)  # capture preceding note
            note = line     # first line of new note
        else:
            note += line
    if note > 0:      # capture last note at EOF
        notes.append(note)
    return notes

# Converts notes in fullpath to into notes associated with specific verses.
def convertFile(notekeeper, chap, fname, fullpath):
    global nSplits
    # Read input file
    if os.access(fullpath, os.F_OK):
        enc = detect_by_bom(fullpath, default="utf-8")
        if enc != "utf-8":
            sys.stderr.write("Warning: UTF-8 not detected: " + shortname(fullpath) + "\n")
        input = io.open(fullpath, "tr", 1, encoding=enc)
        lines = input.readlines(-1)
        input.close()
        notes = parseNotes(lines)   # notes is a list of strings
        verses = []     # list of verses referenced in the note
        n = 0
        for note in notes:      # each note is a single string
            n += 1
            pair = linkedVerses(note, chap, fullpath)
            newnote = pair[1]
            verses = pair[0]
            if len(verses) == 0:
                notekeeper.addNoteDefault(newnote)
            else:
                # sys.stdout.write("Split found in " + shortname(fullpath) + '\n')
                notekeeper.addNote(newnote, verses)
                nSplits += len(verses)
            verses = []

# Writes out all the notes in verse-specific files
def writeChapter(notekeeper):
    # print notekeeper.verseDict.keys()
    # print notekeeper.verseDict.values()
    
    chapDir = makeChapterDir(notekeeper.book, notekeeper.chapter)
    for verse in list(notekeeper.verseDict.keys()):         # would this work: verse in notekeeper.verseDict
        versePath = os.path.join(chapDir, ("%02d" % verse) + ".md")
        verseFile = io.open(versePath, "tw", buffering=1, encoding='utf-8', newline='\n')
        addline = False
        for note in notekeeper.verseDict[verse]:
            if addline and note[0] != '\n':
                verseFile.write('\n')
            verseFile.write( note )
            addline = (note[-2:] != '\n\n')
        verseFile.close()

    statinfo = os.stat(versePath)
    if statinfo.st_size == 0:
        sys.stderr.write("Removed: " + shortname(versePath) + "\n")
        os.remove(versePath)

# This method is called to convert the text files in the specified chapter folder
# If it is not a chapter folder
def convertChapter(bookdir, chapdir, fullpath):
    notekeeper = NoteKeeper(bookdir, chapdir)
    for fname in os.listdir(fullpath):
        if isChunk(fname):
            notekeeper.addChunk(fname)
            convertFile(notekeeper, chapdir, fname, os.path.join(fullpath, fname))
        if nSplits > max_changes:
            break
    if len(notekeeper.verseDict) > 0:
        writeChapter(notekeeper)

# Determines if the specified path is a book folder, and processes it if so.
# Return book title, or empty string if not a book.
def convertBook(path):
    bookfolder = os.path.split(path)[1]
    sys.stdout.write("Converting: " + shortname(path) + "\n")
    sys.stdout.flush()
    for dir in os.listdir(path):
        if isChapter(dir):
            # sys.stdout.write( " " + dir )
            convertChapter(bookfolder, dir, os.path.join(path, dir))
        if nSplits > max_changes:
            break
 
# Converts the book or books contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if not convertBook(dir):
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if os.path.isdir(folder):
                convertBook(folder)
            if nSplits > max_changes:
                break


# Processes each directory and its files one at a time
if __name__ == "__main__":
    nSplits = 0

    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convert(r'C:\DCS\French\fr_tq.temp')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print("\nDone. Made", nSplits, "file splits.")
