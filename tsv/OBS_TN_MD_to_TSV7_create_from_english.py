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
#   Last modified: 2021-12-21 by RJH
#
"""
Quick script to create a TSV tn_OBS.tsv file from markdown files
    and put into a TSV file with the same format (7 columns) as UTN and uses IDs from en_obs-tn.
"""
from typing import List, Tuple
import os
import sys
import argparse
from pathlib import Path
import random
import logging
import csv
import re

english = None
target = None
branch = "tsvConverter"
previously_generated_ids:List[str] = [''] # We make ours unique per file (spec only used to say unique per verse)

def get_source_notes() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-TN markdown files
        and return quotes and notes.

    Returns a 6-tuple with:
        line number story number frame number reference strings
        quote note
    """
    contents_path = os.path.join(target, 'content')
    print(f"      Getting content lines from {contents_path}")

    for story_number in range(1, 50+1):
        for frame_number in range(0, 99+1):
            filepath = os.path.join(contents_path, str(story_number).zfill(2), f'{str(frame_number).zfill(2)}.md')
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
                        else: 
                            sys.exit(1)
                    elif state == 0:
                        # print(f"Have continuation part {filepath} line {line_number}: '{line}'");
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

def generate_rowID():
    generated_id = ''
    while generated_id in previously_generated_ids:
        generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
    previously_generated_ids.append(generated_id)
    return generated_id

def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-TN links to TSV…")
    english_tsv_path = os.path.join(english, 'tn_OBS.tsv')
    target_tsv_path = os.path.join(target, 'tn_OBS.tsv')
    english_header = []
    english_rows = []

    # Load the previous file so we can use the same row ID fields
    try:
        with open(english_tsv_path, 'rt') as english_file:
            english_tsv = csv.reader(english_file, delimiter="\t")
            english_header = next(english_tsv)
            for row in english_tsv:
                english_rows.append(row)
                previously_generated_ids.append(row[1])
            print(f"      Loaded {len(english_tsv):,} lines from english tsv file at {english_tsv_path}")
    except Exception as e:
        if 'No such file' in str(e):
            print(f"      No existing file to preload row IDs: {english_tsv_path}")
        else:
            print(f"      Failed to load {english_tsv_path}: {e}")

    # Add all the existing English IDs just to make sure we don't generate a new one the same

    def get_rowFromOriginal(row):
        """
        """
        story_str, frame_str = row[0].split(':')
        story = -1
        frame = -1
        try:
            story = int(story_str)
            frame = int(frame_str)
        except Exception:
            pass
        while len(english_rows) and story >= 0 and frame >= 0:
            old_reference, old_id, old_tags, old_support_reference, _, _, _ = english_rows[0]
            print(old_support_reference)
            print(row[3])
            if row[0] == old_reference and old_support_reference == row[4]:
                english_rows.pop(0)
                row[1] = old_id
                row[2] = old_tags
                return row
            else:
                old_story_str, old_frame_str = old_reference.split(':')
                try:
                    old_story = int(old_story_str)
                    old_frame = int(old_frame_str)
                    if old_story > story or (old_story == story and old_frame > frame):
                        break
                    else:
                        english_rows.pop(0)
                except Exception:
                    break
        row[1] = generate_rowID()
        return row
    #end of make_TSV_file.get_rowFromOriginal function

    def write_row(row, target_tsv):
        match = re.match(r'.*(rc://[*a-zA-Z0-9_/-]+).*', row[6])
        if match:
            row[3] = match[1]
            print(row)
            print(match)
            exit(1)
        row = get_rowFromOriginal(row)
        target_tsv.writerow(row)

    num_quotes = 0
    with open(target_tsv_path, 'wt') as target_tsv_file:
        target_tsv = csv.writer(target_tsv_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        target_tsv.writerow(english_header)
        row = None
        for j, (_line_number,story_number,frame_number,quote,note) in enumerate(get_source_notes(), start=1):
            reference = f'{story_number}:{frame_number}'
            note = note.strip()
            note = note.replace('<br>', '\\n')

            if quote and row:
                write_row(row, target_tsv)

            if quote: # Normally quote is an English OBS quote
                quote = quote.strip()
                quote = quote.replace('...', '…')
                quote = quote.replace(' …', '…').replace('… ', '…')
                quote = quote.replace('…', ' & ')
                quote = quote.strip()

                occurrence = '1' # default assumption -- could be wrong???

                row = [reference, '', '', '', quote, occurrence, note]
                num_quotes += 1
            elif row and len(row) >= 7: # We have a continuation line
                row[6] += f"\\n\\n{note}"
        if row:
            write_row(row, target_tsv)
    print(f"      {num_quotes:,} quotes and notes written")
    return num_quotes
# end of make_TSV_file function

def main():
    """
    """
    print("OBS_TN_MD_to_TSV7.py")
    print(f"  Source folderpath is {english}/")
    print(f"  Output folderpath is {target}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-e', '--english', dest='english', required=False,
                        help='Path to the en_obs-tn repo which we can get the existing .tsv file with IDs. Will try to find in parent directory of target')
    parser.add_argument('-t', '--target', dest='target', required=True,
                        help=f'Path to the target obs-tn repo in which we can clobber the tn_OBS.tsv file if it exists. It has the contents/ directory with markdown files for OBS')
    parser.add_argument('-b', '--branch', dest='branch', default=branch,
                        help='Branch to create with the new file')

    args = parser.parse_args(sys.argv[1:])
    english = args.english
    target = args.target
    branch = args.branch

    if not os.path.exists(target):
        print(f"Path does not exist: {target}")
        sys.exit(1)
    if not english:
        english = os.path.join(os.path.dirname(target), "en_obs-tn")
    if not os.path.exists(english):
        print(f"Unable to find the English repo at {english}")
        sys.exit(1)
    main()
# end of OBS_TN_MD_to_TSV7.py
