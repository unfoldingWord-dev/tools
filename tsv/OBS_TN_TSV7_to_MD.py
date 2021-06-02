#!/usr/bin/env python3
#
# OBS_TN_TSV7_to_MD.py
#
# Copyright (c) 2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written June 2021 by RJH
#   Last modified: 2021-06-02 by RJH
#
"""
Quick script to copy TN from 7-column TSV files
    and put back into the older markdown format (for compatibility reasons)
"""
from typing import List, Tuple, Optional
import os
import shutil
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_obs-tn2/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_obs-tn/')

def get_TSV_fields(input_folderpath:Path) -> Tuple[str,str,str]:
    """
    Generator to read the TN 7-column TSV file for OBS
        and return the needed fields.

    Skips the heading row.
    Checks that unused fields are actually unused.

    Returns a 3-tuple with:
        reference, quote, note
    """
    print(f"    Loading OBS TN links from 7-column TSV…")
    input_filepath = input_folderpath.joinpath(f'tn_OBS.tsv')
    with open(input_filepath, 'rt') as input_TSV_file:
        for line_number, line in enumerate(input_TSV_file, start=1):
            line = line.rstrip('\n\r')
            # print(f"{line_number:3}/ {line}")
            if line_number == 1:
                assert line == 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote'
            else:
                reference, rowID, tags, support_reference, quote, occurrence, note = line.split('\t')
                print(f"{reference}, {rowID}, {tags}, {support_reference}, {quote}, {occurrence}, {note}")
                assert reference; assert rowID
                assert quote; assert occurrence; assert occurrence.isdigit()
                assert note
                assert not tags; assert not support_reference
                if occurrence != '1':
                    logging.warning(f"We lost OBS {reference} '{quote}' occurrence={occurrence} for '{note}'")
                yield reference, quote.replace(' & ','…'), note
# end of get_TSV_fields function


current_StFr = None
markdown_text = ''
def handle_output(output_folderpath:Path, fields:Optional[Tuple[str,str,str]]) -> int:
    """
    Function to write the TN markdown files.

    Needs to be called one extra time with fields = None
        to write the last entry.

    Returns the number of markdown files that were written in the call.
    """
    global current_StFr, markdown_text
    # print(f"handle_output({output_folderpath}, {fields})…")

    num_files_written = 0

    if fields is None:
        frameNum1 = frameNum2 = '1' # Any value would do here
    else: # have fields
        reference, quote, note = fields
        storyNum, frameNum = reference.split(':')
        if frameNum == 'intro': frameNum = '0'
        # if storyNum == '2' and frameNum =='1': halt

        if '-' in frameNum: frameNum1, frameNum2 = frameNum.split('-') # it's a range
        else: frameNum1 = frameNum2 = frameNum

    for intFrameNum in range(int(frameNum1), int(frameNum2)+1):
        frameNum = str(intFrameNum)

        markdown_text = markdown_text.replace('\\n', '\n') # Fix multi-paragraph notes
        if (fields is None # We need to write the last file
        or (markdown_text and (storyNum,frameNum) != current_StFr)): # need to write the previous verse file
            prevStoryNum, prevFrameNum = current_StFr
            this_folderpath = output_folderpath.joinpath(f'content/{prevStoryNum.zfill(2)}/')
            if not os.path.exists(this_folderpath): os.makedirs(this_folderpath)
            output_filepath = this_folderpath.joinpath(f'{prevFrameNum.zfill(2)}.md')
            try:
                with open(output_filepath, 'rt') as previous_markdown_file:
                    previous_markdown_text = previous_markdown_file.read()
            except FileNotFoundError: previous_markdown_text = ''
            if previous_markdown_text:
                # markdown_text = f"{markdown_text}\n{previous_markdown_text}"
                markdown_text = f"{previous_markdown_text}\n{markdown_text}"
            with open(output_filepath, 'wt') as output_markdown_file:
                output_markdown_file.write(markdown_text)
            # print(f"  Wrote {len(markdown_text):,} bytes to {str(output_filepath).replace(str(output_folderpath), '')}")
            num_files_written += 1
            markdown_text = ''

        if fields is not None:
            current_StFr = storyNum, frameNum
            if markdown_text: markdown_text = f'{markdown_text}\n' # Blank line between questions
            markdown_text += f'# {quote}\n\n{note}\n' # will be written on the next call

    return num_files_written
# end of handle_output function


def main():
    """
    """
    print("OBS_TN_TSV7_to_MD.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_files_read = total_questions = total_files_written = 0

    # Remove the folder first in case any questions have been deleted
    try: shutil.rmtree(LOCAL_OUTPUT_FOLDERPATH.joinpath('content/'))
    except FileNotFoundError: pass # wasn't there
    for input_fields in get_TSV_fields(LOCAL_SOURCE_FOLDERPATH):
        total_files_written += handle_output(LOCAL_OUTPUT_FOLDERPATH,input_fields)
        total_questions += 1
    total_files_read += 1
    total_files_written += handle_output(LOCAL_OUTPUT_FOLDERPATH,None) # To write last file

    print(f"  {total_questions:,} total questions and answers read from {total_files_read} TSV file")
    print(f"  {total_files_written:,} total verse files written to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of OBS_TN_TSV7_to_MD.py
