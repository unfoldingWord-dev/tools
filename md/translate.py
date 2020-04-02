# -*- coding: utf-8 -*-
# This program does an unlimited number of string substitutions on a folder full of files.
# It uses the substitutions module to provide the data for string replacements.
# Backs up every file, not just those that are modified.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
# import shutil
#import codecs
import substitutions    # this module specifies the string substitutions to apply
import string
import sys

# Globals
nChanged = 0
max_changes = 3333
#filename_re = re.compile(r'[0-9]*\.md$')
filename_re = re.compile(r'.*\.md$')
yes_backup = True

def shortname(longpath):
    shortname = longpath
    if sourceDir in longpath:
        shortname = longpath[len(sourceDir)+1:]
    return shortname

#sub_re = re.compile(u'figs-modismo', re.UNICODE)
#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
#sub_re = re.compile(r'<!-- -->', re.UNICODE)
#sub_re = re.compile(r'&nbsp;', re.UNICODE)
#sub_re = re.compile(r'rc://en/')
#replacement = u'rc://id/'

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change the count argument to re.sub(), below.
def convertFileBySub(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8")
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
    sys.stdout.write("Translated " + os.path.basename(path) + "\n")
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
            elif filename_re.match(entry):
                convertFileBySub(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        path = r'E:\DCS\Croatian\hr_tw\bible'
    else:
        path = sys.argv[1]

    if path and os.path.isdir(path):
        convertFolder(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(path):
        convertFileBySub(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python translate.py <folder>\n  Use . for current folder.\n")
