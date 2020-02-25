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
nChanged = 0
max_changes = 111
#filename_re = re.compile(r'[0-9]*\.md$')
filename_re = re.compile(r'.*\.md$')
yes_backup = True

# wholestring is used with whole file matches
wholestring = re.compile(r'^##+ +(.*?$)', flags=re.UNICODE+re.MULTILINE)

# keystring is used in line-by-line, but is searched against the whole file once only
keystring = []
keystring.append( re.compile(r'^# [\*\_]', flags=re.UNICODE+re.MULTILINE) )


# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
inlinekey.append( re.compile(r'# +[\*]+([^\*]*)[\*]+ *$', re.UNICODE))
inlinekey.append( re.compile(r'# +[_]+([^\_]*)[_]+ *$', flags=re.UNICODE))

# Strings to replace with
# whole file matches use newstring[0]
newstring = []
newstring.append( u'# ' )
newstring.append( u'# ' )

# Copies lines from input to output.
# Modifies targeted input lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    input = io.open(path, "tr", 1, encoding="utf-8")
    lines = input.readlines()
    input.close()
    if yes_backup:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
    count = 0
    output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    for line in lines:
        count += 1
        for i in range(len(inlinekey)):
            sub = inlinekey[i].match(line)
            if sub:
                line = newstring[i] + sub.group(1) + u'\n'
#            while sub:
#                line = line[0:sub.start()] + newstring[i] + sub.group(1) + u'\n'
#                line = sub.group(1) + u"" + sub.group(2)
#                line = line[0:sub.start()] + newstring[i] + sub.group(1) + u' ' + line[sub.end():]
                sub = inlinekey[i].search(line)
        output.write(line)
    output.close
    
# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
def convertFileByLines(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8")
    alltext = input.read()
    input.close()
    convertme = False
    for key in keystring:
        if key.search(alltext):
            convertme = True
            break
    if convertme:
        convertByLine(path)
        nChanged += 1    
        sys.stdout.write("Converted " + shortname(path) + "\n")

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
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
            headingLevel = line.count(u'#', 0, 5)
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
            headingLevel = line.count(u'#', 0, 5)
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
    

# Converts the text a whole file at a time.
# Uses wholestring, newstring[0]
def convertWholeFile(mdpath):
    global nChanged

    found = classic_pattern(mdpath)
#    found = wholestring.match(alltext)
    if found:
        input = io.open(mdpath, "tr", 1, encoding="utf-8")
        alltext = input.read()
        input.close()
        if yes_backup:
            bakpath = mdpath + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", buffering=1, encoding='utf-8', newline='\n')
        
        # Use a loop for multiple replacements per file
        found = wholestring.search(alltext)
        while found:
         # if found:
            output.write(alltext[0:found.start()] + found.group(1))
            alltext = alltext[found.end():]
            found = wholestring.search(alltext)
        output.write(alltext)
        output.close()
        sys.stdout.write("Converted " + shortname(mdpath) + "\n")
        nChanged += 1    

sub_re = re.compile(u'figs-active]] passive', re.UNICODE)
#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
#sub_re = re.compile(r'</?o:p>', re.UNICODE)
#sub_re = re.compile(r'<!-- -->', re.UNICODE)
#sub_re = re.compile(r'& nbsp;', re.UNICODE)
#sub_re = re.compile(r'rc://en/', re.UNICODE)
#sub_re = re.compile(r'[Ll]ih?at[\s]*\:+[\s]*\n+[\s]*\[\[', re.UNICODE)
#sub_re = re.compile(r'# +[\*]+(.*)[\*]+', re.UNICODE)
replacement = u'figs-activepassive]]'

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change the count argument to re.sub(), below.
def convertFileBySub(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8")
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
#    convertWholeFile(path)
    convertFileBySub(path)


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
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        path = r'E:\DCS\Croatian\hr_tn\lev'
    else:
        path = sys.argv[1]

    if path and os.path.isdir(path):
        convertFolder(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(path):
        convertFile(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
