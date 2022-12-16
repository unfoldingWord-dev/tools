# -*- coding: utf-8 -*-
# This script does some fixup to a folder of tN .tsv files and saves them to a new location.
# It edits the files in these ways:
#    Sets the SupportReference, OrigQuote, and Occurrence column values to match what is in the English tN.
#    Removes leading and trailing spaces from each field value.
#    Supplies missing tab between 4-character ID column and the next column.
#    Converts links of the form "rc://en/...."
# Generates a projects.yaml file, in correct form for manifest.yaml.

######################################################
# It is better to run tsv_cleanup.py on the source
# files before converting the files with this script.
# Maybe also run verifyTSV.py, to catch most errors
# before conversion.
# Then run verifyTSV.py on the target dir.
######################################################

# Global variables
source_dir = r'C:\DCS\Telugu\TN'
target_dir = r'C:\DCS\Telugu\work'
language_code = 'te'
english_dir = r'C:\DCS\English\en_tn.v66'    # latest English tN from https://git.door43.org/Door43-Catalog/en_tn

book = ''
chapter = 0
verse = 0
rowno = 0   # row number in .tsv file
issuesFile = None
projects = []

import re
import io
import os
import sys
import operator
import tsv
import usfm_verses

badheading_re = re.compile(r'#[^# ]', re.UNICODE)

# Reports an error if there is anything wrong with the header row
def checkHeader(row, key, path):
    if key != "ID.Verse.Chapter":
        reportError("Invalid labels in header row", path, "", None)
    if len(row) != 9:
        reportError("Wrong number of columns (" + str(len(row)) + ") in header row", path, "", None)

# Checks the specified non-header row values.
# Reports errors.
# nColumns must be >= 4 or this function will fail
def checkRow(row, nColumns, key, path):
    global book
    global chapter
    global verse

    abort = False
    if not book:
        book = row[0]
    if row[0] != book:
        reportError("Bad book name (" + row[0] + ")", path, key, row[0:4])

    if row[1] != 'front':
        try:
            c = int(row[1])
            if c == chapter + 1:
                chapter = c
            elif c != chapter:
                reportError("Non-sequential chapter number", path, key, row[0:4])
        except ValueError as e:
            c = 0
            reportError("Non-numeric chapter number", path, key, row[0:4])
    if row[2] == 'intro':
        verse = 0
    else:
        try:
#           Based on 10/29/19 discussion on Zulip, the verse order in TSV file is not critical.
#           if int(row[2]) < verse:
#               reportError("Verse number out of order", path, key, row[0:4])
            verse = int(row[2])
        except ValueError as e:
            reportError("Non-numeric verse number", path, key, row[0:4])
    if len(row[3]) != 4:
        reportError("Invalid ID", path, key, row[0:4])

    if nColumns == 9:
        if not row[4].isascii():
            reportError("Invalid SupportReference (column 5)", path, key, row[0:4])
        if len(row[5].strip()) > 0 and row[5].isascii():
            reportError("Invalid OrigQuote (column 6)", path, key, row[0:4])
        if badheading_re.search(row[8]):
            reportError("Missing space after hash mark(s)", path, key, row[0:4])
    else:
        reportError("Wrong number of columns (" + str(nColumns) + ")", path, key, row[0:4])

englishlink_re = re.compile(r'rc://en/', re.UNICODE)

