# -*- coding: utf-8 -*-
# This script copies a repository of tA files in .md format to a second location.
# It cleans up the files in these ways:
#    Ensures blank lines surrounding markdown headers.
#    Uses convert2md.md2md() to convert links and things.

# Global variables
source_dir = r'C:\DCS\Telugu\TA.changed\Stage 2'      # Source and target directories must be at the same level
target_dir = r'C:\DCS\Telugu\te_ta.STR'
language_code = 'te'
resource_type = 'ta'    # should be ta or tw

import re
import io
import os
import sys
import codecs
import convert2md
from shutil import copy


# Returns path of .md file in target directory.
def makeMdPath(category, fname):
    mdPath = os.path.join(target_dir, "bible")
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)

    mdPath = os.path.join(mdPath, category)
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)

    return os.path.join(mdPath, fname)

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Makes a directory under target_dir corresponding to the specified directory
# under source_dir. If the target directory already exists, no error.
# Returns the name of the desired target directory.
def makeTargetDir(fullpath):
    sourceDir = os.path.dirname(fullpath)
    relativePath = sourceDir[len(source_dir)+1:]    # folder containing .md file
    targetDir = os.path.join(target_dir, relativePath)
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)
    return targetDir
    
def copyFile(fname, fullpath):
    targetDir = makeTargetDir(fullpath)
    copy(fullpath, targetDir)       # copy() is from shutil

# Copy file with minimal change: ensure only one trailing newline
def stripcopy(fname, fullpath):
    input = io.open(fullpath, "tr", 1, encoding="utf-8-sig")
    text = input.read().rstrip()
    input.close()
    targetDir = makeTargetDir(fullpath)
    mdPath = os.path.join(targetDir, fname)
    output = io.open(mdPath, "tw", encoding="utf-8")
    output.write(text + '\n')
    output.close    

# Converts .md file in fullpath location to .md file in target dir.
def convertFile(fname, fullpath):
    targetDir = makeTargetDir(fullpath)
    mdPath = os.path.join(targetDir, fname)
    convert2md.md2md(fullpath, mdPath, language_code, shortname)

# Converts the .md files contained in the specified folder
def convertDir(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    ndirs = 0
    for item in os.listdir(dir):
        path = os.path.join(dir, item)
        if os.path.isdir(path) and item[0] != '.':
            ndirs += 1
            convertDir(path)
        elif item[-3:] == ".md":
            if resource_type == 'ta' and item.endswith("title.md"):
                stripcopy(item, path)
            elif resource_type != 'ta' or item == "01.md":
                convertFile(item, path)
            else:
                copyFile(item, path)
        elif item[-5:] == ".yaml":
            copyFile(item, path)
    if ndirs > 0:
        sys.stdout.write("Converted subfolders under " + dir + '\n')
        sys.stdout.flush()

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if resource_type == "ta":
        convert2md.g_multilist = True
#        sys.stdout.write("This is only changing files named 01.md\n")
        sys.stdout.write("Preserving all spaces except trailing spaces.\n")
        sys.stdout.write("Consolidates consecutive blank lines in all files.\n")
        sys.stdout.write("Removes blank line, if any, at tops of files.\n")
        sys.stdout.flush()

    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        convertDir(source_dir)
    else:       # the first command line argument presumed to be a folder
        convertDir(sys.argv[1])

    print("\nDone.")
