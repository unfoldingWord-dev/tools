#!/usr/bin/env python3
#
# OBS_SQ_MD_to_TSV7.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2021-06-02 by RJH
#
"""
Quick script to copy OBS-SQ from markdown files
    and put into a TSV file with 7 columns.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_obs-sq/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/en_study-annotations/')


def get_source_questions() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-SQ markdown files
        and return questions and responses.

    Returns a 6-tuple with:
        line number story number frame number reference strings
        question response
    """
    source_folderpath = LOCAL_SOURCE_FOLDERPATH.joinpath('content/')
    print(f"      Getting source lines from {source_folderpath}")

    for story_number in range(0, 50+1):
        filepath = source_folderpath.joinpath(f'{str(story_number).zfill(2)}.md')
        if os.path.exists(filepath):
            # print(f"Found {filepath}")
            pass
        else:
            print(f"Not found {filepath}")
            continue

        state = 0
        tag = question = response = None
        with open(filepath, 'rt') as mdFile:
            if story_number == 0:
                line_number = 1
                tag = 'intro'
                question = mdFile.read().replace('\n','\\n')
                response = ''
                yield line_number, story_number, tag,question,response
            else: # stories 1..50
                for line_number,line in enumerate(mdFile, start=1):
                    line = line.rstrip() # Remove trailing whitespace including nl char
                    # print(f"  line={line}")
                    if not line: continue # Ignore blank lines
                    if line.startswith('# '): # Ignore the story title
                        if state != 0: halt
                    elif line.startswith('## '):
                        assert not question
                        assert not response
                        tag = line[3:].strip()
                        state = 1
                    elif line.startswith('1. '):
                        assert state == 1
                        assert tag
                        assert not question
                        assert not response
                        question, response = line[3:].strip(), None
                        state = 2
                        continue
                    elif state == 2:
                        assert tag
                        assert question
                        assert not response
                        response = line.strip()
                        state = 1
                        yield line_number, story_number, tag,question,response
                        question = response = None
                    else:
                        logging.error(f"Losing {state} {filepath} line {line_number}: '{line}'");
# end of get_source_questions function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-SQ links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH.joinpath('OBS')
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'sq_OBS.tsv')
    num_questions = 0
    frame_number = '?'
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse\n')
        previous_ids:List[str] = ['']
        for _j, (_line_number, story_number, tag,question,response) in enumerate(get_source_questions(), start=1):
            # print(f"{j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{question}' {response}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            if (ix := response.find('See: [')) != -1:
                frame_number = int(response[ix+9:ix+11])
            reference = f'{"front" if story_number==0 else story_number}:{"intro" if frame_number==0 else frame_number}'


            tags = ''
            if tag == "What the Story Says": tags = 'meaning'
            # elif tag == "What the Story Means": tags = 'means'
            elif tag == "What the Story Means to Us": tags = 'application'
            elif tag:
                print(f"Using tag: {tag}")
                tags = tag

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
    print("OBS_SQ_MD_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    main()
# end of OBS_SQ_MD_to_TSV7.py
