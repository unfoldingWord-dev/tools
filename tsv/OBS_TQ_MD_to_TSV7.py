#!/usr/bin/env python3
#
# OBS_TQ_MD_to_TSV7.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2021-02-16 by RJH
#
"""
Quick script to copy OBS-TQ from markdown files
    and put into a TSV file with 7 columns.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_obs-tq/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_translation-annotations/')


def get_source_questions() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-TQ markdown files
        and return questions and responses.

    Returns a 6-tuple with:
        line number story number frame number reference strings
        question response
    """
    source_folderpath = LOCAL_SOURCE_FOLDERPATH.joinpath('content/')
    print(f"      Getting source lines from {source_folderpath}")

    for story_number in range(1, 50+1):
        for frame_number in range(1, 99+1):
            filepath = source_folderpath.joinpath(str(story_number).zfill(2), f'{str(frame_number).zfill(2)}.md')
            if os.path.exists(filepath):
                # print(f"Found {filepath}")
                pass
            else:
                # print(f"Not found {filepath}")
                continue

            state = 0
            question = response = None
            with open(filepath, 'rt') as mdFile:
                for line_number,line in enumerate(mdFile, start=1):
                    line = line.rstrip() # Remove trailing whitespace including nl char
                    # print(f"  line={line}")
                    if not line: continue # Ignore blank lines
                    if line.startswith('# '):
                        if state == 0:
                            assert not question
                            assert not response
                            question, response = line[2:], None
                            state = 1
                            continue
                        else: halt
                    if state == 1:
                        assert question
                        assert not response
                        response = line
                        state = 0
                        yield line_number, story_number,frame_number, question,response
                        question = response = None
# end of get_source_questions function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-TQ links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH.joinpath('OBS')
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'OBS_tq.tsv')
    num_questions = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse\n')
        previous_ids:List[str] = ['']
        for _j, (_line_number,story_number,frame_number,question,response) in enumerate(get_source_questions(), start=1):
            # print(f"{_j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{question}' {response}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            reference = f'{story_number}:{frame_number}'
            tags = ''

            quote = ''
            occurrence = ''

            question = question.strip()
            response = response.strip()
            # annotation = f'{question}\\n\\n> {response}' # This is the Markdown quoted block formatting

            output_line = f'{reference}\t{generated_id}\t{tags}\t{quote}\t{occurrence}\t{question}\t{response}'
            output_TSV_file.write(f'{output_line}\n')
            num_questions += 1
    print(f"      {num_questions:,} 7-column questions and responses written")
    return num_questions
# end of make_TSV_file function


def main():
    """
    """
    print("OBS_TQ_MD_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    main()
# end of OBS_TQ_MD_to_TSV7.py
