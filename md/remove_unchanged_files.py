# -*- coding: utf-8 -*-
# This program considers a pair of folders. It removes files from the first folder that are
# identical to the corresponding files in the second folder.
# If the files are identical, one is removed.

updated_dir = r'C:\DCS\Telugu\TW'    # new source folder, from which files will be removed
older_dir = r'C:\DCS\Telugu\TW.Feb-23'  # make both of these paths as low level as possible to avoid removing too many files
nRemoved = 0
nLeft = 0

import os
from filecmp import cmp
import sys

# Compares the files and deletes the new file if they are identical
def processFile(newfile, oldfile):
    global nRemoved
    global nLeft
    if cmp(newfile, oldfile, shallow=False):
        os.remove(newfile)
        print("Removed " + newfile)
        nRemoved += 1
    else:
        nLeft += 1

# Recursive routine to remove files from updated folder that are identical in older folder
def processDir(updated, older):
    global nRemoved
    global nLeft
    for entry in os.listdir(updated):
        if entry[0] == '.':
            continue
        newpath = os.path.join(updated, entry)
        oldpath = os.path.join(older, entry)
        if os.path.isdir(newpath) and os.path.isdir(oldpath):
            processDir(newpath, oldpath)
        elif os.path.isfile(oldpath):
            processFile(newpath, oldpath)
        else:
            nLeft += 1
    if os.listdir(updated) == []:
        os.rmdir(updated)          # remove entire folder if empty
        print("Removed folder: " + updated)
        nRemoved += 1
    else:
        nLeft += 1

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if updated_dir != older_dir and os.path.isdir(updated_dir) and os.path.isdir(older_dir):
        processDir(updated_dir, older_dir)
        print("\nDone. Removed " + str(nRemoved) + " unchanged files and folders. " + str(nLeft) + " were changed and remain.")
        print("To facilitate future updates, be sure to keep a full clone of the most recent repo.")
    else:
        sys.stderr.write("Usage: python remove_unchanged_files.py <updated_folder>\n  Use . for current folder. Set globals before running this script.\n")
