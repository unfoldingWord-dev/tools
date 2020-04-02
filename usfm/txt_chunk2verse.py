# -*- coding: utf-8 -*-
# This script splits a repository of tN or tQ chunk-specific text files from tStudio
# into a collection of verse-specific text files of the same format, based on the
# information contained in passage links, e.g. [17:3], in the chunk-specific files.
#    Parses the passage links, even when not perfectly formed.
#    Copies notes to the appropriate, verse-specific file(s) in target location.
#    Handles range of verses by duplicating notes into verse-specific files.
#    Converts multiple books at once.
#    Copies manifest.json files also, as a freebie.
# This script will usually be used to pre-process the data before tntq_txt2md.py is run,
# but don't run it unnecessarily. Ensure that the repository in question actually uses
# passage links. Some, like Vietnamese, may have a few parenthetical verse references that
# match the link_re pattern but are not passage links. The following grep will find
# passage links and false passage links demarked by parentheses.
#            grep -E '\([0-9]+:[0-9]+\)' */*/*.txt > passagelinks.txt
#            grep -E '\[[0-9]+:[0-9]+\]' */*/*.txt >> passagelinks.txt

# Global variables
resource_type = 'tq'
language_code = 'ur-deva'
target_dir = r'C:\Users\Larry\Documents\GitHub\Urdu-Deva\TQ.intermediate'

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
        self.verseList = {}
    
    def addChunk(self, fname):
        self.baseverse = int(fname[0:-4])

    # Adds a note to the default verse
    def addNoteDefault(self, note):
        self.addNote(note, [self.baseverse])
    
    # Adds a note to the specified verses    
    def addNote(self, note, verses):
        for verse in verses:
            if verse in self.verseList:
                self.verseList[verse].append(note)
            else:
                self.verseList[verse] = [ note ]

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
    if re.match('\d\d\d?\.txt', filename) and filename != '00.txt':
        isSect = True
    return isSect

# Returns True if the specified directory is one with files to be converted
def isChapter(dirname):
    isChap = False
    if dirname != '00' and re.match('\d\d\d?$', dirname):
        isChap = True
    return isChap

prefix_re = re.compile(r'C:\\Users\\Larry\\Documents\\GitHub')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[31:]
    return shortname

link_re = re.compile(r'(.+)[\[\(] *(\d+) *: *([\d-]+) *[\]\)](.*)', re.UNICODE+re.DOTALL)
range_re = re.compile(r'([0-9]+)-([0-9]+)')

# Parses str to see if there are any valid passsage links.
# Returns list of verses indicated in the links, if any.
# Also returns the string minus any passage links.
def linkedVerses(str, chap, path):
    ustr = str(str).strip()
    if chap[0] == '0':
        chap = chap[1:]
    verses = []

    link = link_re.match(ustr)
    while link:
        ustr = link.group(1) + ' ' + link.group(4)
        if link.group(2) == chap:   # must be a valid link
            vv = link.group(3)      # the verse(s)
            range = range_re.match(vv)
            if range:
                vn = int(range.group(1))
                vnEnd = int(range.group(2))
                while vn <= vnEnd:
                    verses.append(vn)
                    vn += 1
            else:
                verses.append( int(vv) )
        else:
            sys.stderr.write("Invalid link in " + shortname(path) + " removed: " + link.group(2) + ':' + link.group(3) + '\n')
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

# Converts notes in fullpath to into notes associated with specific verses.
def convertFile(notekeeper, chap, fname, fullpath):
    global nSplits
    # Read input file
    if os.access(fullpath, os.F_OK):
        notes = []
        enc = detect_by_bom(fullpath, default="utf-8")
        if enc != "utf-8":
            sys.stderr.write("Warning: UTF-8 not detected: " + shortname(fullpath) + "\n")
        f = io.open(fullpath, "tr", 1, encoding=enc)
        try:
            notes = json.load(f)
        except ValueError as e:
            sys.stderr.write("Not valid JSON: " + shortname(fullpath) + '\n')
            sys.stderr.flush()
        f.close()

        if len(notes) > 0:
            n = 0   # used in error messages below
            for note in notes:
                n += 1
                if len(note) > 0 and note['title']:
                    title = linkedVerses(note['title'], chap, fullpath)
                    body = linkedVerses(note['body'], chap, fullpath)
                    note['title'] = title[1]
                    note['body'] = body[1]
                    verses = body[0] + title[0]     # concatenate lists
                    if len(verses) == 0:
                        notekeeper.addNoteDefault(note)
                    else:
                        notekeeper.addNote(note, verses)
                        nSplits += len(verses)
                        # sys.stdout.write("Split found in " + shortname(fullpath) + '\n')
                else:
                    sys.stderr.write("Null question in: " + shortname(fullpath) + '\n')
                    sys.stderr.flush()

# Writes out all the notes in verse-specific files
def writeChapter(notekeeper):
    # print notekeeper.verseList.keys()
    # print notekeeper.verseList.values()
    
    chapDir = makeChapterDir(notekeeper.book, notekeeper.chapter)
    for verse in list(notekeeper.verseList.keys()):         # would this work: verse in notekeeper.verseList
        versePath = os.path.join(chapDir, ("%02d" % verse) + ".txt")
        verseFile = io.open(versePath, "tw", buffering=1, encoding='utf-8', newline='\n')
        cards = json.dumps(notekeeper.verseList[verse])
        verseFile.write( str(cards) )
        verseFile.close()

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
    if len(notekeeper.verseList) > 0:
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
    
    # Gratuitous copy of manifest.json to intermediate target folder
    manifestPath = os.path.join(path, "manifest.json")
    if os.path.isfile(manifestPath):
        shutil.copy(manifestPath, os.path.join(target_dir, bookfolder))
 
# Converts the book or books contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if not convertBook(dir):
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if os.path.isdir(folder):
                convertBook(folder)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    nSplits = 0

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python tntq_chunk2verse <folder>\n  Use . for current folder.\n")
    elif sys.argv[1] == 'hard-coded-path':
        convert(r'C:\Users\Larry\Documents\GitHub\Urdu-Deva\ur_tq_nt')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print("\nDone. Made", nSplits, "file splits.")
