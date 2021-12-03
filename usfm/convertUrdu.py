# -*- coding: utf-8 -*-
# This program converts an prepped Urdu text file containing a Bible book to USFM form.
#    Extra-biblical content (book overview, outline, footnotes, etc.) has been removed.
#    Chapters are already marked.
#    Verse numbers all begin on a new line.
# Leaves .txt file unchanged.
# Writes .usfm file to same folder. Backs up existing .usfm file, if any.

# Remaining work to be implemented:
#   Convert numbers (other than numbers that are part of USFM tags) to Urdu.

import re       # regular expression module
import io
import os
import string
import sys

# Globals
source_dir = r'C:\DCS\Urdu\Bible\Genesis.txt'
nChanged = 0
max_changes = 1
filename_re = re.compile(r'.*\.txt$')


def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

chapter_re = re.compile(r'\\c +([0-9]+)', re.UNICODE)
numbers = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# Finds chapters marked with \c 123...
# Adds \cp line with the publishable chapter number.
def convertChapters(alltext, usfmpath):
    output = io.open(usfmpath, "tw", encoding='utf-8', newline='\n')
    found = chapter_re.search(alltext)
    while found:
        chapter = found.group(1)
        output.write(alltext[0:found.end()] + "\n\\cp " + chapter.translate(numbers))
        alltext = alltext[found.end():]
        found = chapter_re.search(alltext)
    output.write(alltext)
    output.close()
    
verse_re = re.compile(r'([0-9\-]+)[۔\. ]', flags=re.UNICODE)

# Positions at text following the first \c 1.
# Finds verses marked by a number followed by an Urdu or ASCII period.
# Inserts \p before verse 1
# Inserts \v at the beginning of a line, before the verse number. Loses the period.
# Inserts \vp ...\vp* with the publishable verse number.
def convertVerses(alltext, usfmpath):
    pos = alltext.find("\\c 1")
    if pos >= 0:
        output = io.open(usfmpath, "tw", encoding='utf-8', newline='\n')
        output.write(alltext[0:pos+5])
        alltext = alltext[pos+5:]
        found = verse_re.search(alltext)
        while found:
            start = found.start()
            if start > 2 and alltext[start-2:start-1] != "v ":
                verse = found.group(1)
                if verse == "1":
                    str = "\\p\n\\v "
                elif alltext[start-1] != '\n':
                    str = "\n\\v "
                else:
                    str = "\\v "
            pubverse = verse.translate(numbers)
            output.write(alltext[0:start] + str + verse + " \\vp " + pubverse + "\\vp* ")
            alltext = alltext[found.end():]
            found = verse_re.search(alltext)
        output.write(alltext)
        output.close()

introtag_re = re.compile(r'\\io[t12] ', re.UNICODE)
versetag_re = re.compile(r'\\v [0-9\-]+ ', re.UNICODE)

# Finds Arabic numbers that need to be converted to urdu and converts them.
# Writes to usfmpath.
def convertNumbers(lines, usfmpath):
    output = io.open(usfmpath, "tw", encoding='utf-8', newline='\n')
    for line in lines:
        found = introtag_re.match(line)
        if not found:
            found = versetag_re.match(line)
        if found:
            publine = line[0:found.end()] + line[found.end():].translate(numbers)
        else:
            publine = line
        output.write(publine)
    output.close()

def convertFile(path):
    global nChanged

    with io.open(path, "tr", 1, encoding="utf-8-sig") as input:
        alltext = input.read()
    pair = os.path.splitext(path)
    usfmPath = pair[0] + ".usfm"
    bakpath = usfmPath + ".orig"
    if os.path.isfile(usfmPath) and not os.path.isfile(bakpath):
        os.rename(usfmPath, bakpath)
    convertChapters(alltext, usfmPath)
    with io.open(usfmPath, "tr", 1, encoding="utf-8-sig") as input:
        alltext = input.read()
    convertVerses(alltext, usfmPath)
    with io.open(usfmPath, "tr", 1, encoding="utf-8-sig") as input:
        lines = input.readlines()
    convertNumbers(lines, usfmPath)
    sys.stdout.write("Converted " + shortname(path) + "\n")
    nChanged += 1

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write(shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                convertFile(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    
    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Converted " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Converted " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python convertUrdu.py <folder>\n  Use . for current folder.\n")
