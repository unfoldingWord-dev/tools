# -*- coding: utf-8 -*-
# This program converts a folder of OBS text files
# in the older format (one .txt file per OBS story)
# to a set of corresponding, OBS story files in Markdown format.
# Outputs .md files to a content folder under target_dir.

import re       # regular expression module
import io
import os
import codecs
import string
import sys

# Globals
en_contentdir = r'/Users/richmahn/repos/git.door43.org/en_obs/content'
target_dir = r'/Users/richmahn/repos/git.door43.org/apt_obs'

def merge(image_list, txtfile, mdfile):
    titleLinesOut = 0
    lines = txtfile.readlines()
    nChunks = countChunks(lines)
    chunksOut = 0
    images_inline = (len(image_list) == nChunks)
    for line in lines:
        line = line.strip()
        if line:
            if titleLinesOut == 0:
                mdfile.write("# " + line + "\n")      # title
                titleLinesOut = 1
            elif titleLinesOut == 1:
                mdfile.write("## " + line + "\n")      # subtitle
                titleLinesOut = 2
            elif chunksOut < nChunks:
                if images_inline and chunksOut < len(image_list):
                    mdfile.write("\n" + image_list[chunksOut])
                mdfile.write("\n")
                mdfile.write(line + "\n")
                chunksOut += 1
            else:
                mdfile.write("\n" + line + "\n")
                chunksOut += 1  # necessary?

    if not images_inline:
        mdfile.write("\n\n")
        for image in image_list:
            mdfile.write(image)


refstart_re = re.compile(r'\:\s*$')     # match colon at end of line

# Returns the number of lines that are not part of the title and not part of the references at the bottom
def countChunks(lines):
    nChunks = -2        # start at -1 to account for title and subtitle
    for line in lines:
        line = line.strip()
        if line:                # don't count blank lines
            if refstart_re.search(line):
                break
            else:
                nChunks += 1
    return nChunks


image_re = re.compile(r'\!\[OBS Image\]')

def listImages(mdpath):
    image_list = []
    enc = detect_by_bom(mdpath, default="utf-8")
    input = io.open(mdpath, "tr", 1, encoding=enc)
    for line in input.readlines():
        if image_re.match(line):
            image_list.append(line)
    input.close()
    return image_list


def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
        f.close()
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default


obsfilename = re.compile(r'([0-5][0-9])\.txt')

# Convert each .txt file in the specified folder to equivalent .md format
def convertStories(folder):
    for filename in sorted(os.listdir(folder)):
        print(filename + "\n")
        obsmatch = obsfilename.match(filename)
        if obsmatch:
            sys.stdout.write(filename + "\n")   # to show progress on stdout
            story = obsmatch.group(1)
            english_md_path = os.path.join(en_contentdir, story + '.md')
            if not os.access(english_md_path, os.F_OK):
                sys.stderr.write("Cannot access English OBS file: " + english_md_path + "\n")
                continue
            image_list = listImages(english_md_path)

            inputpath = os.path.join(folder, filename)
            enc = detect_by_bom(inputpath, default="utf-8")
            input = io.open(inputpath, "tr", 1, encoding=enc)
            outputpath = os.path.join(target_dir, "content")
            if not os.path.isdir(outputpath):
                os.mkdir(outputpath)
            outputpath = os.path.join(outputpath, story + ".md")
            output = io.open(outputpath, "tw", buffering=1, encoding='utf-8', newline='\n')

            merge(image_list, input, output)   # converts this .txt file to .md
            output.close()
            input.close()

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == '.':       # use current directory
        folder = os.getcwd()
    elif sys.argv[1] == 'hard-coded-path':
        folder = r'C:\DCS\Hausa\ha_obs_text_obs_L1'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertStories(folder)
    else:
        sys.stderr.write("Usage: python obs_txt2md.py <folder>\n  Use . for current folder.\n")
