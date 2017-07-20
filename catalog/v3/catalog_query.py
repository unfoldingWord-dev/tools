#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>


"""
This script queries the UW Catalog
"""

import sys
import argparse
from catalog import UWCatalog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='langcode', default=None, required=False, help="Language Code")
    parser.add_argument('-v', '--version', dest='ver', default=None, required=False, help="Bible Version")
    parser.add_argument('-b', '--book', dest='book', default=None, required=False, help="Bible Book")
    parser.add_argument('-k', '--key', dest='key', default=None, help="Key of the catalog to query")

    args = parser.parse_args(sys.argv[1:])

    uwc = UWCatalog()

    langcode=args.langcode
    ver=args.ver
    book=args.book
    key=args.key

    if not langcode:
        if key:
            print(uwc.catalog[key])
        else:
            print(uwc.catalog)
        sys.exit()

    if not ver:
        lang = uwc.get_language(langcode)
        if key:
            print(lang[key])
        else:
            print(lang)
        sys.exit()

    if not book:
        bible = uwc.get_resource(langcode, ver)
        if key:
            if key in bible:
                print(bible[key])
            else:
                print(bible['status'][key])
        else:
            print(bible)
    else:
        book = uwc.get_project(langcode, ver, book)
        if key:
            print(book[key])
        else:
            print(book)
