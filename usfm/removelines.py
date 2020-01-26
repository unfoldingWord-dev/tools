# -*- coding: utf-8 -*-
# This program may be modified to remove selected lines from files.
# Just modify the keeper() function, and maybe the file_qualifies() function.
# Backs up the .md file being modified.
# Outputs .md files of the same name in the same location.
# Variations of this script were extensively used to clean up Indonesian and Papuan Malay tN .md files.

import re       # regular expression module
import io
import os
import sys

# Globals
nChanged = 0
max_changes = 1111
#filename_re = re.compile(r'intro\.md$')
filename_re = re.compile(r'[0-9]+\.md$')
#filename_re = re.compile(r'.+\.md$')
yes_backup = True
prevlost = False
#prevblank = True
nlines = 99     # number of lines in the file before filtering

#blankheading_re = re.compile(r'#+ *$')
#verseref_re = re.compile(r' [\d]{1,3}:[\d]{1,3}', flags=re.UNICODE)
lose_re = re.compile(r'#+ +Arti [Kk]ata-[Kk]ata')  # Arti Kata-kata

heading_re = re.compile(r'#+ ', flags=re.UNICODE)


# Returns True if the file qualifies for line removal
def file_qualifies(lines):
    return True
#    qualifies = False
#    if len(lines) >= 5:
#        if verseref_re.search(lines[0]):
#            if len(lines[1].strip()) == 0 and heading_re.match(lines[2]):
#                qualifies = True
#    return qualifies

# This function contains the main logic of the script.
# Returns True if the line is to be kept, False if not.
# Redefine this function to obtain desired behavior.
def keeper(line, count):
    global prevlost
#    global nlines
    keep = True
    if prevlost:
        keep = False
    elif lose_re.match(line):
        keep = False
        prevlost = True
    return keep

# Copies selected lines from input to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
# Returns
def filterLines(path):
    global prevlost
#    global prevblank
    global nlines
    prevlost = False
#    prevblank = True
    input = io.open(path, "tr", 1, encoding="utf-8")
    lines = input.readlines()
    input.close()
#    nlines = len(lines)
    outputlines = []
    changed = False
    if file_qualifies(lines):
        count = 0
        for line in lines:
            count += 1
            if keeper(line, count):
                outputlines.append(line)
            else:
                changed = True

    if changed:
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.writelines(outputlines)
        output.close
    return changed
#    sys.stdout.write("Converted " + shortname(path) + "\n")
    
prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write(shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':         # exclude .git and other hidden folders
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                if filterLines(path):
                    nChanged += 1
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        path = r'C:\DCS\PapuanMalay\pmy_tn.work'
    else:
        path = sys.argv[1]

    if path and os.path.isdir(path):
        convertFolder(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(path):
        convertFile(path)
        sys.stdout.write("Done. Changed 1 file.\n")
    else:
        sys.stderr.write("Usage: python removelines.py <folder>\n  Use . for current folder.\n")
