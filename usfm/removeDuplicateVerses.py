# -*- coding: utf-8 -*-
# This script is used to fix usfm3 files coming out of tC.
# They often contain empty verse markers on lines by themselves that duplicate verse ranges preceding or following.
# Backs up the .usfm file being modified.
# Outputs .usfm files of the same name in the same location.

import re       # regular expression module
import io
import os
import sys

# Globals
source_dir = r'C:\DCS\Hindi\hi_iev'
nChanged = 0
max_changes = 66
#filename_re = re.compile(r'intro\.md$')
filename_re = re.compile(r'.+\.usfm$')
yes_backup = True
lastv1 = 0
lastv2 = 0

# Returns True if the file qualifies for line removal
def file_qualifies(lines):
    return True

verse_re = re.compile(r'\\v ([0-9]{1,3})', re.UNICODE)
verserange_re = re.compile(r'\\v ([0-9]{1,3})\-([0-9]{1,3}) ', re.UNICODE)
widow_re = re.compile(r'(\\v [0-9]{1,3}) *$', re.UNICODE)       # verse tag on a line by itself

# This function contains the main logic of the script.
# Returns True if the line is to be kept, False if not.
# Redefine this function to obtain desired behavior.
def keeper(line, lookahead):
    global lastv1
    global lastv2
    keep = True
    verse = verse_re.match(line)
    if verse:
        range = verserange_re.match(line)
        if range:
            lastv1 = int(range.group(1))  # remember the first verse in the range
            lastv2 = int(range.group(2))  # remember the last verse in the range
        else:
            widow = widow_re.match(line)
            if widow:
                if lookahead.startswith(widow.group(1)):  # next line starts with same verse number as current (widow) verse
                    keep = False
                else:
                    v = int(verse.group(1))
                    if v >= lastv1 and v <= lastv2:      # current widow is in the range of the previous set
                        keep = False
            lastv1 = int(verse.group(1))    # from verse_re
            lastv2 = lastv1
    return keep

# Copies selected lines from input to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
# Returns
def filterLines(path):
    global prevlost
#    global prevblank
    global nlines
    prevlost = False
#    prevblank = True
    input = io.open(path, "tr", 1, encoding="utf-8")
    lines = input.readlines()
    input.close()
#    nlines = len(lines)
    outputlines = []
    changed = False
    if file_qualifies(lines):
        nIn = 0
        while nIn < len(lines) - 1:
            if keeper(lines[nIn], lines[nIn+1]):
                outputlines.append(lines[nIn])
            else:
                changed = True
            nIn += 1
        outputlines.append(lines[nIn])   # copy the last line

    if changed:
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.writelines(outputlines)
        output.close
    return changed
#    sys.stdout.write("Converted " + shortname(path) + "\n")
    
def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write(shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':         # exclude .git and other hidden folders
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                if filterLines(path):
                    sys.stdout.write("Converted " + shortname(path) + "\n")
                    nChanged += 1
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        if filterLines(path):
            sys.stdout.write("Done. Changed 1 file.\n")
    else:
        sys.stderr.write("Usage: python removelines.py <folder>\n  Use . for current folder.\n")
