#!/usr/bin/env python3
#
# TQ_MD_to_TSV7.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2021-09-03 by RJH
#
"""
Quick script to copy TQ from markdown files
    and put into a TSV file with the new format (7 columns).

The script assumes local clones of DCS repos -- it doesn't use internet.

Note that each run of this script tries to read any existing TSV files
    so that it can reuse the same ID fields where possible.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import logging


LANGUAGE_CODE = 'en'
# LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/DCS_dataRepos/RepoConversions/')
# LANGUAGE_CODE = 'ru'
# LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/Door43-Catalog_repos/')

LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_tq/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_tq2/')

BBB_NUMBER_DICT = {'GEN':'01','EXO':'02','LEV':'03','NUM':'04','DEU':'05',
                'JOS':'06','JDG':'07','RUT':'08','1SA':'09','2SA':'10','1KI':'11',
                '2KI':'12','1CH':'13','2CH':'14','EZR':'15',
                'NEH':'16',
                'EST':'17',
                'JOB':'18','PSA':'19','PRO':'20','ECC':'21','SNG':'22','ISA':'23',
                'JER':'24','LAM':'25','EZK':'26','DAN':'27','HOS':'28','JOL':'29',
                'AMO':'30','OBA':'31','JON':'32','MIC':'33','NAM':'34','HAB':'35',
                'ZEP':'36','HAG':'37','ZEC':'38','MAL':'39',
                'MAT':'41','MRK':'42','LUK':'43','JHN':'44','ACT':'45',
                'ROM':'46','1CO':'47','2CO':'48','GAL':'49','EPH':'50','PHP':'51',
                'COL':'52','1TH':'53','2TH':'54','1TI':'55','2TI':'56','TIT':'57',
                'PHM':'58','HEB':'59','JAS':'60','1PE':'61','2PE':'62','1JN':'63',
                '2JN':'64',
                '3JN':'65', 'JUD':'66', 'REV':'67' }

BOOK_INFO_DICT = { "gen": {"id": "gen", "title": "Genesis", "usfm": "01-GEN", "testament": "old", "verseCount": 1533, "chapters": [31, 25, 24, 26, 32, 22, 24, 22, 29, 32, 32, 20, 18, 24, 21, 16, 27, 33, 38, 18, 34, 24, 20, 67, 34, 35, 46, 22, 35, 43, 55, 32, 20, 31, 29, 43, 36, 30, 23, 23, 57, 38, 34, 34, 28, 34, 31, 22, 33, 26]},
  "exo": {"id": "exo", "title": "Exodus", "usfm": "02-EXO", "testament": "old", "verseCount": 1213, "chapters": [22, 25, 22, 31, 23, 30, 25, 32, 35, 29, 10, 51, 22, 31, 27, 36, 16, 27, 25, 26, 36, 31, 33, 18, 40, 37, 21, 43, 46, 38, 18, 35, 23, 35, 35, 38, 29, 31, 43, 38]},
  "lev": {"id": "lev", "title": "Leviticus", "usfm": "03-LEV", "testament": "old", "verseCount": 859, "chapters": [17, 16, 17, 35, 19, 30, 38, 36, 24, 20, 47, 8, 59, 57, 33, 34, 16, 30, 37, 27, 24, 33, 44, 23, 55, 46, 34]},
  "num": {"id": "num", "title": "Numbers", "usfm": "04-NUM", "testament": "old", "verseCount": 1288, "chapters": [54, 34, 51, 49, 31, 27, 89, 26, 23, 36, 35, 16, 33, 45, 41, 50, 13, 32, 22, 29, 35, 41, 30, 25, 18, 65, 23, 31, 40, 16, 54, 42, 56, 29, 34, 13]},
  "deu": {"id": "deu", "title": "Deuteronomy", "usfm": "05-DEU", "testament": "old", "verseCount": 959, "chapters": [46, 37, 29, 49, 33, 25, 26, 20, 29, 22, 32, 32, 18, 29, 23, 22, 20, 22, 21, 20, 23, 30, 25, 22, 19, 19, 26, 68, 29, 20, 30, 52, 29, 12]},
  "jos": {"id": "jos", "title": "Joshua", "usfm": "06-JOS", "testament": "old", "verseCount": 658, "chapters": [18, 24, 17, 24, 15, 27, 26, 35, 27, 43, 23, 24, 33, 15, 63, 10, 18, 28, 51, 9, 45, 34, 16, 33]},
  "jdg": {"id": "jdg", "title": "Judges", "usfm": "07-JDJ", "testament": "old", "verseCount": 618, "chapters": [36, 23, 31, 24, 31, 40, 25, 35, 57, 18, 40, 15, 25, 20, 20, 31, 13, 31, 30, 48, 25]},
  "rut": {"id": "rut", "title": "Ruth", "usfm": "08-RUT", "testament": "old", "verseCount": 85, "chapters": [22, 23, 18, 22]},
  "1sa": {"id": "1sa", "title": "1 Samuel", "usfm": "09-1SA", "testament": "old", "verseCount": 810, "chapters": [28, 36, 21, 22, 12, 21, 17, 22, 27, 27, 15, 25, 23, 52, 35, 23, 58, 30, 24, 42, 15, 23, 29, 22, 44, 25, 12, 25, 11, 31, 13]},
  "2sa": {"id": "2sa", "title": "2 Samuel", "usfm": "10-2SA", "testament": "old", "verseCount": 695, "chapters": [27, 32, 39, 12, 25, 23, 29, 18, 13, 19, 27, 31, 39, 33, 37, 23, 29, 33, 43, 26, 22, 51, 39, 25]},
  "1ki": {"id": "1ki", "title": "1 Kings", "usfm": "11-1KI", "testament": "old", "verseCount": 816, "chapters": [53, 46, 28, 34, 18, 38, 51, 66, 28, 29, 43, 33, 34, 31, 34, 34, 24, 46, 21, 43, 29, 53]},
  "2ki": {"id": "2ki", "title": "2 Kings", "usfm": "12-2KI", "testament": "old", "verseCount": 719, "chapters": [18, 25, 27, 44, 27, 33, 20, 29, 37, 36, 21, 21, 25, 29, 38, 20, 41, 37, 37, 21, 26, 20, 37, 20, 30]},
  "1ch": {"id": "1ch", "title": "1 Chronicles", "usfm": "13-1CH", "testament": "old", "verseCount": 942, "chapters": [54, 55, 24, 43, 26, 81, 40, 40, 44, 14, 47, 40, 14, 17, 29, 43, 27, 17, 19, 8, 30, 19, 32, 31, 31, 32, 34, 21, 30]},
  "2ch": {"id": "2ch", "title": "2 Chronicles", "usfm": "14-2CH", "testament": "old", "verseCount": 822, "chapters": [17, 18, 17, 22, 14, 42, 22, 18, 31, 19, 23, 16, 22, 15, 19, 14, 19, 34, 11, 37, 20, 12, 21, 27, 28, 23, 9, 27, 36, 27, 21, 33, 25, 33, 27, 23]},
  "ezr": {"id": "ezr", "title": "Ezra", "usfm": "15-EZR", "testament": "old", "verseCount": 280, "chapters": [11, 70, 13, 24, 17, 22, 28, 36, 15, 44]},
  "neh": {"id": "neh", "title": "Nehemiah", "usfm": "16-NEH", "testament": "old", "verseCount": 406, "chapters": [11, 20, 32, 23, 19, 19, 73, 18, 38, 39, 36, 47, 31]},
  "est": {"id": "est", "title": "Esther", "usfm": "17-EST", "testament": "old", "verseCount": 167, "chapters": [22, 23, 15, 17, 14, 14, 10, 17, 32, 3]},
  "job": {"id": "job", "title": "Job", "usfm": "18-JOB", "testament": "old", "verseCount": 1070, "chapters": [22, 13, 26, 21, 27, 30, 21, 22, 35, 22, 20, 25, 28, 22, 35, 22, 16, 21, 29, 29, 34, 30, 17, 25, 6, 14, 23, 28, 25, 31, 40, 22, 33, 37, 16, 33, 24, 41, 30, 24, 34, 17]},
  "psa": {"id": "psa", "title": "Psalms", "usfm": "19-PSA", "testament": "old", "verseCount": 2461, "chapters": [6, 12, 8, 8, 12, 10, 17, 9, 20, 18, 7, 8, 6, 7, 5, 11, 15, 50, 14, 9, 13, 31, 6, 10, 22, 12, 14, 9, 11, 12, 24, 11, 22, 22, 28, 12, 40, 22, 13, 17, 13, 11, 5, 26, 17, 11, 9, 14, 20, 23, 19, 9, 6, 7, 23, 13, 11, 11, 17, 12, 8, 12, 11, 10, 13, 20, 7, 35, 36, 5, 24, 20, 28, 23, 10, 12, 20, 72, 13, 19, 16, 8, 18, 12, 13, 17, 7, 18, 52, 17, 16, 15, 5, 23, 11, 13, 12, 9, 9, 5, 8, 28, 22, 35, 45, 48, 43, 13, 31, 7, 10, 10, 9, 8, 18, 19, 2, 29, 176, 7, 8, 9, 4, 8, 5, 6, 5, 6, 8, 8, 3, 18, 3, 3, 21, 26, 9, 8, 24, 13, 10, 7, 12, 15, 21, 10, 20, 14, 9, 6]},
  "pro": {"id": "pro", "title": "Proverbs", "usfm": "20-PRO", "testament": "old", "verseCount": 915, "chapters": [33, 22, 35, 27, 23, 35, 27, 36, 18, 32, 31, 28, 25, 35, 33, 33, 28, 24, 29, 30, 31, 29, 35, 34, 28, 28, 27, 28, 27, 33, 31]},
  "ecc": {"id": "ecc", "title": "Ecclesiastes", "usfm": "21-ECC", "testament": "old", "verseCount": 222, "chapters": [18, 26, 22, 16, 20, 12, 29, 17, 18, 20, 10, 14]},
  "sng": {"id": "sng", "title": "Song of Songs", "usfm": "22-SNG", "testament": "old", "verseCount": 117, "chapters": [17, 17, 11, 16, 16, 13, 13, 14]},
  "isa": {"id": "isa", "title": "Isaiah", "usfm": "23-ISA", "testament": "old", "verseCount": 1292, "chapters": [31, 22, 26, 6, 30, 13, 25, 22, 21, 34, 16, 6, 22, 32, 9, 14, 14, 7, 25, 6, 17, 25, 18, 23, 12, 21, 13, 29, 24, 33, 9, 20, 24, 17, 10, 22, 38, 22, 8, 31, 29, 25, 28, 28, 25, 13, 15, 22, 26, 11, 23, 15, 12, 17, 13, 12, 21, 14, 21, 22, 11, 12, 19, 12, 25, 24]},
  "jer": {"id": "jer", "title": "Jeremiah", "usfm": "24-JER", "testament": "old", "verseCount": 1364, "chapters": [19, 37, 25, 31, 31, 30, 34, 22, 26, 25, 23, 17, 27, 22, 21, 21, 27, 23, 15, 18, 14, 30, 40, 10, 38, 24, 22, 17, 32, 24, 40, 44, 26, 22, 19, 32, 21, 28, 18, 16, 18, 22, 13, 30, 5, 28, 7, 47, 39, 46, 64, 34]},
  "lam": {"id": "lam", "title": "Lamentations", "usfm": "25-LAM", "testament": "old", "verseCount": 154, "chapters": [22, 22, 66, 22, 22]},
  "ezk": {"id": "ezk", "title": "Ezekiel", "usfm": "26-EZK", "testament": "old", "verseCount": 1273, "chapters": [28, 10, 27, 17, 17, 14, 27, 18, 11, 22, 25, 28, 23, 23, 8, 63, 24, 32, 14, 49, 32, 31, 49, 27, 17, 21, 36, 26, 21, 26, 18, 32, 33, 31, 15, 38, 28, 23, 29, 49, 26, 20, 27, 31, 25, 24, 23, 35]},
  "dan": {"id": "dan", "title": "Daniel", "usfm": "27-DAN", "testament": "old", "verseCount": 357, "chapters": [21, 49, 30, 37, 31, 28, 28, 27, 27, 21, 45, 13]},
  "hos": {"id": "hos", "title": "Hosea", "usfm": "28-HOS", "testament": "old", "verseCount": 197, "chapters": [11, 23, 5, 19, 15, 11, 16, 14, 17, 15, 12, 14, 16, 9]},
  "jol": {"id": "jol", "title": "Joel", "usfm": "29-JOL", "testament": "old", "verseCount": 73, "chapters": [20, 32, 21]},
  "amo": {"id": "amo", "title": "Amos", "usfm": "30-AMO", "testament": "old", "verseCount": 146, "chapters": [15, 16, 15, 13, 27, 14, 17, 14, 15]},
  "oba": {"id": "oba", "title": "Obadiah", "usfm": "31-OBA", "testament": "old", "verseCount": 21, "chapters": [21]},
  "jon": {"id": "jon", "title": "Jonah", "usfm": "32-JON", "testament": "old", "verseCount": 48, "chapters": [17, 10, 10, 11]},
  "mic": {"id": "mic", "title": "Micah", "usfm": "33-MIC", "testament": "old", "verseCount": 105, "chapters": [16, 13, 12, 13, 15, 16, 20]},
  "nam": {"id": "nam", "title": "Nahum", "usfm": "34-NAM", "testament": "old", "verseCount": 47, "chapters": [15, 13, 19]},
  "hab": {"id": "hab", "title": "Habakkuk", "usfm": "35-HAB", "testament": "old", "verseCount": 56, "chapters": [17, 20, 19]},
  "zep": {"id": "zep", "title": "Zephaniah", "usfm": "36-ZEP", "testament": "old", "verseCount": 53, "chapters": [18, 15, 20]},
  "hag": {"id": "hag", "title": "Haggai", "usfm": "37-HAG", "testament": "old", "verseCount": 38, "chapters": [15, 23]},
  "zec": {"id": "zec", "title": "Zechariah", "usfm": "38-ZEC", "testament": "old", "verseCount": 211, "chapters": [21, 13, 10, 14, 11, 15, 14, 23, 17, 12, 17, 14, 9, 21]},
  "mal": {"id": "mal", "title": "Malachi", "usfm": "39-MAL", "testament": "old", "verseCount": 55, "chapters": [14, 17, 18, 6]},
  "mat": {"id": "mat", "title": "Matthew", "usfm": "41-MAT", "testament": "new", "verseCount": 1071, "chapters": [25, 23, 17, 25, 48, 34, 29, 34, 38, 42, 30, 50, 58, 36, 39, 28, 27, 35, 30, 34, 46, 46, 39, 51, 46, 75, 66, 20]},
  "mrk": {"id": "mrk", "title": "Mark", "usfm": "42-MRK", "testament": "new", "verseCount": 678, "chapters": [45, 28, 35, 41, 43, 56, 37, 38, 50, 52, 33, 44, 37, 72, 47, 20]},
  "luk": {"id": "luk", "title": "Luke", "usfm": "43-LUK", "testament": "new", "verseCount": 1151, "chapters": [80, 52, 38, 44, 39, 49, 50, 56, 62, 42, 54, 59, 35, 35, 32, 31, 37, 43, 48, 47, 38, 71, 56, 53]},
  "jhn": {"id": "jhn", "title": "John", "usfm": "44-JHN", "testament": "new", "verseCount": 879, "chapters": [51, 25, 36, 54, 47, 71, 53, 59, 41, 42, 57, 50, 38, 31, 27, 33, 26, 40, 42, 31, 25]},
  "act": {"id": "act", "title": "Acts", "usfm": "45-ACT", "testament": "new", "verseCount": 1007, "chapters": [26, 47, 26, 37, 42, 15, 60, 40, 43, 48, 30, 25, 52, 28, 41, 40, 34, 28, 41, 38, 40, 30, 35, 27, 27, 32, 44, 31]},
  "rom": {"id": "rom", "title": "Romans", "usfm": "46-ROM", "testament": "new", "verseCount": 433, "chapters": [32, 29, 31, 25, 21, 23, 25, 39, 33, 21, 36, 21, 14, 23, 33, 27]},
  "1co": {"id": "1co", "title": "1 Corinthians", "usfm": "47-1CO", "testament": "new", "verseCount": 437, "chapters": [31, 16, 23, 21, 13, 20, 40, 13, 27, 33, 34, 31, 13, 40, 58, 24]},
  "2co": {"id": "2co", "title": "2 Corinthians", "usfm": "48-2CO", "testament": "new", "verseCount": 257, "chapters": [24, 17, 18, 18, 21, 18, 16, 24, 15, 18, 33, 21, 14]},
  "gal": {"id": "gal", "title": "Galatians", "usfm": "49-GAL", "testament": "new", "verseCount": 149, "chapters": [24, 21, 29, 31, 26, 18]},
  "eph": {"id": "eph", "title": "Ephesians", "usfm": "50-EPH", "testament": "new", "verseCount": 155, "chapters": [23, 22, 21, 32, 33, 24]},
  "php": {"id": "php", "title": "Philippians", "usfm": "51-PHP", "testament": "new", "verseCount": 104, "chapters": [30, 30, 21, 23]},
  "col": {"id": "col", "title": "Colossians", "usfm": "52-COL", "testament": "new", "verseCount": 95, "chapters": [29, 23, 25, 18]},
  "1th": {"id": "1th", "title": "1 Thessalonians", "usfm": "53-1TH", "testament": "new", "verseCount": 89, "chapters": [10, 20, 13, 18, 28]},
  "2th": {"id": "2th", "title": "2 Thessalonians", "usfm": "54-2TH", "testament": "new", "verseCount": 47, "chapters": [12, 17, 18]},
  "1ti": {"id": "1ti", "title": "1 Timothy", "usfm": "55-1TI", "testament": "new", "verseCount": 113, "chapters": [20, 15, 16, 16, 25, 21]},
  "2ti": {"id": "2ti", "title": "2 Timothy", "usfm": "56-2TI", "testament": "new", "verseCount": 83, "chapters": [18, 26, 17, 22]},
  "tit": {"id": "tit", "title": "Titus", "usfm": "57-TIT", "testament": "new", "verseCount": 46, "chapters": [16, 15, 15]},
  "phm": {"id": "phm", "title": "Philemon", "usfm": "58-PHM", "testament": "new", "verseCount": 25, "chapters": [25]},
  "heb": {"id": "heb", "title": "Hebrews", "usfm": "59-HEB", "testament": "new", "verseCount": 303, "chapters": [14, 18, 19, 16, 14, 20, 28, 13, 28, 39, 40, 29, 25]},
  "jas": {"id": "jas", "title": "James", "usfm": "60-JAS", "testament": "new", "verseCount": 108, "chapters": [27, 26, 18, 17, 20]},
  "1pe": {"id": "1pe", "title": "1 Peter", "usfm": "61-1PE", "testament": "new", "verseCount": 105, "chapters": [25, 25, 22, 19, 14]},
  "2pe": {"id": "2pe", "title": "2 Peter", "usfm": "62-2PE", "testament": "new", "verseCount": 61, "chapters": [21, 22, 18]},
  "1jn": {"id": "1jn", "title": "1 John", "usfm": "63-1JN", "testament": "new", "verseCount": 105, "chapters": [10, 29, 24, 21, 21]},
  "2jn": {"id": "2jn", "title": "2 John", "usfm": "64-2JN", "testament": "new", "verseCount": 13, "chapters": [13]},
  "3jn": {"id": "3jn", "title": "3 John", "usfm": "65-3JN", "testament": "new", "verseCount": 15, "chapters": [15]},
  "jud": {"id": "jud", "title": "Jude", "usfm": "66-JUD", "testament": "new", "verseCount": 25, "chapters": [25]},
  "rev": {"id": "rev", "title": "Revelation", "usfm": "67-REV", "testament": "new", "verseCount": 404, "chapters": [20, 29, 22, 11, 14, 17, 17, 13, 21, 11, 19, 17, 18, 20, 8, 21, 18, 24, 21, 15, 27, 21]}
}


def get_source_questions(BBB:str, nn:str) -> Tuple[str,str,str,str,str]:
    """
    Generator to read the TQ markdown files
        and return questions and responses.

    Returns a 5-tuple with:
        BBB C V (reference strings)
        question response (strings)
    """
    bbb = BBB.lower()
    source_folderpath = LOCAL_SOURCE_FOLDERPATH.joinpath(f'{bbb}/')
    print(f"      Getting source lines from {source_folderpath}…")

    book_info_line = BOOK_INFO_DICT[bbb]
    verses_per_chapter = book_info_line['chapters']

    for C in range(1, len(verses_per_chapter)+1):
        for V in range(1, verses_per_chapter[C-1]+1):
            filepath = source_folderpath.joinpath(str(C).zfill(2), f'{str(V).zfill(2)}.md')
            if os.path.exists(filepath):
                # print(f"Found {filepath}")
                pass
            else:
                # print(f"Not found {filepath}")
                continue

            state = 'Waiting for question'
            question = response = None
            with open(filepath, 'rt') as mdFile:
                for line_number,line in enumerate(mdFile, start=1):
                    line = line.rstrip() # Remove trailing whitespace including nl char
                    # print(f"  line={line}")
                    if not line:
                        if state == 'Got answer':
                            state = 'Waiting for question'
                        else:
                            assert state == 'Waiting for answer', f"Didn't expect blank line in {filepath} at state '{state}'"
                        continue # Ignore blank lines
                    if line.startswith('# '):
                        if state == 'Waiting for question':
                            if question and response: # We already have a question
                                yield BBB,C,V, question,response
                                question = response = None
                            assert not question
                            assert not response
                            question, response = line[2:], None
                            state = 'Waiting for answer'
                            continue
                        else: programmer_error
                    elif state == 'Waiting for answer':
                        assert question
                        assert not response
                        response = line
                        state = 'Got answer'
                    else:
                        if state == 'Got answer':
                            response = f'{response} {line}' # Append continuer line
                        else:
                            logging.error(f"Losing {filepath} line {line_number}: '{line}' at state '{state}'");
            if response:
                assert question
                yield BBB,C,V, question,response
# end of get_source_questions function


def make_TSV_file(BBB:str, nn:str) -> int:
    """
    Function to assemble 7-column TSV rows and output them.

    If consecutive verses have an identical question and answer, they're combined into a verse range

    Note that each row gets a newly generated ID field.
    """
    print(f"    Converting TQ {BBB} links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH #.joinpath(BBB)
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'tq_{BBB}.tsv')

    # Load the previous file so we can use the same row ID fields
    try:
        with open(output_filepath, 'rt') as previous_file:
            previous_text = previous_file.read()
        original_TSV_TQ_lines = previous_text.split('\n')
        # for j,line in enumerate(original_TSV_TQ_lines):
        #     print(f"{j+1}: '{line}'")
        original_TSV_TQ_lines = original_TSV_TQ_lines[1:] # Skip header row
        if not original_TSV_TQ_lines[-1]: original_TSV_TQ_lines = original_TSV_TQ_lines[:-1] # Skip last empty line
        print(f"      Loaded {len(original_TSV_TQ_lines):,} lines from previous version of {output_filepath}")
        # print(original_TSV_TQ_lines[:10])
    except Exception as e:
        if 'No such file' in str(e):
            print(f"      No existing file to preload row IDs: {output_filepath}")
        else:
            print(f"      Failed to load {output_filepath}: {e}")
        print(f"        Will generate all new row IDs!")
        original_TSV_TQ_lines = []

    def get_rowID(reference:str, tags:str, quote:str, occurrence:str, qr:str) -> str:
        """
        """
        # print(f"{BBB} get_rowID({reference}, {tags=}, {quote=}, {occurrence}, {qr=})…")
        question, response = qr.split('\t')
        found_id = None
        for old_line in original_TSV_TQ_lines:
            old_reference, old_id, old_tags, old_quote, old_occurrence, old_question, old_response = old_line.split('\t')
            # print(f"OLD {old_reference} {old_id} {old_tags} {old_quote} {old_occurrence} '{old_question}' '{old_response}'")
            if old_reference==reference and old_tags==tags and old_quote==quote and old_occurrence==occurrence \
            and old_question==question and old_response==response:
                found_id = old_id
                break
            # else:
            #     print(f"Ref '{old_reference}', '{reference}', {old_reference==reference}")
            #     print(f"Tags '{old_tags}', '{tags}', {old_tags==tags}")
            #     print(f"Quote '{old_quote}', '{quote}', {old_quote==quote}")
            #     print(f"Occurrence '{old_occurrence}', '{occurrence}', {old_occurrence==occurrence}")
            #     print(f"Question '{old_question}', '{question}', {old_question==question}")
            #     print(f"Response '{old_response}', '{response}', {old_response==response}")
        if found_id:
            # print(f"        Found {found_id} for {reference} {tags} {quote} {occurrence} {question} {response}")
            if found_id in previously_generated_ids:
                print(f"We had an error with {found_id} for {reference} {tags} {occurrence} {question} {response}!!!")
                halt
            # print(f"  Returning {found_id=}")
            return found_id
        else:
            generated_id = ''
            while generated_id in previously_generated_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previously_generated_ids.append(generated_id)
            if len(original_TSV_TQ_lines) > 0: # we don't print this message if we're generating ALL of the  new row IDs
                print(f"        Returning generated id for {BBB} {reference}: {generated_id} '{question}'")
            return generated_id
    #end of make_TSV_file.get_rowID function

    last_CV_reference = this_CV_reference = '0:0'
    last_verse_question_responses, this_verse_question_responses = [], []
    repeat_dict = {} # Key is QR, Value is list of consecutive references
    num_written_questions = num_with_ranges = 0
    tags = quote = occurrence = ''
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse\n')
        previously_generated_ids:List[str] = [''] # We make ours unique per file (spec only used to say unique per verse)
        for _j, (BBB,C,V,question,response) in enumerate(get_source_questions(BBB, nn), start=1):
            # print(f"{_j:3}/ {BBB} {C:>3}:{V:<3} '{question}' {response}")
            # print(f"    {last_verse_question_responses=} {this_verse_question_responses=} {repeat_dict=}")

            new_CV_reference = f'{C}:{V}'
            if new_CV_reference != this_CV_reference: # We're into a new verse
                # See if we need to write a question/response with a verse range
                for qr,refs in repeat_dict.copy().items():
                    if this_CV_reference not in refs:
                        q = qr.split('\t')[0]
                        # print(f"    Now heading into {BBB} {new_CV_reference} after {this_CV_reference}, need to write '{q[:20]}…' for {refs}")

                        # Just check that repeat questions didn't cross a chapter boundary (our code doesn't handle that yet)
                        refs_C = refs[0].split(':')[0]
                        for ref in refs[1:]: assert ref.split(':')[0] == refs_C # Should all be in the same chapter

                        range_CV_reference = f"{refs_C}:{refs[0].split(':')[-1]}-{refs[-1].split(':')[-1]}"
                        row_id = get_rowID(range_CV_reference, tags, quote, occurrence, qr)

                        output_line = f"{range_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
                        # print(f"      WriteA: {output_line}")
                        output_TSV_file.write(f'{output_line}\n')
                        num_written_questions += 1
                        num_with_ranges += 1
                        del repeat_dict[qr]
                        last_verse_question_responses.remove(qr) # So we don't get the last QR repeated again in the file
                # Write the QRs for the verse BEFORE the one just finished
                for qr in last_verse_question_responses:
                    if qr not in repeat_dict:
                        row_id = get_rowID(last_CV_reference, tags, quote, occurrence, qr)

                        output_line = f"{last_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
                        # print(f"      WriteB: {output_line}")
                        output_TSV_file.write(f'{output_line}\n')
                        num_written_questions += 1
                # Update our variables
                last_verse_question_responses = this_verse_question_responses
                this_verse_question_responses = []
                last_CV_reference = this_CV_reference
                this_CV_reference = new_CV_reference

            question = question.strip()
            response = response.strip()
            qr = f'{question}\t{response}'
            this_verse_question_responses.append(qr)
            if qr in last_verse_question_responses: # found the same question&response in at least two verses, but are they consecutive?
                lastV = int(last_CV_reference.split(':')[1])
                thisV = int(this_CV_reference.split(':')[1])
                if thisV == lastV+1: # they're consecutive
                    if qr not in repeat_dict: repeat_dict[qr] = [last_CV_reference]
                    repeat_dict[qr].append(this_CV_reference)
                    # print(f"    Got {BBB} repeated '{question[:20]}…' in {repeat_dict[qr]}")
                    # NOTE: this qr is also in this_verse_question_responses so output of that will have to be suppressed later
                # else: print(f"    {BBB } '{question[:20]}…' NOT in consecutive verses: {last_CV_reference} and {this_CV_reference}")
        # NOTE: I think that at least part of the EOF stuff below is unnecessary (will never execute) but never mind
        # if repeat_dict: print(f"  At end of {BBB} with {len(repeat_dict)} saved QRs: {repeat_dict}")
        # if last_verse_question_responses:
        #     print(f"    last_CV_reference = {last_CV_reference}")
        #     print(f"    Have {BBB} {len(last_verse_question_responses)} last_verse_question_responses: {last_verse_question_responses}")
        # if this_verse_question_responses:
        #     print(f"    this_CV_reference = {this_CV_reference}")
        #     print(f"    Have {BBB} {len(this_verse_question_responses)} this_verse_question_responses: {this_verse_question_responses}")

        # See if we need to write a question/response with a verse range
        for qr,refs in repeat_dict.copy().items():
            if this_CV_reference not in refs:
                q = qr.split('\t')[0]
                # print(f"    Now heading into {BBB} end after {this_CV_reference}, need to write '{q[:20]}…' for {refs}")

                # Just check that repeat questions didn't cross a chapter boundary (our code doesn't handle that yet)
                refs_C = refs[0].split(':')[0]
                for ref in refs[1:]: assert ref.split(':')[0] == refs_C # Should all be in the same chapter

                range_CV_reference = f"{refs_C}:{refs[0].split(':')[-1]}-{refs[-1].split(':')[-1]}"
                row_id = get_rowID(range_CV_reference, tags, quote, occurrence, qr)

                output_line = f"{range_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
                # print(f"      WriteC: {output_line}")
                output_TSV_file.write(f'{output_line}\n')
                num_written_questions += 1
                num_with_ranges += 1
                del repeat_dict[qr]
                last_verse_question_responses.remove(qr) # So we don't get the last QR repeated again in the file

        # Write the QRs for the 2nd-to-last verse
        # print(f"  Have {BBB} {len(last_verse_question_responses)} last_verse_question_responses: {last_verse_question_responses}")
        for qr in last_verse_question_responses:
            if qr not in repeat_dict:
                row_id = get_rowID(last_CV_reference, tags, quote, occurrence, qr)

                output_line = f"{last_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
                # print(f"      WriteD: {output_line}")
                output_TSV_file.write(f'{output_line}\n')
                num_written_questions += 1

        # See if we need to write a question/response with a verse range
        for qr,refs in repeat_dict.copy().items():
            q = qr.split('\t')[0]
            # print(f"    Finally heading into {BBB} end after {this_CV_reference} after {last_CV_reference}, need to write '{q[:20]}…' for {refs}")

            # Just check that repeat questions didn't cross a chapter boundary (our code doesn't handle that yet)
            refs_C = refs[0].split(':')[0]
            for ref in refs[1:]: assert ref.split(':')[0] == refs_C # Should all be in the same chapter

            range_CV_reference = f"{refs_C}:{refs[0].split(':')[-1]}-{refs[-1].split(':')[-1]}"
            row_id = get_rowID(range_CV_reference, tags, quote, occurrence, qr)

            output_line = f"{range_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
            # print(f"      WriteE: {output_line}")
            output_TSV_file.write(f'{output_line}\n')
            num_written_questions += 1
            num_with_ranges += 1
            del repeat_dict[qr]
            this_verse_question_responses.remove(qr) # So we don't get the last QR repeated again in the file
        assert not repeat_dict # We haven't written code to handle repeat questions right near the end of the file

        # Write the QRs for the last verse
        # print(f"  Have {BBB} {len(this_verse_question_responses)} this_verse_question_responses: {this_verse_question_responses}")
        for qr in this_verse_question_responses:
            if qr not in repeat_dict:
                row_id = get_rowID(this_CV_reference, tags, quote, occurrence, qr)

                output_line = f"{this_CV_reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}"
                # print(f"      WriteZ: {output_line}")
                output_TSV_file.write(f'{output_line}\n')
                num_written_questions += 1

    aux_string = f" (including {num_with_ranges} with verse ranges)" if num_with_ranges else ''
    print(f"      {num_written_questions:,} TSV7 questions and response lines written{aux_string}")
    return num_written_questions
# end of make_TSV_file function


def main():
    """
    """
    print("TQ_MD_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_questions = 0
    for BBB,nn in BBB_NUMBER_DICT.items():
        # if BBB != '1TH': continue # Only process this one book
        question_count = make_TSV_file(BBB,nn)
        total_questions += question_count
    print(f"    {total_questions:,} total questions and responses written to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TQ_MD_to_TSV7.py
