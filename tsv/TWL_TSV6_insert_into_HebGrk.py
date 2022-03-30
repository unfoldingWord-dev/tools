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
#   Last modified: 2021-11-25 by RJH
#
#   Modified 2021-09-14 by RJH to presort TWLs before applying
#   Modified 2021-11-25 by RJH to reduce input and output folder paths to just one
#
"""
Quick script to:
    1/ Read UHB/UGNT USFM and strip out x-tw attributes and k-s/k-e milestones (if they exist -- they have now been removed from uW masters)
    2/ Read TWL TSV6 files
    3/ Insert x_tw attributes and k-s/k-e milestones into UHB/GNT USFM
"""
from typing import List, Tuple
from pathlib import Path
import re


# You have to change this single line to be correct for your own filesystem
# It should point to a folder, under which are the cloned and up-to-date en_twl, hbo_uhb, and el-x-koine_ugnt repos
LOCAL_BASE_FOLDERPATH = Path('/tmp/publish/')


# These are the derived repo paths -- input is TWL and UHB/UGNT (without TW links), output is UHB/UGNT with TW links.
LOCAL_TWL_SOURCE_FOLDERPATH = LOCAL_BASE_FOLDERPATH.joinpath('en_twl/')
# The two output folders below must also already exist and be up-to-date (because they're also used as input)!
LOCAL_OT_FOLDERPATH = LOCAL_BASE_FOLDERPATH.joinpath('hbo_uhb/')
LOCAL_NT_FOLDERPATH = LOCAL_BASE_FOLDERPATH.joinpath('el-x-koine_ugnt/')
# So this script will add TWLs to the above two folders
#  and you will probably later copy them to a Door43-Catalog repo
#   and then restore the files here changed by the script
#    (as we don't want the TW links added back into our uW repos -- only in Door43-Catalog repos)


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

debugMode = False # Enables lots more debugging output
debugMode2 = False # Enables lots more debugging output again


verse_words_list_dict = {}
def read_USFM_file(BBB:str, nn:str) -> Tuple[Path,List[str]]:
    """
    Function to read the original language (Heb/Grk) book
        and return all lines
    """
    source_folderpath = LOCAL_OT_FOLDERPATH if int(nn)<40 \
                    else LOCAL_NT_FOLDERPATH # Select HEB or GRK repo
    source_filename = f'{nn}-{BBB}.usfm'
    source_filepath = source_folderpath.joinpath(source_filename)
    # print(f"    Getting USFM source lines from {source_filepath}…")

    C = V = '0'
    source_lines = []
    verse_words_list = []
    verse_words_list_dict.clear()
    with open(source_filepath, 'rt') as source_usfm_file:
        for usfm_line in source_usfm_file:
            usfm_line = usfm_line.rstrip() # Remove trailing whitespace including nl char
            # if not line: continue # Ignore blank lines
            # print(f"Read USFM {BBB} line {line_number:3}: '{line}'")
            source_lines.append(usfm_line)

            # Keep track of where we are at
            # Note: we use strings for C & V so should handle verse ranges ok
            if usfm_line.startswith('\\c '):
                if verse_words_list:
                    verse_words_list_dict[f'{C}:{V}'] = verse_words_list
                    verse_words_list = []
                C, V = usfm_line[3:], '0'
            elif usfm_line.startswith('\\v '):
                if verse_words_list:
                    verse_words_list_dict[f'{C}:{V}'] = verse_words_list
                    verse_words_list = []
                V = usfm_line[3:]
            elif C == '0':
                if verse_words_list:
                    verse_words_list_dict[f'{C}:{V}'] = verse_words_list
                    verse_words_list = []
                V = str(int(V)+1)

            # Collect a list of words for each verse
            line_words = re.findall(r'\\w ([^|]+?)\|', usfm_line)
            # if debugMode: print(f"{line_words=}")
            verse_words_list.extend(line_words)
    if verse_words_list:
        verse_words_list_dict[f'{C}:{V}'] = verse_words_list

    return source_filepath, source_lines
# end of read_USFM_file function


def generate_USFM_source_lines(source_lines: List[str]) -> Tuple[int,int,int,str]:
    """
    Generator to read the original language (Heb/Grk) book
        and return all lines

    Yields a 3-tuple with:
        line_number C V line
    """
    C = V = 0
    for line_number,line in enumerate(source_lines, start=1):
        # Keep track of where we are at
        if line.startswith('\\c '):
            C, V = int(line[3:]), 0
        elif line.startswith('\\v '):
            V = int(line[3:])
        elif C == 0:
            V += 1

        # if line and not line.startswith('\\'): print(f"Found {source_filepath}, {line_number}, {C}:{V}, '{line}'"); halt

        # print(f"        generate_USFM_source_lines returning {source_filepath} {line_number}, {C}, {V}, '{line}'")
        yield line_number, C, V, line
