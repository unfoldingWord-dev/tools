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
#   Last modified: 2021-12-22 by RJH
#
"""
Quick script to copy OBS-TQ from markdown files
    and put into a TSV file with 7 columns.

Note that each run of this script tries to read any existing TSV files
    so that it can reuse the same ID fields where possible.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LANGUAGE_CODE = 'en'
# LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/DCS_dataRepos/RepoConversions')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-tq/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-tq2/')


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
            # print(f"        Looking for filepath: {filepath}")
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
                    elif state == 1:
                        assert question
                        assert not response
                        response = line
                        state = 0
                        yield line_number, story_number,frame_number, question,response
                        question = response = None
                    else:
                        logging.error(f"Losing {state} {filepath} line {line_number}: '{line}'");
# end of get_source_questions function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-TQ links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH #.joinpath('OBS')
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'tq_OBS.tsv')

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
            # print(f"        Returning generated id for OBS {reference}: {generated_id} '{question}'")
            return generated_id
    #end of make_TSV_file.get_rowID function

    num_questions = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tQuote\tOccurrence\tQuestion\tResponse\n')
        previously_generated_ids:List[str] = [''] # We make ours unique per file (spec only used to say unique per verse)
        for _j, (_line_number,story_number,frame_number,question,response) in enumerate(get_source_questions(), start=1):
            # print(f"{_j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{question}' {response}")

            # generated_id = ''
            # while generated_id in previous_ids:
            #     generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            # previous_ids.append(generated_id)

            reference = f'{story_number}:{frame_number}'
            tags = ''

            quote = ''
            occurrence = ''

            question = question.strip()
            response = response.strip()
            # annotation = f'{question}\\n\\n> {response}' # This is the Markdown quoted block formatting
            qr = f'{question}\t{response}'

            row_id = get_rowID(reference, tags, quote, occurrence, qr)

            output_line = f'{reference}\t{row_id}\t{tags}\t{quote}\t{occurrence}\t{qr}'
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
