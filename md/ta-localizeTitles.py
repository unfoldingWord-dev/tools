# -*- coding: utf-8 -*-
# This program localizes the titles of tA articles in toc.yaml files.
# It copies titles from the title.md files into the toc.yaml files.
# It also removes (title,link) pairs from the toc.yaml files where the article does not exist.

import re
import io
import os
import codecs
import string
import sys

# Globals
source_dir = r'C:\DCS\Malayalam\ml_ta'
nRewritten = 0

# Reads the translated title from the specified title.md file.
def fetchTitle(folder, linkstr):
    title = None
    titlepath = os.path.join(os.path.join(folder, linkstr), "title.md")
    if os.path.isfile(titlepath):
        input = io.open(titlepath, "tr", 1, encoding="utf-8")
        title = input.read()
        input.close()
        title = title.strip()
    return title

title_re = re.compile(r'([ \-]*title: +)[\'"](.*)[\'"]', flags=re.UNICODE)
link_re =  re.compile(r'    +link: +([\w\-]+)')
section_re = re.compile(r' *sections', re.UNICODE)

def rewriteTocLines(folder, lines, output):
    title_line = None
    missing_article = False
    for line in lines:
        titlematch = title_re.match(line)
        if titlematch:
            title_line = line
            title_prefix = titlematch.group(1)
            title_text = titlematch.group(2)
        elif section_re.match(line) or line.strip() == "":
            if title_line:
                output.write(title_line)
                title_line = None
            output.write(line)
        elif title_line:      # previous line was a title
#                if title_text.isascii():    # not a valid test because English titles include non-ascii like '®'
                newtitle = ""
                linkmatch = link_re.match(line)
                if linkmatch:
                    newtitle = fetchTitle(folder, linkmatch.group(1))
                    if newtitle == None:
                        missing_article = True
                        sys.stdout.write("Article does not exist, removing: " + linkmatch.group(1) + "\n")
                    else:
                        if '"' in newtitle:
                            title_line = title_prefix + "'" + newtitle + "'\n"
                        elif len(newtitle) > 0:
                            title_line = title_prefix + '"' + newtitle + '"\n'
                if not missing_article:
                    output.write(title_line)
                    output.write(line)
                title_line = None
                missing_article = False
    
# Rewrites the toc.yaml files in the specified folder, changing the title of each entry.
def rewriteToc(folder):
    global nRewritten
    tocpath = os.path.join(folder, "toc.yaml")
    input = io.open(tocpath, "tr", 1, encoding="utf-8-sig")
    lines = input.readlines()
    input.close()
    bakpath = tocpath + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(tocpath, bakpath)
    with io.open(tocpath, "tw", encoding="utf-8", newline='\n') as output:
        rewriteTocLines(folder, lines, output)
    nRewritten += 1
    
def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Recursive routine to process files under the specified folder
# Only one toc.yaml file is processed under each folder considered.
def convertFolder(folder):
    tocpath = os.path.join(folder, "toc.yaml")
    if os.path.isfile(tocpath):
        sys.stdout.write("Rewriting: " + shortname(tocpath) + '\n')
        rewriteToc(folder)
    else:
        for entry in os.listdir(folder):
            if entry[0] != '.':
                path = os.path.join(folder, entry)
                if os.path.isdir(path):
                    convertFolder(path)

# Rewrites toc.yaml files under the specified directory
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        sys.stdout.write("Done. Rewrote " + str(nRewritten) + " files.\n")
    else:
        sys.stderr.write("Usage: python ta-localizeTitles.py <folder>\n  Use . for current folder.\n")
