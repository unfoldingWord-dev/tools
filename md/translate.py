# -*- coding: utf-8 -*-
# This program does an unlimited number of string substitutions on a folder full of files.
# It uses the substitutions module to provide the data for string replacements.
# Backs up every file with .orig extension, not just those that are modified.
# Outputs files of the same name in the same location.

import re       # regular expression module
import io
import os
import substitutions    # this module specifies the string substitutions to apply
import string
import sys

# Globals
source_dir = r"C:\DCS\Malayalam\ml_ta.work"
#filename_re = re.compile(r'[0-9]*\.md$')
filename_re = re.compile(r'.*\.md$')
nChanged = 0
max_changes = 111
yes_backup = True

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Returns True if the specified file contains any of the strings to be translated.
def fileQualifies(path):
    qualify = False
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    for pair in substitutions.subs:
        if pair[0] in alltext:
            qualify = True
            break
    return qualify

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change the count argument to re.sub(), below.
def convertFileBySub(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    if yes_backup:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
    output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')

    for pair in substitutions.subs:
        alltext = alltext.replace(pair[0], pair[1])
   
    output.write( alltext )
    output.close()
    sys.stdout.write("Translated " + shortname(path) + "\n")
    nChanged += 1    

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write(folder + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry) and fileQualifies(path):
                convertFileBySub(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    
    if os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        if fileQualifies(path):
            convertFileBySub(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python translate.py <folder>\n  Use . for current folder.\n")
