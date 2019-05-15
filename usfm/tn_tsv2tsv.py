# -*- coding: utf-8 -*-
# This script does some fixup to a folder of tN .tsv files and saves them to a new location.
# It edits the files in these ways:
#    Sets the OrigQuote column values to match what is in the English tN.
#    Removes leading and trailing spaces from each field value.
#    Specify target output folder.
#    Standardizes the names of book folders in the target folder.
#    Ensures blank lines surrounding markdown headers.
#    Makes a manifest.txt file to be pasted into manifest.yaml.
#    Fixes links of this form [[:en:...]]

# Global variables
language_code = u'hi'
target_dir = r'C:\DCS\Hindi\hi_tn'
english_dir = r'C:\DCS\English\en_tn'    # English tN
book = u''
chapter = 0
verse = 0

import re
import io
import os
import sys
import codecs
import tsv

badheading_re = re.compile(r'#[^# ]', re.UNICODE)

def checkRow(row, key, path):
    global book
    global chapter
    global verse

    if len(row[3]) != 4 and row[3] != u'ID':
        sys.stderr.write("Invalid ID for u'" + key + "' in: " + path + '\n')
    if len(row) != 9:
        sys.stderr.write("Wrong number of columns (" + str(len(row)) + ") in u'" + key + "' row in: " + path + '\n')
    if badheading_re.search(row[8]):
        sys.stderr.write("Missing space after heading marker in u'" + key + "' in: " + path + '\n')

    if row[0] == u'Book':   # first row in a new file
        book = u''
        chapter = 0
        verse = 0
    else:
        if not book:
            book = row[0]
        if row[0] != book:
            sys.stderr.write("Bad book name (" + row[0] + ") for u'" + key + "' in: " + path + '\n')

        if row[1] == u'front':
            chapter = 0
            verse = 0
        else:
            if int(row[1]) == chapter + 1:
                chapter = int(row[1])
            elif int(row[1]) != chapter:
                sys.stderr.write("Bad chapter number for u'" + key + "' in: " + path + '\n')
        if row[2] == u'intro':
            verse = 0
        else:
            if int(row[2]) < verse:
                sys.stderr.write("Bad verse number for u'" + key + "' in: " + path + '\n')
            verse = int(row[2])

# Converts the specified TSV file
def convertFile(path, fname):
    englishPath = os.path.join(english_dir, fname.replace(language_code, "en", 1))
    if os.path.isfile(englishPath):
        data = tsv.tsvRead(englishPath)
        english = tsv.list2Dict(data, [3,2,1])
        data = tsv.tsvRead(path)
        for row in data:
            key = tsv.make_key(row, [3,2,1])
            try:
                origquote = english[key][5]
            except KeyError as e:
                sys.stderr.write("Key: u'" + key + "' is not found in English file: " + englishPath + '\n')
            else:
                if origquote and not row[5]:
                    row[5] = origquote
                    row[6] = english[key][6]
            while len(row) < 9:
                row.append(u'')
            fix invalid links!!
            checkRow(row, key, path)
        targetpath = os.path.join(target_dir, fname)
        tsv.tsvWrite(data, targetpath)
    else:
        sys.stderr.write("No such file: " + englishPath + '\n')

# Converts the file or files contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    for fname in os.listdir(dir):
        if fname[-4:] == ".tsv":
            path = os.path.join(dir, fname)
            convertFile(path, fname)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convert(r'C:\DCS\Hindi\hi_tN.lversaw_fork')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print "\nDone."
