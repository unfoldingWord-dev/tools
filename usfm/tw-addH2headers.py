# -*- coding: utf-8 -*-
# This program adds 2nd level header (H2) immediately after top level (H1) header if missing in markdown files.
# A level 2 header containing the word for "Definition" is required in every tW markdown file.
# Assumes input .md files are already in UTF-8 format.
# Checks that .md file begins with a properly formatted H1 heading.
# Requires that any existing H2 header immediately after H1 is properly formatted as well.
# Backs up the .md file being modified, using a .orig extension.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
import codecs
import string
import sys

# Globals
# Heading to the added where needed.
# Include hash marks, word for "Definition" in target language, and 2 newlines
h2_terms = u"## વ્યાખ્યા: \n\n"   # คำจำกัดความ    
h2_names = u"## તથ્યો: \n\n"

max_changes = 3000
nChanged = 0
nRead = 0

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname

h1_re = re.compile(r'[ \t\n]*#[ \t].*?\n[ \t\n]*', re.UNICODE+re.DOTALL)
# h2_re = re.compile(r'##[ \t][\w: ]+?\n', re.UNICODE+re.DOTALL)
h2_re = re.compile(r'##[ \t].+?\n', re.UNICODE+re.DOTALL)

# Converts the text a whole file at a time.
def convertWholeFile(mdpath, folder):
    global nChanged
    input = io.open(mdpath, "tr", 1, encoding="utf-8")
    alltext = input.read()
    input.close()
    found = h1_re.match(alltext)
    if found:
        bakpath = mdpath + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.write( alltext[0:found.end()] )
        alltext = alltext[found.end():]
        
        found = h2_re.match(alltext)
        if not found:       # level 2 heading is missing
            h2 = h2_terms
            if folder == 'names':
                h2 = h2_names
            output.write(h2)
            nChanged += 1  
            sys.stdout.write("Converted " + shortname(mdpath) + "\n")
        output.write(alltext)
        output.close()
        
        if found:       # H2 was there all along, revert to original file
            os.remove(mdpath)
            os.rename(bakpath, mdpath)
        # sys.stdout.write("Converted " + shortname(mdpath) + "\n")
    else:
        sys.stderr.write("File does not begin with H1 header: " + shortname(mdpath) + "\n")  

filename_re = re.compile(r'.*\.md$')

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nRead
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write("Convert folder: " + folder + '\n')
    sys.stdout.flush()
    dir = os.path.basename(folder)
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            convertFolder(path)
        elif filename_re.match(entry):
            nRead += 1
            convertWholeFile(path, dir)
        if nChanged >= max_changes:
            break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        folder = r'C:\DCS\Gujarati\gu_tw\bible'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertFolder(folder)
        sys.stdout.write("Done. Changed " + str(nChanged) + " of " + str(nRead) + " files checked.\n")
    else:
        sys.stderr.write("Usage: python tw-addH2headers.py <folder>\n  Use . for current folder.\n")
