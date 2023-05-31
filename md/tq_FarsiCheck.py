# -*- coding: utf-8 -*-
# This script checks files that have been modified by tq_FarsiPre.py.
#    Checks chapters and chunk references occur in expected order.

# Global variables
source_dir = r"C:\DCS\Farsi\TQ"
#nChanged = 0

import re
import io
import os
import sys

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def reportError(msg, path, lineno):
    # issues = openIssuesFile()
    if msg[-1] != '\n':
        msg += '\n'
    path = shortname(path)
    if lineno:
        sys.stderr.write(f"{path}: line {lineno}:  {msg}")

reference_re = re.compile(r'([123A-Z]+) +([0123456789\-\:\;]+)')
chunk_re = re.compile(r'([0123456789]+)\:([0123456789]+)')

def checkFile(path):
    abbreviation = os.path.basename(path)[0:3]
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    bookid = lines[0].strip()
    if bookid != abbreviation:
        reportError("First line does not match file name.", path, 1)

    prevverse = 0
    chapter = 0
    lineno = 1
    for line in lines:
        line = line.strip()
        reference = reference_re.match(line)
        if reference:
            if reference.group(1) != bookid:
                reportError(f"Book id is wrong", path, lineno)
            else:
                chunk = reference.group(2)
                if '-' in chunk:
                    reportError(f"Verse range detected", path, lineno)
                if not ':' in chunk:
                    if chunk != str(chapter+1):
                        reportError(f"Unexpected chapter number ({chunk})", path, lineno)
                    chapter = int(chunk)
                    prevverse = 0
                else:
                    vcref = chunk_re.match(chunk)
                    if vcref:
                        if int(vcref.group(2)) != chapter:
                            reportError(f"Unexpected verse:chapter ({chunk})", path, lineno)
                        verse = int(vcref.group(1))
                        if verse <= prevverse:
                            reportError(f"Verse number out of order ({vcref.group(1)})", path, lineno)
                        prevverse = verse
                    else:
                        reportError(f"Unrecognized chunk reference ({chunk})", path, lineno)
        lineno += 1

# Checks the .txt files contained in the specified folder
def checkDir(dir):
    for entry in os.listdir(dir):
        path = os.path.join(dir, entry)
        if os.path.isdir(path):
            checkDir(path)
        elif os.path.isfile(path) and path.endswith(".txt"):
            checkFile(path)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        checkDir(source_dir)
        sys.stdout.write("Done.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        current_dir = source_dir
        checkFile(path)
        sys.stdout.write("Done. Checked 1 file.\n")
    else:
        reportError("Usage: python tq_FarsiCheck <folder or file>\n  Use . for current folder.", source_dir, 0)
