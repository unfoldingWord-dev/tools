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
import logging
import re
import glob
import string
import random
from pathlib import Path

# Set the following to true or false
# If true, a GL file like 01.md contains questions for the CHUNK starting at v1
# If false, 01.md contains questions only for v1
IS_GL_CHUNKS = False

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


def convertMarkdownToList(adjustedFilepath, tn_checks):
    """
    Iterates through each verse file
    """
    # print(f"convertMarkdownToList {f}…")
    b, c, v = adjustedFilepath.rstrip('.md').split('/')
    if c == '00':
        c = 'front'
    adjustedFilepath = adjustedFilepath.replace(b, books_nums[b], 1).lower()
    b = books_nums[b]
    if not b in tn_checks:
        tn_checks[b] = [['Book', 'Chapter', 'Verse', 'ID', 'SupportReference',
                         'OrigQuote', 'Occurrence', 'GLQuote',  'OccurrenceNote']]
    if v == '00':
        # This is an introduction, which has a different format than a regular note
        if not os.path.exists(adjustedFilepath):
            adjustedFilepath = adjustedFilepath.replace('/00/00.md','/front/intro.md')
            adjustedFilepath = adjustedFilepath.replace('/00.md','/intro.md')
        with open(adjustedFilepath, 'r', encoding='utf-8') as mdFile:
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
    with open(adjustedFilepath, 'r', encoding='utf-8') as mdFile:
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
                except UnboundLocalError as e:
                    print(f"ERROR: {b} {c}:{v} {line} gave {e} -- does this mean bad formatting (e.g., missing #) in {adjustedFilepath}???")
    return tn_checks


