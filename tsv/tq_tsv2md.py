# -*- coding: utf-8 -*-
# This Python 3 converts translation questions from TSV to the older markdown format.
# It only processes a single folder or a single file, no recursion.
# Removes line breaks <br>

import re
import io
import os
import sys
import operator
import tsv
import usfm_verses
from shutil import copy


# Globals
source_dir = r'C:\DCS\Gujarati\TQ'  # Where are the TSV files located
target_dir = r'C:\DCS\Gujarati\work'
resource_type = 'tq'
max_files = 99    # max number of TSV files to be processed
nProcessed = 0
filename_re = re.compile(r'.*\.tsv$')
projects = []

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def reportError(msg):
    sys.stderr.write(msg + '\n')

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    title = bookTitle
    sort = usfm_verses.verseCounts[bookId]["sort"]
    testament = 'nt'
    if sort < 40:
        testament = 'ot'
    project = { "title": title, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + bookId.lower(),\
                "categories": "[ 'bible-" + testament + "' ]" }
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
        manifest.write("    categories: " + p['categories'] + "\n")
        manifest.write("    versification:\n")
    manifest.close()

def copyOtherFile(fname):
    path = os.path.join(source_dir, fname)
    if os.path.isfile(path):
        newpath = os.path.join(target_dir, fname + ".field")
        copy(path, newpath)

# Copies LICENSE, README, and manifest.yaml files
def copyOtherFiles():
    copyOtherFile("LICENSE.md")
    copyOtherFile("LICENSE")
    copyOtherFile("README.md")
    copyOtherFile("manifest.yaml")
    copyOtherFile("media.yaml")

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

def writeMdfile(bookId, chap, verse, question, response):
    path = makeMdPath(bookId, chap, verse)
    if verse != writeMdfile.prevverse:
        mode = "tw"
        start = "# "
    else:
        mode = "ta"
        start = "\n# "
    file = io.open(path, mode, encoding="utf-8", newline="\n")
    file.write(start + convertQR(question) + "\n\n" + convertQR(response) + "\n")
    file.close()
    writeMdfile.prevverse = verse

writeMdfile.prevverse = 0

#hash_re = re.compile(r'#([^# \n].*)')    # missing space after #
#blanklines_re = re.compile(r'[^\>]\<br\>#')     # less than two lines breaks before heading

# Removes unwanted leading and trailing characters from question or response string
# Removes line breaks <br>
def convertQR(text):
    text = text.replace("<br>", " ")
    return text.strip('#\\ ')     # remove leading and trailing spaces and quotes

filename_re = re.compile(r'tq_([123A-Za-z][A-Za-z][A-Za-z]).tsv')

# Returns a (bookId, bookName) pair.
def getBookId(filename):
    if resource_type == 'obs-tq':
        book = ("content", "OBS")
    else:
        book = None
        fname = filename_re.search(filename)
        if fname:
            bookid = fname.group(1).upper()
            if bookid in usfm_verses.verseCounts.keys():
                book = (bookid, usfm_verses.verseCounts[bookid]["en_name"])
            else:
                reportError("Can't get book ID from filename: " + filename)
        else:
            reportError("Invalid TSV file name: " + filename)
    return book

ref_re = re.compile(r'([0-9]+):([0-9]+)')

def convertRow(bookId, row, nrow):
    ref = ref_re.match(row[0])
    if ref:
        writeMdfile(bookId, ref.group(1), ref.group(2), row[5], row[6])
    else:
        reportError("  Row " + str(nrow) + " has invalid reference: " + row[0])

# Converts a single obs-tq TSV file into several hundred .md files.
# Places the output files in target folder/content
def convertObsTqFile(path):
    print("Converting ", shortname(path))
    sys.stdout.flush()
    content_dir = os.path.join(target_dir, "content")
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows); each row is a list of strings (columns)
    nrow = 0
    for row in data:
        nrow += 1
        if nrow > 1:
            if len(row) == 7:
                convertRow(bookId, row, nrow)
            else:
                reportError("  Row " + str(nrow) + " has " + str(len(row)) + " columns.")


# Writes all the notes in the specified file to .md files.
# Success depends on correctness of the TSV file. Verify beforehand.
def convertTQFile(path):
    if book := getBookId(path):
        print("Converting ", shortname(path))
        sys.stdout.flush()
        if resource_type == 'tq':
            appendToProjects(book[0], book[1])
        data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows); each row is a list of strings.
        nrow = 0
        for row in data:
            nrow += 1
            if nrow > 1:
                if len(row) == 7:
                    convertRow(book[0], row, nrow)
                else:
                    reportError("  Row " + str(nrow) + " has " + str(len(row)) + " columns.")

# Writes all the notes in the specified file to .md files.
# Success depends on correctness of the TSV file. Verify beforehand.
def convertFile(path):
    # if resource_type == 'tq':
    #     convertTQFile(path)
    # elif resource_type == 'obs-tq':
    convertTQFile(path)
    # else:
        # reportError("Resource type not supported: " + resource_type)

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
        reportError("Usage: python tsv2md.py <folder>\n  Use . for current folder.")
