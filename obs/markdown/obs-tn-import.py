#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>


"""
This script reconstructs files into the door43 structure, given an input file
which is created by obs/markdown/obs-tn-export.sh.
"""

import os
import sys
import codecs

#pages='/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages'
pages='/tmp/pages'


def fileImport(fl):
    for i in fl:
        if i in [u'', u'\n', u'\r', u'\r\n']:
            continue
        fparts = i.split('\n')
        writeFile(fparts[0], u'\n'.join(fparts[1:]))

def writeFile(outfile, content):
    makeDir(outfile.rpartition(u'/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(content)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = str(sys.argv[1]).strip()
        if not os.path.exists(f):
            print 'File not found: {0}'.format(f)
            sys.exit(1)
    else:
        print 'Please specify an input file.'
        sys.exit(1)
    os.chdir(pages)
    flist = codecs.open(f, 'r', encoding='utf-8').read().split(u'filename: ')
    fileImport(flist)
