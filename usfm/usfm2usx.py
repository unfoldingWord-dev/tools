# -*- coding: utf-8 -*-
# This script produces a set of .usx files in tStudio-compatible resource container format from
# USFM source text.
# The resulting containers are importable to BTT-Writer or tStudio to use as source text.
# Chunk division and paragraph locations are based on \s5 markers in the usfm files.
# Uses parseUsfm module to parse the usfm files.
# This script was originally written for converting the Spanish Reina-Valera 1909 Bible
# so that Bible could be used as a source text in BTT-Writer.
# It has also been used for the Danish 'Hellig Bibel'.
# The input file(s) should be verified, correct USFM.
# Before running the script, set the global variables below.

# Global variables
# source_dir = r'C:\DCS\Persian\pes_opcb'
config = None
gui = None
nConverted = 0
# rc_dir = r'C:\Users\lvers\AppData\Local\BTT-Writer\library\resource_containers'

# Values to be written into each of the package.json files
# language_code = 'dan'
# language_name = 'Dansk'
# bible_id = 'det'      # lowercase 'ulb' or other bible identifier
# bible_name = 'Hellig Bibel'
# direction = "ltr"
# pub_date = "2022-06-29"
# license = "Public Domain (NT)"
# version = "1"

import configmanager
from pathlib import Path
import sys
import os
import parseUsfm
import usfm_verses
import io
import codecs
import re
import json
import yaml
from shutil import copy
from datetime import date

lastToken = parseUsfm.UsfmToken(None)
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    ID = ""
    title = ""
    chapter = 0
    chapterPad = "00"
    verse = 0
    lastVerse = 0
    versePad = "00"
    needingVerseText = False
    pendingVerse = 0
    sectionPending = ""
    reference = ""
    lastRef = ""
    en_content_dir = ""
    en_chapter_dir = ""
    target_content_dir = ""
    target_chapter_dir = ""
    usxOutput = None

    def addID(self, id):
        State.ID = id
        State.title = ""
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.needingVerseText = False
        State.lastRef = State.reference
        State.reference = id
        rc_dir = config['rc_dir']
        State.en_content_dir = os.path.join( os.path.join(rc_dir, "en_" + id.lower() + "_ulb"), "content")
        State.target_content_dir = os.path.join( os.path.join(rc_dir, config['language_code'] + "_" + id.lower() + "_" + config['bible_id']), "content")

    def addTitle(self, bookTitle, mt):
        if not State.title:
            State.title = bookTitle
        if State.title.isascii() and not bookTitle.isascii():
            State.title = bookTitle
        if mt and State.title.isascii() == bookTitle.isascii(): # \mt is highest priority title, everything else being equal
            State.title = bookTitle

    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        if len(c) == 1:
            State.chapterPad = "0" + c
        else:
            State.chapterPad = c
        State.lastVerse = 0
        State.verse = 0
        State.versePad = ""
        State.needingVerseText = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c
        State.en_chapter_dir = os.path.join(State.en_content_dir, State.chapterPad)
        State.target_chapter_dir = os.path.join(State.target_content_dir, State.chapterPad)

    def addText(self):
        State.needingVerseText = False

    # Reports if vv is a range of verses, e.g. 3-4. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        if vv.find('-') > 0:
            reportError("Range of verses encountered at " + State.reference)
            vv_range = vv_re.search(vv)
            self.addVerse(vv_range.group(1))
            self.addVerse(vv_range.group(2))
        else:
            self.addVerse(vv)

    # Sets State.versePad for file naming purposes.
    # Updates State.reference
    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        if len(v) == 1:
            State.versePad = "0" + v
        else:
            State.versePad = v
        State.needingVerseText = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v

    def setUsxOutput(self, file):
        State.usxOutput = file

    def needVerseText(self):
        return State.needingVerseText

    def saveSection(self, s):
        State.sectionPending = s

