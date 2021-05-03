#!/usr/bin/env python3
#
# TW_HebGrk_to_TSV6_TWL.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Apr 2020 by RJH
#   Last modified: 2021-04-30 by RJH
#
"""
Quick script to copy TW links out of UHB and UGNT
    and put into a TSV file with 6 columns.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_OT_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('hbo_uhb/')
LOCAL_NT_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('el-x-koine_ugnt/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_twl/')

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
SIMPLE_TW_LINK_RE = re.compile(r'x-tw="([-:/\*a-z0-9]+?)" ?\\w\*') # Only occurs inside a \\w field (at end)
MILESTONE_TW_LINK_RE = re.compile(r'\\k-s \| ?x-tw="([:/\*a-z0-9]+?)" ?\\\*')
BAD_CONSECUTIVE_TW_LINK_RE = re.compile(r'x-tw="([-:/\*a-z0-9]+?)" ?x-tw="([-:/\*a-z0-9]+?)" ?\\w\*')
BAD_CONSECUTIVE_MORPH_RE = re.compile(r'x-morph="([,A-za-z0-9]+?)" ?x-morph="([,A-za-z0-9]+?)" ?\\w\*')
# WORD_JOINER_RE = re.compile(r'\\w\*(.)\\w ') # Whatever's between two word fields

def get_source_lines(BBB:str, nn:str) -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the original language (Heb/Grk) book
        and return lines containing TW links.

    Yields a 7-tuple with:
        line_number(int) B C V word occurrence(int) link
    """
    source_folderpath = LOCAL_OT_SOURCE_FOLDERPATH if int(nn)<40 \
                    else LOCAL_NT_SOURCE_FOLDERPATH
    source_filename = f'{nn}-{BBB}.usfm'
    source_filepath = source_folderpath.joinpath(source_filename)
    print(f"      Getting source lines from {source_filepath}…")

    C = V = ''
    lastLine = ''
    is_in_k = False
    this_verse_words:List[str] = []
    with open(source_filepath, 'rt') as source_usfm_file:
        for line_number,line in enumerate(source_usfm_file, start=1):
            line = line.rstrip() # Remove trailing whitespace including nl char
            if not line: continue # Ignore blank lines

            # Keep track of where we are at
            if line.startswith('\\c '):
                C, V = line[3:], '0'
                assert C.isdigit()
                continue
            elif line.startswith('\\v '):
                V = line[3:]
                assert V.isdigit()
                this_verse_words = []
                continue

            # if line == '\\w עַל|lemma="עַל" strong="H5921a" x-morph="He,R" x-tw="rc://*/tw/dict/bible/other/overseer" \\w*־\\k-s | x-tw="rc://*/tw/dict/bible/names/redsea" \\w יַם|lemma="יָם" strong="H3220" x-morph="He,Ncmsc" \\w*־\\w סֽוּף|lemma="סוּף" strong="H5488" x-morph="He,Ncmsa" \\w*\\k-e\\*׃':
            #     print("FIXING BAD NEH 9:9 LINE!!!!")
            #     line = '\\w עַל|lemma="עַל" strong="H5921a" x-morph="He,R" x-tw="rc://*/tw/dict/bible/other/overseer" \\w*־\\k-s | x-tw="rc://*/tw/dict/bible/names/redsea"\\* \\w יַם|lemma="יָם" strong="H3220" x-morph="He,Ncmsc" \\w*־\\w סֽוּף|lemma="סוּף" strong="H5488" x-morph="He,Ncmsa" \\w*\\k-e\\*׃'

            # Get any words out of line (needed for occurrences)
            this_line_words = []
            word_match = SINGLE_WORD_RE.search(line, 0)
            # NOTE: This doesn't tell us what the character is between the words -- we later wrongly assume it's just a space
            while word_match:
                this_line_words.append(word_match.group(1))
                this_verse_words.append(word_match.group(1))
                word_match = SINGLE_WORD_RE.search(line, word_match.end())

            if 'x-tw' not in line and '\\k' not in line and not is_in_k:
                continue # Ignore unnecessary lines
            # print(f"{BBB} {C}:{V} line={line}")
            assert line.count('x-tw') <= line.count('\\w ') + line.count('\\k-s'), f"Too many x-tw's in line: '{line}' -- please fix first and rerun"
            assert not BAD_CONSECUTIVE_MORPH_RE.search(line), f"Too many consecutive x-morph's in word: '{line}' -- please fix first and rerun"
            assert not BAD_CONSECUTIVE_TW_LINK_RE.search(line), f"Too many consecutive x-tw's in word: '{line}' -- please fix first and rerun"

            # Should only have relevant lines of the file now
            # NOTE: Be careful as \\k-s can occur mid-line, e.g., NEH 9:9 !!!
            if '\\k-s' in line:
                assert not is_in_k
                if line.startswith( '\\k-s'):
                    is_in_k = True
                else:
                    # print(f"NOTE: \\k-s field in the middle of a line: {line}")
                    is_in_k = 0.5 # !!!!
            # print(f"{line_number:4}/ {BBB} {C}:{V:<3} is_in_k={is_in_k} line={line}")

            # Make sure that the data looks like what we were expecting -- no surprises
            if '\\k' not in line:
                # print(line)
                assert line.startswith('\\w ') \
                    or line[0] in '([' and line[1:].startswith('\\w ') \
                    or line.startswith('\\f ') # and '\\ft* \\w ' in line # Josh 8:16
            if not line.startswith('\\k-e\\*') and not line.startswith('\\k-s |'):
                assert line.count('\\w ') >= 1
                assert line.count('\\w*') == line.count('\\w ')

            searchW_startIndex = 'BAD' # Just to catch any logic errors below
            if is_in_k == 0.5: # the \\k-s is MID-LINE
                assert '\\k-s' in line and not line.startswith('\\k-s')
                assert line.count('x-tw="') >= 1
                milestone_link_match = MILESTONE_TW_LINK_RE.search(line)
                if milestone_link_match:
                    milestone_link = milestone_link_match.group(1)
                    assert milestone_link.startswith('rc://*/tw/dict/bible/')
                    remembered_line_number = line_number
                    milestone_words_list = []
                    searchW_startIndex = milestone_link_match.end()
                else:
                    logging.critical(f"Have a problem with \\k-s on {BBB} {C}:{V} line {line_number:,} in {source_filename}")
                if '\\k-e' in line:
                    ke_index = line.index('\\k-e')

                    assert len(this_line_words) >= 1
                    word_field_match = WORD_FIELD_RE.search(line, searchW_startIndex)
                    while word_field_match:
                        word_field = word_field_match.group(1)
                        word_match = SINGLE_WORD_RE.search(word_field)
                        assert word_match
                        word = word_match.group(1)
                        assert ' ' not in word
                        assert word_match.start() < ke_index
                        occurrence = this_verse_words.count(word)
                        if is_in_k: milestone_words_list.append(word)
                        simple_link_match = SIMPLE_TW_LINK_RE.search(word_field)
                        if simple_link_match:
                            word_link = simple_link_match.group(1)
                            assert word_link.startswith('rc://*/tw/dict/bible/')
                            # print("here2", C,V, word, occurrence, this_verse_words, word_link)
                            yield line_number, BBB, C, V, word, occurrence, word_link
                        word_field_match = WORD_FIELD_RE.search(line, word_field_match.end())
                    searchW_startIndex = 'BADBAD' # Just to catch any logic errors

                    is_in_k = False
                    assert milestone_words_list
                    if len(milestone_words_list) == 1:
                        milestone_words = milestone_words_list[0]
                    elif len(milestone_words_list) == 2:
                        # print(f"HERE A2: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'")
                        joiner = '־' if '\\w*־\\w' in lastLine else ' '
                        milestone_words = f"{milestone_words_list[0]}{joiner}{milestone_words_list[1]}"
                    elif len(milestone_words_list) == 3:
                        # print(f"HERE A3: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'")
                        second_joiner = '־' if '\\w*־\\w' in lastLine else ' '
                        milestone_words = f"{milestone_words_list[0]} {milestone_words_list[1]}{second_joiner}{milestone_words_list[2]}"
                    else:
                        # print(f"HERE A9: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'")
                        milestone_words = ' '.join(milestone_words_list)
                    # print("here0", C,V, milestone_words_list, occurrence, milestone_link)
                    yield remembered_line_number, BBB, C, V, milestone_words, occurrence, milestone_link
                    del remembered_line_number, milestone_words, milestone_link # Don't let them persist -- just so we catch any logic errors
                    continue
                else: # k-s is fully open now
                    is_in_k = True
                # There might still be a \w field on the line, but it's caught below
            elif is_in_k: # line started with \\k-s
                if '\\k-s' in line:
                    assert line.startswith('\\k-s ')
                    assert line.count('x-tw="') >= 1
                    milestone_link_match = MILESTONE_TW_LINK_RE.search(line)
                    if milestone_link_match:
                        milestone_link = milestone_link_match.group(1)
                        assert milestone_link.startswith('rc://*/tw/dict/bible/')
                        remembered_line_number = line_number
                        milestone_words_list = []
                        searchW_startIndex = milestone_link_match.end()
                    else:
                        logging.critical(f"Have a problem with \\k-s on {BBB} {C}:{V} line {line_number:,} in {source_filename}")
                    # There might still be a \w field on the line, but it's caught below
                    assert '\\k-e' not in line
                elif '\\k-e' in line:
                    assert line.startswith('\\k-e\\*')
                    assert '\\w' not in line  #  } Don't really care about
                    assert 'x-tw' not in line #  }  any left-over Hebrew chars in line
                    is_in_k = False
                    assert milestone_words_list
                    if len(milestone_words_list) == 1:
                        milestone_words = milestone_words_list[0]
                    elif len(milestone_words_list) == 2:
                        # print(f"HERE B2: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'");
                        joiner = '־' if '\\w*־\\w' in lastLine else ' '
                        milestone_words = f"{milestone_words_list[0]}{joiner}{milestone_words_list[1]}"
                    elif len(milestone_words_list) == 3:
                        # print(f"HERE B3: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'");
                        second_joiner = '־' if '\\w*־\\w' in lastLine else ' '
                        milestone_words = f"{milestone_words_list[0]} {milestone_words_list[1]}{second_joiner}{milestone_words_list[2]}"
                    else:
                        # print(f"HERE B9: {BBB} {C}:{V} have ({len(milestone_words_list)}) {milestone_words_list} from '{lastLine}'");
                        milestone_words = ' '.join(milestone_words_list)
                    # print("here1a", C,V, milestone_words_list, occurrence, milestone_link, this_verse_words)
                    words_occurrence = ' '.join(this_verse_words).count(' '.join(milestone_words_list))
                    assert words_occurrence >= 1 # else we didn't find the words at all! (What about punctuation???)
                    if words_occurrence != occurrence:
                        occurrence = words_occurrence
                        # print("here1b", C,V, milestone_words, occurrence, milestone_link)
                    yield remembered_line_number, BBB, C, V, milestone_words, occurrence, milestone_link
                    del remembered_line_number, milestone_words_list, milestone_link # Don't let them persist -- just so we catch any logic errors
                    continue
                else: # the simpler single line case -- usually one, sometimes two \\w fields on a line
                    searchW_startIndex = 0 # Look for words right from the beginning of the line
            else: # the simpler single line case -- usually one, sometimes two \\w fields on a line
                searchW_startIndex = 0 # Look for words right from the beginning of the line

            if this_line_words:
                # print(f"        line={line}")
                # assert len(this_line_words) >= 1 or line.startswith('\\k-s |')
                # print(f"        this_line_words ({len(this_line_words)})={this_line_words}")
                word_field_match = WORD_FIELD_RE.search(line, searchW_startIndex)
                while word_field_match:
                    # print(f"\n          {C}:{V} searchW_startIndex={searchW_startIndex}")
                    # print(f"          word_field_match={word_field_match}")
                    word_field = word_field_match.group(1)
                    # print(f"          word_field={word_field}")
                    word_match = SINGLE_WORD_RE.search(word_field)
                    # print(f"          word_match={word_match}")
                    assert word_match
                    word = word_match.group(1)
                    assert ' ' not in word
                    occurrence = this_verse_words.count(word)
                    # print(f"          occurrence={occurrence}")
                    if is_in_k: milestone_words_list.append(word)
                    simple_link_match = SIMPLE_TW_LINK_RE.search(word_field)
                    # print(f"          simple_link_match={simple_link_match}")
                    if simple_link_match:
                        word_link = simple_link_match.group(1)
                        assert word_link.startswith('rc://*/tw/dict/bible/')
                        # print("here9", C,V, word, occurrence, this_verse_words, word_link)
                        yield line_number, BBB, C, V, word, occurrence, word_link
                    word_field_match = WORD_FIELD_RE.search(line, word_field_match.end())
                searchW_startIndex = 'BADBADBAD' # Just to catch any logic errors above

            lastLine = line
