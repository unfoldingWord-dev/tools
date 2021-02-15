# -*- coding: utf-8 -*-
# This program may be modified to do any kind of stream operation on a folder full of files.
# Backs up the .md file being modified.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys

# Globals
source_dir = r'C:\DCS\Urdu-Deva\ur-deva_tn.RPP'
nChanged = 0
max_changes = 1111
filename_re = re.compile(r'.*\.md$')
#filename_re = re.compile(r'.*\.usfm$')
yes_backup = True


# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
inlinekey.append( re.compile(r'(##+ )', flags=re.UNICODE) )

# Copies lines from input to output.
# Modifies targeted input lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines()
    input.close()
    if yes_backup:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
    count = 0
    output = io.open(path, "tw", encoding='utf-8', newline='\n')
    for line in lines:
        for i in range(len(inlinekey)):
            sub = inlinekey[i].match(line)
            if sub:
                line = line[len(sub.group(1)):]
        output.write(line)
    output.close


# keystring is used only in line-by-line, but it is searched against the entire file one time.
keystring = re.compile(r'^##+ ', flags=re.UNICODE+re.MULTILINE)

def convertFileByLines(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    convertme = False
    if keystring.search(alltext):
        convertme = True
    if convertme:
        convertByLine(path)
        nChanged += 1    
        sys.stdout.write("Converted " + shortname(path) + "\n")

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

#h1_re = re.compile(r'# ', flags=re.UNICODE)
heading_re = re.compile(r'#+ ', flags=re.UNICODE)

# Returns True if the file shows a classic erroneous pattern for tN or tQ files.
# Where the translator has marked note titles (or questions) with a single hash mark (which is correct)
# and marked all notes (or answers) with higher level headings (which is incorrect) or as plain text.
# Requirements for classic pattern:
#   First heading and every other line is a level 1 heading.
#   Between level 1 headings are single lines that are either text or a higher level heading.
#   There is at least one heading level 2 or higher.
#   Ends with higher level heading or text.
#   Blank lines are disregarded.
def classic_pattern(mdpath):
    fp = io.open(mdpath, "tr", 1, encoding="utf-8")
    lines = fp.readlines()
    fp.close()
    classic = True
    prevHeadingLevel = 0
    maxHeadingLevel = 0
#    prevtype = TEXT     # initial value to make algorithm simpler
    
    for line in lines:
        if len(line.strip()) == 0:
            continue
        if heading_re.match(line):      # we found a heading
            headingLevel = line.count('#', 0, 5)
            if prevHeadingLevel != 1 and headingLevel != 1:
                classic = False
            elif prevHeadingLevel == 1 and headingLevel == 1:
                classic = False
#            elif ...
#                if altHeadingLevel == 0:
#                    altHeadingLevel = headingLevel
#                elif altHeadingLevel != headingLevel:
#                    classic = False
            prevHeadingLevel = headingLevel
            if headingLevel > maxHeadingLevel:
                maxHeadingLevel = headingLevel
        else:                   # found plain text
            classic = (prevHeadingLevel == 1)
            prevHeadingLevel = 0
        if not classic:
            break
    if prevHeadingLevel == 1 or maxHeadingLevel < 2:
        classic = False
    return classic


# Returns True if the file shows a classic erroneous pattern for tN or tQ files.
# Where the translator has marked note titles (or questions) with 2-or-more level heading (which is incorrect)
# and not marked the notes with a heading (which is correct).
# Requirements for classic pattern:
#   The first line is a heading.
#   Headings alternate with plain text lines.
#   At least one of the headings is level 2 or higher (has 2 or more hash marks).
#   A plain text line follows the last heading.
#   Blank lines may occur anywhere.
def classic_pattern2(mdpath):
    fp = io.open(mdpath, "tr", 1, encoding="utf-8")
    lines = fp.readlines()
    fp.close()
    classic = True
    prevHeadingLevel = 0
    maxHeadingLevel = 0

    for line in lines:
        if len(line.strip()) == 0:
            continue
        if heading_re.match(line):      # we found a heading
            headingLevel = line.count('#', 0, 5)
            if prevHeadingLevel > 0:
                classic = False
            elif headingLevel > maxHeadingLevel:
                maxHeadingLevel = headingLevel
            prevHeadingLevel = headingLevel
        else:           # we found a text line
            if prevHeadingLevel == 0:
                classic = False
            prevHeadingLevel = 0
        if not classic:
            break
    if maxHeadingLevel < 2:
        classic = False
    return classic            
    

wholestring = re.compile(r'([^#\n]+)(\n[^#\n])', flags=re.UNICODE)  # two non-empty lines, neither has a heading
newstring = []
newstring.append('# x\n\n')


# Converts the text a whole file at a time.
# Uses wholestring, newstring[0]
def convertWholeFile(mdpath):
    global nChanged

    input = io.open(mdpath, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    found = wholestring.match(alltext)
    if found:
        if yes_backup:
            bakpath = mdpath + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", buffering=1, encoding='utf-8', newline='\n')
        
        # Use a loop for multiple replacements per file
        if found:
            output.write("# " + found.group(1) + "\n" + found.group(2))
            alltext = alltext[found.end():]
#            found = wholestring.search(alltext)
        output.write(alltext)
        output.close()
        sys.stdout.write("Converted " + shortname(mdpath) + "\n")
        nChanged += 1    

#sub_re = re.compile('figs-questions?', re.UNICODE)
#replacement = 'figs-rquestion'

#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
sub_re = re.compile(r'# *\n', re.UNICODE)
replacement = ""
#sub_re = re.compile(r'</?o:p>', re.UNICODE)
#sub_re = re.compile(r'<!--.*-->', re.UNICODE)
#sub_re = re.compile(r'& *nbsp;', re.UNICODE)
#sub_re = re.compile(r'rc://en/', re.UNICODE)
#sub_re = re.compile(r'[Ll]ih?at[\s]*\:+[\s]*\n+[\s]*\[\[', re.UNICODE)
#sub_re = re.compile(r'# +[\*]+(.*)[\*]+', re.UNICODE)

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change the count argument to re.sub(), below.
def convertFileBySub(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    found = sub_re.search(alltext)
    if found:
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
            
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.write( re.sub(sub_re, replacement, alltext, count=0) )
        output.close()
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1    

def convertFile(path):
#    convertFileByLines(path)
    convertWholeFile(path)
#    convertFileBySub(path)


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
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
