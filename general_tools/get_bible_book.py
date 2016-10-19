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

import sys

books = { 
    u'GEN': [u'Genesis', '01'],
    u'EXO': [u'Exodus', '02'],
    u'LEV': [u'Leviticus', '03'],
    u'NUM': [u'Numbers', '04'],
    u'DEU': [u'Deuteronomy', '05'],
    u'JOS': [u'Joshua', '06'],
    u'JDG': [u'Judges', '07'],
    u'RUT': [u'Ruth', '08'],
    u'1SA': [u'1 Samuel', '09'],
    u'2SA': [u'2 Samuel', '10'],
    u'1KI': [u'1 Kings', '11'],
    u'2KI': [u'2 Kings', '12'],
    u'1CH': [u'1 Chronicles', '13'],
    u'2CH': [u'2 Chronicles', '14'],
    u'EZR': [u'Ezra', '15'],
    u'NEH': [u'Nehemiah', '16'],
    u'EST': [u'Esther', '17'],
    u'JOB': [u'Job', '18'],
    u'PSA': [u'Psalms', '19'],
    u'PRO': [u'Proverbs', '20'],
    u'ECC': [u'Ecclesiastes', '21'],
    u'SNG': [u'Song of Solomon', '22'],
    u'ISA': [u'Isaiah', '23'],
    u'JER': [u'Jeremiah', '24'],
    u'LAM': [u'Lamentations', '25'],
    u'EZK': [u'Ezekiel', '26'],
    u'DAN': [u'Daniel', '27'],
    u'HOS': [u'Hosea', '28'],
    u'JOL': [u'Joel', '29'],
    u'AMO': [u'Amos', '30'],
    u'OBA': [u'Obadiah', '31'],
    u'JON': [u'Jonah', '32'],
    u'MIC': [u'Micah', '33'],
    u'NAM': [u'Nahum', '34'],
    u'HAB': [u'Habakkuk', '35'],
    u'ZEP': [u'Zephaniah', '36'],
    u'HAG': [u'Haggai', '37'],
    u'ZEC': [u'Zechariah', '38'],
    u'MAL': [u'Malachi', '39'],
    u'MAT': [u'Matthew', '40'],
    u'MRK': [u'Mark', '41'],
    u'LUK': [u'Luke', '42'],
    u'JHN': [u'John', '43'],
    u'ACT': [u'Acts', '44'],
    u'ROM': [u'Romans', '45'],
    u'1CO': [u'1 Corinthians', '46'],
    u'2CO': [u'2 Corinthians', '47'],
    u'GAL': [u'Galatians', '48'],
    u'EPH': [u'Ephesians', '49'],
    u'PHP': [u'Philippians', '50'],
    u'COL': [u'Colossians', '51'],
    u'1TH': [u'1 Thessalonians', '52'],
    u'2TH': [u'2 Thessalonians', '53'],
    u'1TI': [u'1 Timothy', '54'],
    u'2TI': [u'2 Timothy', '55'],
    u'TIT': [u'Titus', '56'],
    u'PHM': [u'Philemon', '57'],
    u'HEB': [u'Hebrews', '58'],
    u'JAS': [u'James', '59'],
    u'1PE': [u'1 Peter', '60'],
    u'2PE': [u'2 Peter', '61'],
    u'1JN': [u'1 John', '62'],
    u'2JN': [u'2 John', '63'],
    u'3JN': [u'3 John', '64'],
    u'JUD': [u'Jude', '65'],
    u'REV': [u'Revelation', '66'],
}

book_order = ['GEN', 'EXO', 'LEV', 'NUM', 'DEU', 'JOS', 'JDG', 'RUT', '1SA', '2SA', '1KI', '2KI', '1CH', '2CH', 'EZR', 'NEH', 'EST', 'JOB', 'PSA', 'PRO', 'ECC', 'SNG', 'ISA', 'JER', 'LAM', 'EZK', 'DAN', 'HOS', 'JOL', 'AMO', 'OBA', 'JON', 'MIC', 'NAM', 'HAB', 'ZEP', 'HAG', 'ZEC', 'MAL', 'MAT', 'MRK', 'LUK', 'JHN', 'ACT', 'ROM', '1CO', '2CO', 'GAL', 'EPH', 'PHP', 'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE', '2PE', '1JN', '2JN', '3JN', 'JUD', 'REV']

if __name__ == '__main__':
    if sys.argv[1]:
        bk = sys.argv[1].upper()
    else:
        print "Must specify book (e.g gen)."
        sys.exit(1)

    if bk not in books:
        print "Book code not found: {0}".format(bk)
        sys.exit(1)

    print books[bk][0]