def saveToTSV(languageCode:str, BBB:str, glData, enTSVData:List[list]) -> None:
    """
    Merges the GL notes into the English notes
        thus transforming from 9 columns to 11 columns
        for manually editing.

    NOTE: In some cases, the GL numbers represent chunks,
            i.e., Gen 1:1 means the chunk starting at 1:1 and covering multiple verses until the next chunk.
          In some cases, the GL numbers represent the actual verse numbers.
          We handle that simply with a global IS_GL_CHUNKS flag.
    """
    tn_check_filename = f'{languageCode}_tn_{books[BBB][1]}-{BBB}.tsv'
    print(f"  Processing {BBB} by {'chunk' if IS_GL_CHUNKS else 'verse'} for {tn_check_filename}…")
    combinedCount = enOnlyCount = glChunkInsertCount = combinedChunkCount = glVerseInsertCount = glLeftOverCount = 0
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
                break # all done

            # See if we're just looping without progressing
            if enIndex==lastEnIndex and glIndex==lastGlIndex: # infinite loop???
                logging.critical("PROGRAM LOGIC ERROR: We seem to be looping infinitely!!!!")
                break
            lastEnIndex, lastGlIndex = enIndex, glIndex

            # Get next two lots of EN fields
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
                        logging.error(f"en {enBBB} seems to have chapter {enCint} AFTER {lastEnCint}")
                    elif enCint > lastEnCint:
                        lastEnVint = 0
                    if enVint < lastEnVint:
                        logging.error(f"en {enBBB} {enC} seems to have verse {enVint} AFTER {lastEnVint}")
                    enX = enCint*1000 + enVint # Gives us a single int representing C:V (that we can compare easily)
            else: # Must be already finished the English
                # enCint, enVint = 999, 999
                enFields = None

            # Uncomment this if need to know the next GL C:V that's coming
            # if enIndex+1 < len(enTSVData):
            #     nextEnFields = enTSVData[enIndex+1]
            #     assert len(nextEnFields) == 9
            #     _enBBB2, enC2, enV2 = nextEnFields[:3]
            #     if enC2 == 'front': enC2 = '0'
            #     if enV2 == 'intro': enV2 = '0'
            #     enCint2, enVint2 = int(enC2), int(enV2)
            # else: # No more English following
            #     enCint2, enVint2 = 999, 999
            # enX2 = enCint2*1000 + enVint2

            # Get next two lots of GL fields
            if glIndex < len(glData):
                glFields = glData[glIndex]
                assert len(glFields) == 9
                glBBB, glC, glV = glFields[:3]
                glC = glC.lstrip('0')
                glV = glV.lstrip('0')
                # print(f"  Got {languageCode} {glBBB} {glC}:{glV}")
                assert glBBB == BBB
                if glC == 'front': glC = '0'
                if glV == 'intro': glV = '0'
                glCint = int(glC)
                try:
                    glVint = int(glV)
                except ValueError:
                    print(f"{glBBB} what is {glC}:{glV} ??? {glFields}")
                    glVint = 0
                if glCint < lastGlCint:
                    logging.error(f"{languageCode} {glBBB} seems to have chapter {glCint} AFTER {lastGlCint}")
                elif glCint > lastGlCint:
                    lastGlVint = 0
                if glVint < lastGlVint:
                    logging.error(f"{languageCode} {glBBB} {glC} seems to have verse {glVint} AFTER {lastGlVint}")
            else: # Must be already finished the GL records
                glCint, glVint = 999, 999
                glFields = None
            glX = glCint*1000 + glVint

            if glIndex+1 < len(glData): # Get the following one also so we know what's coming next
                nextGLfields = glData[glIndex+1]
                assert len(nextGLfields) == 9
                _glBBB2, glC2, glV2 = nextGLfields[:3]
                glC2 = glC2.lstrip('0')
                glV2 = glV2.lstrip('0')
                if glC2 == 'front': glC2 = '0'
                if glV2 == 'intro': glV2 = '0'
                glCint2 = int(glC2)
                try:
                    glVint2 = int(glV2)
                except ValueError:
                    # print(f"{glBBB2} what is {glC2}:{glV2} ??? {nextGLfields2}")
                    glVint2 = 0
            else: # No more GL following
                glCint2, glVint2 = 999, 999
            glX2 = glCint2*1000 + glVint2

            # Ok, now we have all the information we need
            # This is the control logic for everything apart from writing the header row (above)
            if enFields:
                if glX==enX: # that's easy -- we're at matching C:Vs
                    enFields.append(glFields[7]) # GL Quote
                    enFields.append(glFields[8]) # Occurrence Note
                    # print(f"Writing matching combined {len(enFields)} {enFields}")
                    assert len(enFields) == 11
                    writer.write(f'{TAB.join(enFields)}\n')
                    enIndex += 1 # Used that one now
                    glIndex += 1 # Used that one now
                    combinedCount += 1
                    continue

                if glX > enX:
                    # If we get here, didn't have GL fields to append, so write our en fields only
                    assert len(enFields) == 9
                    enFields.append('') # } pad out to 11 fields
                    enFields.append('') # }
                    # print(f"Writing en only {len(enFields)} {enFields}")
                    assert len(enFields) == 11
                    writer.write(f'{TAB.join(enFields)}\n')
                    enIndex += 1 # Used that one
                    enFields = None
                    enOnlyCount += 1
                    continue

                if glX < enX: # English has gone past, but GL might be in chunks
                    if IS_GL_CHUNKS: # (c.f verses)
                        if enX > glX2: # English is into the next chunk already
                            # print(f"Gone past ({enC}:{enV}={enX} vs {glC}:{glV}={glX}")
                            # We need to add a line to the table
                            newRow = [BBB,glC,glV,glFields[3],glFields[4],glFields[5],glFields[6],'','', glFields[7], glFields[8]]
                            # print(f"    Inserting chunk new glRow: {newRow}")
                            assert len(newRow) == 11
                            writer.write(f'{TAB.join(newRow)}\n')
                            glIndex += 1 # Used that one now
                            glChunkInsertCount += 1
                            continue
                        else: # all ok
                            enFields.append(glFields[7]) # GL Quote
                            enFields.append(glFields[8]) # Occurrence Note
                            # print(f"    Writing chunked combined {len(enFields)} {enFields}")
                            assert len(enFields) == 11
                            writer.write(f'{TAB.join(enFields)}\n')
                            enIndex += 1 # Used that one now
                            glIndex += 1 # Used that one now
                            combinedChunkCount += 1
                            continue
                    else: # in verses (not chunks)
                        # print(f"Gone past ({enC}:{enV}={enX} vs {glC}:{glV}={glX}")
                        # We need to add a line to the table
                        newRow = [BBB,glC,glV,glFields[3],glFields[4],glFields[5],glFields[6],'','', glFields[7], glFields[8]]
                        # print(f"    Inserting verse new glRow: {newRow}")
                        assert len(newRow) == 11
                        writer.write(f'{TAB.join(newRow)}\n')
                        glIndex += 1 # Used that one now
                        glVerseInsertCount += 1
                        continue
                # If we get here, we didn't write anything
                logging.critical(f"PROGRAMMING LOGIC ERROR: have enFields with enX={enX} and glX={glX}")

            if glFields: # We have a left over
                assert not enFields
                if glX < enX:
                    logging.error(f"SEEMS OUT OF ORDER: {BBB} gl {glC}:{glV} AFTER en {enC}:{enV}")
                newRow = [BBB,glC,glV,glFields[3],glFields[4],glFields[5],glFields[6],'','', glFields[7], glFields[8]]
                # print(f"    Appending new glRow: {newRow}")
                assert len(newRow) == 11
                writer.write(f'{TAB.join(newRow)}\n')
                glIndex += 1 # Used that one now
                glLeftOverCount += 1
                continue

            # If we get to the bottom of the loop here, we didn't write anything
            logging.critical(f"PROGRAMMING LOGIC ERROR: reached end of loop with enX={enX} and glX={glX}")

    if enIndex != len(enTSVData):
        logging.critical(f"Something went wrong: en has {enIndex} instead of {len(enTSVData)}")
    if glIndex != len(glData):
        logging.critical(f"Something went wrong: {languageCode} has {glIndex} instead of {len(glData)}")

    # Give some statistics
    print(f"    combinedBoth={combinedCount:,} EngOnly={enOnlyCount}"
          f"{' glChunkInserts='+str(glChunkInsertCount) if glChunkInsertCount else ''}"
          f"{' combinedChunkRows='+str(combinedChunkCount) if combinedChunkCount else ''}"
          f"{' GLVerseInserts='+str(glVerseInsertCount) if glVerseInsertCount else ''}"
          f"{' GLAddedToEnd='+str(glLeftOverCount) if glLeftOverCount else ''}")
