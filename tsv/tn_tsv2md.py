# -*- coding: utf-8 -*-
# This Python 3 converts translation notes from TSV to the older markdown format.
# Some data is lost because the markdown format is not as content rich.
# It only processes a single folder or a single file, no recursion.
# The TSV files should be clean and completely correct format. (Use verifyTSV.py and tsv_cleanup.py)

import re       # regular expression module
import io
import os
import sys
import operator
import tsv
import usfm_verses
from shutil import copy


# Globals
source_dir = r'C:\DCS\Kannada\TN.Dec-21\new'  # Where are the TSV files located
target_dir = r'C:\DCS\Kannada\TN'
max_files = 27      # max number of TSV files to be processed
nProcessed = 0
filename_re = re.compile(r'.*\.tsv$')
projects = []

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    title = bookTitle + " translationNotes"
    project = { "title": title, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + bookId.lower() }
    projects.append(project)

# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects
    
    projects.sort(key=operator.itemgetter('sort'))
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    versification: ''\n")
        manifest.write("    categories: []\n")
    manifest.close()

# Copies LICENSE, README, and manifest.yaml files
def copyOtherFiles():
    path = os.path.join(source_dir, "LICENSE.md")
    if os.path.isfile(path):
        copy(path, target_dir)       # copy() is from shutil
    path = os.path.join(source_dir, "README.md")
    if os.path.isfile(path):
        copy(path, target_dir)
    path = os.path.join(source_dir, "manifest.yaml")
    if os.path.isfile(path):
        copy(path, target_dir)

# Returns path of temporary manifest file block listing projects converted
def makeManifestPath():
    return os.path.join(target_dir, "projects.yaml")

# Returns the path of the markdown file to contain the notes for the specified verse
# Creates the parent directory of the markdown file, if necessary.
def makeMdPath(bookId, chap, verse):
    bookId = bookId.lower()
    if len(chap) == 0:
        chap = "front"
    if len(chap) == 1:
        chap = "0" + chap
    if bookId == 'psa' and len(chap) == 2:
        chap = "0" + chap
    if len(verse) == 0:
        verse = "intro"
    if len(verse) == 1:
        verse = "0" + verse
    if bookId == 'psa' and len(verse) == 2:
        verse = "0" + verse
    folder = os.path.join(target_dir, bookId)
    if not os.path.isdir(folder):
        os.mkdir(folder)
    folder = os.path.join(folder, chap)
    if not os.path.isdir(folder):
        os.mkdir(folder)
    return os.path.join(folder, verse) + ".md"

def writeMdfile(bookId, chap, verse, notes):
    path = makeMdPath(bookId, chap, verse)
    if os.path.isfile(path):
        start = "\n# "
        sys.stdout.write(shortname(path) + ": file exists, appending notes\n")
    else:
        start = "# "
    file = io.open(path, "ta", encoding="utf-8", newline="\n")
    for note in notes:
        if verse == "intro":
            file.write( convertNote(note[1]) + "\n")
        else:
            file.write(start + convertNote(note[0]) + "\n\n" + convertNote(note[1]) + "\n")
            start = "\n# "
    file.close()

hash_re = re.compile(r'#([^# \n].*)')    # missing space after #
blanklines_re = re.compile(r'[^\>]\<br\>#')     # less than two lines breaks before heading

# Removes leading and trailing spaces and quotes
# Translates <br> to line breaks
def convertNote(text):
    text = re.sub("<br>", r"\n", text)
    return text.strip('" ')     # remove leading and trailing spaces and quotes

# Writes all the notes in the specified file to .md files.
# Success depends on correctness of the TSV file. Verify beforehand.
def convertFile(path):
    print("Converting ", shortname(path))
    sys.stdout.flush()
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows); each row is a list of strings.
    notes = []
    bookId = None
    chapter = None
    verse = None
    for row in data:
        if not bookId:
            if row[0] == "Book":
                continue
            else:
                bookId = row[0]
                appendToProjects(bookId, usfm_verses.verseCounts[bookId]["en_name"])
        if row[1] != chapter or row[2] != verse:
            if bookId and chapter and verse:
                writeMdfile(bookId, chapter, verse, notes)
            chapter = row[1]
            verse = row[2]
            notes = []
        notes.append( (row[7],row[8]) )
    writeMdfile(bookId, chapter, verse, notes)
    # row = convertRow(row)

# Converts all TSV files in the specified folder. Not recursive.
def convertFolder(folder):
    global nProcessed
    global max_files
    if nProcessed >= max_files:
        return
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if filename_re.match(entry):
            convertFile(path)
            nProcessed += 1
        if nProcessed >= max_files:
            break
    copyOtherFiles()
    dumpProjects()

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Processed " + str(nProcessed) + " files.\n")
    elif filename_re.match(source_dir) and os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Processed 1 file.\n")
    else:
        sys.stderr.write("Usage: python tsv2md.py <folder>\n  Use . for current folder.\n")
