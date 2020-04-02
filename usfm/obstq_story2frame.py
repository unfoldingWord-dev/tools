# -*- coding: utf-8 -*-
# This script splits a repository of OBS-tQ story-specific markdown files from old
# OBS-tQ version 3.2.1, into a collection of frame-specific markdown files as in v.4.
# The file splits are based on the information contained in frame links, e.g. [02:01],
# on each question in the story-specific files.
#    Parses the frame links, even when not perfectly formed.
#    Copies notes to the appropriate, frame-specific file(s) in target location.
#    Handles multiple frame links per question.
# This script was originally developed 6/1/18 for converting Hindi OBS-tQ that was
# apparently translated from obsolete English version of same.

# Global variables
resource_type = 'obs-tq'
language_code = 'hi'
target_dir = r'C:\Users\Larry\Documents\GitHub\Hindi\OBS-TQ.intermediate\content'

import re
import io
import os
import sys
import shutil
import codecs

# Writer temporarily stores the QAs for a single story.
# It is important that the NoteKeeper is one per story because multiple
# questions can pertain to the same frame.
# Each question/answer should be associated to one or more frames in the story.
class NoteKeeper:
#     
    def __init__(self, strStory):
        # self.story = strStory
        self.lastframe = 1
        self.frameList = {}
    
    # Adds a note to the last referenced frame
    def addNoteDefault(self, question, answer):
        self.addNote(question, answer, self.lastframe)
    
    # Adds a note to the specified frame    
    def addNote(self, question, answer, frame):
        if frame in self.frameList:
            self.frameList[frame].append( (question,answer) )
        else:
            self.frameList[frame] = [ (question,answer) ]
        self.lastframe = frame

def makeStoryDir(strStory):
    path = os.path.join(target_dir, strStory)
    if not os.path.isdir(path):
        os.mkdir(path)
    return path

# Returns True if the specified directory is one with text files to be converted
def isStory(path, filename):
    isStory = False
    if re.match('\d\d.md', filename) and os.access(path, os.F_OK):
        story = filename[0:2]
        isStory = (int(story) >= 1 and int(story) <= 50)
    return isStory

prefix_re = re.compile(r'C:\\Users\\Larry\\Documents\\GitHub')

def shortname(longpath):
    shortname = longpath
    if prefix_re.match(longpath):
        shortname = "..." + longpath[31:]
    return shortname

def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default


# links_re = re.compile(r'(.*)[ _](\[(\d+)[, -\d\[\]]*)(.*)', re.UNICODE)
link_re = re.compile(r'(.*)\[(\d+)-(\d+)\],?(.*)', re.UNICODE)

# Parses str to see if there are any valid frame links.
# Returns list of frames indicated by the links, if any.
# Also returns the string minus any frame links.
def linkedFrames(str, story, shortpath):
    ustr = str(str).strip()
    storynum = int(story)
    frames = []

    link = link_re.match(ustr)
    while link:
        ustr = link.group(1) + ' ' + link.group(4)
        if int(link.group(2)) == storynum:   # must be a valid link
            frames.append( int(link.group(3)) )
        else:
            sys.stderr.write("Invalid link in " + shortpath + " removed: " + link.group(2) + '-' + link.group(3) + '\n')
        link = link_re.match(ustr)  # find another link in the same string

    return frames, ustr


# Writes out all the QAs in frame-specific files
def writeStoryQAs(notekeeper, strStory):
    # print notekeeper.frameList.keys()
    # print notekeeper.frameList.values()
    
    storyDir = makeStoryDir(strStory)
    for frame in list(notekeeper.frameList.keys()):     # would this work: frame in notekeeper.frameList
        framePath = os.path.join(storyDir, ("%02d" % frame) + ".md")
        frameFile = io.open(framePath, "tw", buffering=1, encoding='utf-8', newline='\n')
        started = False
        for qaPair in notekeeper.frameList[frame]:
            if started:
                frameFile.write("\n")
            frameFile.write("# " + qaPair[0] + "\n")
            frameFile.write(qaPair[1] + "\n")
            started = True
        frameFile.close()

    statinfo = os.stat(framePath)
    if statinfo.st_size == 0:
        sys.stderr.write("Removed: " + shortname(framePath) + "\n")
        os.remove(framePath)

question_re = re.compile(r'1\. +_+(.*)_ *$', re.UNICODE)
answer_re = re.compile(r'[ \t]*\* *(.*)', re.UNICODE)

def convertQAs(lines, strStory, shortpath):
    global nSplits
    notekeeper = NoteKeeper(strStory)
    n = 0   # used in error messages below
    question = ''
    answer = ''
    for line in lines:
        n += 1
        line = line.strip()
        if line:
            qmatch = question_re.match(line)
            amatch = answer_re.match(line)
            if qmatch:
                if question:
                    sys.stderr.write("Unanswered question in: " + shortpath + '\n')
                question = qmatch.group(1).rstrip("_ ")
            elif amatch:
                if answer:
                    sys.stderr.write("Orphaned answer in: " + shortpath + '\n')
                answer = amatch.group(1)
            
        if question and answer:     # we have a pair
            (frames, answer) = linkedFrames(answer, strStory, shortpath)
            answer = re.sub("_ *_$", "", answer, 1, re.UNICODE)
            if len(frames) == 0:
                notekeeper.addNoteDefault(question.strip(), answer.strip())
            else:
                for frame in frames:
                    notekeeper.addNote(question.strip(), answer.strip(), frame)
                nSplits += len(frames)
            question = ''
            answer = ''

    if len(notekeeper.frameList) > 0:
        writeStoryQAs(notekeeper, strStory)

# This method is called to convert the specified story file
# Converts QAs from fullpath into into QAs associated to frame-specific files in target_dir/story/
def convertStory(fullpath, strStory):
    enc = detect_by_bom(fullpath, default="utf-8")
    if enc != "utf-8":
        sys.stderr.write("Warning: UTF-8 not detected: " + shortname(fullpath) + "\n")
    f = io.open(fullpath, "tr", 1, encoding=enc)
    lines = f.readlines()
    f.close()

    if len(lines) > 0:
        convertQAs(lines, strStory, shortname(fullpath))

# Converts the story files contained in the specified folder
def convert(dir):
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    for storyfile in os.listdir(dir):
        fullpath = os.path.join(dir, storyfile)
        if isStory(fullpath, storyfile):
            sys.stdout.write("Converting: " + shortname(fullpath) + "\n")
            sys.stdout.flush()
            convertStory(fullpath, storyfile[0:2])

# Processes each directory and its files one at a time
if __name__ == "__main__":
    nSplits = 0

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python obstq_story2frame <folder>\n  Use . for current folder.\n")
    elif sys.argv[1] == 'hard-coded-path':
        convert(r'C:\Users\Larry\Documents\GitHub\Hindi\OBS-TQ\content')
    else:       # the first command line argument presumed to be a folder
        convert(sys.argv[1])

    print("\nDone. Made", nSplits, "file splits.")
