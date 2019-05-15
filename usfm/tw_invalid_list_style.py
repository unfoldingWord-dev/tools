# -*- coding: utf-8 -*-
# This program is intended to remove blank lines between markdown list items.
# List items start with an asterisk followed by a space.
# Backs up the original .md files that are modified.
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
max_changes = 200
filename_re = re.compile(r'.*\.md$')
wholestring = re.compile(u'(\n\* .*)\n\n\* ', flags=re.UNICODE)
prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname


# Converts the text a whole file at a time.
def convertWholeFile(mdpath):
    global nChanged
    input = io.open(mdpath, "tr", encoding="utf-8")
    alltext = input.read()
    input.close()
    found = wholestring.search(alltext)
    if found:
        bakpath = mdpath + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", encoding='utf-8', newline='\n')
        
        # Use this loop if I want multiple replacements per file
        while found:
            output.write( alltext[0:found.start()] + found.group(1) )
            alltext = alltext[found.end()-3:]
            found = wholestring.search(alltext)
        output.write(alltext)
        output.close()
        sys.stdout.write("Fixed " + shortname(mdpath) + "\n")
        nChanged += 1    

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write("Folder: " + shortname(folder) + '\n')
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            convertFolder(path)
        elif filename_re.match(entry):
            convertWholeFile(path)
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
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python fix_invalid_list_style.py <folder>\n  Use . for current folder.\n")
