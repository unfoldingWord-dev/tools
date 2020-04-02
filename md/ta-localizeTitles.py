# -*- coding: utf-8 -*-
# This program localizes the titles of tA articles.
# Used when the translators did not translate the titles found in toc.yaml files,
#   but did translate the titles of each article, found in title.md files.

import re       # regular expression module
import io
import os
# import shutil
import codecs
import string
import sys

# Globals
nChanged = 0
max_changes = 5     # There should only be 4 altogether

def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
        f.close
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default

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
    enc = detect_by_bom(tocpath, default="utf-8")
    input = io.open(tocpath, "tr", 1, encoding=enc)
    lines = input.readlines()
    input.close()
    bakpath = tocpath + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(tocpath, bakpath)
    output = io.open(tocpath, "tw", encoding="utf-8")
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
    

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
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
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        folder = r'C:\DCS\Kannada\kn_tA'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertFolder(folder)
        sys.stdout.write("Done. Changed " + str(nChanged) + " files.\n")
    else:
        sys.stderr.write("Usage: python ta-localizeTitles.py <folder>\n  Use . for current folder.\n")
