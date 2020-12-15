# -*- coding: utf-8 -*-
# This program cleans up common issuss in USFM files.
# Backs up the .usfm files being modified.
# Outputs .usfm files of the same name in the same location.
#
# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.

import re       # regular expression module
import io
import os
import substitutions
import codecs
import string
import sys

# Globals
source_dir = r'C:\DCS\Bangwinji\bsj_reg.TA'
nChanged = 0
max_changes = 66
# Customize the behavior of this program by setting these globals:
enable_move_pq = True
enable_fix_punctuation = True
enable_add_spaces = True    # Add spaces between commo/period and a letter

# keystring is used only in line-by-line. It is searched against the entire file one time.
keystring = []
keystring.append( re.compile(r'^[A-Z]', flags=re.UNICODE+re.MULTILINE) )

# Each element of inlinekey is matched against each line of a file.
# The matches occur in sequence, so the result of one match impacts the next.
inlinekey = []
inlinekey.append( re.compile(r'[A-ZƁƊƗɨǑ\',\.;\: \-]+$', re.UNICODE))
#inlinekey.append( re.compile(r'# +[_]+([^\_]*)[_]+ *$', flags=re.UNICODE))

# Strings to replace with
# whole file matches use newstring[0]
newstring = []
newstring.append('\s1 ')

# Copies lines from input to output.
# Modifies targeted input lines before writing them to output.
# Renames the input file to a backup name.
# Renames the output file to the original input file name.
def convertByLine(path):
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
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
            sub = inlinekey[i].match(line)
            if sub:
                line = newstring[i] + line
#            while sub:
#                line = line[0:sub.start()] + newstring[i] + sub.group(1) + u'\n'
#                line = sub.group(1) + u"" + sub.group(2)
#                line = line[0:sub.start()] + newstring[i] + sub.group(1) + u' ' + line[sub.end():]
#                sub = inlinekey[i].search(line)
        output.write(line)
    output.close
    
# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
def convertFileByLines(path):
    global nChanged
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    convertme = False
    for key in keystring:
        if key.search(alltext):
            convertme = True
            break
    # Convert the file if there are any lines to change
    if convertme:
        convertByLine(path)
        nChanged += 1    
        sys.stdout.write("Converted " + shortname(path) + "\n")

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

movepq_re = re.compile(r'\n(\\[pqm][i1-9]*?)\n+(\\s[1-9].*?)\n', flags=re.UNICODE+re.DOTALL)

# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.
def usfm_move_pq(path):
    global nChanged
    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    found = movepq_re.search(alltext)
    if found:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        while found:
#            output.write(alltext[0:found.start()] + newstring[0])
            output.write( alltext[0:found.start()] + '\n' + found.group(2) + '\n' + found.group(1) + '\n' )
            alltext = alltext[found.end():]
            found = movepq_re.search(alltext)
        output.write(alltext)
        output.close()
        nChanged += 1    

# Returns True if the specified file contains any of the strings to be translated.
def fileQualifies(path):
    qualify = False
    input = io.open(path, "tr", 1, encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    for pair in substitutions.subs:
        if pair[0] in alltext:
            qualify = True
            break
    return qualify

# Stream edit the file by a simple, regular expression substitution
def fix_punctuation(path):
    global nChanged
    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    bakpath = path + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(path, bakpath)

    for pair in substitutions.subs:
        alltext = alltext.replace(pair[0], pair[1])
    output = io.open(path, "tw", encoding='utf-8', newline='\n')
    output.write( alltext )
    output.close()
    nChanged += 1

spacing_list = [
    (re.compile(r'[\.,;][A-Za-z]', re.UNICODE))
]

# Adds spaces where needed. spacing_list contrals what happens.
# spacing_list may need to be customized for every language.
def add_spaces(path):
    global nChanged
    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    input.close()
    for sub_re in spacing_list:
        found = sub_re.search(alltext)
        if found:
            bakpath = path + ".orig"
            if not os.path.isfile(bakpath):
                os.rename(path, bakpath)
            while found:
                pos = found.start() + 1
                x = alltext[pos-3:pos+4]
                y = len(alltext)
                alltext = alltext[0:pos] + ' ' + alltext[pos:]
                z = alltext[pos-3:pos+5]
                found = sub_re.search(alltext)
            output = io.open(path, "tw", encoding='utf-8', newline='\n')
            output.write(alltext)
            output.close()
            nChanged += 1    

def convertFile(path):
    global nChanged
    prev_nChanged = nChanged
#    convertFileByLines(path)
    if enable_move_pq:
        usfm_move_pq(path)
    if enable_fix_punctuation and fileQualifies(path):
        fix_punctuation(path)
    if enable_add_spaces:
        add_spaces(path)

    if nChanged > prev_nChanged:
        nChanged = prev_nChanged + 1
        sys.stdout.write("Changed " + shortname(path) + "\n")

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
            elif entry.endswith(".usfm"):
                convertFile(path)
            if nChanged >= max_changes:
                break

# Processes all .usfm files in specified directory, one at a time
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
        sys.stderr.write("Source file(s) not found: " + source_dir)
        sys.stderr.write("Usage: python usfm_cleanup.py <folder>\n  Use . for current folder.\n")