# end of saveToTSV function


def main():
    cwd = os.getcwd()
    basename = os.path.basename(cwd)
    print(f"Trying to determine language code (from '{basename}' folder name)…")
    languageCode = basename.split('_',1)[0]
    print(f"  Found {languageCode!r}")

    print("Discovering markdown files…")
    tn_checks = {}
    mdFilepathList = [x for x in glob.glob('*/*/*.md')]

    # Replace the names of the book abbreviation folders with the book number
    numberedMDFilenameList = []
    for actualFilepath in mdFilepathList:
        if 'index' in actualFilepath:
            logging.warning(f"Skipping unexpected GL {actualFilepath}")
            continue
        bbb = actualFilepath.split('/')[0]
        BBB = bbb.upper()
        bookNumber = books[BBB][1]
        adjustedFilepath = actualFilepath.replace(bbb, bookNumber) \
                                .replace('front','00').replace('intro','00') # so they sort correctly
        numberedMDFilenameList.append(adjustedFilepath)
        books_nums[bookNumber] = BBB
    numberedMDFilenameList.sort()
    print(f"  Found {len(numberedMDFilenameList):,} files")

    print(f"Loading {len(numberedMDFilenameList):,} markdown files…")
    for f in numberedMDFilenameList:
        tn_checks = convertMarkdownToList(f, tn_checks)
    print(f"  Loaded markdown files for {len(tn_checks)} book(s)")

    print("Combining and creating output files…")
    for BBB,noteList in tn_checks.items():
        enTSVtable = loadEnglishTSV(BBB)
        saveToTSV(languageCode, BBB, noteList, enTSVtable)
# end of main()

if __name__ == '__main__':
    print("convertGLtoTSVlink.py v0.5.1")

    if IS_GL_CHUNKS: mdIs, mdNot = 'CHUNK', 'each verse'
    else: mdIs, mdNot = 'VERSE', 'chunk'
    print(f"\nAssuming that the markdown files are separated by {mdIs} (not by {mdNot}).\n")

    main()
