#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017-2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>
#  Robert Hunt <Robert.Hunt@unfoldingword.org>

"""
This script was used to convert the MD tN files to TSV format.
Ran on 2018-05-31, see https://git.door43.org/unfoldingWord/en_tn/pulls/1064

Adapted July 2020 by RJH to meld a GL markdown TN to the English TSV.

Copy this script to the markdown TN folder and run it from there.
"""
from typing import Dict, List, Tuple, Optional
import os
import re
import glob
import string
import random
from pathlib import Path


EN_TN_PATH = Path('../en_tn/')


# DONE
# * Clean intro files
#   * remove ## Links (vim)
#   * sed -i 's/ #*$//' */*/intro.md
# * Rename intro files to 00-intro so they sort right
#   * $ for x in `find * -type f -name 'intro.md'`; do mv $x ${x%%intro.md}00.md; done

id_list = []
linkre = re.compile(r'\[\[(.*?)\]\]', re.UNICODE)
books_nums = {}
books = {
          'GEN': [ 'Genesis', '01' ],
          'EXO': [ 'Exodus', '02' ],
          'LEV': [ 'Leviticus', '03' ],
          'NUM': [ 'Numbers', '04' ],
          'DEU': [ 'Deuteronomy', '05' ],
          'JOS': [ 'Joshua', '06' ],
          'JDG': [ 'Judges', '07' ],
          'RUT': [ 'Ruth', '08' ],
          '1SA': [ '1 Samuel', '09' ],
          '2SA': [ '2 Samuel', '10' ],
          '1KI': [ '1 Kings', '11' ],
          '2KI': [ '2 Kings', '12' ],
          '1CH': [ '1 Chronicles', '13' ],
          '2CH': [ '2 Chronicles', '14' ],
          'EZR': [ 'Ezra', '15' ],
          'NEH': [ 'Nehemiah', '16' ],
          'EST': [ 'Esther', '17' ],
          'JOB': [ 'Job', '18' ],
          'PSA': [ 'Psalms', '19' ],
          'PRO': [ 'Proverbs', '20' ],
          'ECC': [ 'Ecclesiastes', '21' ],
          'SNG': [ 'Song of Solomon', '22' ],
          'ISA': [ 'Isaiah', '23' ],
          'JER': [ 'Jeremiah', '24' ],
          'LAM': [ 'Lamentations', '25' ],
          'EZK': [ 'Ezekiel', '26' ],
          'DAN': [ 'Daniel', '27' ],
          'HOS': [ 'Hosea', '28' ],
          'JOL': [ 'Joel', '29' ],
          'AMO': [ 'Amos', '30' ],
          'OBA': [ 'Obadiah', '31' ],
          'JON': [ 'Jonah', '32' ],
          'MIC': [ 'Micah', '33' ],
          'NAM': [ 'Nahum', '34' ],
          'HAB': [ 'Habakkuk', '35' ],
          'ZEP': [ 'Zephaniah', '36' ],
          'HAG': [ 'Haggai', '37' ],
          'ZEC': [ 'Zechariah', '38' ],
          'MAL': [ 'Malachi', '39' ],
          'MAT': [ 'Matthew', '41' ],
          'MRK': [ 'Mark', '42' ],
          'LUK': [ 'Luke', '43' ],
          'JHN': [ 'John', '44' ],
          'ACT': [ 'Acts', '45' ],
          'ROM': [ 'Romans', '46' ],
          '1CO': [ '1 Corinthians', '47' ],
          '2CO': [ '2 Corinthians', '48' ],
          'GAL': [ 'Galatians', '49' ],
          'EPH': [ 'Ephesians', '50' ],
          'PHP': [ 'Philippians', '51' ],
          'COL': [ 'Colossians', '52' ],
          '1TH': [ '1 Thessalonians', '53' ],
          '2TH': [ '2 Thessalonians', '54' ],
          '1TI': [ '1 Timothy', '55' ],
          '2TI': [ '2 Timothy', '56' ],
          'TIT': [ 'Titus', '57' ],
          'PHM': [ 'Philemon', '58' ],
          'HEB': [ 'Hebrews', '59' ],
          'JAS': [ 'James', '60' ],
          '1PE': [ '1 Peter', '61' ],
          '2PE': [ '2 Peter', '62' ],
          '1JN': [ '1 John', '63' ],
          '2JN': [ '2 John', '64' ],
          '3JN': [ '3 John', '65' ],
          'JUD': [ 'Jude', '66' ],
          'REV': [ 'Revelation', '67' ],
}
TAB = '\t'


def getOLQuote(b:str, c:str, v:str, glquote:str) -> List[str]:
    '''Eventually, look at alignment data and return occurrence num and orig quote'''
    # For now, return 0 to indicate not found
    return ['0', '']

