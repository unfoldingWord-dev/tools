#!/usr/bin/env python3
#
# OBS_TN_MD_to_TSV7.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2021-10-05 by RJH
#
"""
Quick script to copy OBS-TN from markdown files
    and put into a TSV file with the same format (7 columns) as UTN.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import logging


LANGUAGE_CODE = 'en'
LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-tn/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-tn2/')


def get_source_notes() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-TN markdown files
        and return quotes and notes.

    Returns a 6-tuple with:
        line number story number frame number reference strings
        quote note
    """
    source_folderpath = LOCAL_SOURCE_FOLDERPATH.joinpath('content/')
    print(f"      Getting source lines from {source_folderpath}")

    for story_number in range(1, 50+1):
        for frame_number in range(0, 99+1):
            filepath = source_folderpath.joinpath(str(story_number).zfill(2), f'{str(frame_number).zfill(2)}.md')
            if os.path.exists(filepath):
                # print(f"Found {filepath}")
                pass
            else:
                # print(f"Not found {filepath}")
                continue

            state = 0
            quote = note = None
            with open(filepath, 'rt') as mdFile:
                for line_number,line in enumerate(mdFile, start=1):
                    line = line.rstrip() # Remove trailing whitespace including nl char
                    # print(f"  line={line}")
                    if not line: continue # Ignore blank lines
                    if line.startswith('# '):
                        if state == 0:
                            assert not quote
                            assert not note
                            quote, note = line[2:], None
                            state = 1
                            continue
                        else: halt
                    elif state == 0:
                        print(f"Have continuation part {filepath} line {line_number}: '{line}'");
                        assert not quote
                        note = line
                        yield line_number, story_number,frame_number, quote,note
                        note = None
                    elif state == 1:
                        assert quote
                        assert not note
                        note = line
                        state = 0
                        yield line_number, story_number,frame_number, quote,note
                        quote = note = None
                    else:
                        logging.error(f"Losing {state} {filepath} line {line_number}: '{line}'");
# end of get_source_notes function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-TN links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH #.joinpath('OBS')
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'tn_OBS.tsv')

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
        print(f"      Failed to load {output_filepath}: {e}")
        original_TSV_TQ_lines = []

    def get_rowID(reference:str, tags:str, support_reference:str, quote:str, occurrence:str, note:str) -> str:
        """
        """
        # print(f"{BBB} get_rowID({reference}, {tags=}, {quote=}, {occurrence}, {note=})…")
        found_id = None
        for old_line in original_TSV_TQ_lines:
            old_reference, old_id, old_tags, old_support_reference, old_quote, old_occurrence, old_note = old_line.split('\t')
            old_note = old_note.split('\\n')[0] # For this task, we don't want any continuation paragraphs
            # print(f"OLD {old_reference} {old_id} {old_tags} {old_quote} {old_occurrence} '{old_question}' '{old_response}'")
            if old_reference==reference and old_tags==tags and old_support_reference==support_reference \
            and old_quote==quote and old_occurrence==occurrence and old_note==note:
                found_id = old_id
                break
        if found_id:
            # print(f"        Found {found_id} for {reference} {tags} {quote} {occurrence} {question} {response}")
            if found_id in previously_generated_ids:
                print(f"We had an error with {found_id} for {reference} {tags} {occurrence} {note}!!!")
                halt
            # print(f"  Returning {found_id=}")
            return found_id
        else:
            # print(f"Need to make a new ID for: ({len(reference)}) '{reference}' ({len(tags)}) '{tags}' ({len(support_reference)}) '{support_reference}' ({len(quote)}) '{quote}' {occurrence} ({len(note)}) '{note}'")
            generated_id = ''
            while generated_id in previously_generated_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previously_generated_ids.append(generated_id)
            # print(f"        Returning generated id for OBS {reference}: {generated_id} '{note}'")
            return generated_id
    #end of make_TSV_file.get_rowID function

    num_quotes = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n')
        previously_generated_ids:List[str] = [''] # We make ours unique per file (spec only used to say unique per verse)
        for j, (_line_number,story_number,frame_number,quote,note) in enumerate(get_source_notes(), start=1):
            # print(f"{_j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{quote}' {note}")

            reference = f'{story_number}:{"intro" if frame_number==0 else frame_number}'
            tags = ''
            support_reference = ''

            note = note.strip()
            note = note.replace('<br>', '\\n')

            if quote: # Normally quote is an English OBS quote
                quote = quote.strip()
                quote = quote.replace('...', '…')
                quote = quote.replace(' …', '…').replace('… ', '…')
                quote = quote.replace('…', ' & ')
                quote = quote.strip()

                occurrence = '1' # default assumption -- could be wrong???

                row_id = get_rowID(reference, tags, support_reference, quote, occurrence, note)

                output_line = f'{reference}\t{row_id}\t{tags}\t{support_reference}\t{quote}\t{occurrence}\t{note}'
                if j > 1: output_line = f'\n{output_line}'
                output_TSV_file.write(output_line)
                num_quotes += 1
            else: # We have a continuation line
                output_TSV_file.write(f'\\n\\n{note}')
        output_TSV_file.write('\n')
    print(f"      {num_quotes:,} quotes and notes written")
    return num_quotes
# end of make_TSV_file function


def main():
    """
    """
    print("OBS_TN_MD_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    main()
# end of OBS_TN_MD_to_TSV7.py
