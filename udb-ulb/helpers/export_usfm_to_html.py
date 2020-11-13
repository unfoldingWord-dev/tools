#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
"""
This script exports a Bible into the given format from local USFM files
"""
import os
import sys
import codecs
import shutil
import argparse
import tempfile
from ...general_tools.bible_books import BOOK_NUMBERS
from usfm_tools.transform import UsfmTransform


def main(source, lang_code, resource_id, books, outfile):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    tmpdir = tempfile.mkdtemp(prefix='uwb-{0}-{1}-'.format(resource_id, lang_code))
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)

    usfm_dir = tmpdir + "/usfm"

    if not books:
        shutil.copytree(source, usfm_dir)
    else:
        os.makedirs(usfm_dir)
        for book in books:
            source_file = '{0}/{1}-{2}.usfm'.format(source, BOOK_NUMBERS[book.lower()], book.upper())
            if not os.path.isfile(source_file):
                raise IOError('File not found: {}'.format(source_file))
            shutil.copy(source_file, usfm_dir)

    UsfmTransform.buildSingleHtml(usfm_dir, tmpdir, "bible")
    shutil.copyfile(tmpdir+'/bible.html', outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--source', dest='source', default=False, required=True, help="USFM Source Directory")
    parser.add_argument('-l', '--lang', dest='langcode', default=False, required=True, help="Language Code")
    parser.add_argument('-r', '--resource', dest='resource_id', default=False, required=True, help="Bible Version")
    parser.add_argument('-b', '--book', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-o', '--outfile', dest='outfile', default=False, required=True, help="Output file")

    args = parser.parse_args(sys.argv[1:])

    main(args.source, args.langcode, args.resource_id, args.books, args.outfile)
