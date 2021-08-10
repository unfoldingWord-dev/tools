#!/usr/bin/env python3
#
# TW_fix_Strongs.py
#
# Copyright (c) 2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Aug 2021 by RJH
#   Last modified: 2021-08-10 by RJH
#
"""
Quick script to fix Strongs numbers in TW markdown files.

Note that each run of this script rewrites existing masrkdown files if there's any changes.
"""
from typing import List
import os
from pathlib import Path
import re
# import logging


LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath('en_tw/')


def handle_line(line_number:int, line:str) -> str:
    """
    Expand the Strongs numbers to the correct number of leading zeroes
        and add the trailing zero for the UGL.

    These regex's are a little more complex (with lookahead) to ensure that
        even if we run the script multiple times, we don't get multiple zeroes appended.
    """
    # print(f"handle_line({line_number} {line=})…")

    def handle_H(match_object) -> str:
        # print(f"handle_H({match_object=}) with {match_object.group(1)} for {line_number} {line=})…")
        return f'H{match_object.group(1).zfill(4)}'
    line = re.sub(r'H(\d{1,4})(?=[^\d]|$)', handle_H, line)

    def handle_G(match_object) -> str:
        # print(f"handle_G({match_object=}) with {match_object.group(1)} for {line_number} {line=})…")
        return f'G{match_object.group(1).zfill(4)}0' # includes a suffix
    line = re.sub(r'G(\d{1,4})(?=[^\d]|$)', handle_G, line)

    return line
# end of handle_line function


def handle_file(folderpath:str, filename:str) -> int:
    """
    Read a TW markdown file, and fix the Strongs numbers if necessary.

    Returns the number of files (0 or 1) written.
    """
    filepath = Path(folderpath).joinpath(filename)
    # print(f"    Getting source lines from {filepath}")

    have_changes = False
    output_lines:List[str] = []
    with open(filepath, 'rt') as mdFile:
        for line_number,line in enumerate(mdFile, start=1):
            line = line.rstrip() # Remove trailing whitespace including nl char
            # print(f"  {line_number} {line=}")
            if 'Strong' in line: # do some basic filtering
                new_line = handle_line(line_number, line)
                output_lines.append(new_line)
                if new_line != line: have_changes = True
            else:
                output_lines.append(line)

    if not have_changes:
        return 0

    print(f"    Writing updated lines to {filepath}")
    with open(filepath, 'wt') as mdFile:
        mdFile.write('\n'.join(output_lines) + '\n') # We always write a final newLine character
    return 1
# end of handle_file function




def main():
    """
    """
    print("TW_fix_Strongs.py")
    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    num_md_files = num_changed_md_files = 0
    for root, dirs, files in os.walk(LOCAL_SOURCE_FOLDERPATH):
        if '.git' in root: continue
        for name in files:
            # print(f"file: {root=} {name=} {os.path.join(root, name)=}")
            if name.lower().endswith('.md'):
                num_md_files += 1
                num_changed_md_files += handle_file(root, name)
        # for name in dirs:
        #     print(f"dir: {root=} {name=} {os.path.join(root, name)=}")
    print(f"    {num_md_files:,} total markdown files found and {num_changed_md_files:,} written in {LOCAL_SOURCE_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of TW_fix_Strongs.py
