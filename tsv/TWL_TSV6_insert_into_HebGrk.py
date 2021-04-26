#!/usr/bin/env python3
#
# TWL_TSV6_insert_into_HebGrk.py
#
# Copyright (c) 2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Apr 2021 by RJH
#   Last modified: 2021-04-26 by RJH
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
        3/ Removes \k milestones (possibly leaving blank lines)
    """
    # print(f"      adjust_USFM_line({raw_fields})…")
    source_filepath, line_number, C, V, line = raw_fields

    # Handle special case
    if line == '\\k-e\\*': # only
        # we want to delete the entire line (rather than leaving in a superfluous blank line)
        return source_filepath, line_number, C, V, 'SKIP', 'SKIP', 'SKIP'

    # Remove existing TW links from USFM line
    if 'x-tw' in line:
        line = re.sub(' ?x-tw=".+?"', '', line)
        if 'x-tw' in line: # likely a missing closing quote or something
            raise Exception(f"Seems bad USFM line -- please fix first -- in: {source_filepath} line{line_number}, {C}:{V}, '{raw_fields[4]}'")

    # Remove \k start and end milestones from line
    line = line.replace('\\k-s |\\*', '')
    line = line.replace('\\k-e\\*', '')
    assert '\\k' not in line

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

    USFM_source_generator = get_USFM_source_lines(BBB, nn) # It finds its own Heb or Grk folderpath
    TWL_source_generator = get_TWL_TSV_fields(LOCAL_TWL_SOURCE_FOLDERPATH, BBB)

    new_USFM_lines = []
    current_usfm_V = -1
    origL_words_in_this_verse = [] # Built up from USFM as we process the verse (in order to detect multiple occurrences)
    outstanding_orig_words_list = [] # Outstanding TWL orig_words still be be processed
    processed_first_outstanding_orig_word = False
    handled_USFM_line = True; finished_USFM = False
    handled_TWL_line = True; finished_TWL = False
    while True:
        # Get a new USFM line if necessary
        if handled_USFM_line and not finished_USFM:
            try:
                source_filepath, usfm_line_number, usfm_C, usfm_V, usfm_line, usfm_marker, usfm_rest = adjust_USFM_line(next(USFM_source_generator))
                if usfm_line == 'SKIP': # This means that it was an end milestone and we want to delete the entire (now blank) line
                    source_filepath, usfm_line_number, usfm_C, usfm_V, usfm_line, usfm_marker, usfm_rest = adjust_USFM_line(next(USFM_source_generator))
                print(f"Got USFM {source_filepath}, {usfm_line_number}, {usfm_C}, {usfm_V}, '{usfm_line}' with {outstanding_orig_words_list} and {origL_words_in_this_verse}")
                assert usfm_line != 'SKIP'
                handled_USFM_line = False
            except StopIteration: print("Finished USFM"); finished_USFM = True
        # if usfm_C == 1 and usfm_V == 14: break

        # Get a new TWL line if necessary
        if handled_TWL_line and not finished_TWL:
            try:
                twl_C, twl_V, orig_words, occurrence, tw_category, tw_word = adjust_TWL_TSV_fields(next(TWL_source_generator))
                print(f"Got TWL {twl_C}, {twl_V}, '{orig_words}', {occurrence}, {tw_category}, {tw_word} with {outstanding_orig_words_list} and {origL_words_in_this_verse}")
                handled_TWL_line = False
            except StopIteration: print("Finished TWL"); orig_words = ''; finished_TWL = True

        # See if we're all finished
        if finished_USFM and finished_TWL: # all happy -- go take a vacation
            break

        if finished_TWL:
            new_USFM_lines.append(usfm_line)
            handled_USFM_line = True
            continue # Get next usfm line

        if usfm_C == twl_C and usfm_V > twl_V+1:
            raise Exception(f"USFM {BBB} {usfm_C}:{usfm_V} went too far past TWL {twl_C}:{twl_V} '{orig_words}' {occurrence}")

        if not handled_USFM_line:
            # Clear the word list for new verses
            # if ' ' not in orig_words: # We have to delay this if still have orig_words to process from the last verse
            if usfm_V != current_usfm_V \
            and twl_C==usfm_C and twl_V > usfm_V : # Have a new USFM verse change but no left over TWLs from the last verse
                print(f"Clearing verse list ready for USFM {BBB} {usfm_C}:{usfm_V} {current_usfm_V=} {twl_C}:{twl_V} '{orig_words}' {occurrence}")
                current_usfm_V = usfm_V
                origL_words_in_this_verse = []

            if '\\w ' not in usfm_line: # we're not really interested in it
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue # Get next usfm line

            # Add origL words that we've found in this verse
            num_words_in_this_line = usfm_line.count('\\w ')
            # print(f"For {BBB} line {usfm_line_number} {usfm_C}:{usfm_V} with marker '{usfm_marker}' found {num_words_in_this_line=}")
            num_words_added_just_now = 0
            if num_words_in_this_line:
                if usfm_marker == '\\w':
                    bar_index = usfm_rest.index('|')
                    orig_word = usfm_rest[:bar_index]
                    assert ' ' not in orig_word and '|' not in orig_word
                    origL_words_in_this_verse.append(orig_word)
                    num_words_added_just_now += 1
                else:
                    w_index = usfm_rest.index('\\w ')
                    bar_index = usfm_rest.index('|', w_index+3)
                    orig_word = usfm_rest[w_index+3:bar_index]
                    assert ' ' not in orig_word and '|' not in orig_word
                    origL_words_in_this_verse.append(orig_word)
                    num_words_added_just_now += 1
                for x in range(1, num_words_in_this_line):
                    w_index = usfm_rest.index('\\w ', bar_index+2)
                    bar_index = usfm_rest.index('|', w_index+3)
                    orig_word = usfm_rest[w_index+3:bar_index]
                    assert ' ' not in orig_word and '|' not in orig_word
                    origL_words_in_this_verse.append(orig_word)
                    num_words_added_just_now += 1
            # if origL_words_in_this_verse: print(f"For {BBB} line {usfm_line_number} {usfm_C}:{usfm_V} just added {num_words_added_just_now}/{num_words_in_this_line} to have ({len(origL_words_in_this_verse)}): {origL_words_in_this_verse}")
            assert num_words_added_just_now == num_words_in_this_line

            if ' ' not in orig_words:
                if twl_C > usfm_C or twl_V > usfm_V: # USFM needs to catch up
                    print(f"Catch up USFM from {BBB} {usfm_C}:{usfm_V} to {twl_C}:{twl_V}")
                    new_USFM_lines.append(usfm_line)
                    handled_USFM_line = True
                    continue

        if orig_words and ' ' not in orig_words \
        and twl_C==usfm_C and twl_V==usfm_V: # in the right verse with a single word TWL
            print(f"In right verse at {BBB} {usfm_C}:{usfm_V} with single word: '{orig_words}'")
            # print(f"Only one origL word: {orig_words}")
            orig_word = orig_words # There's only one!
            if f'w {orig_word}|' not in usfm_line:
                print(f"No, {BBB} {twl_C}:{twl_V} '{orig_word}' doesn't go in this line: {usfm_C}:{usfm_V} '{usfm_line}'")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            if occurrence > origL_words_in_this_verse.count(orig_word): # not there yet
                print(f"No, {orig_word} not at occurrence {occurrence} yet")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            if usfm_line.count('\\w ') == 1: # simple case -- only one word on the line
                print(f"Doing single simple action {BBB} {twl_C}:{twl_V} {orig_word}, {occurrence}, {tw_category}, {tw_word} with {usfm_line_number} {usfm_marker} {usfm_rest}")
                usfm_line = usfm_line.replace('\\w*', f' x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\w*', 1) # Add TWL to end of \w field
                simple_TWL_count += 1
                handled_TWL_line = True
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            else: # two words or more on one USFM line -- we need to insert our link in the right place
                line_word_count = usfm_line.count('\\w ')
                assert line_word_count > 1
                print(f"Got {line_word_count} words on USFM line: {usfm_line}")
                print(f"  We want to replace {orig_word}")
                line_words = re.findall(r'\\w ([^|]+?)\|', usfm_line)
                print(f"{line_words=}")
                assert len(line_words) == line_word_count
                assert len(set(line_words)) == line_word_count # i.e. no duplicates
                assert orig_word in line_words
                word_index_in_words = line_words.index(orig_word)
                print(f"{word_index_in_words=}")
                word_index_in_line = usfm_line.index(f'\\w {orig_word}|')
                word_end_index = usfm_line.index(f'\\w*', word_index_in_line)
                print(f"  Was {usfm_line=}")
                usfm_line = f'{usfm_line[:word_end_index]} x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"{usfm_line[word_end_index:]}'
                print(f"  Now {usfm_line=}")
                simple_TWL_count += 1
                handled_TWL_line = True
                if word_index_in_words == line_word_count-1: # it was the last word (if not, might be another TWL for this line)
                    new_USFM_lines.append(usfm_line)
                    handled_USFM_line = True
                continue

        if ' ' in orig_words: # multiple origL words in TWL -- this is WAY more complex -- we need \\k milestones
            print(f"At USFM {BBB} {usfm_C}:{usfm_V} and TWL {twl_C}:{twl_V} with multiple TWL words: '{orig_words}' {occurrence}")
            if new_USFM_lines[-5]: print(f" 6th previous line: {new_USFM_lines[-6]}")
            if new_USFM_lines[-5]: print(f" 5th previous line: {new_USFM_lines[-5]}")
            if new_USFM_lines[-4]: print(f" 4th previous line: {new_USFM_lines[-4]}")
            if new_USFM_lines[-3]: print(f" 3rd previous line: {new_USFM_lines[-3]}")
            if new_USFM_lines[-2]: print(f" 2nd previous line: {new_USFM_lines[-2]}")
            if new_USFM_lines[-1]: print(f"     Previous line: {new_USFM_lines[-1]}")
            print(f"      Current line: {usfm_line}")
            if (usfm_C>twl_C or (twl_C==usfm_C and usfm_V>=twl_V)):
                print(f"In multi-word right place at USFM {BBB} {usfm_C}:{usfm_V} and TWL {twl_C}:{twl_V} for '{orig_words}' {occurrence}")

                # if orig_words == 'θυσιαστηρίου τοῦ θυμιάματος': print(f"{usfm_C}:{usfm_V} {twl_C}:{twl_V}")
                # assert occurrence == 1 # Not true!!!
                assert ',' not in orig_words
                if not outstanding_orig_words_list: # we're at the first processing of the words
                    outstanding_orig_words_list = orig_words.split(' ')
                    processed_first_outstanding_orig_word = False
                    complex_TWL_count += 1

                if outstanding_orig_words_list:
                    print(f"Have outstanding TWL words: {outstanding_orig_words_list}")
                    if not processed_first_outstanding_orig_word \
                    and occurrence > ' '.join(origL_words_in_this_verse).count(orig_words): # not there yet
                        print(f"No, not at right occurrence of phrase yet: '{orig_words}' {occurrence}")
                        new_USFM_lines.append(usfm_line)
                        handled_USFM_line = True
                        continue

                    if not processed_first_outstanding_orig_word: # haven't processed any of the multiple words yet, but they should all be there now I think
                        print( f"HERE with {outstanding_orig_words_list=} and {origL_words_in_this_verse=}" )
                        assert occurrence <= ' '.join(origL_words_in_this_verse).count(orig_words)
                        last_word = outstanding_orig_words_list[-1]
                        print( f"{ outstanding_orig_words_list=} {usfm_line=}")
                        start_at = 999
                        if f'w {last_word}|' in usfm_line:
                            print(f"Mark final word '{last_word}' off in current {usfm_line=}")
                            del outstanding_orig_words_list[-1]
                            new_USFM_lines.append(usfm_line) # Note: These appends and inserts push the lines containing the earlier words even further back
                            handled_USFM_line = True
                            new_USFM_lines.append('\\k-e\\*')
                            start_at = -3
                        else: # look for the last_word in lines that were previously saved
                            for index in range (1, 7):
                                print(f"In loop1 {index=}")
                                if len(new_USFM_lines)>=index and f'w {last_word}|' in new_USFM_lines[-index]:
                                    print(f"Mark final word '{last_word}' off in {-index} line {new_USFM_lines[-index]=}")
                                    del outstanding_orig_words_list[-1]
                                    if index == 1: new_USFM_lines.append('\\k-e\\*')
                                    else: new_USFM_lines.insert(1-index, '\\k-e\\*')
                                    start_at = -index
                                    break

                        if start_at < 0: # we found the first word
                            offset = 0
                            while outstanding_orig_words_list:
                                print(f"  In outer loop2 with '{outstanding_orig_words_list}' {start_at=}")
                                while True:
                                    last_word = outstanding_orig_words_list[-1]
                                    print(f"    In inner loop2 with '{last_word}' {start_at=} {offset=} so {start_at-offset=} {offset-start_at=}")
                                    if len(new_USFM_lines)>=offset-start_at and f'w {last_word}|' in new_USFM_lines[start_at-offset]:
                                        print(f"Mark next last word '{last_word}' off in {start_at-offset} line {new_USFM_lines[start_at-offset]=}")
                                        del outstanding_orig_words_list[-1]
                                        if not outstanding_orig_words_list:
                                            new_USFM_lines[start_at-offset] = f'\\k-s |x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\*{new_USFM_lines[start_at-offset]}'
                                        break
                                    offset += 1
                                    if offset > 7:
                                        loop_overload
                            assert not outstanding_orig_words_list

                        last_word = outstanding_orig_words_list[-1] if outstanding_orig_words_list else None
                        if last_word: to_be_written_for_longer_word_list
                        else:
                            handled_TWL_line = True
                        continue
            else:
                print(f"Catch up USFM from {BBB} {usfm_C}:{usfm_V} to {twl_C}:{twl_V} with '{orig_words}' {occurrence}")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue

        raise Exception(f"Why are we looping in {BBB} USFM {usfm_C}:{usfm_V} with TWL {twl_C}:{twl_V}")

    # if new_USFM_lines: print(f"Created USFM ({len(new_USFM_lines)}): {new_USFM_lines}")
    # assert finished_USFM and finished_TWL

    if new_USFM_lines:
        print(f"Writing {len(new_USFM_lines):,} lines to {source_filepath}")
        usfm_text = '\n'.join(new_USFM_lines)
        # Fix known multi-line issues
        usfm_text = usfm_text.replace('\\k-e\\*\n.', '\\k-e\\*.').replace('\\k-e\\*\n,', '\\k-e\\*,').replace('\\k-e\\*\n;', '\\k-e\\*;').replace('\\k-e\\*\n!', '\\k-e\\*!').replace('\\k-e\\*\n?', '\\k-e\\*?')
        with open(source_filepath, 'wt') as new_USFM_output_file:
            new_USFM_output_file.write(f'{usfm_text}\n')
    return simple_TWL_count, complex_TWL_count
# end of handle_book function


def main():
    """
    """
    print("TWL_TSV6_insert_into_HebGrk.py")
    print(f"  TWL source folderpath is {LOCAL_TWL_SOURCE_FOLDERPATH}/")
    print(f"  OrigL folderpaths are {LOCAL_OT_FOLDERPATH}/ and {LOCAL_NT_FOLDERPATH}/")
    total_simple_links = total_complex_links = 0
    for BBB,nn in BBB_NUMBER_DICT.items(): # This script just handles exactly 66 books
        # if BBB != '1PE': continue
        # if BBB in ('GEN','EXO'): continue
        # if BBB not in ('MAT','MRK','LUK','JHN','ACT','ROM','1CO','2CO','GAL','EPH','PHP','COL','1TH','2TH','1TI','2TI','TIT','PHM','HEB','JAS','1PE','2PE','1JN','2JN','3JN','JUD','REV'): continue
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
# end of TWL_TSV6_insert_into_HebGrk.py
