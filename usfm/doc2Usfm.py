# -*- coding: utf-8 -*-
# This script converts text files containing whole Bible books to USFM.
# Originally written for a Kurdish Kalhori book of Matthew that was done in MS Word.
# I exported from MS Word to a UTF-8 text file before using this script.
# After running this script, may run segond2rc.py to add section markers.

import codecs
import io
import os
import re
import sys


number_re = re.compile(r'([0-9]+)', re.UNICODE)

def convertText(lines, output):
    for line in lines:
        versenum = number_re.search(line)
        while versenum:
            startpos = versenum.start()
            endpos = versenum.end()
            length = len(line)
            if versenum.group(0) == u"1":
                # I would add a chapter marker here, but the text has chapter labels before
                # each verse 1, which I need to check manually and add \cl marker.
                output.write(u"\n\\p")
            output.write(line[:versenum.start()] + u"\n\\v " + versenum.group(0) + u' ')
            line = line[versenum.end():]
            length = len(line)
            versenum = number_re.search(line)
        output.write(line)
            
def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
        f.close
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default

# Accepts a single file name which contains a book in text format.
# Reads all the lines from that file and converts the text to a single
# USFM file with the same name but different extension.
def convertFile(folder, fname):
    path = os.path.join(folder, fname)
    enc = detect_by_bom(path, default="utf-8")
    input = io.open(path, "tr", 1, encoding=enc)
    lines = input.readlines()
    input.close()
    usfm = fname.replace(".txt", ".usfm")
    outputpath = os.path.join(folder, usfm)
    output = io.open(outputpath, "tw", buffering=1, encoding="utf-8", newline='\n')
    
    convertText(lines, output)   # converts this .txt file to .usfm
    output.close()
    sys.stdout.write("Converted " + fname + '\n')

def convertFolder(folder):
    for fname in os.listdir(folder):
        if fname[-4:].lower() == ".txt":
            convertFile(folder, fname)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convertFolder(r'C:\DCS\Kurdish Kalhori')
    else:       # the first command line argument presumed to be a folder
        convertFolder(sys.argv[1])

    print "\nDone."