# def printToken(token):
#     if token.isV():
#         print("Verse number " + token.value)
#     elif token.isC():
#         print("Chapter " + token.value)
#     elif token.isS():
#         sys.stdout.write("Section heading: " + token.value)
#     elif token.isTEXT():
#         print("Text: <" + token.value + ">")
#     else:
#         print(token)

# Removes UTF-8 Byte Order Marks (BOM) from specified file if it has one or more.
def removeBOM(path):
    bytes_to_remove = 0
    MAX = 60
    with open(path, 'rb') as f:
        raw = f.read(MAX + 3)
        while raw[bytes_to_remove:bytes_to_remove+3] == codecs.BOM_UTF8 and bytes_to_remove < MAX:
            bytes_to_remove += 3
        if bytes_to_remove > 0:
            f.seek(bytes_to_remove)
            raw = f.read()
    if bytes_to_remove > 0:
        with open(path, 'wb') as f:
            f.write(raw)

def takeID(id):
    state = State()
    state.addID(id[0:3])

# When a chapter marker is encountered in the USFM file, we close the current .usx files
# and change the target chapter folder.
# We also write a default title.usx for the chapter.
def takeC(c):
    state = State()
    closeUsx()
    state.addChapter(c)
    makeChapterDir(state.chapterPad)
    createChapterTitleFile(str(state.chapter))  # default, in case \cl does not follow
    path = os.path.join(state.target_chapter_dir, "01.usx")
    state.setUsxOutput( io.open(path, "tw", encoding="utf-8", newline='\n') )

def takeCL(value):
    createChapterTitleFile(value)

def takeF(value):
    State().usxOutput.write('<note style="f" caller="+"> ')

def takeFTFQA(type, value):
    State().usxOutput.write(f'<char style="{type}">\n{value} </char>\n')

def takeFE():
    State().usxOutput.write('</note>\n')

# Currently this function does nothing, as paragraphs are not relevant to tStudio/BTTW (confirmed 3/29/22).
def takeP(type):
    state = State()
    # state.usxOutput.write('<para style="' + type + '">\n\n')

# Writes the section heading immediately if at the beginning of a chapter.
# Saves the section heading if it occurs after the first verse in a chapter.
def takeS(s):
    state = State()
    if state.verse == 0:    # section heading is at the start of the chapter
        state.usxOutput.write(s)
    else:
        state.saveSection(s)

# When a verse marker is encountered in the USFM file, we open a new usx file if needed.
# We write the <verse> element into the usx file.
def takeV(v):
    state = State()
    state.addVerses(v)
    if not state.usxOutput:
        path = os.path.join(state.target_chapter_dir, state.versePad + ".usx")
        state.setUsxOutput( io.open(path, "tw", encoding="utf-8", newline='\n') )
    state.usxOutput.write('<verse number="' + v + '" style="v" />')

# Writes the specified text to the current usx file.
def takeText(t):
    state = State()
    if state.verse > 0:
        if state.usxOutput:
            state.usxOutput.write(t + "\n\n")
    else:
        reportError("Unhandled text before verse 1. See " + state.reference)
    state.addText()

# Handles each usfm token as the usfm files is parsed.
def take(token):
    state = State()
    if state.needVerseText() and not token.isTEXT():
        reportError("Empty verse: " + state.reference)
    if token.isID():
        takeID(token.value)
    elif token.isH() or token.isTOC1() or token.isTOC2() or token.isMT():
        state.addTitle(token.value, token.isMT())
    elif token.isC():
        takeC(token.value)
    elif token.isCL():
        takeCL(token.value)
    # elif token.isS():     # section headings are ignored currently
        # printToken(token)
        # takeS(token.value)
    elif token.isS5():
        closeUsx()
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isP() or token.isPI() or token.isPC() or token.isNB() or token.isQ() \
        or token.isQ1() or token.isQA() or token.isSP() or token.isQR() or token.isQC():
        takeP(token.type)
    elif token.isF_S():
        takeF(token.value)
    elif token.isFT() or token.isFQA():
        takeFTFQA(token.type, token.value)
    elif token.isF_E():
        takeFE()
    else:
        if not token.type in {'ide','toc3'}:
            reportError("Unhandled token: " + token.type)
    global lastToken
    lastToken = token

