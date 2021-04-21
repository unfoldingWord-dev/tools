#!/usr/bin/env python3
#
# TWL_TSV6_to_HebGrk.py
#
# Copyright (c) 2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Apr 2021 by RJH
#   Last modified: 2021-04-20 by RJH
#
"""
Quick script to:
    1/ Read UHB/UGNT USFM and strip out x-tw attributes
    2/ Read TWL
    3/ Insert x_tw attributes into UHB/GNT USFM
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_TWL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_twl/')

# The output folders below must also already exist!
LOCAL_OT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('hbo_uhb/')
LOCAL_NT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('el-x-koine_ugnt/')

BBB_NUMBER_DICT = {'GEN':'01','EXO':'02','LEV':'03','NUM':'04','DEU':'05',
                'JOS':'06','JDG':'07','RUT':'08','1SA':'09','2SA':'10','1KI':'11',
                '2KI':'12','1CH':'13','2CH':'14','EZR':'15',
                'NEH':'16',
                'EST':'17',
                'JOB':'18','PSA':'19','PRO':'20','ECC':'21','SNG':'22','ISA':'23',
                'JER':'24','LAM':'25','EZK':'26','DAN':'27','HOS':'28','JOL':'29',
                'AMO':'30','OBA':'31','JON':'32','MIC':'33','NAM':'34','HAB':'35',
                'ZEP':'36','HAG':'37','ZEC':'38','MAL':'39',
                'MAT':'41','MRK':'42','LUK':'43','JHN':'44','ACT':'45',
                'ROM':'46','1CO':'47','2CO':'48','GAL':'49','EPH':'50','PHP':'51',
                'COL':'52','1TH':'53','2TH':'54','1TI':'55','2TI':'56','TIT':'57',
                'PHM':'58','HEB':'59','JAS':'60','1PE':'61','2PE':'62','1JN':'63',
                '2JN':'64',
                '3JN':'65', 'JUD':'66', 'REV':'67' }


WORD_FIELD_RE = re.compile(r'(\\w .+?\\w\*)')
SINGLE_WORD_RE = re.compile(r'\\w (.+?)\|')
SIMPLE_TW_LINK_RE = re.compile(r'x-tw="([:/\*a-z0-9]+?)" ?\\w\*') # Only occurs inside a \\w field (at end)
MILESTONE_TW_LINK_RE = re.compile(r'\\k-s \| ?x-tw="([:/\*a-z0-9]+?)" ?\\\*')
# WORD_JOINER_RE = re.compile(r'\\w\*(.)\\w ') # Whatever's between two word fields

def get_USFM_source_lines(BBB:str, nn:str) -> Tuple[Path,int,int,int,str]:
    """
    Generator to read the original language (Heb/Grk) book
        and return all lines but with x-tw links removed.

    Yields a 4-tuple with:
        source_filepath line_number C V line
    """
    source_folderpath = LOCAL_OT_FOLDERPATH if int(nn)<40 \
                    else LOCAL_NT_FOLDERPATH # Select HEB or GRK repo
    source_filename = f'{nn}-{BBB}.usfm'
    source_filepath = source_folderpath.joinpath(source_filename)
    print(f"    Getting USFM source lines from {source_filepath}…")

    C = V = 0
    with open(source_filepath, 'rt') as source_usfm_file:
        for line_number,line in enumerate(source_usfm_file, start=1):
            line = line.rstrip() # Remove trailing whitespace including nl char
            # if not line: continue # Ignore blank lines
            # print(f"Read USFM {BBB} line {line_number:3}: '{line}'")

            # Keep track of where we are at
            if line.startswith('\\c '):
                C, V = int(line[3:]), 0
            elif line.startswith('\\v '):
                V = int(line[3:])
            elif C == 0:
                V += 1

            # if line and not line.startswith('\\'): print(f"Found {source_filepath}, {line_number}, {C}:{V}, '{line}'"); halt

            # print(f"        get_USFM_source_lines returning {source_filepath} {line_number}, {C}, {V}, '{line}'")
            yield source_filepath, line_number, C, V, line
# end of get_USFM_source_lines function


def adjust_USFM_line(raw_fields:Tuple[Path,int,int,int,str]) -> Tuple[Path,int,int,str,int,str,str,str]:
    """
    Takes the raw USFM line, then
        1/ Splits the line into marker (including leading backslash) and rest
        2/ Removes existing x-tw="..." links
    """
    # print(f"      adjust_USFM_line({raw_fields})…")
    source_filepath, line_number, C, V, line = raw_fields

    # Remove existing TW links from USFM line
    if 'x-tw' in line:
        line = re.sub(' ?x-tw=".+?"', '', line)
        if 'x-tw' in line: # likely a missing closing quote or something
            raise Exception(f"Seems bad USFM line -- please fix first -- in: {source_filepath} line{line_number}, {C}:{V}, '{raw_fields[4]}'")

    # Separate into marker and rest
    # NOTE: Some lines start with opening punctuation, e.g., "(\w ...") -- this all goes in rest
    if line.startswith('\\'):
        if ' ' in line: marker, rest = line.split(' ', 1)
        else: marker, rest = line, ''
    else: marker, rest = '', line
    # print(f"        adjust_USFM_line returning {source_filepath}, {line_number}, {C}, {V} '{marker}', '{rest}'")

    return source_filepath, line_number, C, V, line, marker, rest
# end of adjust_USFM_line function


def get_TWL_TSV_fields(input_folderpath:Path, BBB:str) -> Tuple[str,str,str,str,int,str]:
    """
    Generator to read the TWL 6-column TSV file for a given book (BBB)
        and return the needed fields.

    Skips the heading row.
    Checks all fields for expected ranges.

    Returns a 6-tuple with:
        reference, rowID, tags, orig_words, occurrence, TWLink
    """
    input_filepath = input_folderpath.joinpath(f'twl_{BBB}.tsv')
    print(f"    Loading TWL {BBB} links from 6-column TSV at {input_filepath}…")
    with open(input_filepath, 'rt') as input_TSV_file:
        for line_number, line in enumerate(input_TSV_file, start=1):
            line = line.rstrip('\n\r')
            # print(f"Read TWL {BBB} line {line_number:3}: '{line}'")
            if line_number == 1:
                assert line == 'Reference\tID\tTags\tOrigWords\tOccurrence\tTWLink'
            else:
                reference, rowID, tags, orig_words, occurrence, TWLink = line.split('\t')
                assert reference; assert rowID; assert orig_words; assert occurrence; assert TWLink # tags is optional
                assert ':' in reference
                assert len(rowID) == 4
                assert occurrence.isdigit()
                assert TWLink.startswith('rc://*/tw/dict/bible/')
                assert TWLink.count('/') == 7
                # print(f"get_TWL_TSV_fields returning {reference}, {rowID}, {tags}, {orig_words}, {occurrence}, {TWLink}")
                yield reference, rowID, tags, orig_words, int(occurrence), TWLink
# end of get_TWL_TSV_fields function


def adjust_TWL_TSV_fields(raw_fields:Tuple[str,str,str,str,int,str]) -> Tuple[int,int,str,int,str,str]:
    """
    Takes the 6 raw TWL TSV fields, then
        1/ Splits the reference into C and V and converts them to integers
        2/ Gets the category and word out of the link
        3/ Drops unneeded fields
    """
    # print(f"      adjust_TWL_TSV_fields({raw_fields})…")
    reference, _rowID, _tags, orig_words, occurrence, TWLink = raw_fields
    C, V = reference.split(':')
    category, word = TWLink[len('rc://*/tw/dict/bible/'):].split('/')
    # print(f"        adjust_TWL_TSV_fields returning {int(C)}, {int(V)} {orig_words}, {int(occurrence)}, {category}, {word}")
    return int(C), int(V), orig_words, int(occurrence), category, word
# end of adjust_TWL_TSV_fields function


def handle_book(BBB:str, nn:str) -> Tuple[int,int]:
    """
    """
    print(f"  Processing ({nn}) {BBB}…")
    simple_TWL_count = complex_TWL_count = 0

    USFM_source_generator = get_USFM_source_lines(BBB, nn)
    new_USFM_lines = []
    finished_USFM = False

    current_V = -1
    words_in_this_verse = [] # Built up from USFM as we process the verse (in order to detect multiple occurrences)
    orig_words_list = [] # Outstanding TWL orig_words still be be processed
    orig_words = ''
    for raw_TSV_fields in get_TWL_TSV_fields(LOCAL_TWL_SOURCE_FOLDERPATH, BBB):
        last_orig_words = orig_words
        C1, V1, orig_words, occurrence, tw_category, tw_word = adjust_TWL_TSV_fields(raw_TSV_fields)
        # if ' ' in orig_words:
        print(f"      handle_book got TWL {C1}, {V1}, {orig_words}, {occurrence}, {tw_category}, {tw_word} with {orig_words_list}")
        # got_new_TWL = True

        # while got_new_TWL or orig_words_list:
        while not finished_USFM:
            try:
                source_filepath, line_number, C2, V2, usfm_line, usfm_marker, usfm_rest = adjust_USFM_line(next(USFM_source_generator))
                print(f"        handle_book got USFM {source_filepath}, {line_number}, {C2}, {V2}, {usfm_marker}, {usfm_rest} with {orig_words_list}")
            except StopIteration: finished_USFM = True; break
            # if C2 > 1: halt

            # NOTE: Inside this inner loop,
            #           continue: basically means go to the next USFM line
            #           break: basically means go to the next TWL line

            # Check for a new verse change
            if V2 != current_V:
                current_V = V2
                words_in_this_verse = []

            # Add origL words that we've found in this verse
            num_words_in_this_line = usfm_rest.count('\\w*')
            num_added = 0
            if num_words_in_this_line:
                if usfm_marker == '\\w':
                    bar_index = usfm_rest.index('|')
                    orig_word = usfm_rest[:bar_index]
                    assert ' ' not in orig_word and '|' not in orig_word
                    words_in_this_verse.append(orig_word)
                    num_added += 1
                elif usfm_marker == '\\k-s':
                    w_index = usfm_rest.index('\\w ')
                    bar_index = usfm_rest.index('|', w_index+3)
                    orig_word = usfm_rest[w_index+3:bar_index]
                    assert ' ' not in orig_word and '|' not in orig_word
                    words_in_this_verse.append(orig_word)
                    num_added += 1
            # if words_in_this_verse: print(f"For {BBB} {C2}:{V2} just added {num_added}/{num_words_in_this_line} to have ({len(words_in_this_verse)}): {words_in_this_verse}")
            assert num_added == num_words_in_this_line

            if orig_words_list and C2==C1 and (V2==V1 or V2==V1-1): # in/past the right verse
                # Check for left-over multi-word TWLs to ensure that these words are passed over
                num_removed = 0
                while orig_words_list and orig_words_list[0] != 'NOT_FOUND_K_YET': # we still have left-overs from a multi-word TWL
                    print(f"Trying to handle remaining {orig_words_list}")
                    orig_words_list_copy = orig_words_list.copy()
                    orig_word = orig_words_list[0]
                    if f'\\w {orig_word}|' in usfm_line:
                        del orig_words_list[0] # We've found it in the line
                        num_removed += 1
                        print(f"  Now remaining {len(orig_words_list)} words are: {orig_words_list}")
                    else:
                        if not num_removed: print(f"Why were no words removed from {orig_words_list}???")
                        break
                if num_removed > 0 and not orig_words_list: # We've handled this TWL properly now
                    print(f"  We've finished handling multiple orig words {orig_words_list_copy} now")
                    # break

            if C2 < C1 or V2 < V1: # Not up to the right point in the USFM yet
                new_USFM_lines.append(usfm_line)
                continue

            if C2==C1 and V2==V1: # in the right verse
                if ' ' not in orig_words: # simplest case -- single word
                    orig_word = orig_words # There's only one!
                    if f' {orig_word}|' not in usfm_line:
                        new_USFM_lines.append(usfm_line)
                        continue
                    if occurrence > words_in_this_verse.count(orig_word): # not there yet
                        new_USFM_lines.append(usfm_line)
                        continue
                    if usfm_line.count('\\w ') == 1: # simple case -- only one word on the line
                        # print(f"Doing simple action {BBB} {C1}:{V1} {orig_word}, {occurrence}, {tw_category}, {tw_word} with {line_number} {usfm_marker} {usfm_rest}")
                        usfm_line = usfm_line.replace('\\w*', f' x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\w*', 1) # Add TWL to end of \w field
                        new_USFM_lines.append(usfm_line)
                        simple_TWL_count += 1
                        got_new_TWL = False
                        break # Done with this USFM line and TWL
                    else: not_done_yet
                else: # this is WAY more complex -- we need \\k milestones
                    assert occurrence == 1
                    assert not orig_words_list or orig_words_list[0] == 'NOT_FOUND_K_YET'
                    orig_word = orig_words.split(' ')[0]
                    if not orig_words_list and orig_word == last_orig_words \
                    and new_USFM_lines and new_USFM_lines[-1].startswith('\\k-s') \
                    and f'{orig_word}|' in new_USFM_lines[-1] and f'{orig_word}|' not in usfm_line:
                        last_line = new_USFM_lines.pop()
                        print(f"WOW! We are having to backup to the previous USFM line: '{last_line}'")
                        print(f"Doing complex2 action {BBB} {C1}:{V1} {orig_words_list}, {occurrence}, {tw_category}, {tw_word} with {line_number} {usfm_marker} {usfm_rest}")
                        last_line = last_line.replace('\\k-s |', f'\\k-s |x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"', 1)
                        new_USFM_lines.append(last_line)
                        complex_TWL_count += 1
                        # got_new_TWL = False
                        # assert usfm_line.count('\\w ') == 1 and f'\\w {orig_word}|' in usfm_line
                        # del orig_words_list[0] # We've found it in the above line
                        # print(f"  XXXRemaining {len(orig_words_list)} words are: {orig_words_list}")
                        orig_words_list = orig_words.split(' ')
                        del orig_words_list[0]
                        orig_word = orig_words_list[0]
                        print(f"  WOWRemaining {len(orig_words_list)} words are: {orig_words_list}")
                    else:
                        orig_words_list = orig_words.split(' ')
                        if f' {orig_word}|' not in usfm_line:
                            orig_words_list.insert(0, 'NOT_FOUND_K_YET')
                            new_USFM_lines.append(usfm_line)
                            continue
                    print(f"Got {orig_words_list} and '{usfm_line}'")
                    if usfm_marker == '\\k-s':
                        print(f"Doing complex1 action {BBB} {C1}:{V1} {orig_words_list}, {occurrence}, {tw_category}, {tw_word} with {line_number} {usfm_marker} {usfm_rest}")
                        usfm_line = usfm_line.replace('\\k-s |', f'\\k-s |x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"', 1)
                        new_USFM_lines.append(usfm_line)
                        complex_TWL_count += 1
                        got_new_TWL = False
                        assert usfm_line.count('\\w ') == 1 and f'\\w {orig_word}|' in usfm_line
                        del orig_words_list[0] # We've found it in the above line
                        print(f"  Remaining {len(orig_words_list)} words are: {orig_words_list}")
                        break
                    elif usfm_line.count('\\w ')==1 and f'\\w {orig_word}|' in usfm_line:
                        print(f"Doing simple2 action {BBB} {C1}:{V1} {orig_words_list}, {occurrence}, {tw_category}, {tw_word} with {line_number} {usfm_marker} {usfm_rest}")
                        usfm_line = usfm_line.replace('\\w*', f' x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\w*', 1) # Add TWL to end of \w field
                        new_USFM_lines.append(usfm_line)
                        simple_TWL_count += 1
                        got_new_TWL = False
                        del orig_words_list[0] # We've found it in the above line
                        print(f"  Remaining {len(orig_words_list)} words are: {orig_words_list}")
                        break
                    else:
                        print(f"Got USFM line '{usfm_line}' with '{orig_word}' from {orig_words_list}")
                        not_finished_yet

            # else:
            print(f"We've gone too far!!! At {BBB} {C1}:{V1} {orig_words}, {occurrence}, {tw_word} with {C2}:{V2} {line_number} {usfm_marker} {usfm_rest}")
            print(f"  Last ten lines: {new_USFM_lines[-10:]}")
            halt
            # raise Exception(f"We've gone too far!!! At {BBB} {C1}:{V1} {orig_words}, {occurrence}, {word} with {C2}:{V2} {line_number} {usfm_marker} {usfm_rest}")

    if new_USFM_lines:
        # print(f"Created USFM ({len(new_USFM_lines)}): {new_USFM_lines}")
        print(f"Writing {len(new_USFM_lines)} lines to {source_filepath}")
        usfm_text = '\n'.join(new_USFM_lines)
        with open(source_filepath, 'wt') as new_USFM_output_file:
            new_USFM_output_file.write(f'{usfm_text}\n')
    return simple_TWL_count, complex_TWL_count
# end of handle_book function


def main():
    """
    """
    print("TWL_TSV6_to_HebGrk.py")
    print(f"  TWL source folderpath is {LOCAL_TWL_SOURCE_FOLDERPATH}/")
    print(f"  OrigL folderpaths are {LOCAL_OT_FOLDERPATH}/ and {LOCAL_NT_FOLDERPATH}/")
    total_simple_links = total_complex_links = 0
    for BBB,nn in BBB_NUMBER_DICT.items(): # This script just handles exactly 66 books
        if BBB != 'MAT': continue
        # try:
        if 1:
            simple_count, complex_count = handle_book(BBB, nn)
            total_simple_links += simple_count
            total_complex_links += complex_count
        # except Exception as e:
        #     print(f"ERROR: failed to process {BBB}: {e}")
    print(f"    {total_simple_links+total_complex_links:,} total links written ({total_simple_links:,} simple links and {total_complex_links:,} multiword links) to {LOCAL_OT_FOLDERPATH}/ and {LOCAL_NT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TWL_TSV6_to_HebGrk.py
