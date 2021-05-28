# -*- coding: utf-8 -*-
# This script copies a directory of OBS-tQ or OBS-tN markdown files to a second location.
# It cleans up the files in these ways:
#    Ensures blank lines surrounding markdown headers.
#    Fixes links of this form [[:en:...]]
#    Removes leading spaces.

# Global variables
source_dir = r'C:\DCS\Russian\OBS-TN\content'
target_dir = r'C:\DCS\Russian\ru_obs-tn.work\content'    # path should end with "\content"
resource_type = 'obs-tn'
language_code = 'ru'

import re
import io
import os
import sys
import convert2md

# Returns path of .md file in target directory.
def makeMdPath(story, fname):
    mdPath = os.path.join(target_dir, story)
    if not os.path.isdir(mdPath):
        os.mkdir(mdPath)
    return os.path.join(mdPath, fname)

#prefix_re = re.compile(r'C:\\DCS')
def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Converts .md file in fullpath location to .md file in target dir.
def convertFile(story, fname, fullpath):
    if os.access(fullpath, os.F_OK):
        mdPath = makeMdPath(story, fname)
        convert2md.md2md(fullpath, mdPath, language_code, shortname)

# This method is called to convert the text files in the specified story folder.
# It renames files that have only a single digit in the name.
def convertStory(story, fullpath):
    for fname in os.listdir(fullpath):
        if re.match('\d\.md', fname):
            goodPath = os.path.join(fullpath, '0' + fname)
            if not os.path.exists(goodPath):
                badPath = os.path.join(fullpath, fname)
                os.rename(badPath, goodPath)
                fname = '0' + fname
        if (re.match('\d\d\.md', fname) and fname != '00.md'):
            convertFile(story, fname, os.path.join(fullpath, fname))

# It looks like OBS-sQ repos consist only of 50 .md files in one folder
def convertSQfolder(folder):
    for fname in os.listdir(folder):
        if re.match('\d\d\.md', fname):
            convertFile("", fname, os.path.join(folder, fname))

# Converts the stories contained in the specified folder
def convert(source_dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)
    if resource_type == 'obs-sq':
        convertSQfolder(source_dir)
    else:
        for item in os.listdir(source_dir):
            folder = os.path.join(source_dir, item)
            if os.path.isdir(folder):
                convertStory(item, folder)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if os.path.isdir(source_dir):
        convert(source_dir)
    print("\nDone.")
