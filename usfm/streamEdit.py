# -*- coding: utf-8 -*-
# This program may be modified to do any kind of stream operation on a folder full of files.
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
source_dir = r'C:\DCS\Danish\work'
nChanged = 0
max_changes = 66
filename_re = re.compile(r'.*\.usfm$')
yes_backup = True


# Strings to replace with
# whole file matches use newstring[0]
newstring = []
newstring.append('# ')

# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
inlinekey.append( re.compile(r'\{ \[([^\]]+)\] \}', flags=re.UNICODE) )

# Copies lines from input to output.
# Modifies targeted input lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines()
    input.close()
    if yes_backup:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
    count = 0
    output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
    for line in lines:
        #count += 1
        #if count in {3,7} and line.startswith("# ") and not line.endswith("?\n"):
            #line = line[2:]
        for i in range(len(inlinekey)):
            sub = inlinekey[i].search(line)
            while sub:
                line = line[0:sub.start()] + "\\f + \\ft " + sub.group(1) + " \\f*" + line[sub.end():]
                #line = sub.group(1) + u"" + sub.group(2)
                sub = inlinekey[i].search(line)
        output.write(line)
    output.close()


# keystring is used only in line-by-line. But it is searched against the entire file one time.
keystring = []
keystring.append( re.compile(r'\{ \[[^\]]+\] \}', flags=re.UNICODE) )

def convertFileByLines(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    str = input.read()
    input.close()
    convertme = False
    for exp in keystring:
        if exp.search(str):
            convertme = True
    if convertme:
        convertByLine(path)
        nChanged += 1
        sys.stdout.write("Converted " + shortname(path) + "\n")

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# wholestring = re.compile(r' \\wj \\wj\*[ \n]', flags=re.UNICODE)
#wholestring = re.compile(r'[^v] ([1-9][0-9]?)[^0-9 ,\.\n\-]', flags=re.UNICODE)
wholestring = re.compile(r'[^v] ([1-9][0-9]?)[ \.]', flags=re.UNICODE)

# Converts the text a whole file at a time.
# Uses wholestring, newstring[0]
def convertWholeFile(path):
    global nChanged

#    found = classic_pattern(mdpath)
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    found = wholestring.search(alltext)
    if found:
#        input = io.open(mdpath, "tr", 1, encoding="utf-8-sig")
#        alltext = input.read()
#        input.close()
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')

        # Use a loop for multiple replacements per file
        while found:
            output.write(alltext[0:found.start()+2] + "\n\\v " + found.group(1))
            alltext = alltext[found.end()-1:]
            found = wholestring.search(alltext)
        output.write(alltext)
        output.close()
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1

#sub_re = re.compile('figs-questions?', re.UNICODE)
#replacement = 'figs-rquestion'

#sub_re = re.compile(r'<o:p> *</o:p>', re.UNICODE)
sub_re = re.compile(r'\\em \\em\*', re.UNICODE)
replacement = ""
#sub_re = re.compile(r'</?o:p>', re.UNICODE)
#sub_re = re.compile(r'<!--.*-->', re.UNICODE)
#sub_re = re.compile(r'& *nbsp;', re.UNICODE)
#sub_re = re.compile(r'rc://en/', re.UNICODE)
#sub_re = re.compile(r'[Ll]ih?at[\s]*\:+[\s]*\n+[\s]*\[\[', re.UNICODE)
#sub_re = re.compile(r'# +[\*]+(.*)[\*]+', re.UNICODE)

# Stream edit the file by a simple, regular expression substitution
# To do only one substitution per file, change the count argument to re.sub(), below.
def convertFileBySub(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    found = sub_re.search(alltext)
    if found:
        if yes_backup:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)

        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.write( re.sub(sub_re, replacement, alltext, count=0) )
        output.close()
        sys.stdout.write("Converted " + shortname(path) + "\n")
        nChanged += 1

def convertFile(path):
    convertFileByLines(path)
#    convertWholeFile(path)
    #convertFileBySub(path)


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
                convertFile(path)
            if nChanged >= max_changes:
                break

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    elif os.path.isfile(source_dir):
        path = source_dir
        source_dir = os.path.dirname(path)
        convertFile(path)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python streamEdit.py <folder>\n  Use . for current folder.\n")
