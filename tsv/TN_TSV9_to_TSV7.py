#!/usr/bin/env python3
#
# TN_TSV9_to_TSV7.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2020 by RJH
#   Last modified: 2021-05-07 by RJH
#
"""
Quick script to copy TN from 9-column TSV files
    and put into a TSV file with the new 7-column format.
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tn/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tn2/')

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


def get_source_lines(BBB:str, nn:str) -> Tuple[str,str,str,str,str,str,str]:
    """
    Generator to read the TN TSV files
        and return lines containing the fields.

    Returns a 5-tuple with:
        line number B C V reference strings
        actual line (without trailing nl)
    """
    source_filename = f'en_tn_{nn}-{BBB}.tsv'
    source_filepath = LOCAL_SOURCE_FOLDERPATH.joinpath(source_filename)
    print(f"      Getting source lines from {source_filepath}")

    with open(source_filepath, 'rt') as source_tsv_file:
        for line_number,line in enumerate(source_tsv_file, start=1):
            line = line.rstrip() # Remove trailing whitespace including nl char
            # print(f"  line={line}")
            # if not line: continue # Ignore blank lines
            fields = line.split('\t')
            yield line_number, fields
# end of get_source_lines function


def make_TSV_file(BBB:str, nn:str) -> int:
    """
    Combines chapter and verse number into reference

    Does a little checking and cleaning of other fields

    Drops the GL Quote field

    Writes the 7-column TSV file

    Returns the number of lines written
    """
    print(f"    Converting TN {BBB} links to TSV…")
    output_folderpath = LOCAL_OUTPUT_FOLDERPATH #.joinpath(BBB)
    if not os.path.isdir(output_folderpath): os.mkdir(output_folderpath)
    output_filepath = output_folderpath.joinpath(f'tn_{BBB}.tsv')
    num_lines = j = 0
    with open(output_filepath, 'wt') as output_TSV_file:
        for j, (line_number,fields) in enumerate(get_source_lines(BBB, nn), start=1):
            try:
                B,C,V,ID, support_reference,orig_quote,occurrence,_gl_quote,occurrence_note = fields
            except ValueError:
                print(f"Expected 9 fields but found {len(fields)} in {fields}")
                raise ValueError
            # print(f"{j:3}/ Line {line_number:<5} {BBB} {C:>3}:{V:<3} {ID }'{support_reference}' '{orig_quote}' '{occurrence}' '{_gl_quote}' '{occurrence_note}'")
            if j == 1:
                assert B=='Book' and C=='Chapter' and V=='Verse' # etc.
                output_line = 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote'
            else:
                # Do some tidying up while we're at it
                C = C.strip(); V = V.strip(); ID = ID.strip()
                reference = f'{C}:{V}'

                assert len(ID) == 4
                if ID[0] not in 'abcdefghijklmnopqrstuvwxyz':
                    print(f"Bad ID: {BBB} {reference} {line_number} '{ID}' fixed.")
                    convert_dict = {'1':'a', '2':'t', '3':'c', '4':'d', '5':'f', '6':'g', '7':'s', '8':'h', '9':'n', '0':'z' }
                    ID = f"{convert_dict[ID[0]]}{ID[1:]}" # We don't use i l o (more easily confused)
                assert ID[0] in 'abcdefghijklmnopqrstuvwxyz'
                assert ID[1] in 'abcdefghijklmnopqrstuvwxyz0123456789'
                assert ID[2] in 'abcdefghijklmnopqrstuvwxyz0123456789'
                assert ID[3] in 'abcdefghijklmnopqrstuvwxyz0123456789'

                tags = ''

                support_reference = support_reference.strip()
                if support_reference: support_reference = f'rc://*/ta/man/translate/{support_reference}'

                orig_quote = orig_quote.replace('\u00A0', ' ') # Replace non-break spaces
                orig_quote = orig_quote.replace('\u200B', '') # Delete zero-width spaces
                orig_quote = orig_quote.replace('...', '…')
                orig_quote = orig_quote.replace(' …', '…').replace('… ', '…')
                orig_quote = orig_quote.strip('…') # Should only be BETWEEN words
                orig_quote = orig_quote.replace('…', ' & ')
                orig_quote = orig_quote.strip()

                occurrence = occurrence.strip()

                occurrence_note = occurrence_note.strip()
                occurrence_note = occurrence_note.replace('<BR>', '<br>')
                if occurrence_note.startswith('<br>'): occurrence_note = occurrence_note[4:]
                if occurrence_note.endswith('<br>'): occurrence_note = occurrence_note[:-4]
                occurrence_note = occurrence_note.replace('<br>', '\\n')
                occurrence_note = occurrence_note.replace('rc://en/', 'rc://*/')
                occurrence_note = occurrence_note.replace('…', ' … ').replace('  …', ' …').replace('…  ', '… ')
                while '*  ' in occurrence_note: occurrence_note = occurrence_note.replace('*  ', '* ')
                occurrence_note = occurrence_note.replace('\\n   ', '\\n@@@').replace('\\n  ', '\\n@@')
                occurrence_note = occurrence_note.replace('  ', ' ') # Might mess up markdown indents ???
                occurrence_note = occurrence_note.replace('\\n@@@', '\\n   ').replace('\\n@@', '\\n  ')
                occurrence_note = occurrence_note.strip()
                if '  ' in occurrence_note: print(f"NOTE: {BBB} {reference} {line_number} OccurrenceNote has double-spaces: '{occurrence_note}'")

                output_line = f'{reference}\t{ID}\t{tags}\t{support_reference}\t{orig_quote}\t{occurrence}\t{occurrence_note}'
            output_TSV_file.write(f'{output_line}\n')
            num_lines += 1
    print(f"      {num_lines:,} lines written")
    return num_lines
# end of make_TSV_file function


def main():
    """
    """
    print("TN_TSV9_to_TSV7.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_BASE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_questions = 0
    for BBB,nn in BBB_NUMBER_DICT.items():
        try:
            question_count = make_TSV_file(BBB,nn)
        except ValueError as err:
            print(f"ERROR: Failed to process {BBB}: {err}")
        total_questions += question_count
    print(f"    {total_questions:,} total notes written to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TN_TSV9_to_TSV7.py
