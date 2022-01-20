# -*- coding: utf-8 -*-

# Script for removing empty files

# Globals
source_dir = r'C:\DCS\Gujarati\gu_tq.STR'
min_size = 9
remove_folders = True   # to remove empty folders
nChecked = 0
nRemoved = 0
max_remove = 111

import sys
import os
import io
import re

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath and source_dir != longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def isEmpty(path):
    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    size = len(alltext.strip())
    nlines = alltext.count('\n')
    if size >= min_size and size < 40 and nlines < 2:
        print(shortname(path) + " size is " + str(size))
    return (size < min_size and nlines < 2)

def removeFile(path):
    os.remove(path)
    sys.stdout.write("Removed: " + shortname(path) + "\n")

def removeDir(dirpath):
    os.rmdir(dirpath)
    sys.stdout.write("Removed: " + shortname(dirpath) + "\n")

filename_re = re.compile(r'.*\.md$')    # candidate for removal if empty')

def processDir(dirpath):
    global nRemoved
    global max_remove
    global nChecked
    if nRemoved >= max_remove:
        return
    for entry in os.listdir(dirpath):
        path = os.path.join(dirpath, entry)
        if os.path.isdir(path) and entry[0] != '.':
            processDir(path)
        elif os.path.isfile(path) and filename_re.match(entry):
            nChecked += 1
            if isEmpty(path):
                removeFile(path)
                nRemoved += 1
        if nRemoved >= max_remove:
            break
    if nRemoved < max_remove and len(os.listdir(dirpath)) == 0:
        removeDir(dirpath)
        nRemoved += 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        processDir(source_dir)
    else:
        sys.stderr.write("Not a valid folder: " + source_dir + '\n') 

    print("Done. Checked " + str(nChecked) + " files and removed " + str(nRemoved) + ".\n")