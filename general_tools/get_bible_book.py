#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

'''
This script returns the name of the Bible code given.
'''

from __future__ import unicode_literals

import sys

books = { 
    'GEN': ['Genesis', '01'],
    'EXO': ['Exodus', '02'],
    'LEV': ['Leviticus', '03'],
    'NUM': ['Numbers', '04'],
    'DEU': ['Deuteronomy', '05'],
    'JOS': ['Joshua', '06'],
    'JDG': ['Judges', '07'],
    'RUT': ['Ruth', '08'],
    '1SA': ['1 Samuel', '09'],
    '2SA': ['2 Samuel', '10'],
    '1KI': ['1 Kings', '11'],
    '2KI': ['2 Kings', '12'],
    '1CH': ['1 Chronicles', '13'],
    '2CH': ['2 Chronicles', '14'],
    'EZR': ['Ezra', '15'],
    'NEH': ['Nehemiah', '16'],
    'EST': ['Esther', '17'],
    'JOB': ['Job', '18'],
    'PSA': ['Psalms', '19'],
    'PRO': ['Proverbs', '20'],
    'ECC': ['Ecclesiastes', '21'],
    'SNG': ['Song of Solomon', '22'],
    'ISA': ['Isaiah', '23'],
    'JER': ['Jeremiah', '24'],
    'LAM': ['Lamentations', '25'],
    'EZK': ['Ezekiel', '26'],
    'DAN': ['Daniel', '27'],
    'HOS': ['Hosea', '28'],
    'JOL': ['Joel', '29'],
    'AMO': ['Amos', '30'],
    'OBA': ['Obadiah', '31'],
    'JON': ['Jonah', '32'],
    'MIC': ['Micah', '33'],
    'NAM': ['Nahum', '34'],
    'HAB': ['Habakkuk', '35'],
    'ZEP': ['Zephaniah', '36'],
    'HAG': ['Haggai', '37'],
    'ZEC': ['Zechariah', '38'],
    'MAL': ['Malachi', '39'],
    'MAT': ['Matthew', '41'],
    'MRK': ['Mark', '42'],
    'LUK': ['Luke', '43'],
    'JHN': ['John', '44'],
    'ACT': ['Acts', '45'],
    'ROM': ['Romans', '46'],
    '1CO': ['1 Corinthians', '47'],
    '2CO': ['2 Corinthians', '48'],
    'GAL': ['Galatians', '49'],
    'EPH': ['Ephesians', '50'],
    'PHP': ['Philippians', '51'],
    'COL': ['Colossians', '52'],
    '1TH': ['1 Thessalonians', '53'],
    '2TH': ['2 Thessalonians', '54'],
    '1TI': ['1 Timothy', '55'],
    '2TI': ['2 Timothy', '56'],
    'TIT': ['Titus', '57'],
    'PHM': ['Philemon', '58'],
    'HEB': ['Hebrews', '59'],
    'JAS': ['James', '60'],
    '1PE': ['1 Peter', '61'],
    '2PE': ['2 Peter', '62'],
    '1JN': ['1 John', '63'],
    '2JN': ['2 John', '64'],
    '3JN': ['3 John', '65'],
    'JUD': ['Jude', '66'],
    'REV': ['Revelation', '67'],
}

book_order = ['GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA', '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP', 'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL', 'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE', '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV']

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1]:
        bk = sys.argv[1].upper()
    else:
        print "Must specify book (e.g gen)."
        sys.exit(1)

    if bk not in books:
        print "Book code not found: {0}".format(bk)
        sys.exit(1)

    print books[bk][0]