# end of generate_USFM_source_lines function


def adjust_USFM_line(raw_fields:Tuple[int,int,int,str]) -> Tuple[int,int,int,str,str,str]:
    """
    Takes the raw USFM line, then
        1/ Splits the line into marker (including leading backslash) and rest
        2/ Removes existing x-tw="..." links
        3/ Removes k-s/k-e milestones (possibly leaving blank lines)
    """
    # print(f"      adjust_USFM_line({raw_fields})…")
    line_number, C, V, line = raw_fields

    # Handle special case
    if line == '\\k-e\\*': # only
        # we want to delete the entire line (rather than leaving in a superfluous blank line)
        return line_number, C, V, 'SKIP', 'SKIP', 'SKIP'

    # Remove existing TW links from USFM line
    if 'x-tw' in line:
        line = re.sub(' ?x-tw=".+?"', '', line)
        if 'x-tw' in line: # likely a missing closing quote or something
            raise Exception(f"Seems bad USFM line -- please fix first -- in line {line_number}, {C}:{V}, '{raw_fields[3]}'")

    # Remove \k start and end milestones from line
    line = line.replace('\\k-s |\\*', '')
    line = line.replace('\\k-e\\*', '')
    assert '\\k' not in line, f"\\k shouldn't be in line: '{line}'"

    # Separate into marker and rest
    # NOTE: Some lines start with opening punctuation, e.g., "(\w ...") -- this all goes in rest
    if line.startswith('\\'):
        if ' ' in line: marker, rest = line.split(' ', 1)
        else: marker, rest = line, ''
    else: marker, rest = '', line
    # print(f"        adjust_USFM_line returning {source_filepath}, {line_number}, {C}, {V} '{marker}', '{rest}'")

    return line_number, C, V, line, marker, rest
# end of adjust_USFM_line function


def read_TWL_file(input_folderpath:Path, BBB:str) -> List[List[str]]:
    """
    Function to read the TWL 6-column TSV file for a given book (BBB)
    """
    input_filepath = input_folderpath.joinpath(f'twl_{BBB}.tsv')
    # print(f"    Loading TWL {BBB} links from 6-column TSV at {input_filepath}…")
    source_fields_list = []
    with open(input_filepath, 'rt') as input_TSV_file:
        for line in input_TSV_file:
            line = line.rstrip('\n\r')
            source_fields_list.append(line.split('\t'))

    def make_TWL_line_key(line_data: List[str]) -> str:
        """
        The sort function for TWL lines

        We put headings first,
            then sort by C:V and word order from original UHB/UGNT text
        """
        if ':' not in line_data[0]: return '000' # Usually only the header line

        def clean_word(word: str) -> str:
            """
            Remove trailing punctuation, e.g., trailing comma
            """
            assert word, f"clean_word expected a non-blank word from {BBB} {reference} '{orig_TWL_words}'"
            while word[-1] in ',.!?”': word = word[:-1] # NOTE: We don't remove final single apostrophe
            return word
        # end of clean_word function

        reference, _rowID, _tags, orig_TWL_words, occurrence, _TWLink = line_data
        assert orig_TWL_words, f"make_TWL_line_key expected a non-blank word from {line_data}"
        C, V = reference.split(':')
        verse_words_list = verse_words_list_dict[reference]
        # print(f"{C}:{V} '{orig_TWL_words}' ('{occurrence}') {verse_words_list}")
        suffix = '1'
        try:
            if occurrence=='1' and ' ' not in orig_TWL_words and '־' not in orig_TWL_words: # most of the time
                orig_TWL_word = clean_word(orig_TWL_words)
                word_order = verse_words_list.index(orig_TWL_word)
                # print(f"\nGot word order {word_order} for {line_data} in {verse_words_list}\n")
            elif ' ' not in orig_TWL_words and '־' not in orig_TWL_words: # must be a higher occurrence number
                orig_TWL_word = clean_word(orig_TWL_words)
                occurrence = int(occurrence)
                word_order = -1
                while (occurrence > 0): # find the correct occurrence of the word
                    word_order = verse_words_list.index(orig_TWL_word, word_order+1)
                    # print(f"Got temp word order {word_order} for '{orig_TWL_words}' ({occurrence}) in {verse_words_list}\n")
                    occurrence -= 1
                # print(f"\nGot word order {word_order} for {line_data} in {verse_words_list}\n")
            else: # must have a space in the words
                # print(f"{C}:{V} multiword '{orig_TWL_words}' ('{occurrence}') in {verse_words_list}")
                orig_TWL_words_list = orig_TWL_words.replace('־',' ').split(' ')
                if occurrence == '1':
                    clean_first_TWL_word = clean_word(orig_TWL_words_list[0])
                    word_order = verse_words_list.index(clean_first_TWL_word)
                else:
                    occurrence = int(occurrence)
                    word_order = -1
                    clean_first_TWL_word = clean_word(orig_TWL_words_list[0])
                    while (occurrence > 0): # find the correct occurrence of the first word
                        word_order = verse_words_list.index(clean_first_TWL_word, word_order+1)
                        # print(f"Got temp word order {word_order} for '{orig_TWL_words}' ({occurrence}) in {verse_words_list}\n")
                        occurrence -= 1
                # print(f"Got temp word order {word_order} for '{orig_TWL_words}' ({occurrence}) in {verse_words_list}\n")
                while True: # Check that the remaining words also follow
                    for offset, orig_TWL_word in enumerate(orig_TWL_words_list[1:], start=1):
                        clean_TWL_word = clean_word(orig_TWL_word)
                        if verse_words_list[word_order+offset] != clean_TWL_word: # must have been the wrong occurrence
                            word_order = verse_words_list.index(clean_first_TWL_word, word_order+1)
                            break # from for
                    else: # did not break above, so must be all ok
                        break # from while
                word_order = word_order + len(orig_TWL_words_list) -1 # We use the index of the LAST word here
                suffix = str(len(orig_TWL_words_list))
        except ValueError as e:
            # One of the .index() functions above probably failed
            print(f"sort_TWL_lines: FAILED to find {BBB} {reference} '{orig_TWL_words}' ({occurrence}) in {verse_words_list}")
            return '999'
        return f'{C.zfill(3)}{V.zfill(3)}{str(word_order).zfill(2)}{suffix.zfill(2)}'
    # end of sort_TWL_lines function

    sorted_source_fields_list = sorted(source_fields_list, key=make_TWL_line_key)
    # test_reference = '3:34'
    # print(verse_words_list_dict[test_reference])
    # for fields_list in sorted_source_fields_list:
    #     if fields_list[0] == test_reference: print(fields_list)
    return sorted_source_fields_list
