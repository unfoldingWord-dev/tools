# coding=utf-8

from __future__ import unicode_literals
import re

def usfm3_to_usfm2(usfm):
    """
    Converts a USFM 3 string to a USFM 2 compatible string
    :param usfm3:
    :return: the USFM 2 version of the string
    """
    # Kind of usfm3 to usfm2
    usfm = re.sub(r'\\zaln-s[^\\]*\n', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-e\\\*\n', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-e\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\w ([^|]+)\|.*?\\w\*', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\n', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^([^\\].*)\n(?=[^\\])', r'\1 ', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\\(.*)\n(?=[^\\])', r'\\\1 ', usfm, flags=re.UNICODE | re.MULTILINE)

    # Clean up bad USFM data and fixing punctuation
    usfm = re.sub(r"\s*' s(?!\w)", "'s", usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\s5', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\fqa([^*]+)\\fqa(?![*])', r'\\fqa\1\\fqa*', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r' +([\\:;.?,!)-])', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'([(-]) +', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    chapters = re.compile(r'\\c').split(usfm)
    usfm = chapters[0];
    for chapter in chapters[1:]:
        chapter = re.sub(r'\s*"\s*([^"]+)\s*"\s*', r' "\1" ', chapter, flags=re.UNICODE | re.MULTILINE | re.DOTALL)
        usfm += '\c'+chapter
    usfm = re.sub(r'\\(\w+\**)([^\w* \n])', r'\\\1 \2', usfm, flags=re.UNICODE | re.MULTILINE) # \\q1" => \q1 "
    usfm = re.sub(r" ' ", r" '", usfm, flags=re.UNICODE | re.MULTILINE)

    return usfm.strip()
