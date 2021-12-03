# -*- coding: utf-8 -*-
# This script merges the footnotes marked with \footnote into the appropriate location in the USFM text.
# This script was originally written for Assamese books done in MS Word.
# I enhanced it to handle Urdu books, which do not have the a,b,c footnote markers.
# I do some modifications to the text in MS Word first, and export to a UTF-8 text file before using this script.
# The input text has been converted to USFM format except for the footnotes, which are still at the end of the file.

source_dir = r'C:\DCS\Urdu\Bible\Genesis.usfm'
language_code = 'ur'

import io
import os
import re
import sys
from filecmp import cmp

footnotes = []
footnote_re = re.compile(r'\\footnote ([a-z]+)([\d]+)\:([\d]+) +[\d]+\:[\d]+ +(.+)', re.UNICODE)
footnote2_re = re.compile(r'\\footnote Z([\d]+)\:([\d]+) +(.+)', re.UNICODE)
urdu_numbers = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


# Returns a Dictionary object with all information about the footnote in the specified line
# Returns an empty Dictionary if parsing fails.
def parseFootnote(line, n):
    footnote = {}
    if parsed := footnote_re.match(line):
        footnote["spot"] = parsed.group(1)
        footnote["chapter"] = int(parsed.group(2))
        footnote["verse"] = int(parsed.group(3))
        footnote["text"] = parsed.group(4)
        footnote["found"] = False
    elif parsed := footnote2_re.match(line):
        footnote["spot"] = "Z"
        footnote["chapter"] = int(parsed.group(2))
        footnote["verse"] = int(parsed.group(1))
        footnote["text"] = parsed.group(3)
        if language_code == "ur":
            footnote["text"] = footnote["text"].translate(urdu_numbers)
        footnote["found"] = False
    else:
        sys.stderr.write("Unable to parse footnote in line " + str(n) + '\n')
        footnote = None
    return footnote    

# Populates the global footnotes list from the list of lines.
def parseFootnotes(lines):
    global footnotes
    footnotes.clear()
    n = 0
    for line in lines:
        n += 1
        if line.startswith("\\footnote "):
            footnote = parseFootnote(line, n)
            if footnote:
                footnotes.append(footnote)

# Returns the first position in the line where the specified string is found not preceded by a backslash
# Returns -1 if not found.
def findspot(spot, line):
    if spot == "Z":
        pos = len(line) - 2     # keep the newline
    else:
        pos = line.find(spot, 3)
        while pos > 0 and line[pos-1] == '\\':
            pos = line.find(spot, pos+2)
    return pos

# Determines whether there is a footnote or footnotes for the specified line and
# inserts them at the marked spot using the most basic USFM footnote tags.
# Returns the modified line.
def insertFootnote(chapter, verse, line):
    global footnotes
    for footnote in footnotes:
        if footnote["chapter"] > chapter:
            break
        if footnote["chapter"] == chapter and footnote["verse"] == verse:
            pos = findspot(footnote["spot"], line)
            if pos > 0:
                line = line[:pos] + " \\f + \\ft " + footnote["text"] + " \\f* " + line[pos+len(footnote["spot"]):]
                footnote["found"] = True
    return line

# Prints the number of footnotes inserted and the number of footnotes unable to be inserted.
def reportChanges():
    global footnotes
    nInserts = 0
    for footnote in footnotes:
        if footnote["found"]:
            nInserts += 1
    nMissed = len(footnotes) - nInserts
    sys.stdout.write("    Inserted " + str(nInserts) + " footnotes. Missed " + str(nMissed) + ".\n")
    for footnote in footnotes:
        if not footnote["found"]:
            print("      Missed " + str(footnote)[0:10])

# Returns False if the line should not be written to output file.
# This is the case when it is a footnote line that has been successfully inserted.
def okayToWrite(line):
    global footnotes
    okay = True
    if line.startswith("\\footnote "):
        footnote = parseFootnote(line, "unknown")
        okay = (footnote in footnotes)
    return okay

# number_re = re.compile(r'([0-9]+)', re.UNICODE)
chapter_re = re.compile(r'\\c +([\d]+)')
verse_re = re.compile(r'\\v ([\d\-]+)')
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

# First gathers all the footnotes into a Python list.
# Then goes through each line looking for location matches to a footnote or footnotes.
# Where there are matches, inserts footnote at the intended location(s) in the line.
# Modifies the lines list directly, and writes the new lines to the specified output file.
# Omits \footnote lines from the output, if the footnote was successfully inserted in the text.
def convertText(lines, output):
    parseFootnotes(lines)   # First pass, only populates the global footnotes list
    if footnotes:
        for line in lines:
            if chap := chapter_re.match(line):
                chapter = int(chap.group(1))
            elif vv := verse_re.match(line):
                vstr = vv.group(1)
                vv_range = vv_re.match(vstr)
                if vv_range:
                    vn = int(vv_range.group(1))
                    vnEnd = int(vv_range.group(2))
                    while vn <= vnEnd:
                        line = insertFootnote(chapter, vn, line)
                        vn += 1
                else:
                    line = insertFootnote(chapter, int(vstr), line)
            if okayToWrite(line):
                output.write(line)
            
# Integrates the footnotes in the specified USFM file.
# Backs up the original .usfm files to .usfm.orig.
def convertFile(folder, fname):
    path = os.path.join(folder, fname)
    input = io.open(path, "tr", encoding='utf-8-sig')
    lines = input.readlines()
    input.close()
    outputpath = path  + ".tmp"
    output = io.open(outputpath, "tw", encoding="utf-8", newline='\n')
    convertText(lines, output)
    output.close()

    statinfo = os.stat(outputpath)
    if statinfo.st_size > 1000 and not cmp(path, outputpath, shallow=False):
        bakpath = path + ".orig"
        if not os.path.exists(bakpath):
            os.rename(path, bakpath)
        else:
            os.remove(path)
        os.rename(outputpath, path)
        sys.stdout.write("Converted " + fname + '\n')
        reportChanges()
    else:
        os.remove(outputpath)

# Converts a single folder of USFM files.
def convertFolder(folder):
    for fname in os.listdir(folder):
        if fname.endswith(".usfm"):
            convertFile(folder, fname)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if os.path.isdir(source_dir):
        convertFolder(source_dir)
        print("\nDone.")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(source_dir, os.path.basename(path))
        print("\nDone.")
    else:
        print("Not a valid folder: " + source_dir + '\n')
