# -*- coding: utf-8 -*-
# This script does some fixup to a folder of tN .tsv files and saves them to a new location.
# It edits the files in these ways:
#    Sets the OrigQuote column values to match what is in the English tN.
#    Removes leading and trailing spaces from each field value.
#    Specify target output folder.
#    Standardizes the names of book folders in the target folder.
#    Ensures blank lines surrounding markdown headers.
#    Makes a manifest.txt file to be pasted into manifest.yaml.
#    Fixes links of this form 'rc://en/'

# Global variables
language_code = u'kn'
target_dir = r'C:\DCS\Kannada\kn_tn_tsv'
english_dir = r'C:\DCS\English\en_tn'    # English tN
book = u''
chapter = 0
verse = 0
issuesFile = None

import re
import io
import os
import sys
import codecs
import tsv

badheading_re = re.compile(r'#[^# ]', re.UNICODE)

# Reports an error if there is anything wrong with the header row
def checkHeader(row, key, path):
    if key != u"ID.Verse.Chapter":
        reportError("Invalid labels in header row", path, "")
    if len(row) != 9:
        reportError("Wrong number of columns (" + str(len(row)) + ") in header row", path, "")

# Checks the specified non-header row values.
# Reports errors.
def checkRow(row, key, path):
    global book
    global chapter
    global verse

    abort = False
    if not book:
        book = row[0]
    if row[0] != book:
        reportError("Bad book name (" + row[0] + ")", path, key)

    if row[1] != u'front':
        try:
            c = int(row[1])
            if c == chapter + 1:
                chapter = c
            elif c != chapter:
                reportError("Non-sequential chapter number", path, key)
        except ValueError as e:
            c = 0
            reportError("Non-numeric chapter number", path, key)
    if row[2] == u'intro':
        verse = 0
    else:
        try:
#           Based on 10/29/19 discussion on Zulip, the verse order in TSV file is not important.
#           if int(row[2]) < verse:
#               reportError("Verse number out of order", path, key)
            verse = int(row[2])
        except ValueError as e:
            reportError("Non-numeric verse number", path, key)

    if len(row[3]) != 4:
        reportError("Invalid ID", path, key)
    if len(row) != 9:
        reportError("Wrong number of columns (" + str(len(row)) + ")", path, key)
    if badheading_re.search(row[8]):
        reportError("Missing space after hash mark(s)", path, key)


englishlink_re = re.compile(r'rc://en/', re.UNICODE)

# Converts the specified TSV file
def convertFile(path, fname):
    global book
    global chapter
    global verse

    englishPath = os.path.join(english_dir, fname.replace(language_code, "en", 1))
    if os.path.isfile(englishPath):
        data = tsv.tsvRead(englishPath)
        english = tsv.list2Dict(data, [3,2,1])
        data = tsv.tsvRead(path)
        heading = True
        for row in data:
            if len(row) > 3:
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
                try:
                    origquote = english[key][5]
                except KeyError as e:
                    # If row no longer exists in the English notes, delete the snippet but keep the note.
                    # Based on Zulip discussion, Jesse, Larry S on 10/29/19.
                    row[2] = str(verse)     # back to original verse number
                    row[5] = u''            # OrigQuote is no longer valid
                else:
                    row[5] = origquote
                    row[6] = english[key][6]    # Occurrence
                while len(row) < 9:
                    row.append(u'')
                if heading:
                    checkHeader(row, key, path)
                    heading = False
                    chapter = 0     # Do this here in case header is corrupted
                    verse = 0
                else:
                    checkRow(row, key, path)
                    if englishlink_re.search(row[8]):
                        new = u"rc://" + language_code + r"/"
                        row[8] = row[8].replace(u"rc://en/", new)
            else:
                reportError("Not enough columns in row", path, key)

        targetpath = os.path.join(target_dir, fname)
        tsv.tsvWrite(data, targetpath)
    else:
        reportError("No such file: " + shortname(englishPath), path, "")

# Converts the file or files contained in the specified folder
def convert(dir):
    global book

    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(dir):
        if fname[-4:] == ".tsv":
            path = os.path.join(dir, fname)
            book = u''
            convertFile(path, fname)

# If issues.txt file is not already open, opens it for writing.
# First renames existing issues.txt file to issues-oldest.txt unless
# issues-oldest.txt already exists.
# Returns new file pointer.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global sourceDir
        path = os.path.join(sourceDir, "issues.txt")
        if os.path.exists(path):
            bakpath = os.path.join(sourceDir, "issues-oldest.txt")
            if not os.path.exists(bakpath):
                os.rename(path, bakpath)
        issuesFile = io.open(path, "tw", buffering=4096, encoding='utf-8', newline='\n')
    return issuesFile
    
prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname

# Writes error message to stderr and to issues.txt.
def reportError(msg, path, key):
    try:
        sys.stderr.write(shortname(path) + ": " + key + ": " + msg + ".\n")
    except UnicodeEncodeError as e:
        sys.stderr.write(shortname(path) + ": (Unicode...): " + msg + "\n")
 
    issues = openIssuesFile()       
    issues.write(shortname(path) + u": " + key + u": " + msg + u".\n")


# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        source = r'C:\DCS\Kannada\TSV\Stage 3'
    else:       # the first command line argument presumed to be a folder
        source = sys.argv[1]

    if os.path.isdir(source):
        sourceDir = source
        convert(sourceDir)
    elif os.path.isfile(source):
        sourceDir = os.path.dirname(source)
        convert(sourceDir)
    else:
        reportError("File not found: " + source + '\n') 

    if issuesFile:
        issuesFile.close()
    print "\nDone."
