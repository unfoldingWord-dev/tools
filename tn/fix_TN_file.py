#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Robert Hunt <Robert.Hunt@unfoldingword.org>

"""
This script takes a TSV TN file
and writes a new copy with typical small errors repaired.
"""
from pathlib import Path
import unicodedata


OVERWRITE_FLAG = False
BOOK_NUMBER, BOOK_CODE = '16', 'NEH'
# BOOK_NUMBER, BOOK_CODE = '31', 'OBA'
SOURCE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/en_tn/')


source_filename = f'en_tn_{BOOK_NUMBER}-{BOOK_CODE}.tsv'


# Unicode characters
# Punctuation
NO_BREAK_SPACE_CHAR = '\u00A0'
WORD_JOINER_CHAR = '\u2060'
ZERO_WIDTH_SPACE_CHAR = '\u200B'
# Hebrew
MAQAF = '\u05BE'


def repair_line(line_number:int, existing_line:str) -> str:
    """
    """
    if (num_tabs := existing_line.count('\t')) != 8:
        print(f"  ERROR: Wrong number of tabs ({num_tabs} instead of 8) in line {line_number}")
        print( "    YOU NEED TO FIX THIS MANUALLY!")
        halt

    # # Check for unexpected characters
    # for char in existing_line:
    #     if char not in ('\t abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-*#/\\.,:;?!%()[]<>‘’“”–…'):
    #         int_char = ord(char)
    #         if int_char>=243 and int_char<=250: continue # Accept accented Latin block
    #         if (int_char>=1425 and int_char<=1514) or char==WORD_JOINER_CHAR: continue # Accept Hebrew block
    #         print(f"\nLine {line_number} contains '{char}' {unicodedata.name(char)} {int_char}: {existing_line}")

    # Do repairs to the entire line
    repaired_line = existing_line.replace('<BR>','<br>').replace('See: <br>','See: ') \
                            .replace(NO_BREAK_SPACE_CHAR,' ') \
                            .replace(' \t','\t').replace('\t ','\t').replace('\t<br>','\t') \
                            .replace('\t'+WORD_JOINER_CHAR,'\t').replace(WORD_JOINER_CHAR+'\t','\t') \
                            .replace('\t'+ZERO_WIDTH_SPACE_CHAR,'\t').replace(ZERO_WIDTH_SPACE_CHAR+'\t','\t') \
                            .replace(MAQAF+' ',MAQAF) \
                            .replace('...','…') \
                            .replace('  ',' ')
    if repaired_line.endswith('<br>'): repaired_line = repaired_line[:-4]
    repaired_line = repaired_line.rstrip(ZERO_WIDTH_SPACE_CHAR)
    # Straight quotes to typographical notes
    if repaired_line.count('"') == 2: # Only do it if we're reasonably sure
        repaired_line = repaired_line.replace('"','“',1).replace('"','”',1)
    # Apostrophe to typographical version
    if repaired_line.count("'") == 1: # Only do it if we're reasonably sure
        repaired_line = repaired_line.replace("'",'’',1)

    # Check for mismatched pairs
    for lChar,rChar in (('“','”'),('«','»'),('‹','›'),('(',')'),('[',']'),('<','>'),): # Remove apostrophe ('‘','’'),
        if (lCount := repaired_line.count(lChar)) != (rCount := repaired_line.count(rChar)):
            print(f"\n\nNOTE: Line {line_number} contains {lCount} {lChar} but {rCount} {rChar}: {repaired_line}")

    # Check for unexpected characters
    for char in repaired_line:
        if char not in ('\t abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-*#/\\.,:;?!%()[]<>‘’“”–…'):
            int_char = ord(char)
            if int_char>=243 and int_char<=250: continue # Accept accented Latin block
            if (int_char>=1425 and int_char<=1514) or char==WORD_JOINER_CHAR: continue # Accept Hebrew block
            adjusted_line = repaired_line.replace(WORD_JOINER_CHAR,'WJC').replace(NO_BREAK_SPACE_CHAR,'NBS').replace(ZERO_WIDTH_SPACE_CHAR,'ZWS')
            print(f"\n\nNOTE: Line {line_number} contains '{char}' {unicodedata.name(char)} {int_char}: {adjusted_line}")

    return repaired_line


def main():
    """
    Read and possibly correct the file
    """
    filepath = SOURCE_FOLDERPATH.joinpath(source_filename)
    print(f"Fixing {BOOK_CODE} TSV from {filepath}…")

    repaired_line_count = 0
    lines, new_lines = [], []
    with open(filepath, 'rt') as input_file:
        for n, line in enumerate(input_file, start=1):
            line = line.rstrip('\n')
            lines.append(line)
            # print(f"Line {n}: '{line}'")

            if n==1: field_names = line.split('\t')

            new_line = repair_line(n, line)
            if new_line != line:
                repaired_line_count += 1
                print(f"\n\n  Changed line {n} to '{new_line}'")
                print(f"                   was '{line}'")
                old_fields = line.split('\t')
                new_fields = new_line.split('\t')
                for n, (old_field,new_field) in enumerate(zip(old_fields,new_fields)):
                    if new_field != old_field:
                        print(f"  {field_names[n]} was {old_field}")
                        print(f"  {field_names[n]} now {new_field}")
            new_lines.append(new_line)

    if repaired_line_count:
        print(f"\nRepaired {repaired_line_count} TN lines.")

    if OVERWRITE_FLAG:
        print(f"\nOverwriting {filepath}…")
        with open(filepath, 'wt') as output_file:
            output_file.write('\n'.join(new_lines)+'\n') # Ensure a final blank line
    elif new_lines != lines:
        print(f"\nOverwriting {source_filename} is disabled!")

if __name__ == '__main__':
    main()
# end of tx_TN_file.py
