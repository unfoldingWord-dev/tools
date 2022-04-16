# -*- coding: utf-8 -*-
# This script converts OBS translation notes from TSV to the supported markdown format.
# It only processes a single folder or a single file, no recursion.
# The TSV files should be clean and completely correct format. (Use verify_obstnTSV.py)
#
# Column descriptions:
#   1. "Reference" -- story:paragraph  e.g. 1:2 is the second paragraph in story 1.
#   2. "ID" -- unique 4-character ID
#   3. "Tags" (ignored) -- is "title" for paragraph 0 and blank for other paragraphs
#   4. "SupportReference" -- should match an RC link the note (last column) but without the square brackets
#   5. "Quote" -- note title, becomes an H1 heading in a markdown file
#   6. "Occurrence" (ignored) -- always 1
#   7. "Note" -- note text

import re       # regular expression module
import io
import os
import sys
import operator
import tsv
from shutil import copy

# Globals
source_dir = r'C:\DCS\Spanish-es-419\OBSTN'  # Where are the TSV files located
target_dir = r'C:\DCS\Spanish-es-419\work'

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def copyFile(fname):
    path = os.path.join(source_dir, fname)
    targetpath = os.path.join(target_dir, fname)
    bakpath = targetpath + ".orig"
    if os.path.isfile(path):
        if os.path.exists(targetpath) and not os.path.exists(bakpath):
            os.rename(targetpath, bakpath)
        copy(path, target_dir)       # copy() is from shutil

# Returns the path of the markdown file to contain the notes for the specified paragraph
# Creates the parent directory of the markdown file, if necessary.
def makeMdPath(story, paragraph):
    story = str(story)
    paragraph = str(paragraph)
    if len(story) == 1:
        story = "0" + story
    if len(paragraph) == 1:
        paragraph = "0" + paragraph
    content_dir = os.path.join(target_dir, "content")
    if not os.path.isdir(content_dir):
        os.mkdir(content_dir)
    folder = os.path.join(content_dir, story)
    if not os.path.isdir(folder):
        os.mkdir(folder)
    return os.path.join(folder, paragraph + ".md")

# Writes the specified notes to content/<story>/<paragraph>.md
def writeMdfile(story, paragraph, notes):
    path = makeMdPath(story, paragraph)
    if os.path.isfile(path):
        sys.stdout.write(f"Overwriting {shortname(path)}\n")
    start = "# "
    file = io.open(path, "tw", encoding="utf-8", newline="\n")
    for note in notes:
        file.write(start + note[0] + "\n\n" + note[1] + "\n")
        start = "\n# "
    file.close()

hash_re = re.compile(r'#([^# \n].*)')    # missing space after #
blanklines_re = re.compile(r'[^\>]\<br\>#')     # less than two lines breaks before heading

# Removes leading and trailing spaces and quotes
def convertNote(text):
    return text.strip('" ')     # remove leading and trailing spaces and quotes

refcheck_re = re.compile(r'([0-9]+):([0-9]+) *$')

# Writes all the notes in the specified file to .md files.
# Success depends on correctness of the TSV file. Verify beforehand.
def convertFile(path):
    print("Converting ", shortname(path))
    sys.stdout.flush()
    data = tsv.tsvRead(path)  # The entire file is returned as a list of lists of strings (rows); each row is a list of strings.
    story = 0
    prevstory = 1
    prevparagraph = 0
    notes = []
    for row in data:
        if ref := refcheck_re.match(row[0].strip()):
            story = int(ref.group(1))
            paragraph = int(ref.group(2))
        elif story > 0:
            sys.stderr.write("Invalid row, reference: " + row[0] + "\n")
            story = 0
        if story > 0:
            if story != prevstory or paragraph != prevparagraph:
                writeMdfile(prevstory, prevparagraph, notes)
                prevstory = story
                prevparagraph = paragraph
                notes = []
            notes.append( (row[4],row[6]) )
    writeMdfile(story, paragraph, notes)

# Converts all TSV files in the specified folder. Not recursive.
def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if entry.endswith(".tsv"):
            convertFile(path)
    copyFile("LICENSE.md")
    copyFile("README.md")
    copyFile("manifest.yaml")

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done.\n")
    elif os.path.isfile(source_dir) and source_dir.endswith(".tsv"):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Processed 1 file.\n")
    else:
        sys.stderr.write("Usage: python tsv2md.py <folder>\n  Use . for current folder.\n")
