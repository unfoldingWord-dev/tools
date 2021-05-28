# -*- coding: utf-8 -*-
# This program ensures that the last lines in a set of OBS markdown files are italicized.

import re       # regular expression module
import io
import os
import string
import sys
import shutil

# Globals
source_dir = r'C:\DCS\Russian\ru_obs.STR\content'

# Inserts underscores at beginning and end of line.
# If line already has asterisk in place of underscores, change them.
def fixline(line):
    line = line.strip()
    if line[0] == '*':
        line = '_' + line[1:]
    if line[-1] == '*':
        line = line[:-1] + '_'
    if line[0] != '_':
        line = '_' + line
    if line[-1] != '_':
        line = line + '_'   
    return line + '\n'

# Ensure the last line is properly italicized
def convertFile(path, folder):
    mdfile = io.open(path, "tr", encoding="utf-8-sig")
    lines = mdfile.readlines()
    mdfile.close()

    italicized = False
    count = len(lines)
    iLast = 0
    while -iLast < count:
        iLast -= 1
        line = lines[iLast].strip()
        if len(line) > 0:
            italicized = (line[0] == '_' and line[-1] == '_')
            break
    
    if -iLast <= count and not italicized:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
        output = io.open(path, "tw", encoding='utf-8', newline='\n')
        i = 0
        while i < count:
            if i - iLast != count:
                output.write(lines[i])
            else:
                output.write(fixline(lines[i]))
            i += 1
        output.close()

filename_re = re.compile(r'[\d][\d]\.md$')

# Creates content folder if needed.
# Calls convertStory to merge and convert one folder (one story) at a time.
def convertFolder(folder):
    for entry in os.listdir(folder):
        if entry[0] == '.':
            continue
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            convertFolder(path)
        elif filename_re.match(entry):
            convertFile(path, folder)
  
# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        print("Done.")
    elif os.path.isfile(source_dir) and filename_re.search(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        current_dir = source_dir
        convertFile(path, source_dir)
        print("Done.")
    else:
        sys.stderr.write("Usage: python obs_italicize_last_line.py <folder>\n  Use . for current folder or hard code the path.\n")