# Converts the specified TSV file
def convertFile(path, fname):
    global book
    global chapter
    global verse
    global rowno
    rowno = 0

    englishPath = os.path.join(english_dir, fname.replace(language_code, "en", 1))
    if os.path.isfile(englishPath):
        data = tsv.tsvRead(englishPath)         # list of rows
        english = tsv.list2Dict(data, [3,2,1])  # dictionary of rows
        data = tsv.tsvRead(path)
        heading = True
        for row in data:
            rowno += 1
            nColumns = len(row)
            if nColumns > 3:
                if nColumns == 8 and len(row[3]) > 4: # A common problem in Gujarati tN, where the ID column is merged with the next column.
                    reportError("Wrong number of columns (8); ID column is invalid", path, key, row[0:4])
                    row = fixID(row)
                    nColumns = 9
                try:
                    verse = int(row[2])
                except ValueError as e:
                    verse = 0
                key = tsv.make_key(row, [3,2,1])
                if not key in english:
                    # The verse number could have changed in the English
                    row[2] = str(verse+1)
                    key = tsv.make_key(row, [3,2,1])
                if not key in english:
                    row[2] = str(verse-1)
                    key = tsv.make_key(row, [3,2,1])
                if nColumns == 9:
                    # Update SupportReference, OrigQuote, and Occurrence to current values from English tN
                    try:
                        origquote = english[key][5]
                    except KeyError as e:
                        # If row no longer exists in the English notes, delete the OrigQuote snippet but keep the note.
                        # Based on Zulip discussion, Jesse, Larry S on 10/29/19.
                        row[2] = str(verse)     # back to original verse number
                        row[5] = ''            # OrigQuote is no longer valid
                    else:
                        row[4] = english[key][4]    # SupportReference
                        row[5] = origquote
                        if english[key][6]  in {'0', '1', '2'}:
                            row[6] = english[key][6]    # Occurrence
                if heading:
                    checkHeader(row, key, path)
                    heading = False
                    chapter = 0     # Do this here in case header is corrupted
                    verse = 0
                else:
                    checkRow(row, nColumns, key, path)
                    if nColumns > 8 and englishlink_re.search(row[8]):
                        new = "rc://" + language_code + "/"
                        row[8] = row[8].replace("rc://en/", new)
            else:
                key = row[0][0:3] + "... "
                reportError("Wrong number of columns (" + str(nColumns) + ")", path, key, None)

        if fname.startswith("en_tn"):
            fname = fname.replace("en_tn", language_code + "_tn", 1)
        targetpath = os.path.join(target_dir, fname)
        tsv.tsvWrite(data, targetpath)
        appendToProjects(book, fname)
    else:
        reportError("No such file in English notes: " + shortname(englishPath), path, "", None)

# Converts the file or files contained in the specified folder
def convert(dir):
    global book

    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(dir):
        if fname[-4:] == ".tsv":
            path = os.path.join(dir, fname)
            book = ''
            convertFile(path, fname)

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global source_dir
        path = os.path.join(source_dir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(source_dir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile

# The fix applies if column 3 has more than four characters, and the row has exactly 8 columns to start.
# This output row should have 9 columns and column 3 is four characters long.
def fixID(row):
    if len(row) == 8 and len(row[3]) > 4:
        col4 = row[3][4:]
        row.insert(4, col4)
        row[3] = row[3][0:4]
    return row

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, fname):
    global projects

    title = usfm_verses.verseCounts[bookId]["en_name"]
    sort = usfm_verses.verseCounts[bookId]["sort"]
    testament = 'nt'
    if sort < 40:
        testament = 'ot'
    project = { "title": title, "id": bookId.lower(), "sort": sort, \
                "path": "./" + fname, "categories": "[ 'bible-" + testament + "' ]" }
    projects.append(project)

# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects

    projects.sort(key=operator.itemgetter('sort'))
    path = os.path.join(target_dir, "projects.yaml")
    manifest = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    versification: 'ufw'\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: " + p['categories'] + "\n")
    manifest.close()

# Writes error message to stderr and to issues.txt.
# locater is the first four columns of a row
def reportError(msg, path, key="", locater=None):
    global rowno
    issue = shortname(path) + ": (" + key + "), row " + str(rowno) + ": " + msg + ".\n"
    try:
        if locater and len(locater) > 3:
            issue = shortname(path) + ": " + locater[0] + " " + locater[1] + ":" + locater[2] + " ID=(" + locater[3] + "), line " + str(rowno) + ": " + msg + ".\n"
        else:
            issue = shortname(path) + ": line " + str(rowno) + ": " + msg + ".\n"
        sys.stderr.write(issue)
    except UnicodeEncodeError as e:
        sys.stderr.write(shortname(path) + ": (Unicode...), line " + str(rowno) + ": " + msg + "\n")

    issues = openIssuesFile()
    issues.write(issue)


# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convert(source_dir)
        dumpProjects()
    elif source_dir[-4:] == ".tsv" and os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path, os.path.basename(path))
    else:
        sys.stderr.write("Invalid directory: " + source_dir)
        exit(-1)

    if issuesFile:
        issuesFile.close()
    print("\nDone.")
