# -*- coding: utf-8 -*-
# This program localizes the titles of tA articles.
# Used when the translators did not translate the titles found in toc.yaml files,
#   but did translate the titles of each article, found in title.md files.

import re       # regular expression module
import io
import os
import codecs
import string
import sys

# Globals
source_dir = r'C:\DCS\Assamese\TA\Stage 1'
nChanged = 0
max_changes = 4     # There should only be 4 altogether

title_re = re.compile(r'  +- title: "', flags=re.UNICODE)
link_re =  re.compile(r'    +link: ', flags=re.UNICODE)

def fetchTitle(folder, linkstr):
    title = ""
    titlepath = os.path.join(os.path.join(folder, linkstr), "title.md")
    if os.path.isfile(titlepath):
        input = io.open(titlepath, "tr", 1, encoding="utf-8")
        title = input.read()
        input.close()
        title = title.strip()
    return title

# Rewrites the toc.yaml files in the specified folder, changing the title of each entry.
def rewriteToc(folder):
    global nChanged
    tocpath = os.path.join(folder, "toc.yaml")
    input = io.open(tocpath, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines()
    input.close()
    bakpath = tocpath + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(tocpath, bakpath)
    output = io.open(tocpath, "tw", encoding="utf-8", newline='\n')
    title_line = ""
    for line in lines:
        if nChanged >= max_changes:
            break
        titlematch = title_re.match(line)
        if titlematch:
            title_line = line
            title_match = line[0:titlematch.end()]
        else:
            if title_line:
                newtitle = ""
                linkmatch = link_re.match(line)
                if linkmatch:
                    newtitle = fetchTitle(folder, line[linkmatch.end(0):].rstrip())
                if newtitle:
                    output.write(title_match + newtitle + "\"\n")
                else:
                    output.write(title_line)
                title_line = ""
            output.write(line)
    output.close()
    nChanged += 1
    
def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Recursive routine to process files under the specified folder
# Only one toc.yaml file is processed under each folder considered.
def convertFolder(folder):
    global nChanged
    global max_changes
    if nChanged >= max_changes:
        return
    tocpath = os.path.join(folder, "toc.yaml")
    if os.path.isfile(tocpath):
        sys.stdout.write("Rewriting: " + shortname(tocpath) + '\n')
        rewriteToc(folder)
    else:
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                convertFolder(path)

# Rewrites toc.yaml files under the specified directory
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python ta-localizeTitles.py <folder>\n  Use . for current folder.\n")
