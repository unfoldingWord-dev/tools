# -*- coding: utf-8 -*-
#
# Converts tN files from 7-column to 9-column TSV format, as needed for publishing for tS.
#
#
"""
TSV7 column             TSV7 example                        TSV9
----------------------  ----------------------------------  --------------------------------------------
1 (Reference)           front:intro, 1:intro, 1:1           Split into Chapter (col 2) and Verse (col 3)
2 (ID)                  ab1p                                Copy to ID (col 4)
3 (Tags)                (always blank in Russian)           N/A
4 (SupportReference)    rc://*/ta/man/translate/figs-idiom  Copy only the last part (figs-idiom) to SupportReference (col 5)
5 Quote                 English (PSA),                      Copy to GLQuote (col 8)
                        Greek (TIT),                        Copy to OrigQuote (col 6)
                        Russian (PRO)                       Copy to GLQuote (col 8)
6 Occurrence            0, 1                                Copy to Occurrence (col 7)
7 Note                  “помочь тебе понять мудрые учения”  Copy to OccurrenceNote (col 9)
"""

# Global variables
source_dir = r'C:\DCS\Kannada\TN'
output_dir = r'C:\DCS\Kannada\work'
language_code = "kn"

import io
import langdetect
import os
import re
import sys
import tsv
import usfm_verses

def reportError(msg):
    if msg[-1] != '\n':
        msg += '\n'
    sys.stderr.write(msg)

def shortname(path):
    shortname = path
    if source_dir in path and source_dir != path:
        shortname = path[len(source_dir)+1:]
    return shortname

# Returns 3-character book ID based on file name
def getBookId(fname):
    return fname[-7:-4].upper()

def getBookNumber(bookId):
    return usfm_verses.verseCounts[bookId]['usfm_number']

def makeOutputPath(bookId):
    bookNumber = getBookNumber(bookId)
    return os.path.join(output_dir, f"{language_code}_tn_{bookNumber}-{bookId}.tsv")

# Returns the index of the column where the quote should go in the 9-column file.
# English quotes and Russian quotes will go into the GLQuote column.
# Greek and Hebrew quotes will go into the OrigQuote column.
def row9column(quote):
    row9column.n = 7
    if quote:
        try:
            langid = langdetect.detect(quote)
            if langid in {'he', 'el'}:  # Hebrew or Greek
                row9column.n = 5
            elif langid in {'en','mk'}:     # mk is Russian
                row9column.n = 7
            else:
                reportError(f"New language detected in quote: {langid}")
        except langdetect.LangDetectException as e:
            x = 1   # handle the exception by doing nothing
    return row9column.n

# Strips leading and trailing spaces from each field in the data.
# Strips paired quotes surrounding each field.
def strip_quotes(data):
    for row in data:
        for i in range(0, len(row)):
            str = row[i].strip(' ')     # remove leading and trailing spaces
            while len(str) > 1 and str[0] == '"' and str[-1] == '"':
                str = str[1:-1]
            row[i] = str

# Maps values from TSV7 row to TSV9
# Converts \n to <br> in the Note column
def convertRow(bookId, row7):
    row9 = [''] * 9
    row9[0] = bookId
    (row9[1], row9[2]) = row7[0].split(':')
    row9[3] = row7[1]
    row9[4] = row7[3].split('/')[-1]    # copies necessary part of SupportReference value
    col = row9column(row7[4])   # returns 5 or 7
    row9[col] = row7[4]
    row9[6] = row7[5]
    row9[8] = row7[6].replace('\\n', '<br>')
    return row9

# Converts each row from 7-column to 9-column format.
# The input format must be correct for this to work.
def convertFile(path, fname):
    sys.stdout.write(f"Converting {fname}\n")
    sys.stdout.flush()
    data7 = tsv.tsvRead(path)
    strip_quotes(data7)
    data9 = []
    bookId = getBookId(fname)
    rowno = 1
    for row in data7:
        if len(row) != 7:
            reportError(f"Wrong number of colums ({len(row)}) in row {rowno}")
            break
        elif rowno == 1:
            newrow = ['Book','Chapter','Verse','ID','SupportReference','OrigQuote','Occurrence','GLQuote','OccurrenceNote']
        else:
            newrow = convertRow(bookId, row)
        data9.append(newrow)
        rowno += 1
    outpath = makeOutputPath(bookId)
    tsv.tsvWrite(data9, outpath)

# Converts the file or files contained in the specified folder
def convert(dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for fname in os.listdir(dir):
        if fname[-4:] == ".tsv":
            path = os.path.join(dir, fname)
            book = ''
            convertFile(path, fname)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    if os.path.isdir(source_dir):
        convert(source_dir)
    elif source_dir[-4:] == ".tsv" and os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path, os.path.basename(path))
    else:
        sys.stderr.write("Invalid directory: " + source_dir)
        exit(-1)

    print("\nDone.")
