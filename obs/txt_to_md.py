#!/usr/bin/env python3
# 
#  Copyright (c) 2021 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

# Python imports
from typing import Dict, List, Set, Tuple, Any, Optional
import os
import re
import sys
import json
import tempfile
import argparse
from glob import glob
from shutil import copy, copytree
from urllib.request import urlopen
from urllib.error import HTTPError
import unicodedata

# Local importsre
from general_tools.file_utils import write_file, read_file, make_dir, unzip, remove_tree
from general_tools.url_utils import get_url, download_file
from .ResourceContainer import RC

def do_preprocess(source_dir:str, output_dir:str):
    rc = RC(directory=source_dir)
    preprocessor = ObsPreprocessor(rc=rc, source_dir=source_dir, output_dir=output_dir)
    preprocessor.run()

class Preprocessor:
    # NOTE: Both of these lists are used for CASE-SENSITIVE comparisons
    ignoreDirectories = ['.apps', '.git', '.github', '00']
    ignoreFiles = ['.DS_Store', 'reference.txt', 'title.txt', 'LICENSE.md', 'README.md', 'README.rst']


    def __init__(self, rc:RC, source_dir:str, output_dir:str) -> None:
        """
        :param RC rc:
        :param string source_dir:
        :param string output_dir:
        """
        self.rc = rc
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.num_files_written = 0
        self.messages:List[str] = [] # { Messages only display if there's warnings or errors
        self.errors:List[str] = []   # { Errors float to the top of the list
        self.warnings:List[str] = [] # {    above warnings

        # Check that we had a manifest (or equivalent) file
        # found_manifest = False
        # for some_filename in ('manifest.yaml','manifest.json','package.json','project.json','meta.json',):
        #     if os.path.isfile(os.path.join(source_dir,some_filename)):
        #         found_manifest = True; break
        # if not found_manifest:
        if not self.rc.loadeded_manifest_file:
            self.warnings.append("Possible missing manifest file in project folder")

        # Write out the new manifest file based on the resource container
        write_file(os.path.join(self.output_dir, 'manifest.yaml'), self.rc.as_dict())


    def run(self) -> Tuple[int, List[str]]:
        """
        Default Preprocessor

        Case #1: Project path is a file, then we copy the file over to the output dir
        Case #2: It's a directory of files, so we copy them over to the output directory
        Case #3: The project path is multiple chapters, so we piece them together
        """
        for idx, project in enumerate(self.rc.projects):
            project_path = os.path.join(self.source_dir, project.path)

            if os.path.isfile(project_path):
                filename = f'{str(idx + 1).zfill(2)}-{project.identifier}.{self.rc.resource.file_ext}'
                copy(project_path, os.path.join(self.output_dir, filename))
                self.num_files_written += 1
            else:
                # Case #2: It's a directory of files, so we copy them over to the output directory
                files = glob(os.path.join(project_path, f'*.{self.rc.resource.file_ext}'))
                if files:
                    for file_path in files:
                        output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                        if os.path.isfile(file_path) and not os.path.exists(output_file_path) \
                                and os.path.basename(file_path) not in self.ignoreFiles:
                            copy(file_path, output_file_path)
                            self.num_files_written += 1
                else:
                    # Case #3: The project path is multiple chapters, so we piece them together
                    chapters = self.rc.chapters(project.identifier)
                    if chapters:
                        text = ''
                        for chapter in chapters:
                            text = self.mark_chapter(project.identifier, chapter, text)
                            for chunk in self.rc.chunks(project.identifier, chapter):
                                text = self.mark_chunk(project.identifier, chapter, chunk, text)
                                text += read_file(os.path.join(project_path, chapter, chunk))+"\n\n"
                        filename = f'{str(idx+1).zfill(2)}-{project.identifier}.{self.rc.resource.file_ext}'
                        write_file(os.path.join(self.output_dir, filename), text)
                        self.num_files_written += 1
        if self.num_files_written == 0:
            self.errors.append("No source files discovered")
        return self.num_files_written, self.errors + self.warnings + (self.messages if self.errors or self.warnings else [])
    # end of Preprocessor.run()


    def mark_chapter(self, ident:int, chapter:str, text:str) -> str:
        return text  # default does nothing to text


    def mark_chunk(self, ident:int, chapter:str, chunk:str, text:str) -> str:
        return text  # default does nothing to text


    def get_book_list(self):
        return None


    def check_and_clean_title(self, title_text:str, ref:str) -> str:
        """
        """
        if title_text.lstrip() != title_text:
            self.warnings.append(f"{ref}: Unexpected whitespace at beginning of {title_text!r}")
        if title_text.rstrip() != title_text:
            # We will ignore a single final newline
            if title_text[-1]=='\n' and title_text[:-1].rstrip() != title_text[:-1]:
                self.warnings.append(f"{ref}: Unexpected whitespace at end of {title_text!r}")
        title_text = title_text.strip()
        if '  ' in title_text:
            self.warnings.append(f"{ref}: Doubled spaces in '{title_text}'")

        if not title_text:
            self.warnings.append(f"{ref}: Missing title text")

        for char in '.[]:"':
            if char in title_text:
                self.warnings.append(f"{ref}: Unexpected '{char}' in '{title_text}'")

        self.check_punctuation_pairs(title_text, ref)
        return title_text
    # end of Preprocessor.check_and_clean_title function


    def check_punctuation_pairs(self, some_text:str, ref:str, allow_close_parenthesis_points=False) -> None:
        """
        Check matching number of pairs.

        If closing parenthesis is used for points, e.g., 1) This point.
            then set the optional flag.

        Copied here from linter.py 23Mar2020.
        """
        punctuation_pairs_to_check = (('(',')'), ('[',']'), ('{','}'), ('**_','_**'))

        found_any_paired_chars = False
        # found_mismatch = False
        for pairStart,pairEnd in punctuation_pairs_to_check:
            pairStartCount = some_text.count(pairStart)
            pairEndCount   = some_text.count(pairEnd)
            if pairStartCount or pairEndCount:
                found_any_paired_chars = True
            if pairStartCount > pairEndCount:
                self.warnings.append(f"{ref}: Possible missing closing '{pairEnd}' — found {pairStartCount:,} '{pairStart}' but {pairEndCount:,} '{pairEnd}'")
                # found_mismatch = True
            elif pairEndCount > pairStartCount:
                if allow_close_parenthesis_points:
                    # possible_points_list = re.findall(r'\s\d\) ', some_text)
                    # if possible_points_list: print("possible_points_list", possible_points_list)
                    possible_point_count = len(re.findall(r'\s\d\) ', some_text))
                    pairEndCount -= possible_point_count
                if pairEndCount > pairStartCount: # still
                    self.warnings.append(f"{ref}: Possible missing opening '{pairStart}' — found {pairStartCount:,} '{pairStart}' but {pairEndCount:,} '{pairEnd}'")
                    # found_mismatch = True
        if found_any_paired_chars: # and not found_mismatch:
            # Double-check the nesting
            lines = some_text.split('\n')
            nestingString = ''
            line_number = 1
            for ix, char in enumerate(some_text):
                if char in '({[':
                    nestingString += char
                elif char in ')}]':
                    if char == ')': wanted_start_char = '('
                    elif char == '}': wanted_start_char = '{'
                    elif char == ']': wanted_start_char = '['
                    if nestingString and nestingString[-1] == wanted_start_char:
                        nestingString = nestingString[:-1] # Close off successful match
                    else: # not the closing that we expected
                        if char==')' \
                        and ix>0 and some_text[ix-1].isdigit() \
                        and ix<len(some_text)-1 and some_text[ix+1] in ' \t':
                            # This could be part of a list like 1) ... 2) ...
                            pass # Just ignore this—at least they'll still get the above mismatched count message
                        else:
                            locateString = f" after recent '{nestingString[-1]}'" if nestingString else ''
                            self.warnings.append(f"{ref} line {line_number:,}: Possible nesting error—found unexpected '{char}'{locateString} near {lines[line_number-1]}")
                elif char == '\n':
                    line_number += 1
            if nestingString: # handle left-overs
                reformatted_nesting_string = "'" + "', '".join(nestingString) + "'"
                self.warnings.append(f"{ref}: Seem to have the following unclosed field(s): {reformatted_nesting_string}")
        # NOTE: Notifying all those is probably overkill,
        #  but never mind (it might help detect multiple errors)

        # These are markdown specific checks, but hopefully shouldn't hurt to be done for all strings
        # They don't seem to be picked up by the markdown linter libraries for some reason.
        for field,regex in ( # Put longest ones first
                        # Seems that the fancy ones (commented out) don't find occurrences at the start (or end?) of the text
                        ('___', r'___'),
                        # ('___', r'[^_]___[^_]'), # three underlines
                        ('***', r'\*\*\*'),
                        # ('***', r'[^\*]\*\*\*[^\*]'), # three asterisks
                        ('__', r'__'),
                        # ('__', r'[^_]__[^_]'), # two underlines
                        ('**', r'\*\*'),
                        # ('**', r'[^\*]\*\*[^\*]'), # two asterisks
                    ):
            count = len(re.findall(regex, some_text)) # Finds all NON-OVERLAPPING matches
            if count:
                # print(f"check_punctuation_pairs found {count} of '{field}' at {ref} in '{some_text}'")
                if (count % 2) != 0:
                    # print(f"{ref}: Seem to have have mismatched '{field}' pairs in '{some_text}'")
                    content_snippet = some_text if len(some_text) < 85 \
                                        else f"{some_text[:40]} …… {some_text[-40:]}"
                    self.warnings.append(f"{ref}: Seem to have have mismatched '{field}' pairs in '{content_snippet}'")
                    break # Only want one warning per text
    # end of Preprocessor.check_punctuation_pairs function
