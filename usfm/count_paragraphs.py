# -*- coding: utf-8 -*-
# This script reports a count of paragraph and poetry markers in one or more valid .usfm files.
# The input file(s) should be verified, correct USFM.

# Global variables
source_dir = r"C:\DCS\Indonesian\id_ayt.TA"

issuesFile = None
countsFile = None
import sys
import os
import io

# Counts paragraphs in the book or books contained in the specified folder
def countFolder(folder):
    if not os.path.isdir(folder):
        reportError("Invalid folder path given: " + folder)
        return
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname[0] != '.' and os.path.isdir(path):
            countFolder(path)
        elif fname.endswith('sfm'):
            processFile(path)

# If issues.txt file is not already open, opens it for writing.
# Overwrites existing issues.txt file, if any.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile

def closeFiles():
    global issuesFile, countsFile
    if issuesFile:
        issuesFile.close()
        issuesFile = None
    if countsFile:
        countsFile.close()
        countsFile = None

# If count_pp.txt file is not already open, opens it for writing.
# Overwrites existing count_pp.txt file, if any.
# Returns file pointer.
def openCountsFile():
    global countsFile
    if not countsFile:
        global source_dir
        path = os.path.join(source_dir, "count_pp.txt")
        countsFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return countsFile

# Writes the error messages to stderr and to issues.txt.
def reportError(msg):
    try:
        sys.stderr.write(msg + "\n")
    except UnicodeEncodeError as e:
        sys.stderr.write("(Unicode...)\n")
    issues = openIssuesFile()
    issues.write(msg + "\n")

# Returns number of chapters, paragraph markers and poetry markers in the specified file.
def countParagraphs(path):
    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        str = input.read(-1)
    nchapters = str.count("\\c ")
    nparagraphs = str.count("\\p") + str.count("\\nb") + str.count("\\li")
    npoetry = str.count("\\q")
    return (nchapters, nparagraphs, npoetry)

def reportCounts(fname, nParagraphs, nPoetry, nChapters):
    countsFile = openCountsFile()
    msg = f"{fname} has {nParagraphs} paragraphs and {nPoetry} poetry marks in {nChapters} chapters.\n"
    sys.stdout.write(msg)
    countsFile.write(msg)
    if nParagraphs / nChapters > 2.5 or nPoetry / nChapters > 15:
        msg = f"      this book already has paragraphs or poetry marked.\n"
        sys.stdout.write(msg)
        countsFile.write(msg)
        # msg = f"      p/c = {nParagraphs / nChapters}"
        # msg = f"      q/c = {nPoetry / nChapters}"

# Reports number of chapters, paragraphs and poetry marks contained in the specified file.
def processFile(path):
    global model_dir
    fname = os.path.basename(path)
    (nChapters, nParagraphs, nPoetry) = countParagraphs(path)
    reportCounts(fname, nParagraphs, nPoetry, nChapters)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if os.path.isdir(source_dir):
        countFolder(source_dir)
    elif os.path.isfile(source_dir) and source_dir.endswith("sfm"):
        path = source_dir
        source_dir = os.path.dirname(path)
        processFile(path)
    else:
        sys.stderr.write("Invalid folder or file: " + source_dir)
        exit(-1)
    closeFiles()