def getNoteID() -> str:
    '''Returns a unique 4 character alpha-numberic string'''
    while True:
        ID = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        if not any(char.isdigit() for char in ID): continue
        if not any(char.isalpha() for char in ID): continue
        if '0' in ID: continue
        if 'o' in ID: continue
        if ID[0].isdigit(): continue
        if ID not in id_list:
            id_list.append(ID)
            return ID


def loadEnglishTSV(BBB):
    """
    Loads the English TSV TN data for the given bookcode.
    """
    BBBupper = BBB.upper()
    enTSVfilepath = EN_TN_PATH.joinpath(f'en_tn_{books[BBB][1]}-{BBB}.tsv')
    # print(f"Loading English TSV for {BBB} from {enTSVfilepath}…")
    with open(enTSVfilepath, 'r', encoding='utf-8') as enTSVbook:
        tsvTable = []
        for line in enTSVbook:
            line = line.rstrip('\r\n')
            if line:
                fields = line.split('\t')
                assert len(fields) == 9
                tsvTable.append(fields)
        # print(f"  returning {len(tsvTable):,} TSV lines")
        return tsvTable


def convertMarkdownToList(f, tn_checks):
    """
    Iterates through each verse file
    """
    # print(f"convertMarkdownToList {f}…")
    b, c, v = f.rstrip('.md').split('/')
    if c == '00':
        c = 'front'
    f = f.replace(b, books_nums[b], 1).lower()
    b = books_nums[b]
    if not b in tn_checks:
        tn_checks[b] = [['Book', 'Chapter', 'Verse', 'ID', 'SupportReference',
                         'OrigQuote', 'Occurrence', 'GLQuote',  'OccurrenceNote']]
    if v in ['00']:
        # This is an introduction, which has a different format than a regular note
        with open(f, 'r', encoding='utf-8') as mdFile:
            for line in mdFile:
                if line.startswith('# '):
                    ID = getNoteID()
                    # We'll use the intro text for the ref
                    ref = line.replace('#', '').strip()
                    olquote = ''
                    occurrence = '0'
                    glquote = ''
                    note_text = line.strip()
                    continue
                # This is the note text
                note_text += line.strip()
                note_text += '<br>'
        tn_checks[b].append([b, c, 'intro', ID, ref, olquote, occurrence, glquote, note_text])
        return tn_checks
    with open(f, 'r', encoding='utf-8') as mdFile:
        for line in mdFile:
            # This is the text snippet from the ULB
            if line.startswith('#'):
                ID = getNoteID()
                ref = ''
                glquote = line.strip('#').strip()
                occurrence, olquote = getOLQuote(b, c, v, glquote)
                continue
            # This is the note text (skips blank lines)
            if not line.startswith('\n'):
                note_text = line.strip()
                if '/en/ta/' in note_text:
                    if linkre.search(note_text):
                        ref = linkre.search(note_text).group(1).split('/')[-1]
                try:
                    tn_checks[b].append([b, c, v, ID, ref, olquote, occurrence, glquote, note_text])
                except UnboundLocalError:
                    print( b, c, v, line)
    return tn_checks