# end of Preprocessor class



class ObsPreprocessor(Preprocessor):
    # def __init__(self, *args, **kwargs) -> None:
    #     super(ObsPreprocessor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_chapters(project_path:str) -> List[Dict[str,Any]]:
        chapters:List[Dict[str,Any]] = []
        for chapter in sorted(os.listdir(project_path)):
            if os.path.isdir(os.path.join(project_path, chapter)) and chapter not in ObsPreprocessor.ignoreDirectories:
                chapters.append({
                    'id': chapter,
                    'title': ObsPreprocessor.get_chapter_title(project_path, chapter),
                    'reference': ObsPreprocessor.get_chapter_reference(project_path, chapter),
                    'frames': ObsPreprocessor.get_chapter_frames(project_path, chapter)
                })
        return chapters


    @staticmethod
    def get_chapter_title(project_path:str, chapter) -> str:
        """
        Get a chapter title.
        if the title file does not exist, it will hand back the number with a period only.
        """
        title_filepath = os.path.join(project_path, chapter, 'title.txt')
        if os.path.exists(title_filepath):
            # title = self.check_and_clean_title(read_file(title_filepath), f'{chapter}/title/txt')
            title = read_file(title_filepath).strip()
        else:
            title = chapter.lstrip('0') + '. '
        return title


    @staticmethod
    def get_chapter_reference(project_path:str, chapter:str) -> str:
        """Get the chapters reference text"""
        reference_file = os.path.join(project_path, chapter, 'reference.txt')
        reference = ''
        if os.path.exists(reference_file):
            contents = read_file(reference_file)
            reference = contents.strip()
        return reference


    @staticmethod
    def get_chapter_frames(project_path:str, chapter:str) -> List[Dict[str,Any]]:
        frames:List[Dict[str,Any]] = []
        chapter_dir = os.path.join(project_path, chapter)
        for frame in sorted(os.listdir(chapter_dir)):
            if frame not in ObsPreprocessor.ignoreFiles:
                text = read_file(os.path.join(project_path, chapter, frame))
                frames.append({
                    'id': chapter + '-' + frame.strip('.txt'),
                    'text': text
                })
        return frames


    def is_chunked(self, project) -> bool:
        chapters = self.rc.chapters(project.identifier)
        if chapters and len(chapters):
            chunks = self.rc.chunks(project.identifier, chapters[0])
            for chunk in chunks:
                if os.path.basename(chunk) in ['title.txt', 'reference.txt', '01.txt']:
                    return True
        return False


    def run(self) -> Tuple[int, List[str]]:
        for project in self.rc.projects:
            project_path = os.path.join(self.source_dir, project.path)
            # Copy all the markdown files in the project root directory to the output directory
            for file_path in glob(os.path.join(project_path, '*.md')):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path) \
                        and os.path.basename(file_path) not in self.ignoreFiles:
                    copy(file_path, output_file_path)
                    self.num_files_written += 1
            if self.is_chunked(project):
                for chapter in self.get_chapters(project_path):
                    markdown = f"# {chapter['title']}\n\n"
                    for frame in chapter['frames']:
                        markdown += f"![OBS Image](https://cdn.door43.org/obs/jpg/360px/obs-en-{frame.get('id')}.jpg)\n\n"
                        markdown += frame['text'] + '\n\n'
                    markdown += f"_{chapter['reference']}_\n"
                    output_file = os.path.join(self.output_dir, f"{chapter.get('id')}.md")
                    write_file(output_file, markdown)
                    self.num_files_written += 1
            else:
                for chapter in self.rc.chapters(project.identifier):
                    f = None
                    if os.path.isfile(os.path.join(project_path, chapter, '01.md')):
                        f = os.path.join(project_path, chapter, '01.md')
                    elif os.path.isfile(os.path.join(project_path, chapter, 'intro.md')):
                        f = os.path.join(project_path, chapter, 'intro.md')
                    if f:
                        copy(f, os.path.join(self.output_dir, f'{chapter}.md'))
                        self.num_files_written += 1
        if self.num_files_written == 0:
            self.errors.append("No OBS source files discovered")
        return self.num_files_written, self.errors + self.warnings + (self.messages if self.errors or self.warnings else [])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--source', dest='source_dir', default=False, required=False, help='Working Directory')
    parser.add_argument('-o', '--output', dest='output_dir', default=False, required=False, help='Output Directory')
    args = parser.parse_args(sys.argv[1:])
    output_dir = args.output_dir
    source_dir = args.source_dir
    do_preprocess(source_dir, output_dir)
    
