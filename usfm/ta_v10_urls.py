# -*- coding: utf-8 -*-
# This program is intended to replacr v.9 URLs in tA with v.10 URLs.
# Its work is limited to a predefined dictionary of URLs.
# Backs up the .md file being modified.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys

# Globals
nChanged = 0
max_changes = 25
filename_re = re.compile(r'01\.md$')

# Keystring is used only to find the lines that may need replacements done.
keystring = []
keystring.append(re.compile(r'https://unfoldingword.org', flags=re.UNICODE) )
keystring.append(re.compile(r'\(bita-', flags=re.UNICODE) )
keystring.append(re.compile(r'\(figs-', flags=re.UNICODE) )

# Each element of v9string is matched against every line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
v9string = []
v9string.append(u'https://unfoldingword.org/en/?resource=translation-words')
v9string.append(u'https://unfoldingword.org/network')
v9string.append(u'(bita-part1)')
v9string.append(u'(bita-part2)')
v9string.append(u'(bita-part3)')
v9string.append(u'(bita-hq)')
v9string.append(u'(bita-humanbehavior)')
v9string.append(u'(bita-plants)')
v9string.append(u"(bita-phenom)")
v9string.append(u"(bita-manmade)")
v9string.append(u"(figs-metonymy)")
v9string.append(u"(figs-personification)")
v9string.append(u"(figs-partsofspeech)")
v9string.append(u"(figs-verbs)")
v9string.append(u"(figs-distinguish)")
v9string.append(u"(figs-verbs)")

# Strings to replace with
v10string = []
v10string.append( u'https://unfoldingword.org/tw/' )
v10string.append( u'https://unfoldingword.org' )
v10string.append( u'(../bita-part1/01.md)' )
v10string.append( u'(../bita-part2/01.md)' )
v10string.append( u'(../bita-part3/01.md)' )
v10string.append( u"(../bita-hq/01.md)" )
v10string.append( u"(../bita-humanbehavior/01.md)" )
v10string.append( u"(../bita-plants/01.md)" )
v10string.append( u"(../bita-phenom/01.md)" )
v10string.append( u"(../bita-manmade/01.md)" )
v10string.append( u"(../figs-metonymy/01.md)" )
v10string.append( u"(../figs-personification/01.md)" )
v10string.append( u"(../figs-partsofspeech/01.md)" )
v10string.append( u"(../figs-verbs/01.md)" )
v10string.append( u"(../figs-distinguish/01.md)" )
v10string.append( u"(../figs-verbs/01.md)" )


# Copies lines from input to output.
# Modifies targeted input lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    input = io.open(path, "tr", 1, encoding="utf-8")
    lines = input.readlines()
    input.close()
    bakpath = path + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(path, bakpath)
    output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    for line in lines:
        for i in range(len(v9string)):
            line = line.replace( v9string[i], v10string[i] )
        output.write(line)
    output.close
    
# Detects whether the specified file contains any of the strings we are looking for.
# If there is a match, calls convertByLine() to do the conversion.
def convertFileByLines(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8")
    alltext = input.read()
    input.close()
    convertme = False
    for key in keystring:
        if key.search(alltext):
            convertme = True
            break
    if convertme:
        convertByLine(path)
        nChanged += 1    
        sys.stdout.write("Converted " + shortname(path) + "\n")

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
    sys.stdout.write("Convert folder: " + shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif filename_re.match(entry):
                convertFileByLines(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        folder = r'C:\DCS\Kannada\kn_tA'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertFolder(folder)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
