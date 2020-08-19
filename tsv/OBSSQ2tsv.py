#!/usr/bin/env python3
#
# OBSSQ2tsv.py
#
# Copyright (c) 2020 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2020-08-19 by RJH
#
"""
Quick script to copy OBS-SQ from markdown files
    and put into a TSV file with the same format (7 columns) as UTN.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_obs-sq/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/en_study-annotations/')


def get_source_questions() -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the OBS-SQ markdown files
        and return questions and answers.

    Returns a 6-tuple with:
        line number story number frame number reference strings
        question answer
    """
    source_folderpath = LOCAL_SOURCE_FOLDERPATH.joinpath('content/')
    print(f"      Getting source lines from {source_folderpath}")

    for story_number in range(1, 50+1):
        filepath = source_folderpath.joinpath(f'{str(story_number).zfill(2)}.md')
        if os.path.exists(filepath):
            # print(f"Found {filepath}")
            pass
        else:
            print(f"Not found {filepath}")
            continue

        state = 0
        tag = question = answer = None
        with open(filepath, 'rt') as mdFile:
            for line_number,line in enumerate(mdFile, start=1):
                line = line.rstrip() # Remove trailing whitespace including nl char
                # print(f"  line={line}")
                if not line: continue # Ignore blank lines
                if line.startswith('# '): # Ignore the story title
                    if state != 0: halt
                if line.startswith('## '):
                    assert not question
                    assert not answer
                    tag = line[3:].strip()
                    state = 1
                if line.startswith('1. '):
                    assert state == 1
                    assert tag
                    assert not question
                    assert not answer
                    question, answer = line[3:].strip(), None
                    state = 2
                    continue
                if state == 2:
                    assert tag
                    assert question
                    assert not answer
                    answer = line.strip()
                    state = 1
                    yield line_number, story_number, tag,question,answer
                    question = answer = None
# end of get_source_questions function


def make_TSV_file() -> Tuple[int,int]:
    """
    """
    print(f"    Converting OBS-SQ links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH.joinpath('obs')
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'obs_sq.tsv')
    num_questions = j = 0
    frame_number = '?'
    with open(output_filepath, 'wt') as output_TSV_file:
        # output_TSV_file.write('Book\tChapter\tVerse\tID\tSupportReference\tOrigQuote\tOccurrence\tGLQuote\tOccurrenceNote\n')
        output_TSV_file.write('Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tAnnotation\n')
        previous_ids:List[str] = ['']
        for j, (_line_number, story_number, tag,question,answer) in enumerate(get_source_questions(), start=1):
            # print(f"{j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{question}' {answer}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            if (ix := answer.find('See: [')) != -1:
                frame_number = int(answer[ix+9:ix+11])
            reference = f'{"front" if story_number==0 else story_number}:{"intro" if story_number==0 else frame_number}'


            tags = ''
            if tag == "What the Story Says": tags = 'meaning'
            # elif tag == "What the Story Means": tags = 'means'
            elif tag == "What the Story Means to Us": tags = 'application'
            elif tag:
                print(f"Using tag: {tag}")
                tags = tag

            support_reference = ''
            quote = ''
            occurrence = ''
            question = question.strip()
            answer = answer.strip()
            annotation = f'{question}<br>{answer}'
            output_line = f'{reference}\t{generated_id}\t{tags}\t{support_reference}\t{quote}\t{occurrence}\t{annotation}'
            output_TSV_file.write(f'{output_line}\n')
            num_questions += 1
    print(f"      {num_questions:,} questions and answers written")
    return num_questions
# end of make_TSV_file function


def main():
    """
    """
    print("OBSSQ2tsv.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    make_TSV_file()
# end of main function

if __name__ == '__main__':
    main()
# end of OBSSQ2tsv.py