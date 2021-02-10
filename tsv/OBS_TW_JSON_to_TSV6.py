#!/usr/bin/env python3
#
# OBSTW2tsv.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Apr 2020 by RJH
#   Last modified: 2021-02-10 by RJH
#
"""
Quick script to copy TW links out of Catalog v2 JSON
    and put into a TSV file with the 6 columns.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import json
import re
import logging


LOCAL_SOURCE_FILEPATH = Path('/home/robert/Downloads/tw_cat.json')

LOCAL_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_TW_SOURCE_FILEPATH = LOCAL_BASE_FOLDERPATH.joinpath('en_tw/bible/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_BASE_FOLDERPATH.joinpath('en_translation-annotations/OBS/')


def get_source_lines() -> Tuple[str,str,str]:
    """
    Generator to read the JSON
        and return lines containing OBS TW links.

    Yields a 3-tuple with:
        story number string (2 digits, zero filled)
        frame number string (2 digits, zero filled)
        translation word
    """
    print(f"      Getting source lines from {LOCAL_SOURCE_FILEPATH}")

    with open(LOCAL_SOURCE_FILEPATH, 'rt') as json_input_file:
        source_JSON = json.load(json_input_file)
    print(f"        Loaded source json last modified {source_JSON['date_modified']}")

    chapters = {}
    for chapter in source_JSON['chapters']:
        chapters[chapter['id']] = chapter

    for chapter_number in range(1, 50+1):
        chapter_number_string = str(chapter_number).zfill(2)

        frames = {}
        for frame in chapters[chapter_number_string]['frames']:
            frames[frame['id']] = frame

        for frame_number in range(1, len(frames)+1):
            frame_number_string = str(frame_number).zfill(2)
            try:
                # print(f"Story/chapter {chapter_number_string} frame {frame_number_string} = {frames[frame_number_string]['items']}")
                for word in frames[frame_number_string]['items']:
                    # print(word['id'])
                    assert ' ' not in word
                    yield chapter_number_string, frame_number_string, word['id']
            except KeyError:
                pass # Not all frames have TWs
# end of get_source_lines function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS TW links to TSV…")
    if not os.path.isdir(LOCAL_OUTPUT_FOLDERPATH): os.mkdir(LOCAL_OUTPUT_FOLDERPATH)
    output_filepath = LOCAL_OUTPUT_FOLDERPATH.joinpath('OBS_twl.tsv')
    num_links = j = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        # output_TSV_file.write('Book\tChapter\tVerse\tID\tSupportReference\tOrigQuote\tOccurrence\tGLQuote\tOccurrenceNote\n')
        output_TSV_file.write('Reference\tID\tTags\tOrigWords\tOccurrence\tTWLink\n')
        previous_ids:List[str] = ['']
        for j, (story_number_string, frame_number_string, word) in enumerate(get_source_lines(), start=1):
            # print(f"{j:3}/ Line {line_number:<5} '{word}' {story_number_string} {frame_number_string}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            reference = f'{int(story_number_string)}:{int(frame_number_string)}'

            # We don't know if it's a KT, name, or other
            #   so we'll try each one
            link = None
            for category in ('kt','names','other'):
                check_link = LOCAL_TW_SOURCE_FILEPATH.joinpath(f'{category}/{word}.md')
                if os.path.isfile(check_link):
                    # print(f"Found '{word}' in {category}")
                    link = f'rc://*/tw/dict/bible/{category}/{word}'
                    break
            if not link: # Bad word
                logging.critical(f"Unable to find '{word}' link for OBS {reference}")
                continue

            tags = ''
            if '/bible/kt/jesus' in link: tags = 'keyterm; name'
            elif '/bible/names/' in link: tags = 'name'
            elif '/bible/kt/' in link: tags = 'keyterm'
            # elif '/bible/other/' in link: tags = 'other'

            occurrence = 1 # assumed

            output_line = f'{reference}\t{generated_id}\t{tags}\t{word}\t{occurrence}\t{link}'
            output_TSV_file.write(f'{output_line}\n')
            num_links += 1
    print(f"      {j:,} links found ({num_links:,} links written)")
    return num_links
# end of make_TSV_file function


def main():
    """
    """
    print("OBSTW2tsv.py")
    print(f"  Source folderpath is {LOCAL_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    link_count = make_TSV_file()
    print(f"    {link_count:,} OBS TW links written")
# end of main function

if __name__ == '__main__':
    main()
# end of OBSTW2tsv.py
