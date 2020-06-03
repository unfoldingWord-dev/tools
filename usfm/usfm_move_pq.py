# -*- coding: utf-8 -*-
# This program moves standalone \p \m and \q markers which occur just before an \s# marker
# to the next line after the \s# marker.
# This is to avoid the Door43 warning message, "useless \q# markers before \s# markers"
# Outputs .usfm files of the same name in the same location.
# Backs up the original files to .usfm.orig files.

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys

# Globals
nChanged = 0            # number of files changed
max_changes = 8
sourceDir = r'E:\DCS\Kannada\kn_iev'
filename_re = re.compile(r'.*\.usfm$')

# wholestring is used with whole file matches
wholestring = re.compile(r'\n(\\[pqm][1-9]*?)\n(\\s[0-9])\n', flags=re.UNICODE+re.DOTALL)

def shortname(longpath):
    shortname = longpath
    if sourceDir in longpath:
        shortname = longpath[len(sourceDir)+1:]
    return shortname


# Converts the text a whole file at a time.
def convertWholeFile(mdpath):
    global nChanged
    input = io.open(mdpath, "tr", 1, encoding="utf-8")
    alltext = input.read()
    input.close()
    found = wholestring.search(alltext)
    if found:
        bakpath = mdpath + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", buffering=1, encoding='utf-8', newline='\n')
        while found:
            output.write( alltext[0:found.start()] + '\n' + found.group(2) + '\n' + found.group(1) + '\n' )
            alltext = alltext[found.end():]
            found = wholestring.search(alltext)
        output.write(alltext)
        output.close()
        sys.stdout.write("Converted " +shortname(mdpath) + "\n")
        nChanged += 1    

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write("Convert folder: " + shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                convertWholeFile(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        sourceDir = sys.argv[1]
    if sourceDir and os.path.isdir(sourceDir):
        convertFolder(sourceDir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python usfm_move_pq.py <folder>\n  Use . for current folder.\n")
