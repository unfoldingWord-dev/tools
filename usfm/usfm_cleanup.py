# -*- coding: utf-8 -*-
# This program cleans up common issuss in USFM files.
# Backs up the .usfm files being modified.
# Outputs .usfm files of the same name in the same location.
#
# Moves standalone \p \m and \q markers which occur just before an \s# marker
#    to the next line after the \s# marker.

# Set these globals
source_dir = r"C:\DCS\Kubu\work\41-MAT.usfm"
promote_all_quotes = True
promote_double_quotes = True

nChanged = 0
max_changes = 66
# Customize the behavior of this program by setting these globals:
enable_move_pq = True
enable_fix_punctuation = True   # substitutions.py, double periodd, and spacing at beginning of verse
enable_add_spaces = True    # Add spaces between commo/period/colon and a letter
promote_quotes = False       # Promote straight quote to curly quotes. Not recommended until confident of quote placements.
aligned_usfm = False
remove_s5 = True

import re       # regular expression module
import io
import os
import shutil
import sys
import substitutions
import quotes
import doublequotes


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

#losepq_re = re.compile(r'\n(\\[pqm][i1-9]?)\n+(\\[pqm][i1-9 ]?.*?)\n', flags=re.UNICODE+re.DOTALL)
losepq_re = re.compile(r'\n\\[pqm][i1-9]? *\n+(\\[^v].*?\n)', flags=re.UNICODE)

# Remove standalone paragraph markers not followed by verse marker.
def usfm_remove_pq(str):
    newstr = ""
    found = losepq_re.search(str)
    while found:
        newstr += str[:found.start()] + "\n" + found.group(1)
        str = str[found.end():]
        found = losepq_re.search(str)
    newstr += str
    return newstr

s5_re = re.compile(r'\n\\s5 *?\n', flags=re.UNICODE+re.DOTALL)

# Removes \s5 markers
def usfm_remove_s5(str):
    newstr = ""
    found = s5_re.search(str)
    while found:
        newstr += str[:found.start()] + "\n"
        str = str[found.end():]
        found = s5_re.search(str)
    newstr += str
    return newstr


spacey3_re = re.compile(r'\\v [0-9]+ ([\(\'"«“‘])[\s]', re.UNICODE)    # verse starts with free floating quote mark

# Replaces substrings from substitutions module
# Reduces double periods to single periods
# Removes space after quote or left paren at beginning of verse.
def fix_punctuation(str):
    for pair in substitutions.subs:
        str = str.replace(pair[0], pair[1])
    pos = str.find("..", 0)
    while pos >= 0:
        if pos != str.find("...", pos):
            str = str[:pos] + str[pos+1:]
        pos = str.find("..", pos+2)
    pos = 0
    bad = spacey3_re.search(str)
    while bad:
        pos += bad.end()
        str = str[:pos-1] + str[pos:]
        bad = spacey3_re.search(str[pos:])
    return str

# spacing_list is a list of compiled expressions where a space needs to be inserted
spacing_list = [ re.compile(r'[\.,;:][A-Za-z]') ]

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


# Rewrites file and returns True if any changes are made.
def convert_wholefile(path):
    global aligned_usfm

    input = io.open(path, "tr", encoding="utf-8-sig")
    alltext = input.read()
    origtext = alltext
    input.close()
    aligned_usfm = ("lemma=" in alltext)
    changed = False

    if remove_s5:
        alltext = usfm_remove_s5(alltext)
    if enable_move_pq:
        alltext = usfm_move_pq(alltext)
        alltext = usfm_remove_pq(alltext)
    if enable_fix_punctuation and not aligned_usfm:  # and fileQualifies(path):
        alltext = fix_punctuation(alltext)
    if enable_add_spaces and not aligned_usfm:
        alltext = add_spaces(alltext)
    if promote_all_quotes and not aligned_usfm:
        alltext = quotes.promoteQuotes(alltext)
    elif promote_double_quotes and not aligned_usfm:
        alltext = doublequotes.promoteQuotes(alltext)
    if alltext != origtext:
        output = io.open(path, "tw", buffering=1, encoding='utf-8', newline='\n')
        output.write(alltext)
        output.close()
        changed = True
    return changed