# end of read_TWL_file function


def get_TWL_TSV_fields(source_TSV_lines: List[str]) -> Tuple[str,str,str,str,int,str]:
    """
    Generator to read the TWL 6-column TSV file for a given book (BBB)
        and return the needed fields.

    Skips the heading row.
    Checks all fields for expected ranges.

    Returns a 6-tuple with:
        reference, rowID, tags, orig_TWL_words, occurrence, TWLink
    """
    for line_number, line in enumerate(source_TSV_lines, start=1):
        # print(f"Read TWL {BBB} line {line_number:3}: '{line}'")
        if line_number == 1:
            assert line == ['Reference','ID','Tags','OrigWords','Occurrence','TWLink'], f"Not the expected header: Got '{line}'"
        else:
            reference, rowID, tags, orig_TWL_words, occurrence, TWLink = line
            assert reference; assert rowID; assert orig_TWL_words; assert occurrence; assert TWLink # tags is optional
            assert ':' in reference, f"reference should have a colon: '{reference}'"
            assert len(rowID) == 4, f"rowID should be four characters: '{rowID}'"
            assert occurrence.isdigit(), f"occirrence should be digits: '{occurrence}'"
            assert TWLink.startswith('rc://*/tw/dict/bible/'), f"TWLink is wrong: '{TWLink}'"
            assert TWLink.count('/') == 7, f"Expected 7 slashes, not {TWLink.count('/')} in '{TWLink}'"
            # print(f"get_TWL_TSV_fields returning {reference}, {rowID}, {tags}, {orig_TWL_words}, {occurrence}, {TWLink}")
            yield reference, rowID, tags, orig_TWL_words, int(occurrence), TWLink
# end of get_TWL_TSV_fields function


def adjust_TWL_TSV_fields(raw_fields:Tuple[str,str,str,str,int,str]) -> Tuple[int,int,str,int,str,str]:
    """
    Takes the 6 raw TWL TSV fields, then
        1/ Splits the reference into C and V and converts them to integers
        2/ Gets the category and word out of the link
        3/ Drops unneeded fields
    """
    # print(f"      adjust_TWL_TSV_fields({raw_fields})…")
    reference, _rowID, _tags, orig_TWL_words, occurrence, TWLink = raw_fields
    C, V = reference.split(':')
    category, word = TWLink[len('rc://*/tw/dict/bible/'):].split('/')
    # print(f"        adjust_TWL_TSV_fields returning {int(C)}, {int(V)} {orig_TWL_words}, {int(occurrence)}, {category}, {word}")
    return int(C), int(V), orig_TWL_words, int(occurrence), category, word
# end of adjust_TWL_TSV_fields function


