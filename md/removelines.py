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
source_dir = r'C:\DCS\Cebuano\ceb_tn'   # must be a folder
nChanged = 0
max_changes = 777
filename_re = re.compile(r'[\d]+\.md$')

yes_backup = True
prevlost = False

HEADING1 = 1
HEADINGX = 2
BLANKLINE = 3
TEXT = 4

lose_re = re.compile(r'\[\[rc://ceb/bible/questions/comprehension/', re.UNICODE)
lose2_re = re.compile(r'# \[\[rc://ceb/bible/questions/comprehension/', re.UNICODE)
heading_re = re.compile(r'#+ ', flags=re.UNICODE)


# Returns True if the file qualifies for line removal
def file_qualifies(lines):
    return True
#     qualifies = True
#    if len(lines) > 4 and len(lines) != 8:
#        if lose_re.match(lines[0]):
#            if len(lines[1].strip()) == 0 and heading_re.match(lines[2]):
#                qualifies = True
#    return qualifies

# This function contains the main logic of the script.
# Returns True if the line is to be kept, False if not.
# Redefine this function to obtain desired behavior.
def keeper(line, count, prevlinetype, linetype, nextlinetype):
    global prevlost

    keep = True
    if lose2_re.match(line):
        keep = False
        prevlost = True
    else:
        if prevlost and (len(line.strip()) == 0 or lose_re.match(line)):
            keep = False
        else:
            prevlost = False
    return keep

# Retursn the type of the specified line
def getLinetype(line):
    if line.startswith("# "):
        linetype = HEADING1
    elif line[0] == '#':
        linetype = HEADINGX
    elif len(line.strip()) == 0:
        linetype = BLANKLINE
    else:
        linetype = TEXT
    return linetype

# Copies selected lines from input to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
# Returns
def filterLines(path):
    global prevlost
#    global prevblank
    prevlost = False
#    prevblank = True
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines()
    input.close()
    outputlines = []
    changed = False
    linetypes = []
    if file_qualifies(lines):
        for line in lines:
            linetypes.append(getLinetype(line))
        prevlinetype = None
        n = 0
        for line in lines:
            if n > 0:
                prevlinetype = linetypes[n-1]
            if n+1 < len(linetypes):
                nextlinetype = linetypes[n+1]
            else:
                nextlinetype = None

            if keeper(line, n+1, prevlinetype, linetypes[n], nextlinetype):
                outputlines.append(line)
            else:
                changed = True
            n += 1

    if changed:
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.writelines(outputlines)
        output.close()
    return changed
#    sys.stdout.write("Converted " + shortname(path) + "\n")

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
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
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python removelines.py <folder>\n  Use . for current folder.\n")
