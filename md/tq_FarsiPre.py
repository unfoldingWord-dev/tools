# -*- coding: utf-8 -*-
# This script modifies text files containing Farse tQ data in expected format:
#    Renames all occurrences of the book name in the file to the 3-letter abbreviation.
#    Translates all digits in lines that start with the book name, to ASCII digits.
# The input files must be named with 3-letter abbreviation, e.g. MAT.txt.
# The first line of each file must be the Farsi book name as it is used throughout the file.

# Global variables
source_dir = r"C:\DCS\Farsi\TQ\2PE.txt"
nChanged = 0

import re
import io
import os
import sys

range_re = re.compile(r' ?\- ?[0123456789]+')

# Called when the line represents a verse reference for the questions that follow.
# The verse reference is often mangled.
# This function standardizes the format to be (verse:chapter).
# It eliminates the verse range, if any.
def rectify(line, chapter):
    dashend = range_re.search(line)
    if dashend:
        fixed = line[:dashend.start()] + line[dashend.end():]
    else:
        fixed = line
    # pos = line.rfind(':'+chapter)
    # fixed = line[0:pos+1+len(chapter)]
    return fixed

ascii_digits = "0123456789"
farsi_digits = "۰۱۲۳۴۵۶۷۸۹"
fa2ascii = str.maketrans(farsi_digits, ascii_digits)
chapter_re = re.compile(r'[123A-Z]+ +([0123456789]+)')

def convertFile(path):
    basename = os.path.basename(path) + ".orig"
    abbreviation = basename[0:3]
    bakpath = path + ".orig"
    if not os.path.exists(bakpath):
        os.rename(path, bakpath)
    with io.open(bakpath, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    bookname = lines[0].strip()
    with io.open(path, "tw", encoding='utf-8', newline='\n') as output:
        chapter = "1"
        for line in lines:
            line = line.strip()
            if line.startswith(bookname):
                line = line.replace(bookname, abbreviation)
                line = line.translate(fa2ascii)
                if not ':' in line:
                    chaps = chapter_re.match(line)
                    if chaps:
                        chapter = chaps.group(1)
                else:
                    line = rectify(line, chapter)
            output.write(line + '\n')
    global nChanged
    nChanged += 1

# Converts the .txt files contained in the specified folder
def convertDir(dir):
    for entry in os.listdir(dir):
        path = os.path.join(dir, entry)
        if os.path.isdir(path):
            convertDir(path)
        elif os.path.isfile(path) and path.endswith(".txt"):
            convertFile(path)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convertDir(source_dir)
        sys.stdout.write(f"Done. Converted {nChanged} files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        current_dir = source_dir
        convertFile(path)
        sys.stdout.write("Done. Converted 1 file.\n")
    else:
        sys.stderr.write("Usage: python tq_FarsiPre <folder or file>\n  Use . for current folder.\n")