def saveToTSV(languageCode:str, BBB:str, glData, enTSVData:List[list]) -> None:
    """
    Merges the GL notes into the English notes
        thus transforming from 9 columns to 11 columns
        for manually editing.
    """
    tn_check_filename = f'{languageCode}_tn_{books[BBB][1]}-{BBB}.tsv'
    print(f"  Processing {BBB} for {tn_check_filename}…")
    with open(tn_check_filename, 'w', encoding='utf-8') as writer:
        enIndex, lastEnIndex = 0, -1
        lastEnCint = lastEnVint = 0
        glIndex, lastGlIndex = 1, 0 # We skip the GL heading row
        lastGlCint = lastGlVint = 0
        while True:
            # Have to put checks at beginning of loop since we use 'continue'
            # print(f"\nNew loop with en {enIndex} ({lastEnIndex}) / {len(enTSVData)} and {languageCode} {glIndex} ({lastGlIndex}) / {len(glData)}")

            # See if we're finished
            if enIndex == len(enTSVData) \
            and glIndex == len(glData):
                break; # all done

            # See if we're just looping without progressing
            if enIndex==lastEnIndex and glIndex==lastGlIndex: # infinite loop???
                print("PROGRAM LOGIC ERROR: We seem to be looping infinitely!!!!"); halt
            lastEnIndex, lastGlIndex = enIndex, glIndex

            # Get next EN fields
            if enIndex < len(enTSVData):
                enFields = enTSVData[enIndex].copy()
                assert len(enFields) == 9
                enBBB, enC, enV = enFields[:3]
                # if enC == '2': break
                # print(f"  Got en {enBBB} {enC}:{enV}")
                if enBBB == 'Book': # it's the heading row
                    enFields[7] += '(en)'
                    enFields[8] += '(en)'
                    enFields.append('GLQuote')
                    enFields.append('OccurrenceNote')
                    # print(f"Writing header row: {enFields}")
                    assert len(enFields) == 11
                    writer.write(f'{TAB.join(enFields)}\n')
                    enIndex += 1 # Used that one
                    enFields = None
                    continue
                else: # not the header row
                    assert enBBB == BBB
                    if enC == 'front': enC = '0'
                    if enV == 'intro': enV = '0'
                    enCint, enVint = int(enC), int(enV)
                    if enCint < lastEnCint:
                        print(f"en {enBBB} seems to have chapter {enCint} AFTER {lastEnCint}"); halt
                    elif enCint > lastEnCint:
                        lastEnVint = 0
                    if enVint < lastEnVint:
                        print(f"en {enBBB} {enC} seems to have verse {enVint} AFTER {lastEnVint}"); halt
                    enX = enCint*1000 + enVint
            else:
                enFields = None

            # Get next GL fields
            if glIndex < len(glData):
                nextGLfields = glData[glIndex]
                assert len(nextGLfields) == 9
                glBBB, glC, glV = nextGLfields[:3]
                glC = glC.lstrip('0')
                glV = glV.lstrip('0')
                # print(f"  Got {languageCode} {glBBB} {glC}:{glV}")
                assert glBBB == BBB
                if glC == 'front': glC = '0'
                if glV == 'intro': glV = '0'
                glCint, glVint = int(glC), int(glV)
                if glCint < lastGlCint:
                    print(f"{languageCode} {glBBB} seems to have chapter {glCint} AFTER {lastGlCint}"); halt
                elif glCint > lastGlCint:
                    lastGlVint = 0
                if glVint < lastGlVint:
                    print(f"{languageCode} {glBBB} {glC} seems to have verse {glVint} AFTER {lastGlVint}"); halt
                glX = glCint*1000 + glVint

                if enFields and glX==enX:
                    enFields.append(nextGLfields[7]) # GL Quote
                    enFields.append(nextGLfields[8]) # Occurrence Note
                    # print(f"Writing combined {len(enFields)} {enFields}")
                    assert len(enFields) == 11
                    writer.write(f'{TAB.join(enFields)}\n')
                    enIndex += 1 # Used that one now
                    glIndex += 1 # Used that one now
                    continue
                elif enX > glX or not enFields: # we've gone past our place (or past the end of the English)!!!
                    # print(f"Gone past ({enC}:{enV}={enX} vs {glC}:{glV}={glX}")
                    # We need to add a line to the table
                    newRow = [BBB,glC,glV,nextGLfields[3],nextGLfields[4],nextGLfields[5],nextGLfields[6],'','', nextGLfields[7], nextGLfields[8]]
                    # print(f"Inserting {newRow}")
                    assert len(newRow) == 11
                    writer.write(f'{TAB.join(newRow)}\n')
                    glIndex += 1 # Used that one now
                    continue

            if enFields:
                if len(enFields) == 9: # pad out to 11 fields
                    enFields.append('')
                    enFields.append('')

                # print(f"Writing {len(enFields)} {enFields}")
                assert len(enFields) == 11
                writer.write(f'{TAB.join(enFields)}\n')
                enIndex += 1 # Used that one
                enFields = None

    if enIndex != len(enTSVData):
        print(f"Something went wrong: en has {enIndex} instead of {len(enTSVData)}"); halt
    if glIndex != len(glData):
        print(f"Something went wrong: {languageCode} has {glIndex} instead of {len(glData)}"); halt


if __name__ == '__main__':
    print("Discovering language code…")
    cwd = os.getcwd()
    basename = os.path.basename(cwd)
    languageCode = basename.split('_',1)[0]
    print(f"  Found {languageCode!r}")

    print("Discovering markdown files…")
    tn_checks = {}
    mdFilepathList = [x for x in glob.glob('*/*/*.md')]

    # Replace the names of the book abbreviation folders with the book number
    numberedMDFilenameList = []
    for x in mdFilepathList:
        b = x.split('/')[0]
        bup = b.upper()
        newbook = books[bup][1]
        numberedMDFilenameList.append(x.replace(b, newbook))
        books_nums[newbook] = bup
    numberedMDFilenameList.sort()
    print(f"  Found {len(numberedMDFilenameList):,} files")

    print(f"Loading {len(numberedMDFilenameList):,} markdown files…")
    for f in numberedMDFilenameList:
        tn_checks = convertMarkdownToList(f, tn_checks)
    print(f"  Loaded {len(numberedMDFilenameList):,} files")

    print("Combining and creating output files…")
    for BBB,noteList in tn_checks.items():
        enTSVtable = loadEnglishTSV(BBB)
        saveToTSV(languageCode, BBB, noteList, enTSVtable)
