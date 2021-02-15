# coding: latin-1
# The purpose of this program is to undo changes made by another program that
# at least provided backups of the original files.
# Use with caution as this overwrites files with correct extension.

source_dir = r'C:\DCS\Chinese\zh_tw.RPP\bible'
backupExt = ".md.orig"
correctExt = ".md"
maxChanged = 44444
nChanged = 0

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys


# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
def undoFile(backupPath):
    global nChanged
    global backupExt
    basePath = backupPath[:-len(backupExt)]
#    sys.stdout.write("basePath: <" + basePath + ">\n")
    correctPath = basePath + correctExt
#    sys.stdout.write("correctPath: <" + correctPath + ">\n")
    if os.path.isfile(correctPath):
        os.remove(correctPath)
    os.rename(backupPath, correctPath)
    nChanged += 1    

# Recursive routine to restore all files under the specified folder
def undoFolder(folder):
    global nChanged
    global backupExt
    if nChanged >= maxChanged: 
        return
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            undoFolder(path)
        elif backupExt in entry:
            undoFile(path)
        if nChanged >= maxChanged:
            break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        undoFolder(source_dir)
        sys.stdout.write("Done. Renamed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python revertChanges.py <folder>\n  Use . for current folder.\n")