# Called when a \s5 chunk marker occurs, and at the end of every chapter.
# Closes the current usx file.
def closeUsx():
    state = State()
    if state.usxOutput:
        state.usxOutput.close()
        state.setUsxOutput(None)

def reportError(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    sys.stderr.write(msg + '\n')
    # sys.stderr.flush()

# Sends a progress report to the GUI.
# To be called only if the gui is set.
def reportStatus(msg):
    reportToGui(msg, '<<ScriptMessage>>')
    print(msg)

def reportProgress(msg):
    reportToGui(msg, '<<ScriptProgress>>')
    print(msg)

def reportToGui(msg, event):
    if gui:
        with gui.progress_lock:
            gui.progress = msg if not gui.progress else f"{gui.progress}\n{msg}"
        gui.event_generate(event, when="tail")

# Creates the specified folder and a "content" folder under it
def makeTargetDirs(target_book_dir):
    if not os.path.isdir(target_book_dir):
        os.mkdir(target_book_dir)
    target_content_dir = os.path.join(target_book_dir, "content")
    if not os.path.isdir(target_content_dir):
        os.mkdir(target_content_dir)

# Creates a chapter folder under the target content directory.
def makeChapterDir(chap):
    dir = os.path.join(State().target_content_dir, chap)
    if not os.path.isdir(dir):
        os.mkdir(dir)

idcode_re = re.compile(r'\\id +([\w][\w][\w])')

# Parses the book identifier from the \id tag, which should be on the first line of the usfm file
def getBookId(usfmpath):
    input = io.open(usfmpath, "tr", encoding="utf-8-sig")
    str = input.readline()
    input.close()
    if idcode := idcode_re.match(str):
        bookId = idcode.group(1)
    else:
        reportError("USFM file does not start with standard \\id marker.")
        bookId = ""
    return bookId

# Makes a custom package.json file in the specified target folder.
# Modifies a copy of an English manifest.
def createManifest(en_book_dir, target_book_dir):
    path = os.path.join(en_book_dir, "package.json")
    jsonFile = io.open(path, "tr", encoding='utf-8-sig')
    package = json.load(jsonFile)
    today = date.today()
    s = '%(year)d%(month)02d%(day)02d' % {'year':today.year, 'month':today.month, 'day':today.day}
    package['modified_at'] = int(s)
    package['language']['slug'] = config['language_code']
    package['language']['name'] = config['language_name']
    package['language']['direction'] = config['direction']
    state = State()
    package['project']['slug'] = state.ID.lower()
    package['project']['name'] = state.title
    package['project']['sort'] = usfm_verses.verseCounts[state.ID.upper()]['sort']
    package['project']['chunks_url'] = "https://api.unfoldingword.org/bible/txt/1/" + state.ID.lower() + "/chunks.json"
    category = "bible-nt"
    if usfm_verses.verseCounts[state.ID.upper()]['sort'] < 40:
        category = "bible-ot"
    package['project']['category_slug'] = category
    package['project']['categories'] = [category]
    package['resource']['slug'] = config['bible_id']
    package['resource']['name'] = config['bible_name']
    package['resource']['status']['pub_date'] = config['pub_date']
    package['resource']['status']['license'] = config['license']
    package['resource']['status']['version'] = config['version']

    path = os.path.join(target_book_dir, "package.json")
    jsonFile = io.open(path, "tw", encoding='utf-8', newline='\n')
    json.dump(package, jsonFile, ensure_ascii=False, indent=2)
    jsonFile.close()
    removeBOM(path)     # because tStudio/BTTW chokes on BOM

# Creates or overwrites chapter title file.
def createChapterTitleFile(title):
    state = State()
    path = os.path.join(state.target_chapter_dir, "title.usx")
    with io.open(path, "tw", encoding="utf-8", newline='\n') as usxOutput:
        usxOutput.write( title )

# Adds front folder with title.usx, if the book title is known.
def createBookTitleFile():
    state = State()
    frontFolder = os.path.join(state.target_content_dir, 'front')
    if not os.path.isdir(frontFolder):
        os.mkdir(frontFolder)
    output = io.open(os.path.join(frontFolder, 'title.usx'), 'tw', encoding="utf-8")
    output.write( state.title )
    output.close()

# Writes the toc.yaml file into the specified folder
def createToc(en_content_dir, content_dir):
    # Temporary implemention -- just copies the English toc.yaml
    copy(os.path.join(en_content_dir, 'toc.yml'), content_dir)    # copy() is from shutil

    # TODO: implement a better solution
    path = os.path.join(content_dir, "toc.yaml")

# Converts a single usfm file to a usx resource container.
def convertFile(usfmpath, bookId):
    rc_dir = config['rc_dir']
    en_book_dir = os.path.join(rc_dir, "en_" + bookId.lower() + "_ulb")
    target_book_dir = os.path.join(rc_dir, config['language_code'] + "_" + bookId.lower() + "_" + config['bible_id'])
    if not os.path.isdir(en_book_dir):
        reportError("English book folder not found: " + en_book_dir)
    else:
        makeTargetDirs(target_book_dir)
        en_content_dir = os.path.join(en_book_dir, "content")

        reportProgress("CONVERTING " + usfmpath)
        # sys.stdout.flush()
        input = io.open(usfmpath, "tr", encoding="utf-8-sig")
        str = input.read()
        input.close()
        for token in parseUsfm.parseString(str):
            take(token)
        closeUsx()
        state = State()
        copy(os.path.join(en_book_dir, 'LICENSE.md'), target_book_dir)
        createManifest(en_book_dir, target_book_dir)
        copy(os.path.join(en_content_dir, 'config.yml'), state.target_content_dir)    # copy() is from shutil
        createToc(en_content_dir, state.target_content_dir)
        createBookTitleFile()
        global nConverted
        nConverted += 1

# Parses entire usfm file and writes to .usx files by chunk.
def processFile(usfmpath):
    bookId = getBookId(usfmpath)
    if not bookId:
        reportError("Invalid USFM file: " + usfmpath)
    else:
        convertFile(usfmpath, bookId)

# Processes a whole folder of usfm files, recursively.
def convertDir(dir):
    for entry in os.listdir(dir):
        path = os.path.join(dir, entry)
        if entry[0] != '.' and os.path.isdir(path):
            convertDir(path)
        elif entry.endswith("sfm") and os.path.isfile(path):
            processFile(path)

# Creates the specified folder if necessary.
# Fails if the parent folder does not exist.
# Returns False if not possible.
def make_dir(folder):
    if not os.path.isdir(folder):
        parent = os.path.dirname(folder)
        if os.path.isdir(parent):
            os.mkdir(folder)
    return os.path.isdir(folder)
 
def main(app = None):
    global nConverted
    global gui
    global config
    nConverted = 0
    gui = app
    config = configmanager.ToolsConfigManager().get_section('Usfm2Usx')   # configmanager version
    if config:
        source_dir = config['source_dir']
        rc_dir = config['rc_dir']
    if not make_dir(rc_dir):
        reportError("Invalid resource_containers folder: " + rc_dir)
    elif not os.path.isdir(source_dir):
        reportError("Invalid source folder: " + source_dir)
    else:
        file = config['filename']
        if file:
            path = os.path.join(source_dir, file)
            if os.path.isfile(path):
                processFile(path)
            else:
                reportError(f"No such file: {path}")
        else:
            convertDir(source_dir)
        if nConverted > 0:
            reportStatus(f"\nDone. Converted {nConverted} book(s).")
        else:
            reportStatus("No books were successfully converted.")
    sys.stdout.flush()
    if gui:
        gui.event_generate('<<ScriptEnd>>', when="tail")

if __name__ == "__main__":
    main()
