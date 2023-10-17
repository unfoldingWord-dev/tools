# coding: latin-1
# The purpose of this program is to undo changes made by another program that
# at least provided backups of the original files.
# Use with caution as this overwrites files with correctExt extension.

import configreader
import re       # regular expression module
import io
import os
import string
import sys

config = None
backupExt = None
correctExt = None
maxChanged = 11111
nChanged = 0

# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
def undoFile(backupPath):
    global nChanged
    global backupExt
    basePath = backupPath[:-len(backupExt)]
    correctPath = basePath + correctExt
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
    config = configreader.get_config(sys.argv, 'revertChanges')
    if config:
        source_dir = config['source_dir']
        backupExt = config['backupExt']
        correctExt = config['correctExt']
        undoFolder(source_dir)
        sys.stdout.write("Done. Renamed " + str(nChanged) + " files.\n")
