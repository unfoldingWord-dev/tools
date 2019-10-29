#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>

"""
This script was used to convert the MD tN files to TSV format.
Ran on 2018-05-31, see https://git.door43.org/unfoldingWord/en_tn/pulls/1064
"""
import re
import glob
import codecs
import string
import random


# DONE
# * Clean intro files
#   * remove ## Links (vim)
#   * sed -i 's/ #*$//' */*/intro.md 
# * Rename intro files to 00-intro so they sort right
#   * $ for x in `find * -type f -name 'intro.md'`; do mv $x ${x%%intro.md}00.md; done

id_list = []
linkre = re.compile(ur'\[\[(.*?)\]\]', re.UNICODE)
books_nums = {}
books = {
          u'GEN': [ u'Genesis', '01' ],
          u'EXO': [ u'Exodus', '02' ],
          u'LEV': [ u'Leviticus', '03' ],
          u'NUM': [ u'Numbers', '04' ],
          u'DEU': [ u'Deuteronomy', '05' ],
          u'JOS': [ u'Joshua', '06' ],
          u'JDG': [ u'Judges', '07' ],
          u'RUT': [ u'Ruth', '08' ],
          u'1SA': [ u'1 Samuel', '09' ],
          u'2SA': [ u'2 Samuel', '10' ],
          u'1KI': [ u'1 Kings', '11' ],
          u'2KI': [ u'2 Kings', '12' ],
          u'1CH': [ u'1 Chronicles', '13' ],
          u'2CH': [ u'2 Chronicles', '14' ],
          u'EZR': [ u'Ezra', '15' ],
          u'NEH': [ u'Nehemiah', '16' ],
          u'EST': [ u'Esther', '17' ],
          u'JOB': [ u'Job', '18' ],
          u'PSA': [ u'Psalms', '19' ],
          u'PRO': [ u'Proverbs', '20' ],
          u'ECC': [ u'Ecclesiastes', '21' ],
          u'SNG': [ u'Song of Solomon', '22' ],
          u'ISA': [ u'Isaiah', '23' ],
          u'JER': [ u'Jeremiah', '24' ],
          u'LAM': [ u'Lamentations', '25' ],
          u'EZK': [ u'Ezekiel', '26' ],
          u'DAN': [ u'Daniel', '27' ],
          u'HOS': [ u'Hosea', '28' ],
          u'JOL': [ u'Joel', '29' ],
          u'AMO': [ u'Amos', '30' ],
          u'OBA': [ u'Obadiah', '31' ],
          u'JON': [ u'Jonah', '32' ],
          u'MIC': [ u'Micah', '33' ],
          u'NAM': [ u'Nahum', '34' ],
          u'HAB': [ u'Habakkuk', '35' ],
          u'ZEP': [ u'Zephaniah', '36' ],
          u'HAG': [ u'Haggai', '37' ],
          u'ZEC': [ u'Zechariah', '38' ],
          u'MAL': [ u'Malachi', '39' ],
          u'MAT': [ u'Matthew', '41' ],
          u'MRK': [ u'Mark', '42' ],
          u'LUK': [ u'Luke', '43' ],
          u'JHN': [ u'John', '44' ],
          u'ACT': [ u'Acts', '45' ],
          u'ROM': [ u'Romans', '46' ],
          u'1CO': [ u'1 Corinthians', '47' ],
          u'2CO': [ u'2 Corinthians', '48' ],
          u'GAL': [ u'Galatians', '49' ],
          u'EPH': [ u'Ephesians', '50' ],
          u'PHP': [ u'Philippians', '51' ],
          u'COL': [ u'Colossians', '52' ],
          u'1TH': [ u'1 Thessalonians', '53' ],
          u'2TH': [ u'2 Thessalonians', '54' ],
          u'1TI': [ u'1 Timothy', '55' ],
          u'2TI': [ u'2 Timothy', '56' ],
          u'TIT': [ u'Titus', '57' ],
          u'PHM': [ u'Philemon', '58' ],
          u'HEB': [ u'Hebrews', '59' ],
          u'JAS': [ u'James', '60' ],
          u'1PE': [ u'1 Peter', '61' ],
          u'2PE': [ u'2 Peter', '62' ],
          u'1JN': [ u'1 John', '63' ],
          u'2JN': [ u'2 John', '64' ],
          u'3JN': [ u'3 John', '65' ],
          u'JUD': [ u'Jude', '66' ],
          u'REV': [ u'Revelation', '67' ],
}

def getOLQuote(b, c, v, glquote):
    '''Eventually, look at alignment data and return occurrence num and orig quote'''
    # For now, return 0 to indicate not found
    return [u'0', u'']

def getNoteID():
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

def convertToList(f, tn_checks):
    '''Iterates through each verse file'''
    b, c, v = f.rstrip('.md').split('/')
    if c == u'00':
        c = u'front'
    f = f.replace(b, books_nums[b], 1).lower()
    b = books_nums[b]
    if not b in tn_checks:
        tn_checks[b] = [[u'Book', u'Chapter', u'Verse', u'ID', u'SupportReference',
                         u'OrigQuote', u'Occurrence', u'GLQuote',  u'OccurrenceNote']]
    if v in ['00']:
        # This is an introduction, which has a different format than a regular note
        for line in codecs.open(f, 'r', encoding='utf-8').readlines():
            if line.startswith(u'# '):
                ID = getNoteID()
                # We'll use the intro text for the ref
                ref = line.replace(u'#', u'').strip()
                olquote = u''
                occurrence = u'0'
                glquote = u''
                note_text = line.strip()
                continue
            # This is the note text
            note_text += line.strip()
            note_text += u'<br>'
        tn_checks[b].append([b, c, u'intro', ID, ref, olquote, occurrence, glquote, note_text])
        return tn_checks
    for line in codecs.open(f, 'r', encoding='utf-8').readlines():
        # This is the text snippet from the ULB
        if line.startswith(u'#'):
            ID = getNoteID()
            ref = u''
            glquote = line.strip(u'#').strip()
            occurrence, olquote = getOLQuote(b, c, v, glquote)
            continue
        # This is the note text (skips blank lines)
        if not line.startswith(u'\n'):
            note_text = line.strip()
            if u'/en/ta/' in note_text:
                if linkre.search(note_text):
                    ref = linkre.search(note_text).group(1).split('/')[-1]
            try:
                tn_checks[b].append([b, c, v, ID, ref, olquote, occurrence, glquote, note_text])
            except UnboundLocalError:
                print b, c, v, line
    return tn_checks

def saveToTSV(tsv_file, data):
    with codecs.open(tsv_file, 'w', encoding='utf-8') as writer:
        for item in data:
            row = u'	'.join(item)
            writer.write(u'{0}\n'.format(row))


if __name__ == "__main__":
    tn_checks = {}
    file_list = [x for x in glob.glob('*/*/*.md')]
    numbered_list = []
    for x in file_list:
        b = x.split('/')[0]
        bup = b.upper()
        newbook = books[bup][1]
        numbered_list.append(x.replace(b, newbook))
        books_nums[newbook] = bup
    numbered_list.sort()
    for f in numbered_list:
        tn_checks = convertToList(f, tn_checks)
    for k,v in tn_checks.items():
        tn_check_file = 'en_tn_{0}-{1}.tsv'.format(books[k][1], k)
        saveToTSV(tn_check_file, v)
