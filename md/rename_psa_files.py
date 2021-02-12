# -*- coding: utf-8 -*-
# The purpose of this program is to rename files and folders in Psalms according to the recommended standard.
# For tQ projects, the folder and file names should be a mixture of 2-digit and 3-digit names
# (not counting the .md file extensions)
# For tN projects, the folder and files names should all be 3 digits long (plus the .md extension).

source_dir = r'C:\DCS\Thai\th_tq.RPP\psa'
resource_type = 'tq'
maxChanged = 2000   # there are at least 2000 files possible in Psalms
nChanged = 0

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys

# Detects whether TQ folder is properly named and renames it as appropriate.
def renameTQFolder(folder):
    global nChanged
    dirname = os.path.basename(folder)
    if dirname[0] == '0' and len(dirname) == 3:
        newname = folder[:-3] + folder[-2:]
        os.rename(folder, newname)
        nChanged += 1

# Detects whether Psalms TQ file is properly named and renames it as appropriate.
def renameTQFile(folder, fname):
    global nChanged
    newname = None
    if len(fname) == 6 and fname[0] == '0':
        newname = os.path.join(folder, fname[1:])
        oldname = os.path.join(folder, fname)
        os.rename(oldname, newname)
        nChanged += 1    

# Recursive routine to rename all files and folders under the specified folder.
# Depth first tree traversal.
def traverse(folder):
    global nChanged
    if nChanged >= maxChanged: 
        return
    for entry in os.listdir(folder):
        if entry[0] == '.':
            continue
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            subfolder = path
            traverse(subfolder)
        if 'psa' in folder:
            renameTQFile(folder, entry)
        if nChanged >= maxChanged:
            break
    if 'psa' in folder and nChanged < maxChanged:
        renameTQFolder(folder)

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if resource_type != 'tq':
        sys.stdout.write("Sorry, only tq resources are supported at this time.\n")
        exit()
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        traverse(source_dir)
        sys.stdout.write("Done. Renamed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python rename_psa_files.py <folder>\n")
