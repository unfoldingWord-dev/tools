#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

'''
This script accepts a paragraph of input and outputs typographically correct
text using pandoc.  Note line breaks are not retained.
'''

import os
import sys
import shlex
from subprocess import *


def smartquotes(text):
    '''
    Runs text through pandoc for smartquote correction.
    '''
    command = shlex.split('/bin/pandoc --smart -t plain')
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate(text)).strip()
    return comout, com.returncode


if __name__ == '__main__':
    print smartquotes(sys.stdin.read())[0]
