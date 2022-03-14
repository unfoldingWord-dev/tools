# -*- coding: utf-8 -*-
# This script merges the footnotes marked with \footnote into the appropriate location in the USFM text.
# This script was originally written for Assamese books done in MS Word.
# I enhanced it to handle Urdu books, which do not have the a,b,c footnote markers.
# I do some modifications to the text in MS Word first, and export to a UTF-8 text file before using this script.
# The input text has been converted to USFM format except for the footnotes, which are still at the end of the file.

source_dir = r'C:\DCS\Assamese\ULB\convert\hos.usfm'
language_code = 'as'

import io
import os
import re
import sys
from filecmp import cmp

footnotes = []
nFootnotes = 0
footnote_re = re.compile(r'\\footnote +([a-z]+)([\d]+)\:([\d]+) +[\d\:]* *(.+)', re.UNICODE)
footnote2_re = re.compile(r'\\footnote +Z([\d]+)\:([\d]+) +(.+)', re.UNICODE)
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
    elif parsed := footnote2_re.match(line):
        footnote["spot"] = "Z"
        footnote["chapter"] = int(parsed.group(2))
        footnote["verse"] = int(parsed.group(1))
        footnote["text"] = parsed.group(3)
        if language_code == "ur":
            footnote["text"] = footnote["text"].translate(urdu_numbers)
    else:
        if str(n) != "silent":
            sys.stderr.write("Unable to parse footnote in line " + str(n) + '\n')
        footnote = None
    return footnote

# Populates the global footnotes list from the list of lines.
def parseFootnotes(lines):
    global footnotes
    global nFootnotes
    footnotes.clear()
    n = 0
    for line in lines:
        n += 1
        if line.startswith("\\footnote "):
            footnote = parseFootnote(line, n)
            if footnote:
                footnotes.append(footnote)
    nFootnotes = len(footnotes)

usfmtag_re = re.compile(r'(\\[a-z]+)')
# Returns True if the specified position is part of a usfm tag
# Supports usfm tags up to 4 characters long, like \imte.
def partOfUsfmTag(line, pos):
    left = pos - 4
    if left < 0:
        left = 0
    intag = False
    if tag := usfmtag_re.search(line[left:pos+1]):
        intag = line[pos] in tag.group(1)
    return intag 

# Returns the first position in the line where the specified string is found not preceded by a backslash
# Returns -1 if not found.
def findspot(spot, line):
    if spot == "Z":
        pos = len(line) - 2     # keep the newline
    else:
        pos = line.find(spot, 3)
        while pos > 0 and partOfUsfmTag(line, pos):
            pos = line.find(spot, pos+2)
    return pos

# Determines whether there is a footnote or footnotes for the specified line and
# inserts them at the marked spot using the most basic USFM footnote tags.
# Returns the modified line.
def insertFootnote(matching_footnotes, line):
    global footnotes
    for footnote in matching_footnotes:
        pos = findspot(footnote["spot"], line)
        if pos > 0:
            line = line[:pos] + " \\f + \\ft " + footnote["text"] + " \\f* " + line[pos+len(footnote["spot"]):]
            footnotes.remove(footnote)
            # footnote["found"] = True
    return line

# Returns a list of all footnotes for the specified verse.
# Has to recalculate on every call due to multi-line verses.
def listFootnotes(chapter, verse):
    global footnotes
    matching_footnotes = []
    for footnote in footnotes:
        if footnote["chapter"] == chapter and footnote["verse"] == verse:
            matching_footnotes.append(footnote)
    return matching_footnotes

# Prints the number of footnotes inserted and the number of footnotes unable to be inserted.
def reportChanges():
    global footnotes
    global nFootnotes
    sys.stdout.write("    Inserted " + str(nFootnotes-len(footnotes)) + " footnotes. Missed " + str(len(footnotes)) + ".\n")

# Returns False if the line should not be written to output file.
# This is the case when it is a footnote line that has been successfully inserted.
def okayToWrite(line):
    global footnotes
    okay = True
    if line.startswith("\\footnote "):
        if footnote := parseFootnote(line, "silent"):
            okay = (footnote in footnotes)
    return okay

verseable_re = re.compile(r'\\[vpq]', re.UNICODE)

# Returns True if the line could contain a verse or part of a verse.
# Assumes that usfm markers, if any, occur only at the beginning of the line.
def verseable(line):
    line = line.strip()
    return (len(line) > 0 and line[0] != '\\') or (len(line) > 3 and verseable_re.match(line))

chapter_re = re.compile(r'\\c +([\d]+)')
v_re = re.compile(r'\\v +([0-9]+)')
vv_re = re.compile(r'\\v +([0-9]+)-([0-9]+)')

# Returns a set of verse numbers that are included on the specified line
# If the line does not start with a verse marker, prevn is included in the list.
def listVerses(line, prevn):
    vns = set()
    if prevn > 0 and not line.startswith("\\v "):
        vns.add(prevn)
    vlist = v_re.finditer(line)
    for v in vlist:
        vns.add( int(v.group(1)) )
    if vv_range := vv_re.search(line):
        vn = int(vv_range.group(1))
        while vn <= int(vv_range.group(2)):
            vns.add(vn)
            vn += 1
    return vns

# First gathers all the footnotes into a Python list.
# Then goes through each line looking for location matches to a footnote or footnotes.
# Where there are matches, inserts footnote at the intended location(s) in the line.
# Modifies the lines list directly, and writes the new lines to the specified output file.
# Omits \footnote lines from the output, if the footnote was successfully inserted in the text.
def convertText(lines, output):
    nFootnotes = parseFootnotes(lines)   # First pass, only populates the global footnotes list
    if footnotes:
        chapter = 0
        vn = 0
        for line in lines:
            if chap := chapter_re.match(line):
                chapter = int(chap.group(1))
            elif verseable(line):
                vns = listVerses(line, vn)
                for vn in vns:
                    line = handleVerse(chapter, vn, line)
                if vns:
                    vn = max(vns)
            if okayToWrite(line):
                output.write(line)

def handleVerse(chapter, vn, line):
    matching_footnotes = listFootnotes(chapter, vn)
    if matching_footnotes:
        line = insertFootnote(matching_footnotes, line)
    return line


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
