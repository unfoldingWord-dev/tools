#!/usr/bin/env python3
#
# OBS_SN_MD_to_TSV7.py
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
Quick script to copy OBS-SN from markdown files
    and put into a TSV file with the same format (7 columns) as UTN.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import logging


LANGUAGE_CODE = 'en'
LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-sn/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(f'{LANGUAGE_CODE}_obs-sn2/')


def get_source_notes() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-SN markdown files
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
    print(f"    Converting OBS-SN links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'sn_OBS.tsv')
    num_quotes = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote\n')
        previous_ids:List[str] = ['']
        for _j, (_line_number,story_number,frame_number,quote,note) in enumerate(get_source_notes(), start=1):
            # print(f"{j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{quote}' {note}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            reference = f'{story_number}:{"intro" if frame_number==0 else frame_number}'
            tags = ''
            support_reference = ''
            orig_quote = quote.strip()
            orig_quote = orig_quote.replace('...', '…')
            orig_quote = orig_quote.replace(' …', '…').replace('… ', '…')
            orig_quote = orig_quote.replace('…', ' & ')
            occurrence = '1' # default assumption -- could be wrong???
            note = note.strip()
            note = note.replace('<br>', '\\n')
            output_line = f'{reference}\t{generated_id}\t{tags}\t{support_reference}\t{orig_quote}\t{occurrence}\t{note}'
            output_TSV_file.write(f'{output_line}\n')
            num_quotes += 1
    print(f"      {num_quotes:,} quotes and notes written")
    return num_quotes
# end of make_TSV_file function


def main():
    """
    """
    print("OBS_SN_MD_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    main()
# end of OBS_SN_MD_to_TSV7.py
