#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>


"""
This script renames the DokuWiki export UTB files to appropriate USFM
filenames.

Requires that https://github.com/Door43/USFM-Tools be checked out to
/var/www/vhosts/door43.org/USFM-Tools or be on the path
"""

import os
import sys
# Import the bookKeys mapping from USFM-Tools
USFMTools='/var/www/vhosts/door43.org/USFM-Tools/support'
sys.path.append(USFMTools)
try:
    from books import bookKeys
except ImportError:
    print "Please ensure that {0}/books.py exists.".format(USFMTools)
    sys.exit(1)


def renameToUSFM(d):
    os.chdir(d)
    for f in os.listdir(d):
        bkup = f.replace('.usfm', '').upper()
        if not bookKeys.has_key(bkup):
            print '{0} not found in book dictionary'.format(bkup)
            continue
        os.rename(f, '{0}-{1}-uwb.usfm'.format(bookKeys[bkup], bkup))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        d = str(sys.argv[1]).strip()
        if not os.path.exists(d):
            print 'Directory not found: {0}'.format(d)
            sys.exit(1)
    else:
        print 'Please specify the directory.'
        sys.exit(1)
    bookKeys[u'FRT'] = u'000'
    renameToUSFM(d)
