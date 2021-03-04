# -*- coding: utf-8 -*-
# This script converts a repository of tW text files from tStudio to .md format,
# to create a valid resource container. The old folder structure has only a single
# folder for all 1000+ files. This script is intended to do the following:
#    Convert each .txt file into an equivalent .md file.
#    Determine a location under the target folder for the .md file based on
#       matching the file name to a file in the English tW structure. Assumes that
#       folders are only one level deep under the English and target language folders.

# Global variables
source_dir = r'C:\DCS\Amharic\TW\01'
target_dir = r'C:\DCS\Amharic\am_tw.RPP'
language_code = 'am'
en_ta_dir = r'C:\DCS\English\en_ta.v9'
en_tw_dir = r'C:\DCS\English\en_tw.v10\bible'      # should end in 'bible'

import re
import io
import os
import sys
import convert2md
import string

tapage_re = re.compile(r'\[\[.*/ta/man/(.*)]]', flags=re.UNICODE)
pages = []

# Parse the tA manual page name from the link string.
# Add it to the list of pages to be resolved if it is not in the tA manual
def captureArticle(linkstr):
    global pages
    page = tapage_re.match(linkstr)
    if page:
        manpage = page.group(1)
        path = os.path.join(en_ta_dir, manpage)
        if not os.path.isdir(path):
            pages.append(manpage)

# Writes a file, articles.txt, containing a list of unresolved references to tA articles.
def dumpArticles(dir):
    pages = convert2md.getBadReferences()
    if len(pages) > 0:
        pagelist = list(set(pages))
        pagelist.sort()
        path = os.path.join(dir, "articles.txt")
        file = io.open(path, "tw", encoding='utf-8', newline='\n')
        for article in pagelist:
            file.write(article + '\n')
        file.close()
        sys.stderr.write("Unresolved links, see " + shortname(path) + '\n')

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

def makeMdPath(fname):
    mdName = os.path.splitext(fname)[0] + ".md"
    subdir = "other"
    for trydir in os.listdir(en_tw_dir):
        tryFolder = os.path.join(en_tw_dir, trydir)
        if os.path.isdir(tryFolder):
            if os.path.isfile( os.path.join(tryFolder, mdName) ):
                subdir = trydir
                break

    mdFolder = os.path.join(target_dir, subdir)
    if not os.path.isdir(mdFolder):
        os.mkdir(mdFolder)
    return os.path.join(mdFolder, mdName)

# Converts .txt file in fullpath location to .md file in target dir.
def convertFile(fname, fullpath):
    sys.stdout.write(fname + '\n')
    if os.access(fullpath, os.F_OK):
        mdPath = makeMdPath(fname)
        convert2md.json2md(fullpath, mdPath, language_code, shortname)

# This method is called to convert the text files in the specified folder.
def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if entry[0] != '.' and os.path.isdir(path):
            convertFolder(path)
        elif entry[-4:].lower() == ".txt":
            convertFile(entry, path)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if not target_dir.endswith("bible"):
        target_dir = os.path.join(target_dir, "bible")
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        print("\nDone.")
    else:
        sys.stderr.write("Path not found: " + source_dir + '\n') 