# end of get_source_lines function


def make_TSV_file(BBB:str, nn:str) -> Tuple[int,int]:
    """
    """
    source_text = 'UHB' if int(nn)<40 else 'UGNT'
    print(f"    Converting {source_text} {BBB} links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'twl_{BBB}.tsv')

    try: # Load the previous file so we can use the same row ID fields
        with open(output_filepath, 'rt') as previous_file:
            previous_text = previous_file.read()
        original_TWL_lines = previous_text.split('\n')
        # for j,line in enumerate(original_TWL_lines):
        #     print(f"{j+1}: '{line}'")
        original_TWL_lines = original_TWL_lines[1:] # Skip header row
        if not original_TWL_lines[-1]: original_TWL_lines = original_TWL_lines[:-1] # Skip last empty line
        print(f"      Loaded {len(original_TWL_lines):,} lines from previous version of {output_filepath}")
    except Exception: original_TWL_lines = [] # ignore this if it fails

    num_simple_links = num_multiword_links = j = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Reference\tID\tTags\tOrigWords\tOccurrence\tTWLink\n')
        previously_generated_ids:List[str] = [''] # We make ours unique per file (spec only says unique per verse)
        for j, (_line_number,BBB,C,V,word,occurrence,link) in enumerate(get_source_lines(BBB, nn), start=1):
            # if occurrence != 1:
            #     print(f"{j:3}/ Line {_line_number:<5} {BBB} {C:>3}:{V:<3} '{word}' {occurrence} {link}")
            reference = f'{C}:{V}'
            tags = ''
            if '/bible/kt/jesus' in link: tags = 'keyterm; name'
            elif '/bible/names/' in link: tags = 'name'
            elif '/bible/kt/' in link: tags = 'keyterm'
            # elif '/bible/other/' in link: tags = 'other'

            found_id = None
            # print(f"NEW {reference} ---- {tags} {link} {word} {occurrence} '{annotation}'")
            for old_line in original_TWL_lines:
                old_reference, old_id, old_tags, old_word, old_occurrence, old_link = old_line.split('\t')
                # print(f"OLD {old_reference} {old_id} {old_tags} {old_link} {old_word} {old_occurrence} '{old_annotation}'")
                if old_reference==reference and old_tags==tags and old_link==link and old_word==word and old_occurrence==str(occurrence):
                    found_id = old_id
                    break
            if found_id:
                # print(f"        Found {found_id} for {reference} {tags} {link} {word} {occurrence}")
                if found_id in previously_generated_ids:
                    print(f"We had an error with {found_id} for {reference} {tags} {link} {word} {occurrence}!!!")
                    halt
                row_id = found_id
            else:
                generated_id = ''
                while generated_id in previously_generated_ids:
                    # NOTE: We don't use 0o or 1il below coz they're easier to confuse
                    generated_id = random.choice('abcdefghjkmnpqrstuvwxyz') + random.choice('abcdefghjkmnpqrstuvwxyz23456789') + random.choice('abcdefghjkmnpqrstuvwxyz23456789') + random.choice('abcdefghjkmnpqrstuvwxyz23456789')
                print(f"        Generated {generated_id} for {BBB} {reference} {tags} {word} {occurrence} {link}")
                row_id = generated_id
            previously_generated_ids.append(row_id)

            output_line = f'{reference}\t{row_id}\t{tags}\t{word}\t{occurrence}\t{link}'
            output_TSV_file.write(f'{output_line}\n')
            if ' ' in word: num_multiword_links += 1
            else: num_simple_links += 1
            assert '&' not in word # We don't have any of these
            assert '…' not in word # This one is now obsolete
    print(f"      {j:,} links written ({num_simple_links:,} simple links and {num_multiword_links:,} multiword links)")
    return num_simple_links, num_multiword_links
# end of make_TSV_file function


def main():
    """
    """
    print("TW_HebGrk_to_TSV6_TWL.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_simple_links = total_multiword_links = 0
    fail_list = []
    for BBB,nn in BBB_NUMBER_DICT.items():
        # if BBB != 'MAT': continue
        try:
            simple_count, complex_count = make_TSV_file(BBB,nn)
            total_simple_links += simple_count
            total_multiword_links += complex_count
        except Exception as e:
            fail_list.append(BBB)
            print(f"ERROR: failed to process {BBB}: {e}")
    if fail_list:
        print(f"The following {len(fail_list)} books FAILED: {fail_list}")
        print("PLEASE REVERT THESE CHANGES, FIX THE FAILING BOOKS, AND THEN RERUN!")
    else:
        print(f"    {total_simple_links+total_multiword_links:,} total links written ({total_simple_links:,} simple links and {total_multiword_links:,} multiword links) to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TW_HebGrk_to_TSV6_TWL.py
