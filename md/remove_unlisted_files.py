# -*- coding: utf-8 -*-
# This program removes files that are not listed in keep.py.
# The occasion for it is that STR sometimes requests publishing of a specific list of files
# while the repo contains those files and many more.

source_dir = r'C:\DCS\Spanish-es-419\TW'  # make path as low level as possible to avoid removing too many files
nRemoved = 0
nLeft = 0

import os
import sys
import keep

keepers = []
for keeper in keep.keep:
    keepers.append(keeper.replace("\\", "/"))

# Recursive routine to remove unlisted files
def processDir(folder):
    global nRemoved
    global nLeft
    global keepers

    for entry in os.listdir(folder):
        if entry[0] == '.':
            continue
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            processDir(path)
        else:
            removeit = True
            for keeper in keepers:
                if path.replace("\\", "/").endswith(keeper):
                    removeit = False
                    keepers.remove(keeper)
                    break
            if removeit:
                os.remove(path)
                nRemoved += 1
            else:
                nLeft += 1

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        print(f"{len(keepers)} files to be kept.")
        processDir(source_dir)
        print("\nDone. Removed " + str(nRemoved) + " unlisted files. " + str(nLeft) + " remain.")
        print("To facilitate future updates, be sure to keep a clone of the full repo before removals.")
    else:
        sys.stderr.write("Usage: python remove_unlisted_files.py <updated_folder>\n  Use . for current folder. Set globals before running this script.\n")
