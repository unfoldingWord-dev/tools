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
which is created by obs/dokuwiki/sovee-export.sh.
"""

import os
import sys
import codecs
import shlex
from subprocess import *

pages='/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages'
filenamep = u'<!-- filename: '


def fileImport(fl):
    for i in fl:
        if i in [u'', u'\n', u'\r', u'\r\n']:
            continue
        if len(i) < 10:
            continue
        fparts = i.split('\n')
        fname = fparts[0].replace(u'-->', u'').strip()
        ftext = getDW(u'\n'.join(fparts[1:]).strip())
        ftext = ftext.replace(':https:', 'https:')
        writeFile(fname, ftext)

def getDW(text):
    command = shlex.split(u'pandoc-dev -f html -t dokuwiki')
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, ret = com.communicate(text.encode('utf8'))
    return out.decode('utf-8').strip()

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
    flist = codecs.open(f, 'r', encoding='utf-8').read().split(filenamep)
    fileImport(flist)
