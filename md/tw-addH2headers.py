# -*- coding: utf-8 -*-
# This program adds 2nd level header (H2) immediately after top level (H1) header if missing in markdown files.
# A level 2 header containing the word for "Definition" is required in every tW markdown file.
# Assumes input .md files are already in UTF-8 format.
# Checks that .md file begins with a properly formatted H1 heading.
# Requires that any existing H2 header immediately after H1 is properly formatted as well.
# Backs up the .md file being modified, using a .orig extension.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
import sys
# from difflib import SequenceMatcher   

# Globals
source_dir = r'C:\DCS\Kannada\kn_tw\bible'  # please end with "bible"
h2_terms = "## ಪದದ ಅರ್ಥ ವಿವರಣೆ\n\n"    #  ## Definition  (in the target language, including 2 newlines)
h2_names = "## ಸತ್ಯಾಂಶಗಳು\n\n"     #  ## Facts  (in the target language, including 2 newlines)

max_changes = 5
nChanged = 0
nRead = 0

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

h1_re = re.compile(r'[ \t\n]*#[ \t].*?\n[ \t\n]*', re.UNICODE+re.DOTALL)
# h2_re = re.compile(r'##[ \t][\w: ]+?\n', re.UNICODE+re.DOTALL)
h2_re = re.compile(r'##[ \t].+?\n', re.UNICODE+re.DOTALL)

# Converts the text a whole file at a time.
def convertWholeFile(mdpath, folder):
    global nChanged
    input = io.open(mdpath, "tr", 1, encoding="utf-8")
    alltext = input.read()
    input.close()
    foundH1 = h1_re.match(alltext)
    if foundH1:
        h1 = alltext[0:foundH1.end()]
        alltext = alltext[foundH1.end():]
        
        foundH2 = h2_re.match(alltext)
        if not foundH2:
            bakpath = mdpath + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(mdpath, bakpath)
            output = io.open(mdpath, "tw", buffering=1, encoding='utf-8', newline='\n')
            output.write( h1 )
            h2 = h2_terms
            if folder == 'names':
                h2 = h2_names
            output.write(h2)
            nChanged += 1  
            output.write(alltext)
            output.close()
            sys.stdout.write("Converted " + shortname(mdpath) + "\n")
    else:
        sys.stderr.write("File does not begin with H1 header: " + shortname(mdpath) + "\n")  

filename_re = re.compile(r'.*\.md$')

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nRead
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    sys.stdout.write("Convert folder: " + folder + '\n')
    sys.stdout.flush()
    dir = os.path.basename(folder)
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            convertFolder(path)
        elif filename_re.match(entry):
            nRead += 1
            convertWholeFile(path, dir)
        if nChanged >= max_changes:
            break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " of " + str(nRead) + " files checked.\n")
    else:
        sys.stderr.write("Usage: python tw-addH2headers.py <folder>\n  Use . for current folder.\n")
