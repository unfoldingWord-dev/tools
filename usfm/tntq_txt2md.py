# -*- coding: utf-8 -*-
# This script converts a repository of tN or tQ text files from tStudio export
# format to .md Resource Container format.
#    Reads manifest.json or parses directory names to get the book IDs
#    Specify target output folder.
#    Standardizes the names of book folders in the target folder.
#    Converts multiple books in a single pass.
#    Makes a projects.yaml file to be pasted into manifest.yaml.
#    Fixes links of this form [[:en:...]]
#    Outputs list of unique translators gleaned from all manifest.json files.
#    Outputs list of source versions gleaned from all manifest.json files.
# If there are legitimate passage links, run tntq_chunk2verse.py before running this script.
# This script doesn't do anything if the files are .md files already.

# Global variables
language_code = 'hr'
target_dir = r'E:\DCS\Croatian\hr_tn'
source_dir = r'E:\DCS\Croatian\TN.newest'

projects = []
translators = []
source_versions = []

import re
import io
import os
import sys
import json
import convert2md
import usfm_verses
import operator

# Parses the specified folder name to extract the book ID.
# These folder names may be generated by tStudio in the form: language_book_tn.
# Return upper case bookId or empty string if failed to retrieve.
def parseBookId(folder):
    bookId = ""
    parts = folder.split('_')
    if len(parts) >= 3:
        bookId = parts[1]
    elif len(parts) == 1 and len(folder) == 3:
        bookId = folder
    return bookId.upper()

def getBookId(path):
    bookId = ""
    manifestpath = os.path.join(path, 'manifest.json')
    if os.path.isfile(manifestpath):
        try:
            f = open(manifestpath, 'r')
        except IOError as e:
            sys.stderr.write("   Can't open " + shortname(manifestpath) + "\n")
        else:
            global translators
            global source_versions
            manifest = json.load(f)
            f.close()
            bookId = manifest['project']['id']
            translators += manifest['translators']
            for source in manifest['source_translations']:
                source_versions += source['version']
    if not bookId:
        bookId = parseBookId( os.path.split(path)[1] )
    return bookId.upper()


# Returns the English book name from usfm_verses
def getBookTitle(id):
    title = ""
    if id:
        title = usfm_verses.verseCounts[id]['en_name']
    return title

# Appends information about the current book to the global projects list.
def appendToProjects(bookId, bookTitle):
    global projects
    title = bookTitle + " translationNotes"
    if resource_type == 'tq':
        title = bookTitle + " translationQuestions"
    project = { "title": title, "id": bookId.lower(), "sort": usfm_verses.verseCounts[bookId]["sort"], \
                "path": "./" + bookId.lower() }
    projects.append(project)

# Returns path of temporary manifest file block listing projects converted
def makeManifestPath():
    return os.path.join(target_dir, "projects.yaml")
    
def makeMdPath(id, chap, chunk):
    mdPath = os.path.join(target_dir, id.lower())
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)

    if id.lower() == 'psa' and len(chap) == 2:
        chap = "0" + chap
    mdPath = os.path.join(mdPath, chap)
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)

    chunk = chunk[0:-4]
    if id.lower() == 'psa' and len(chunk) == 2:
        chunk = "0" + chunk
    return os.path.join(mdPath, chunk) + ".md"

# Returns True if the specified file name matches a pattern that indicates
# the file contains text to be converted.
def isChunk(filename):
    isSect = False
    if re.match('\d\d\d?\.txt', filename) and filename != '00.txt':
        isSect = True;
    return isSect

# Returns True if the specified directory is one with text files to be converted
def isChapter(dirname):
    isChap = False
    if dirname != '00' and re.match('\d\d\d?$', dirname):
        isChap = True
    return isChap

prefix_re = re.compile(r'C:\\DCS')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[6:]
    return shortname

# Sort the list of projects and write to projects.yaml
def dumpProjects():
    global projects
    
    projects.sort(key=operator.itemgetter('sort'))
    path = makeManifestPath()
    manifest = io.open(path, "ta", buffering=1, encoding='utf-8', newline='\n')
    for p in projects:
        manifest.write("  -\n")
        manifest.write("    title: '" + p['title'] + "'\n")
        manifest.write("    versification: ''\n")
        manifest.write("    identifier: '" + p['id'] + "'\n")
        manifest.write("    sort: " + str(p['sort']) + "\n")
        manifest.write("    path: '" + p['path'] + "'\n")
        manifest.write("    categories: []\n")
    manifest.close()

def dumpTranslators():
    global translators
    contribs = list(set(translators))
    contribs.sort()
    path = os.path.join(target_dir, "translators.txt")
    f = io.open(path, 'tw', encoding='utf-8', newline='\n')
    for name in contribs:
        f.write('    - "' + name + '"\n')
    
    # Also dump the list of source versions used
    f.write('\n\nSource versions used:\n')
    for version in source_versions:
        f.write(version + ' ')
    f.write('\n')
    f.close()

# Converts .txt file in fullpath location to .md file in target dir.
def convertFile(id, chap, fname, fullpath):
    if os.access(fullpath, os.F_OK):
        mdPath = makeMdPath(id, chap, fname)
        convert2md.json2md(fullpath, mdPath, language_code, shortname)

# This method is called to convert the text files in the specified chapter folder
# If it is not a chapter folder
def convertChapter(bookId, dir, fullpath):
    for fname in os.listdir(fullpath):
        if isChunk(fname):
            convertFile(bookId, dir, fname, os.path.join(fullpath, fname))

# Determines if the specified path is a book folder, and processes it if so.
# Return book title, or empty string if not a book.
def convertBook(path):
    bookId = getBookId(path)
    bookTitle = getBookTitle(bookId)
    if bookId and bookTitle:
        sys.stdout.write("Converting: " + shortname(path) + "\n")
        sys.stdout.flush()
        for dir in os.listdir(path):
            if isChapter(dir):
                # sys.stdout.write( " " + dir )
                convertChapter(bookId, dir, os.path.join(path, dir))
        appendToProjects(bookId, bookTitle)
    else:
        sys.stderr.write("Not identified as a book folder: " + shortname(path) + '\n')
    
    return bookTitle
 
# Converts the book or books contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if os.path.isfile( makeManifestPath() ):
        os.remove( makeManifestPath() )
    if not convertBook(dir):
        for directory in os.listdir(dir):
            folder = os.path.join(dir, directory)
            if os.path.isdir(folder):
                convertBook(folder)
    dumpProjects()
    dumpTranslators()

# Processes each directory and its files one at a time
if __name__ == "__main__":
    resource_type = target_dir[-2:].lower()
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convert(source_dir)
        sys.stdout.write("Done.\n")
    else:
        sys.stderr.write("Usage: python tntq_txt2md.py <folder>\n  Use . for current folder or hard code the path.\n")
