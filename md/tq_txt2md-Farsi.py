# -*- coding: utf-8 -*-
# This script copies questions and responses from Farsi text files into properly
# named and formatted markdown files.
# The Farsi text files must have been preprocessed to have English book names, chapter numbers,
# and verse numbers. (See tq_FarsiPre.py and tq_FarsiCheck.py.)
# Does the following:
#    Copies questions to the appropriate, verse-specific file(s) in target location.

# Global variables
source_dir = r"C:\DCS\Farsi\TQ\1CO.txt"
resource_type = 'tq'
language_code = 'fa'
target_dir = r'C:\DCS\Farsi\work'

import re
import io
import os
import sys
import shutil
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

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath and source_dir != longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def makeChapterDir(bookid, chap):
    path = os.path.join(target_dir, bookid.lower())
    if not os.path.isdir(path):
        os.mkdir(path)
    if len(chap) == 1:
        chap = "0" + chap
    path = os.path.join(path, chap)
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

def writeQAs(bookid, chapter, verse, qas):
    if len(qas) % 2 != 0:
        sys.stderr.write(f"Odd number of Q&A lines for {bookid} {verse}:{chapter}\n")
    else:
        chapterdir = makeChapterDir(bookid, chapter)
        if len(verse) == 1:
            verse = "0" + verse
        chunkpath = os.path.join(chapterdir, verse+".md")
        with io.open(chunkpath, "tw", encoding='utf-8', newline='\n') as output:
            lineno = 0
            while lineno + 1 < len(qas):
                if lineno > 0:
                    output.write('\n')
                output.write("# " + qas[lineno] + '\n\n')
                output.write(qas[lineno + 1] + '\n')
                lineno = lineno + 2

chapter_re = re.compile(r'([123A-Z]+) +([0123456789]+) *$')
reference_re = re.compile(r'([123A-Z]+) +([0123456789]+)\:([0123456789]+)')

# Processes the specified file as a Farsi tQ file for one book.
# Assumes the target_dir is empty to start.
def convertFile(path):
    fname = os.path.basename(path)
    bookid = fname[0:3].upper()
    bookpath = os.path.join(target_dir, bookid.lower())
    if not os.path.exists(bookpath):
        os.mkdir(bookpath)
    sys.stdout.write("Converting: " + shortname(path) + "\n")
    sys.stdout.flush()
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    chapter = "0"
    verse = "0"
    chapterdir = target_dir
    qas = []
    lineno = 0
    for line in lines:
        lineno += 1
        chaps = chapter_re.match(line)
        ref = reference_re.match(line)
        if chaps and chaps.group(1) == bookid:  # we have a new chapter
            if len(qas) > 0:
                writeQAs(bookid, chapter, verse, qas)
                qas = []
            chapter = chaps.group(2)
        elif ref and ref.group(1) == bookid:    # we have a new verse reference
            if ref.group(3) == chapter:
                if len(qas) > 0:
                    writeQAs(bookid, chapter, verse, qas)
                    qas = []
                verse = ref.group(2)
            else:
                sys.stderr.write(f"Unexpected chapter :{ref.group(3)} after chapter {chapter} in shortname(path)\n")
        else:
            line = line.strip()
            if line.startswith(bookid) and not chapter == "0":
                sys.stderr.write(f"Warning: line {lineno} starts with {bookid}\n")
            if len(line) > 0 and chapter != "0" and verse != "0":
                qas.append(line)

# Converts the book or books contained in the specified folder
def convertDir(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for entry in os.listdir(dir):
        path = os.path.join(dir, entry)
        if os.path.isdir(path):
            convertDir(path)
        elif os.path.isfile(path) and path.endswith(".txt"):
            convertBook(path)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convertDir(source_dir)
        sys.stdout.write("Done.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        current_dir = source_dir
        convertFile(path)
        sys.stdout.write("Done. Converted 1 file.\n")
    else:
        sys.stderr.write("Usage: python tq_txt2md-Farsi <folder or file>\n  Use . for current folder.", source_dir, 0)
