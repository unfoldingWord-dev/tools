# coding=utf-8

from __future__ import unicode_literals
import re


def unalign_usfm(aligned_usfm):
    """
    Converts an aligned USFM string to an unaligned USFM compatible string
    :param aligned_usfm:
    :return: the unaligned USFM of the string
    """
    # Remove all tags used for alignments and words
    usfm = re.sub(r'\\ts(-s)*\s*\\\*\s*', r'', aligned_usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-s[^*]*?\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\zaln-e\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\k-s.*?\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\k-e\\\*', r'', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\w ([^|]+)\|.*?\\w\*', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\n', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^([^\\].*)\n(?=[^\\])', r'\1 ', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\\(.*)\n(?=[^\\])', r'\\\1 ', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'  +', ' ', usfm, flags=re.UNICODE | re.MULTILINE)

    # Clean up bad USFM data and fixing punctuation
    usfm = re.sub(r"\s*' s(?!\w)", "'s", usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\s5', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'\\fqa([^*]+)\\fqa(?![*])', r'\\fqa\1\\fqa*', usfm, flags=re.UNICODE | re.MULTILINE)

    # Pair up quotes by chapter
    chapters = re.compile(r'\\c ').split(usfm)
    usfm = chapters[0]
    for chapter in chapters[1:]:
        chapter = re.sub(r'[ \t]*"([^"]+)"[ \t]*', r' "\1" ', chapter, flags=re.UNICODE | re.MULTILINE | re.DOTALL)
        usfm += '\\c {0}'.format(chapter)
    usfm = re.sub(r'\\(\w+\**)([^\w* \n])', r'\\\1 \2', usfm, flags=re.UNICODE | re.MULTILINE)  # \\q1" => \q1 "
    usfm = re.sub(r" ' ", r" '", usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r' +([:;.?,!\]})-])', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'([{(\[-]) +', r'\1', usfm, flags=re.UNICODE | re.MULTILINE)

    return usfm.strip()
