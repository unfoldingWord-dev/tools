#!/usr/bin/env python3
#
# TQ_TSV7_to_MD.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Nov 2020 by RJH
#   Last modified: 2021-03-23 by RJH
#
"""
Quick script to copy TQ from 5-column TSV files
    and put back into the older markdown format (for compatibility reasons)
"""
from typing import List, Tuple, Optional
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tq2/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tq-backported/')

BBB_LIST = ('GEN','EXO','LEV','NUM','DEU',
                'JOS','JDG','RUT','1SA','2SA','1KI',
                '2KI','1CH','2CH','EZR', 'NEH', 'EST',
                'JOB','PSA','PRO','ECC','SNG','ISA',
                'JER','LAM','EZK','DAN','HOS','JOL',
                'AMO','OBA','JON','MIC','NAM','HAB',
                'ZEP','HAG','ZEC','MAL',
                'MAT','MRK','LUK','JHN','ACT',
                'ROM','1CO','2CO','GAL','EPH','PHP',
                'COL','1TH','2TH','1TI','2TI','TIT',
                'PHM','HEB', 'JAS','1PE','2PE',
                '1JN','2JN','3JN', 'JUD', 'REV')
assert len(BBB_LIST) == 66


def get_TSV_fields(input_folderpath:Path, BBB:str) -> Tuple[str,str]:
    """
    Generator to read the TQ 5-column TSV file for a given book (BBB)
        and return the needed fields.

    Skips the heading row.
    Checks that unused fields are actually unused.

    Returns a 3-tuple with:
        reference, question, response
    """
    print(f"    Loading TQ {BBB} links from 7-column TSV…")
    input_filepath = input_folderpath.joinpath(f'tq_{BBB}.tsv')
    with open(input_filepath, 'rt') as input_TSV_file:
        for line_number, line in enumerate(input_TSV_file, start=1):
            line = line.rstrip('\n\r')
            # print(f"{line_number:3}/ {line}")
            if line_number == 1:
                assert line == 'Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse'
            else:
                reference, rowID, tags, quote, occurrence, question, response = line.split('\t')
                assert reference; assert rowID; assert question; assert response
                assert not tags; assert not quote; assert not occurrence
                yield reference, question, response
# end of get_TSV_fields function


current_BCV = None
markdown_text = ''
def handle_output(output_folderpath:Path, BBB:str, fields:Optional[Tuple[str,str,str]]) -> int:
    """
    Function to write the TQ markdown files.

    Needs to be called one extra time with fields = None
        to write the last entry.

    Returns the number of markdown files that were written in the call.
    """
    global current_BCV, markdown_text
    num_files_written = 0

    if fields is not None:
        reference, question, response = fields
        C, V = reference.split(':')
        # print(BBB,C,V,repr(annotation))

    if (fields is None # We need to write the last file
    or (markdown_text and (BBB,C,V) != current_BCV)): # need to write the previous verse file
        assert BBB == current_BCV[0]
        prevC, prevV = current_BCV[1:]
        this_folderpath = output_folderpath.joinpath(f'{BBB.lower()}/{prevC.zfill(2)}/')
        if not os.path.exists(this_folderpath): os.makedirs(this_folderpath)
        output_filepath = this_folderpath.joinpath(f'{prevV.zfill(2)}.md')
        with open(output_filepath, 'wt') as output_markdown_file:
            output_markdown_file.write(markdown_text)
        num_files_written += 1
        markdown_text = ''

    if fields is not None:
        current_BCV = BBB, C, V
        # question, answer = annotation.split('\\n\\n> ')
        if markdown_text: markdown_text += '\n' # Blank line between questions
        markdown_text += f'# {question}\n\n{response}\n' # will be written on the next call

    return num_files_written
# end of handle_output function


def main():
    """
    """
    print("TQ_TSV7_to_MD.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_files_read = total_questions = total_files_written = 0
    for BBB in BBB_LIST:
        for input_fields in get_TSV_fields(LOCAL_SOURCE_FOLDERPATH,BBB):
            total_files_written += handle_output(LOCAL_OUTPUT_FOLDERPATH,BBB,input_fields)
            total_questions += 1
        total_files_read += 1
        total_files_written += handle_output(LOCAL_OUTPUT_FOLDERPATH,BBB,None) # To write last file
    print(f"  {total_questions:,} total questions and answers read from {total_files_read} TSV files")
    print(f"  {total_files_written:,} total verse files written to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TQ_TSV7_to_MD.py
