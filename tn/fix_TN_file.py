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
and writes a new copy with typical errors fixed.
"""
from pathlib import Path
import unicodedata


OVERWRITE_FLAG = False
BOOK_NUMBER, BOOK_CODE = '16', 'NEH'
SOURCE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/unfoldingWord/en_tn/')


source_filename = f'en_tn_{BOOK_NUMBER}-{BOOK_CODE}.tsv'


# Unicode characters
# Punctuation
NO_BREAK_SPACE_CHAR = '\u00A0'
WORD_JOINER_CHAR = '\u2060'
ZERO_WIDTH_SPACE_CHAR = '\u200B'
# Hebrew
MAQAF = '\u05BE'


def fix_line(line_number:int, existing_line:str) -> str:
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

    # Do fixes to the entire line
    fixed_line = existing_line.replace('<BR>','<br>').replace('See: <br>','See: ') \
                            .replace(NO_BREAK_SPACE_CHAR,' ') \
                            .replace(' \t','\t').replace('\t ','\t').replace('\t<br>','\t') \
                            .replace('\t'+WORD_JOINER_CHAR,'\t').replace(WORD_JOINER_CHAR+'\t','\t') \
                            .replace('\t'+ZERO_WIDTH_SPACE_CHAR,'\t').replace(ZERO_WIDTH_SPACE_CHAR+'\t','\t') \
                            .replace(MAQAF+' ',MAQAF) \
                            .replace('  ',' ')
    if fixed_line.endswith('<br>'): fixed_line = fixed_line[:-4]
    fixed_line = fixed_line.rstrip(ZERO_WIDTH_SPACE_CHAR)
    # Straight quotes to typographical notes
    if fixed_line.count('"') == 2: # Only do it if we're reasonably sure
        fixed_line = fixed_line.replace('"','“',1).replace('"','”',1)
    # Apostrophe to typographical version
    if fixed_line.count("'") == 1: # Only do it if we're reasonably sure
        fixed_line = fixed_line.replace("'",'’',1)

    # Check for mismatched pairs
    for lChar,rChar in (('“','”'),('«','»'),('‹','›'),('(',')'),('[',']'),('<','>'),): # Remove apostrophe ('‘','’'),
        if (lCount := fixed_line.count(lChar)) != (rCount := fixed_line.count(rChar)):
            print(f"\n\nNOTE: Line {line_number} contains {lCount} {lChar} but {rCount} {rChar}: {fixed_line}")

    # Check for unexpected characters
    for char in fixed_line:
        if char not in ('\t abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-*#/\\.,:;?!%()[]<>‘’“”–…'):
            int_char = ord(char)
            if int_char>=243 and int_char<=250: continue # Accept accented Latin block
            if (int_char>=1425 and int_char<=1514) or char==WORD_JOINER_CHAR: continue # Accept Hebrew block
            adjusted_line = fixed_line.replace(WORD_JOINER_CHAR,'WJC').replace(NO_BREAK_SPACE_CHAR,'NBS').replace(ZERO_WIDTH_SPACE_CHAR,'ZWS')
            print(f"\n\nNOTE: Line {line_number} contains '{char}' {unicodedata.name(char)} {int_char}: {adjusted_line}")

    return fixed_line


def main():
    """
    Read and possibly correct the file
    """
    filepath = SOURCE_FOLDERPATH.joinpath(source_filename)
    print(f"Fixing {BOOK_CODE} TSV from {filepath}…")

    fixed_line_count = 0
    lines, new_lines = [], []
    with open(filepath, 'rt') as input_file:
        for n, line in enumerate(input_file, start=1):
            line = line.rstrip('\n')
            lines.append(line)
            # print(f"Line {n}: '{line}'")

            new_line = fix_line(n, line)
            if new_line != line:
                fixed_line_count += 1
                print(f"\n  Changed line {n} to '{new_line}'")
                print(f"                   was '{line}'")
            new_lines.append(new_line)

    if fixed_line_count:
        print(f"\nFixed {fixed_line_count} TN lines.")

    if OVERWRITE_FLAG:
        print(f"\nOverwriting {filepath}…")
        with open(filepath, 'wt') as output_file:
            output_file.write('\n'.join(new_lines)+'\n') # Ensure a final blank line
    elif new_lines != lines:
        print(f"\nOverwriting {source_filename} is disabled!")

if __name__ == '__main__':
    main()
# end of tx_TN_file.py
