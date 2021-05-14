#!/usr/bin/env python3
#
# TN_TSV7_to_TSV9.py
#
# Copyright (c) 2020-2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Nov 2020 by RJH
#   Last modified: 2021-05-14 by RJH
#
"""
Quick script to copy TN from 7-column TSV files
    and put back into the older 9-column format (for compatibility reasons)

NOTE: This requires the addition of the GLQuote column!
"""
from typing import List, Tuple
import os
from pathlib import Path
import random
import re
import logging
import subprocess


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tn2/')

# The output folder below must also already exist!
LOCAL_OUTPUT_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tn/')

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


def get_TSV7_fields(input_folderpath:Path, BBB:str) -> Tuple[str,str,str,str,str,str]:
    """
    Generator to read the TN 7-column TSV files
        and return the needed fields.

    Skips the heading row.
    Checks that unused fields are actually unused.

    Returns a 6-tuple with:
        reference, rowID, support_reference, quote, occurrence, note
    """
    print(f"    Loading TQ {BBB} links from 7-column TSV…")
    input_filepath = input_folderpath.joinpath(f'tn_{BBB}.tsv')
    with open(input_filepath, 'rt') as input_TSV_file:
        for line_number, line in enumerate(input_TSV_file, start=1):
            line = line.rstrip('\n\r')
            # print(f"{line_number:3}/ {line}")
            if line_number == 1:
                assert line == 'Reference\tID\tTags\tSupportReference\tQuote\tOccurrence\tNote'
            else:
                reference, rowID, tags, support_reference, quote, occurrence, note = line.split('\t')
                assert reference; assert rowID; assert note
                if quote: assert occurrence and occurrence != '0'
                if occurrence and occurrence != '0': assert quote
                assert not tags
                yield reference, rowID, support_reference, quote, occurrence, note
# end of get_TSV7_fields function


QL_QUOTE_PLACEHOLDER = "NO GLQuote YET!!!"
def convert_TN_TSV(input_folderpath:Path, output_folderpath:Path, BBB:str, nn:str) -> int:
    """
    Function to read and write the TN markdown files.

    Needs to be called one extra time with fields = None
        to write the last entry.

    Returns the number of markdown files that were written in the call.
    """
    testament = 'OT' if int(nn)<40 else 'NT'
    output_filepath = output_folderpath.joinpath(f'en_tn_{nn}-{BBB}.tsv')
    temp_output_filepath = Path(f"{output_filepath}.tmp")
    with open(temp_output_filepath, 'wt') as temp_output_TSV_file:
        temp_output_TSV_file.write('Book\tChapter\tVerse\tID\tSupportReference\tOrigQuote\tOccurrence\tGLQuote\tOccurrenceNote\n')
        for line_count, (reference, rowID, support_reference, quote, occurrence, note) in enumerate(get_TSV7_fields(input_folderpath, BBB), start=1):
            C, V = reference.split(':')
            # print(BBB,C,V,repr(note))

            orig_quote = quote.replace(' & ', '…')
            orig_quote = orig_quote.replace('\u00A0', ' ') # Replace non-break spaces
            orig_quote = orig_quote.replace('\u200B', '') # Delete zero-width spaces
            orig_quote = orig_quote.strip()

            support_reference = support_reference.split('/')[-1] # We only use the very end of the full RC link

            gl_quote = QL_QUOTE_PLACEHOLDER if orig_quote else ""

            occurrence_note = note.replace('\\n', '<br>')
            occurrence_note = occurrence_note.replace('rc://*/', 'rc://en/')
            occurrence_note = occurrence_note.strip().replace('  ', ' ')

            temp_output_TSV_file.write(f'{BBB}\t{C}\t{V}\t{rowID}\t{support_reference}\t{orig_quote}\t{occurrence}\t{gl_quote}\t{occurrence_note}\n')

    # Now use Proskomma to find the ULT GLQuote fields for the OrigQuotes in the temporary outputted file
    print(f"    Running Proskomma for {testament} {BBB}… (might take a few minutes)")
    completed_process_result = subprocess.run(['node', 'TN_TSV9_OLQuotes_to_ULT_GLQuotes.js', temp_output_filepath, testament], capture_output=True)
    # print(f"Proskomma result was: {completed_process_result}")
    if completed_process_result.returncode:
        print(f"Proskomma ERROR result was: {completed_process_result.returncode}")
    if completed_process_result.stderr:
        print(f"Proskomma error output was: {completed_process_result.stderr.decode()}")
    proskomma_output_string = completed_process_result.stdout.decode()
    # print(f"Proskomma output was: {proskomma_output_string}")
    output_lines = proskomma_output_string.split('\n')
    print(f"      Proskomma got: {' / '.join(output_lines[:9])}")
    print(f"      Proskomma did: {output_lines[-2]}")
    # Put the GL Quotes into a dict for easy access
    match_dict = {}
    for match in re.finditer(r'(\w{3})_(\d{1,3}):(\d{1,3}) ►(.+?)◄ “(.+?)”', proskomma_output_string):
        # print(match)
        B, C, V, orig_quote, gl_quote = match.groups()
        assert B == BBB
        match_dict[(C,V,orig_quote)] = gl_quote
    print(f"      Got {len(match_dict)} GL Quotes back from Proskomma")

    # Now put the GL Quotes into the file
    with open(temp_output_filepath, 'rt') as temp_input_TSV_file:
        with open(output_filepath, 'wt') as output_TSV_file:
            output_TSV_file.write(temp_input_TSV_file.readline()) # Write the TSV header
            for line in temp_input_TSV_file:
                B, C, V, rowID, support_reference, orig_quote, occurrence, gl_quote, occurrence_note = line.split('\t')
                if orig_quote: gl_quote = match_dict[(C,V,orig_quote)]
                output_TSV_file.write(f'{B}\t{C}\t{V}\t{rowID}\t{support_reference}\t{orig_quote}\t{occurrence}\t{gl_quote}\t{occurrence_note}')

    os.remove(temp_output_filepath)

    return line_count
# end of convert_TN_TSV


def main():
    """
    """
    print("TN_TSV7_to_TSV9.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    print(f"  Output folderpath is {LOCAL_OUTPUT_FOLDERPATH}/")
    total_files_read = total_notes = 0
    for BBB,nn in BBB_NUMBER_DICT.items():
        if BBB not in ('TIT','2JN','3JN'): continue
        total_notes += convert_TN_TSV(LOCAL_SOURCE_FOLDERPATH, LOCAL_OUTPUT_FOLDERPATH, BBB, nn)
        total_files_read += 1
    print(f"  {total_notes:,} total notes read from {total_files_read} TSV files")
    print(f"  {total_files_read:,} total TSV files written to {LOCAL_OUTPUT_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TN_TSV7_to_TSV9.py
