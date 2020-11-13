#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>


"""
This script queries the Bible Status of a given Bible
"""

import os
import sys
import argparse
from status import BibleStatus

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang', default=None, required=True, help="Language Code")
    parser.add_argument('-v', '--version', dest='ver', default=None, required=True, help="Bible Version")
    parser.add_argument('-b', '--book', dest='book', default=None, required=False, help="Bible Book")
    parser.add_argument('-k', '--key', dest='key', default=None, help="Key of the catalog to query")

    args = parser.parse_args(sys.argv[1:])

    lang=args.lang
    ver=args.ver
    book=args.book
    key=args.key

    status = BibleStatus(ver, lang)

    if not book:
        if not key:
            print status.getBooksPublished()
        else:
            if hasattr(status, key):
                print getattr(status, key)
            else:
                print status.getBibleStatus(key)
    else:
        if not key:
            print status.getBook(book)
        else:
            print status.getBookStatus(book, key)
