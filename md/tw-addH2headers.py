# -*- coding: utf-8 -*-
# This program adds 2nd level header (H2) immediately after top level (H1) header if missing in markdown files.
# A level 2 header containing the word for "Definition" is required in every tW markdown file.
# Assumes input .md files are already in UTF-8 format.
# Checks that .md file begins with a properly formatted H1 heading.
# Requires that any existing H2 header immediately after H1 is properly formatted as well.
# Except for the title at the top of the file, this script demotes H1 headings to H2.
# Backs up the .md file being modified, using a .orig extension.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
import sys

# Globals
source_dir = r'C:\DCS\Telugu\te_tw.STR'  # please end with "bible"
h2_terms = "## నిర్వచనం:\n\n"       #  ## Definition  (in the target language, including 2 newlines)
h2_names = "## వాస్తవాలు:\n\n"     #  ## Facts  (in the target language, including 2 newlines)

max_changes = 1111
nChanged = 0
nRead = 0

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Removes blank lines at top of file (mainly to simplify the algorithm).
# Demotes any level 1 headings to level 2, except for the title.
# Backs up original file if there are any changes.
# Returns True if the file is changed.
def demoteHeadings(mdpath):
    with io.open(mdpath, "tr", 1, encoding="utf-8-sig") as input:
        origtext = input.read()
    newtext = re.sub("\n#[ \t]", "\n## ", origtext.lstrip())
    changed = (newtext != origtext)
    if changed:
        bakpath = mdpath + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(mdpath, bakpath)
        output = io.open(mdpath, "tw", encoding='utf-8', newline='\n')
        output.write(newtext)
        output.close()
    return changed

h1top_re = re.compile(r'[ \t\n]*#[ \t].*?\n[ \t\n]*', re.UNICODE+re.DOTALL)
h2_re = re.compile(r'##[ \t].+?\n', re.UNICODE+re.DOTALL)

# Converts the text a whole file at a time.
def convertWholeFile(mdpath, folder):
    with io.open(mdpath, "tr", 1, encoding="utf-8") as input:
        alltext = input.read()
    changed = False
    foundH1 = h1top_re.match(alltext)
    if foundH1:
        h1 = alltext[0:foundH1.end()]
        alltext = alltext[foundH1.end():]   # alltext should now start with line 3

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
            if alltext.startswith( h2[3:] ):      # text has correct term but without hash marks
                alltext = "## " + alltext
            else:
                output.write(h2)
            output.write(alltext)
            output.close()
            changed = True
            sys.stdout.write("Converted " + shortname(mdpath) + "\n")
    else:
        sys.stderr.write("File does not begin with H1 header: " + shortname(mdpath) + "\n")
    return changed

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
            changed = demoteHeadings(path)
            changed2 = convertWholeFile(path, dir)
            if changed or changed2:
                nChanged += 1
        if nChanged >= max_changes:
            break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " of " + str(nRead) + " files checked.\n")
    else:
        sys.stderr.write("Usage: python tw-addH2headers.py <folder>\n  Use . for current folder.\n")