def handle_book(BBB:str, nn:str) -> Tuple[int,int]:
    """
    The function that handles all of the hard work for the given book
    """
    print(f"  Processing ({nn}) {BBB}…")

    # Firstly we need to read the original language text and then sort our TWL links into the correct order by B/C/V and by word/occurrence in each verse
    source_filepath, all_USFM_source_lines = read_USFM_file(BBB, nn) # It finds its own Heb or Grk folderpath
    all_TWL_source_lines = read_TWL_file(LOCAL_TWL_SOURCE_FOLDERPATH, BBB)

    # The remainder of this function inserts x-tw attributes (and some k-s milestones for multi-word links)
    #   into the UHB or UGNT source files
    simple_TWL_count = complex_TWL_count = 0
    USFM_source_line_generator = generate_USFM_source_lines(all_USFM_source_lines)
    TWL_source_line_generator = get_TWL_TSV_fields(all_TWL_source_lines)

    new_USFM_lines = []
    current_usfm_V = -1
    origLang_words_in_this_USFM_verse = [] # Built up from USFM as we process the verse (in order to detect multiple occurrences)
    outstanding_TWL_orig_words_list = [] # Outstanding TWL orig_TWL_words still to be processed
    # processed_first_outstanding_orig_word = False
    handled_USFM_line = True; finished_USFM = False
    handled_TWL_line = True; finished_TWL = False
    added_origL_words = True
    while True:
        # Get a new USFM line if necessary
        if handled_USFM_line and not finished_USFM:
            if not finished_TWL: assert added_origL_words
            try:
                usfm_line_number, usfm_C, usfm_V, usfm_line, usfm_marker, usfm_rest = adjust_USFM_line(next(USFM_source_line_generator))
                if usfm_line == 'SKIP': # This means that it was an end milestone and we want to delete the entire (now blank) line
                    usfm_line_number, usfm_C, usfm_V, usfm_line, usfm_marker, usfm_rest = adjust_USFM_line(next(USFM_source_line_generator))
                if debugMode: print(f"Got USFM {source_filepath} {usfm_line_number} {usfm_C}:{usfm_V} {current_usfm_V=} '{usfm_line}' with {len(outstanding_TWL_orig_words_list)} {outstanding_TWL_orig_words_list} and {len(origLang_words_in_this_USFM_verse)} {origLang_words_in_this_USFM_verse}")
                assert usfm_line != 'SKIP'
                handled_USFM_line = False
                if '\\w ' in usfm_line or '\\+w ' in usfm_line: added_origL_words = False # We will need to do this further down
            except StopIteration:
                # print("      Finished USFM")
                usfm_line = None
                finished_USFM = True
        # if usfm_C == 1 and usfm_V == 4: break

        # Get a new TWL line if necessary
        if handled_TWL_line and not finished_TWL:
            try:
                twl_C, twl_V, orig_TWL_words, occurrence, tw_category, tw_word = adjust_TWL_TSV_fields(next(TWL_source_line_generator))
                if debugMode: print(f"Got TWL {BBB} {twl_C}:{twl_V}, '{orig_TWL_words}', {occurrence}, '{tw_category}/{tw_word}' with {len(outstanding_TWL_orig_words_list)} {outstanding_TWL_orig_words_list} and {len(origLang_words_in_this_USFM_verse)} {origLang_words_in_this_USFM_verse}")
                handled_TWL_line = False
            except StopIteration:
                # print("      Finished TWL"); orig_TWL_words = ''
                finished_TWL = True

        # See if we're all finished
        if finished_USFM and finished_TWL: # all happy -- go take a vacation
            break

        if finished_TWL:
            new_USFM_lines.append(usfm_line)
            handled_USFM_line = True
            continue # Get next usfm line

        if usfm_C > twl_C+1 \
        or (usfm_C == twl_C+1 and usfm_V > 1) \
        or  (usfm_C == twl_C and usfm_V > twl_V+1):
            raise Exception(f"USFM {BBB} {usfm_C}:{usfm_V} went too far past TWL {twl_C}:{twl_V} '{orig_TWL_words}' {occurrence}")

        if not handled_USFM_line:
            # Clear the word list for new verses
            # if ' ' not in orig_TWL_words: # We have to delay this if still have orig_TWL_words to process from the last verse
            if usfm_V != current_usfm_V \
            and twl_C==usfm_C and twl_V > usfm_V : # Have a new USFM verse change but no left over TWLs from the last verse
                if debugMode: print(f"Clearing verse list ready for USFM {BBB} {usfm_C}:{usfm_V} {current_usfm_V=} {twl_C}:{twl_V} '{orig_TWL_words}' {occurrence}")
                current_usfm_V = usfm_V
                origLang_words_in_this_USFM_verse = [] # definition of a word here is "inside a \w ...\w*" field in the Heb/Grk

            if '\\w ' in usfm_line or '\\+w ' in usfm_line: # we're interested in it
                # Add origL words that we've found in this verse
                num_words_in_this_line = usfm_line.count('\\w ') + usfm_line.count('\\+w ')
                if debugMode: print(f"For {BBB} line {usfm_line_number} {usfm_C}:{usfm_V} with marker '{usfm_marker}' found {num_words_in_this_line=}")
                if num_words_in_this_line and not added_origL_words:
                    num_words_added_just_now = 0
                    bar_index = -1
                    for x in range(0, num_words_in_this_line):
                        try: w_index = usfm_line.index('\\w ', bar_index+1)
                        except ValueError: w_index = usfm_line.index('\\+w ', bar_index+1) + 1 # for plus sign
                        bar_index = usfm_line.index('|', w_index+3)
                        origLang_USFM_word = usfm_line[w_index+3:bar_index]
                        if debugMode: print(f"  About to append '{origLang_USFM_word}' to USFM verse words list: space={' ' in origLang_USFM_word} bar={'|' in origLang_USFM_word} maqaf={'־' in origLang_USFM_word}")
                        assert ' ' not in origLang_USFM_word and '|' not in origLang_USFM_word and '־' not in origLang_USFM_word # maqaf
                        origLang_words_in_this_USFM_verse.append(origLang_USFM_word) # definition of a word here is "inside a \w ...\w*" field in the Heb/Grk
                        num_words_added_just_now += 1
                    if debugMode:
                        if origLang_words_in_this_USFM_verse: print(f"Just appended USFM {num_words_added_just_now}/{num_words_in_this_line} words to have ({len(origLang_words_in_this_USFM_verse)}) {origLang_words_in_this_USFM_verse} for {BBB} line {usfm_line_number} {usfm_C}:{usfm_V}")
                    assert num_words_added_just_now == num_words_in_this_line
                    added_origL_words = True

                if ' ' not in orig_TWL_words and '־' not in orig_TWL_words:
                    if twl_C > usfm_C or twl_V > usfm_V: # USFM needs to catch up
                        if debugMode: print(f"Catch up USFM from {BBB} {usfm_C}:{usfm_V} to {twl_C}:{twl_V}")
                        new_USFM_lines.append(usfm_line)
                        handled_USFM_line = True
                        continue
            else: # no \w in usfm_line so we're not really interested in it
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue # Get next usfm line

        if orig_TWL_words and ' ' not in orig_TWL_words and '־' not in orig_TWL_words \
        and twl_C==usfm_C and twl_V==usfm_V: # in the right verse with a single word TWL
            if debugMode: print(f"In right verse at {BBB} {usfm_C}:{usfm_V} with single TWL word: '{orig_TWL_words}'{'' if occurrence==1 else ' occurrence='+str(occurrence)}")
            orig_TWL_word = orig_TWL_words # There's only one!
            if f'w {orig_TWL_word}|' not in usfm_line:
                if debugMode: print(f"No, {BBB} {twl_C}:{twl_V} '{orig_TWL_word}' doesn't go in this line: {usfm_C}:{usfm_V} '{usfm_line}' having {origLang_words_in_this_USFM_verse}")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            if occurrence > origLang_words_in_this_USFM_verse.count(orig_TWL_word): # not there yet
                if debugMode: print(f"No, '{orig_TWL_word}' not at occurrence {occurrence} yet")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            elif occurrence==1:
                if debugMode: print(f"Yes, seems that '{orig_TWL_word}' is at first occurrence now with {len(origLang_words_in_this_USFM_verse)} {origLang_words_in_this_USFM_verse}")
            else:
                if debugMode: print(f"Yes, seems that '{orig_TWL_word}' is at occurrence {occurrence} already with {len(origLang_words_in_this_USFM_verse)} {origLang_words_in_this_USFM_verse}")
            if usfm_line.count('\\w ') == 1: # simple case -- only one word on the line
                if debugMode: print(f"Doing single simple x-tw insert action {BBB} {twl_C}:{twl_V} {orig_TWL_word}, {occurrence}, {tw_category}, {tw_word} on line {usfm_line_number}: {usfm_marker} {usfm_rest}")
                usfm_line = usfm_line.replace('\\w*', f' x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\w*', 1) # Add TWL to end of \w field
                simple_TWL_count += 1
                handled_TWL_line = True
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            elif usfm_line.count('\\+w ') == 1: # simple case -- only one word on the line (probably in a footnote)
                if debugMode: print(f"Doing single simple+ x-tw insert action {BBB} {twl_C}:{twl_V} {orig_TWL_word}, {occurrence}, {tw_category}, {tw_word} on line {usfm_line_number}: {usfm_marker} {usfm_rest}")
                usfm_line = usfm_line.replace('\\+w*', f' x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\+w*', 1) # Add TWL to end of \w field
                simple_TWL_count += 1
                handled_TWL_line = True
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue
            else: # two words or more on one USFM line -- we need to insert our link in the right place
                line_word_count = usfm_line.count('\\w ') + usfm_line.count('\\+w ')
                if usfm_line.count('\\+w '): print("Haven't written this code yet!!!"); dieWithWPlus
                assert line_word_count > 1
                if debugMode: print(f"Got {line_word_count} words on USFM line: {usfm_line}")
                if debugMode: print(f"  We want to replace {orig_TWL_word}")
                line_words = re.findall(r'\\w ([^|]+?)\|', usfm_line)
                if debugMode: print(f"{line_words=}")
                assert len(line_words) == line_word_count, f"These two word counts should match: {len(line_words)} and {line_word_count}"
                assert len(set(line_words)) == line_word_count, f"There should be no duplicates: {len(set(line_words))} and {line_word_count}"
                assert orig_TWL_word in line_words
                word_index_in_words = line_words.index(orig_TWL_word)
                if debugMode: print(f"{word_index_in_words=}")
                word_index_in_line = usfm_line.index(f'\\w {orig_TWL_word}|')
                word_end_index = usfm_line.index(f'\\w*', word_index_in_line)
                if debugMode: print(f"  Was {usfm_line=}")
                usfm_line = f'{usfm_line[:word_end_index]} x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"{usfm_line[word_end_index:]}'
                if debugMode: print(f"  Now {usfm_line=}")
                simple_TWL_count += 1
                handled_TWL_line = True
                if word_index_in_words == line_word_count-1: # it was the last word (if not, might be another TWL for this line)
                    new_USFM_lines.append(usfm_line)
                    handled_USFM_line = True
                continue

        if ' ' in orig_TWL_words or '־' in orig_TWL_words: # multiple origL words in TWL -- this is WAY more complex -- we need \\k milestones
            if debugMode:
                print(f"At USFM {BBB} {usfm_C}:{usfm_V} and TWL {twl_C}:{twl_V} with multiple TWL words: '{orig_TWL_words}' {occurrence} {outstanding_TWL_orig_words_list}")
                if new_USFM_lines[-5]: print(f" 6th previous line: {new_USFM_lines[-6]}")
                if new_USFM_lines[-5]: print(f" 5th previous line: {new_USFM_lines[-5]}")
                if new_USFM_lines[-4]: print(f" 4th previous line: {new_USFM_lines[-4]}")
                if new_USFM_lines[-3]: print(f" 3rd previous line: {new_USFM_lines[-3]}")
                if new_USFM_lines[-2]: print(f" 2nd previous line: {new_USFM_lines[-2]}")
                if new_USFM_lines[-1]: print(f"     Previous line: {new_USFM_lines[-1]}")
                print(f"      Current line: {usfm_line}")
            if (usfm_C>twl_C or (twl_C==usfm_C and usfm_V>=twl_V)):
                if debugMode: print(f"In multi-word right place at USFM {BBB} {usfm_C}:{usfm_V} and TWL {twl_C}:{twl_V} for TWL '{orig_TWL_words}' {occurrence} {outstanding_TWL_orig_words_list}")

                # if orig_TWL_words == 'θυσιαστηρίου τοῦ θυμιάματος': print(f"{usfm_C}:{usfm_V} {twl_C}:{twl_V}")
                # Not true!!! assert occurrence == 1
                # Not true!!! assert ',' not in orig_TWL_words, f"Should be no comma in {BBB} {twl_C}:{twl_V} '{orig_TWL_words}'"
                assert ';' not in orig_TWL_words and '?' not in orig_TWL_words and '!' not in orig_TWL_words and '.' not in orig_TWL_words, f"Should be no sentence end punctuation in {BBB} {twl_C}:{twl_V} '{orig_TWL_words}'"
                assert '“' not in orig_TWL_words and '”' not in orig_TWL_words and '‘' not in orig_TWL_words, f"Should be no quote marks in {BBB} {twl_C}:{twl_V} '{orig_TWL_words}'"
                if not outstanding_TWL_orig_words_list: # we're at the first processing of the words
                    temp_words = ( orig_TWL_words.replace('־', ' ') # We want to split on either
                                            .replace(',', '') ) # We don't want punctuation to get a list of words
                    outstanding_TWL_orig_words_list = temp_words.split(' ')
                    assert len(outstanding_TWL_orig_words_list) > 1, f"Should be greater than one: {BBB} {twl_C}:{twl_V} {len(outstanding_TWL_orig_words_list)}"
                    # processed_first_outstanding_orig_word = False
                    complex_TWL_count += 1

                if outstanding_TWL_orig_words_list:
                    if debugMode: print(f"Have outstanding TWL origLang words: {outstanding_TWL_orig_words_list}")

                    # if not processed_first_outstanding_orig_word and
                    if occurrence > ' '.join(origLang_words_in_this_USFM_verse).count(orig_TWL_words.replace('־', ' ').replace(',', '')): # not there yet
                        if debugMode: print(f"No, not at right occurrence of {BBB} {twl_C}:{twl_V} phrase yet: '{orig_TWL_words}' {occurrence} with {origLang_words_in_this_USFM_verse}")
                        new_USFM_lines.append(usfm_line)
                        handled_USFM_line = True
                        continue

                    # if not processed_first_outstanding_orig_word: # haven't processed any of the multiple words yet, but they should all be there now I think
                    if debugMode: print( f"NEED ACTION NOW coz here with {outstanding_TWL_orig_words_list=} and {origLang_words_in_this_USFM_verse=}")
                    assert occurrence <= ' '.join(origLang_words_in_this_USFM_verse).count(orig_TWL_words.replace('־', ' ').replace(',', '')), f"Occurrence {occurrence} should be <= {' '.join(origLang_words_in_this_USFM_verse).count(orig_TWL_words.replace('־', ' '))}"
                    # NOTE: We handle the multi-word TWL from the end, i.e., process the last word first
                    last_TWL_word = outstanding_TWL_orig_words_list[-1]
                    if debugMode: print( f"{ outstanding_TWL_orig_words_list=} {usfm_line=}")
                    start_at_line_offset = 999
                    if usfm_line and f'w {last_TWL_word}|' in usfm_line:
                        if debugMode and debugMode2: print(f"Mark final word '{last_TWL_word}' of {len(outstanding_TWL_orig_words_list)} off in current {usfm_line=}")
                        del outstanding_TWL_orig_words_list[-1]
                        new_USFM_lines.append(usfm_line) # Note: These appends and inserts push the lines containing the earlier words even further back
                        handled_USFM_line = True
                        new_USFM_lines.append('\\k-e\\*')
                        start_at_line_offset = -2
                    else: # look for the last_TWL_word in lines that were previously saved
                        if debugMode: print("Look for the last_TWL_word in lines that were previously saved…")
                        for index in range (1, 7):
                            if debugMode and debugMode2: print(f"In loop1 {index=}")
                            if len(new_USFM_lines)>=index and f'w {last_TWL_word}|' in new_USFM_lines[-index]:
                                if debugMode and debugMode2: print(f"Mark final word '{last_TWL_word}' of {len(outstanding_TWL_orig_words_list)} off in {-index} line {new_USFM_lines[-index]=}")
                                del outstanding_TWL_orig_words_list[-1]
                                if index == 1: new_USFM_lines.append('\\k-e\\*')
                                else: new_USFM_lines.insert(1-index, '\\k-e\\*')
                                start_at_line_offset = -index
                                break

                    if start_at_line_offset < 0: # we found the first word of a multi-word TWL
                        next_line_offset = 0
                        while outstanding_TWL_orig_words_list:
                            if debugMode and debugMode2: print(f"  In outer loop2 with '{outstanding_TWL_orig_words_list}' {start_at_line_offset=}")
                            while True:
                                last_TWL_word = outstanding_TWL_orig_words_list[-1]
                                if debugMode and debugMode2: print(f"    In inner loop2 with '{last_TWL_word}' {start_at_line_offset=} {next_line_offset=} so {start_at_line_offset-next_line_offset=} {next_line_offset-start_at_line_offset=}")
                                if len(new_USFM_lines)>=next_line_offset-start_at_line_offset and f'w {last_TWL_word}|' in new_USFM_lines[start_at_line_offset-next_line_offset]:
                                    if debugMode and debugMode2: print(f"Mark next last word '{last_TWL_word}' off in {start_at_line_offset-next_line_offset} line {new_USFM_lines[start_at_line_offset-next_line_offset]=}")
                                    del outstanding_TWL_orig_words_list[-1]
                                    if not outstanding_TWL_orig_words_list: # we've place all the words
                                        # Now we need to place the k-s milestone correctly within the line
                                        old_line_contents = new_USFM_lines[start_at_line_offset-next_line_offset]
                                        char_index = 0 # default to start of line
                                        old_line_word_indexes = [match.start() for match in re.finditer(rf'\\w {last_TWL_word}\|', old_line_contents)]
                                        if debugMode and debugMode2: print(f"Got {len(old_line_word_indexes)} re matches: {old_line_word_indexes=}")
                                        assert len(old_line_word_indexes) == 1, f"Didn't expect the same word twice in one line: {len(old_line_word_indexes)}"
                                        char_index = old_line_word_indexes[0]
                                        if debugMode and debugMode2: print(f"Got {char_index=} from {old_line_word_indexes}")
                                        new_USFM_lines[start_at_line_offset-next_line_offset] = f'{old_line_contents[:char_index]}\\k-s |x-tw="rc://*/tw/dict/bible/{tw_category}/{tw_word}"\\*{old_line_contents[char_index:]}'
                                    break
                                next_line_offset += 1
                                if next_line_offset > 7:
                                    loop_overload
                        assert not outstanding_TWL_orig_words_list, f"Should be no outstanding original words left: {outstanding_TWL_orig_words_list}"

                    last_TWL_word = outstanding_TWL_orig_words_list[-1] if outstanding_TWL_orig_words_list else None
                    if last_TWL_word: to_be_written_for_longer_word_list
                    else:
                        handled_TWL_line = True
                    continue
            else:
                if debugMode: print(f"Catch up USFM from {BBB} {usfm_C}:{usfm_V} to {twl_C}:{twl_V} with '{orig_TWL_words}' {occurrence}")
                new_USFM_lines.append(usfm_line)
                handled_USFM_line = True
                continue

        raise Exception(f"Why are we looping in {BBB} USFM {usfm_C}:{usfm_V} with TWL {twl_C}:{twl_V} '{orig_TWL_words}': {tw_word}")

    # if new_USFM_lines: print(f"Created USFM ({len(new_USFM_lines)}): {new_USFM_lines}")
    # assert finished_USFM and finished_TWL

    if new_USFM_lines:
        print(f"    Writing {len(new_USFM_lines):,} lines to {source_filepath}")
        usfm_text = '\n'.join(new_USFM_lines)
        # Fix known multi-line issues
        usfm_text = ( usfm_text
            # Get rid of blank lines
            .replace('\\k-e\\*\n\n\\w', '\\k-e\\*\n\\w').replace('\\k-e\\*\n\n\\v', '\\k-e\\*\n\\v')
            # Move sentence punctuation out of the end of k-s k-e sets
            .replace('\\w*,\n\\k-e\\*', '\\w*\n\\k-e\\*,').replace('\\w*;\n\\k-e\\*', '\\w*\n\\k-e\\*;').replace('\\w*.\n\\k-e\\*', '\\w*\n\\k-e\\*.').replace('\\w*?\n\\k-e\\*', '\\w*\n\\k-e\\*?').replace('\\w*!\n\\k-e\\*', '\\w*\n\\k-e\\*!')
            # Move stand-alone punctuation up to end of k-e lines
            .replace('\\k-e\\*\n.', '\\k-e\\*.').replace('\\k-e\\*\n,', '\\k-e\\*,').replace('\\k-e\\*\n;', '\\k-e\\*;').replace('\\k-e\\*\n!', '\\k-e\\*!').replace('\\k-e\\*\n?', '\\k-e\\*?')
            # Move stand-alone special Hebrew punctuation up to end of k-e lines
            .replace('\\k-e\\*\nס', '\\k-e\\*ס').replace('\\k-e\\*\nפ', '\\k-e\\*פ').replace('\\k-e\\*\n׃', '\\k-e\\*׃')
        )
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
    fail_list = []
    for BBB,nn in BBB_NUMBER_DICT.items(): # This script just handles exactly 66 books
        # if BBB in ('GEN','EXO','LEV','NUM','DEU','JOS','JDG','RUT','1SA','2SA','1KI',
        #         '2KI','1CH','2CH','EZR', 'NEH', 'EST','JOB','PSA','PRO','ECC','SNG','ISA',
        #         'JER','LAM','EZK','DAN','HOS','JOL', 'AMO','OBA','JON','MIC','NAM','HAB',
        #         'ZEP','HAG','ZEC','MAL'): continue # Skip OT
        # if BBB in ('MAT','MRK','LUK','JHN','ACT','ROM','1CO','2CO','GAL','EPH','PHP','COL','1TH','2TH','1TI','2TI','TIT','PHM','HEB','JAS','1PE','2PE','1JN','2JN','3JN','JUD','REV'):
        #     continue # Skip NT
        # if BBB != 'LUK': continue # only process this one book
        try:
            simple_count, complex_count = handle_book(BBB, nn)
            total_simple_links += simple_count
            total_complex_links += complex_count
        except Exception as e:
            fail_list.append(BBB)
            print(f"ERROR: failed to process {BBB}: {e}")
    if fail_list:
        print(f"The following {len(fail_list)} books FAILED: {fail_list}")
        print("PLEASE REVERT THESE CHANGES, FIX THE FAILING BOOKS, AND THEN RERUN!")
    else:
        print(f"    {total_simple_links+total_complex_links:,} total links written ({total_simple_links:,} simple links and {total_complex_links:,} multiword links) to {LOCAL_OT_FOLDERPATH}/ and {LOCAL_NT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TWL_TSV6_insert_into_HebGrk.py
