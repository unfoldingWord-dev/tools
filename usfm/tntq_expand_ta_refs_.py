# -*- coding: utf-8 -*-
# This program was originally written for use against .md files in hr_tn.
# It expands incomplete references to tA articles.
# For example, expands Vidi: figs_metaphor to Vidi: [[rc://hr/ta/man/translate/figs-metaphor]]
# Backs up the .md file being modified.
# Outputs .md files of the same name in the same location.

import re       # regular expression module
import io
import os
import codecs
import string
import sys

# Globals
nChanged = 0
max_changes = 11111
language_code = u'as'
filename_re = re.compile(r'.*\.md$')

# keystring is used in line-by-line, but is searched against the whole file once only
keystring = []
keystring.append( re.compile(r'figs_', flags=re.UNICODE) )
keystring.append( re.compile(r'translate_', flags=re.UNICODE) )
keystring.append( re.compile(r'writing_', flags=re.UNICODE) )
keystring.append( re.compile(r'guidelines_', flags=re.UNICODE) )


# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
# inlinekey.append( re.compile(r'(.*)https://git.door43.org/Door43/en-ta-translate-vol[12]/src/master/content/([\w_]+)\.md(.*)', flags=re.UNICODE) )
inlinekey.append( re.compile(r'figs_(\w*)', flags=re.UNICODE) )
inlinekey.append( re.compile(r'translate_(\w*)', flags=re.UNICODE) )
inlinekey.append( re.compile(r'writing_(\w*)', flags=re.UNICODE) )
inlinekey.append( re.compile(r'guidelines_(\w*)', flags=re.UNICODE) )

# Strings to replace with
newstring = []
newstring.append( u'figs-' )
newstring.append( u'translate-' )
newstring.append( u'writing-' )
newstring.append( u'guidelines-' )


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
    count = 0
    output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    for line in lines:
        count += 1
        for i in range(len(inlinekey)):
            good_ref = u' [[rc://' + language_code + u'/ta/man/translate/' + newstring[i]
            sub = inlinekey[i].search(line)
            while sub:
                line = line[0:sub.start()] + good_ref + sub.group(1) + u']]' + line[sub.end():]
                sub = inlinekey[i].search(line)
        output.write(line)
    output.close
    
# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
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
    sys.stdout.write(shortname(folder) + '\n')
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
        folder = r'E:\DCS\Assamese\as_obs-tn\content'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertFolder(folder)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