# Returns the complementary quote character
def matechar(quote):
    leftquote  = "\"'«“‘"
    rightquote = "\"'»”’"
    pos = leftquote.find(quote)
    if pos >= 0:
        mate = rightquote[pos]
    else:
        pos = rightquote.find(quote)
        mate = leftquote[pos]   # works even if pos is -1
    return mate

# Returns position of the matching quote mark, or -1 if not found
def find_mate(quote, pos, line):
    mate = matechar(quote)
    nFollowing = line[pos+1:].count(mate)
    nPreceding = line[:pos-1].count(mate)
    if nFollowing % 2 == 1 and nPreceding % 2 == 0:
        matepos = line.find(mate, pos+1)
    elif nFollowing % 2 == 0 and nPreceding % 2 == 1:
        matepos = line.rfind(mate, 0, pos-1)
    else:
        matepos = -1
    return matepos

quotemedial_re = re.compile(r'[\w][\.\?!;\:,](["\'«“‘’”»])[\w]', re.UNICODE)    # adjacent punctuation where second char is a quote mark

def change_quote_medial(line):
    pos = 0
    changed = False
    while bad := quotemedial_re.search(line):
        pos = bad.start() + 2
        matepos = find_mate(bad.group(1), pos, line)
        if matepos > pos:
            line = line[:pos] + ' ' + line[pos:]
            changed = True
        elif 0 <= matepos < pos:
            line = line[:pos+1] + ' ' + line[pos+1:]
            changed = True
        bad = quotemedial_re.search(line)
        if bad and bad.start() <= pos:
            break
    return (changed, line)

quotefloat_re = re.compile(r' (["\'«“‘’”»])[\s]', re.UNICODE)

def change_floating_quotes(line):
    pos = 0
    changed = False
    while bad := quotefloat_re.search(line):
        pos = bad.start() + 1
        matepos = find_mate(bad.group(1), pos, line)
        if matepos > pos:
            line = line[:pos+1] + line[pos+2:]
            changed = True
        elif 0 <= matepos < pos:
            line = line[:pos-1] + line[pos:]
            changed = True
        bad = quotefloat_re.search(line)
        if bad and bad.start() <= pos:
            break
    return (changed, line)

# Rewrites the file, making changes to individual lines
# Returns True if any changes are made
def convert_by_line(path):
    with io.open(path, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    output = io.open(path, "tw", encoding='utf-8', newline='\n')
    changedfile = False

    for line in lines:
        (changed1, line) = change_quote_medial(line)
        (changed2, line) = change_floating_quotes(line)
        if changed1 or changed2:
            changedfile = True
        output.write(line)
    output.close()
    return changedfile

# Corrects issues in the USFM file
def convertFile(path):
    global nChanged
    prev_nChanged = nChanged
    tmppath = path + ".tmp"
    os.rename(path, tmppath)    # to preserve time stamp
    shutil.copyfile(tmppath, path)

    if convert_wholefile(path):
        nChanged += 1
    if convert_by_line(path):
        nChanged += 1

    if nChanged > prev_nChanged:
        nChanged = prev_nChanged + 1
        sys.stdout.write("Changed " + shortname(path) + "\n")
        bakpath = path + ".orig"
        if not os.path.isfile(bakpath):
            os.rename(tmppath, bakpath)
        else:
            os.remove(tmppath)
    else:       # no changes to file
        os.remove(path)
        os.rename(tmppath, path)

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
            elif entry.lower().endswith("sfm"):
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
        sys.stderr.write("\nUsage: python usfm_cleanup.py <folder>\n  Use . for current folder.\n")

    if aligned_usfm:
        sys.stderr.write("Cannot cleanup aligned USFM.\n")
