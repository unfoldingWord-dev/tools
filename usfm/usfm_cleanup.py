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
#import parseUsfm
import sys

# Globals
source_dir = r"C:\DCS\Lusonga\luo-x-lusonga_reg"

nChanged = 0
max_changes = 66
# Customize the behavior of this program by setting these globals:
enable_move_pq = True
enable_fix_punctuation = True
enable_add_spaces = True    # Add spaces between commo/period and a letter
aligned_usfm = False

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

#  Move paragraph marker before section marker to follow the section marker
movepq_re = re.compile(r'\n(\\[pqm][i1-9]*?)\n+(\\s[1-9].*?)\n', flags=re.UNICODE+re.DOTALL)

# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.
def usfm_move_pq(str):
    newstr = ""
    found = movepq_re.search(str)
    while found:
        newstr += str[0:found.start()] + '\n' + found.group(2) + '\n' + found.group(1) + '\n'
        str = str[found.end():]
        found = movepq_re.search(str)
    newstr += str
    return newstr

# Remove paragraph marker followed by another paragraph marker
losepq_re = re.compile(r'\n(\\[pqm][i1-9]?)\n+(\\[pqm][i1-9 ]?.*?)\n', flags=re.UNICODE+re.DOTALL)

def usfm_remove_pq(str):
    newstr = ""
    found = losepq_re.search(str)
    while found:
        newstr += str[:found.start()] + "\n" + found.group(2) + "\n"
        str = str[found.end():]
        found = losepq_re.search(str)
    newstr += str
    return newstr

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

# Stream edit the file by a simple string substitution
def fix_punctuation(str):
    for pair in substitutions.subs:
        str = str.replace(pair[0], pair[1])
    return str

# spacing_list is a list of compiled expressions where a space needs to be inserted
#spacing_list = [ re.compile(r'[\.,;][A-Za-z]', re.UNICODE), re.compile(r'\*[^ \n]', re.UNICODE)]
spacing_list = [ re.compile(r'[\.,;][A-Za-z]', re.UNICODE) ]

# Adds spaces where needed. spacing_list contrals what happens.
# spacing_list may need to be customized for every language.
def add_spaces(str):
    for sub_re in spacing_list:
        found = sub_re.search(str)
        while found:
            pos = found.start() + 1
            str = str[:pos] + ' ' + str[pos:]
            found = sub_re.search(str)
    return str

# Corrects issues treating the whole USFM file as a string.
def convertFile(path):
    global aligned_usfm
    global nChanged
    prev_nChanged = nChanged

    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    origtext = alltext
    input.close()
    aligned_usfm = ("lemma=" in alltext)

    if enable_move_pq:
        alltext = usfm_move_pq(alltext)
        alltext = usfm_remove_pq(alltext)
    if enable_fix_punctuation and not aligned_usfm and fileQualifies(path):
        alltext = fix_punctuation(alltext)
    if enable_add_spaces and not aligned_usfm:
        alltext = add_spaces(alltext)
    if alltext != origtext:
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(path, bakpath)
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.write(alltext)
        output.close()
        nChanged += 1

    if nChanged > prev_nChanged:
        nChanged = prev_nChanged + 1
        sys.stdout.write("Changed " + shortname(path) + "\n")

# Recursive routine to convert all files under the specified folder
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes or aligned_usfm:
        return
    sys.stdout.write(shortname(folder) + '\n')
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)
            elif entry.endswith(".usfm"):
                convertFile(path)
                #convertFileByToken(path)
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

    if aligned_usfm:
        sys.stderr.write("Cannot cleanup aligned USFM.\n")
