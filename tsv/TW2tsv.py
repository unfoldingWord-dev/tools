#!/usr/bin/env python3
#
# TW2tsv.py
#
# Written Apr 2020 by RJH
#   Last modified: 2020-08-18 by RJH
#
"""
Quick script to copy TW links out of UHB and UGNT
    and put into a TSV file with the same format (9 columns) as UTN.
"""
from typing import List, Tuple
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/')
LOCAL_OT_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('hbo_uhb/')
LOCAL_NT_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('el-x-koine_ugnt/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/TSV_test/')

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
def get_source_lines(BBB:str, nn:str) -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the original language (Heb/Grk) book
        and return lines containing TW links.

    Yields a 5-tuple with:
        line number B C V reference strings
        actual line (without trailing nl)
    """
    source_folderpath = LOCAL_OT_SOURCE_FOLDERPATH if int(nn)<40 \
                    else LOCAL_NT_SOURCE_FOLDERPATH
    source_filename = f'{nn}-{BBB}.usfm'
    source_filepath = source_folderpath.joinpath(source_filename)
    print(f"      Getting source lines from ${source_filepath}")

    C = V = ''
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
            while word_match:
                this_line_words.append(word_match.group(1))
                this_verse_words.append(word_match.group(1))
                word_match = SINGLE_WORD_RE.search(line, word_match.end())

            if 'x-tw' not in line and '\\k' not in line and not is_in_k:
                continue # Ignore unnecessary lines
            # print(f"{BBB} {C}:{V} line={line}")

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
                assert line.startswith('\\w ') \
                    or line[0] in '(' and line[1:].startswith('\\w ') \
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
                    milestone_words = []
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
                        assert word_match.start() < ke_index
                        occurrence = this_verse_words.count(word)
                        if is_in_k: milestone_words.append(word)
                        simple_link_match = SIMPLE_TW_LINK_RE.search(word_field)
                        if simple_link_match:
                            word_link = simple_link_match.group(1)
                            assert word_link.startswith('rc://*/tw/dict/bible/')
                            # print("here2", C,V, word, occurrence, this_verse_words, word_link)
                            yield line_number, BBB, C, V, word, occurrence, word_link
                        word_field_match = WORD_FIELD_RE.search(line, word_field_match.end())
                    searchW_startIndex = 'BADBAD' # Just to catch any logic errors

                    is_in_k = False
                    assert milestone_words
                    milestone_words = ' '.join(milestone_words)
                    # print("here0", C,V, milestone_words, occurrence, milestone_link)
                    yield remembered_line_number, BBB, C, V, milestone_words, occurrence, milestone_link
                    del remembered_line_number, milestone_words, milestone_link # Don't let them persist -- just so we catch any logic errors
                    continue
                else: # k-s is fully open now
                    is_in_k = True
                # There might still be a \w field on the line, but it's caught below
            elif is_in_k:
                if '\\k-s' in line:
                    assert line.startswith('\\k-s ')
                    assert line.count('x-tw="') >= 1
                    milestone_link_match = MILESTONE_TW_LINK_RE.search(line)
                    if milestone_link_match:
                        milestone_link = milestone_link_match.group(1)
                        assert milestone_link.startswith('rc://*/tw/dict/bible/')
                        remembered_line_number = line_number
                        milestone_words = []
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
                    assert milestone_words
                    milestone_words = ' '.join(milestone_words)
                    # print("here0", C,V, milestone_words, occurrence, milestone_link)
                    yield remembered_line_number, BBB, C, V, milestone_words, occurrence, milestone_link
                    del remembered_line_number, milestone_words, milestone_link # Don't let them persist -- just so we catch any logic errors
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
                    # print(f"          searchW_startIndex={searchW_startIndex}")
                    # print(f"          word_field_match={word_field_match}")
                    word_field = word_field_match.group(1)
                    # print(f"          word_field={word_field}")
                    word_match = SINGLE_WORD_RE.search(word_field)
                    # print(f"          word_match={word_match}")
                    assert word_match
                    word = word_match.group(1)
                    occurrence = this_verse_words.count(word)
                    # print(f"          occurrence={occurrence}")
                    if is_in_k: milestone_words.append(word)
                    simple_link_match = SIMPLE_TW_LINK_RE.search(word_field)
                    # print(f"          simple_link_match={simple_link_match}")
                    if simple_link_match:
                        word_link = simple_link_match.group(1)
                        assert word_link.startswith('rc://*/tw/dict/bible/')
                        # print("here2", C,V, word, occurrence, this_verse_words, word_link)
                        yield line_number, BBB, C, V, word, occurrence, word_link
                    word_field_match = WORD_FIELD_RE.search(line, word_field_match.end())
                searchW_startIndex = 'BADBADBAD' # Just to catch any logic errors above
# end of get_source_lines function


def make_TSV_file(BBB:str, nn:str) -> Tuple[int,int]:
    """
    """
    source_text = 'UHB' if int(nn)<40 else 'UGNT'
    print(f"    Converting {source_text} {BBB} links to TSV…")
    output_filepath = LOCAL_OUTPUT_FOLDERPATH.joinpath(f'{BBB.lower()}_twl.tsv')
    num_simple_links = num_complex_links = j = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        output_TSV_file.write('Book\tChapter\tVerse\tID\tSupportReference\tOrigQuote\tOccurrence\tGLQuote\tOccurrenceNote\n')
        previous_ids:List[str] = ['']
        for j, (_line_number,BBB,C,V,word,occurrence,link) in enumerate(get_source_lines(BBB, nn), start=1):
            # print(f"{j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} '{word}' {occurrence} {link}")
            generated_id = ''
            while generated_id in previous_ids:
                generated_id = random.choice('abcdefghijklmnopqrstuvwxyz') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789') + random.choice('abcdefghijklmnopqrstuvwxyz0123456789')
            previous_ids.append(generated_id)

            output_line = f'{BBB}\t{C}\t{V}\t{generated_id}\t{link}\t{word}\t{occurrence}\t(GLQuote)\t(OccurrenceNote)'
            output_TSV_file.write(f'{output_line}\n')
            if ' ' in word: num_complex_links += 1
            else: num_simple_links += 1
    print(f"      {j:,} links written ({num_simple_links:,} simple links and {num_complex_links:,} complex links)")
    return num_simple_links, num_complex_links
# end of make_TSV_file function


def main():
    """
    """
    print("TW2tsv.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_simple_links = total_complex_links = 0
    for BBB,nn in BBB_NUMBER_DICT.items():
        simple_count, complex_count = make_TSV_file(BBB,nn)
        total_simple_links += simple_count
        total_complex_links += complex_count
    print(f"    {total_simple_links+total_complex_links:,} total links written ({total_simple_links:,} simple links and {total_complex_links:,} multiword links)")
# end of main function

if __name__ == '__main__':
    main()
# end of TW2tsv.py