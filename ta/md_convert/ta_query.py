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
This script queries the tA Collection
"""

import os
import sys
import argparse
from ta import taCollection

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-m', '--manual', dest='manual', default=None, required=True, help="Manual name")
    parser.add_argument('-p', '--module', dest='module', default=None, required=False, help="Manual name")
    parser.add_argument('-k', '--key', dest='key', default=None, required=True, help="Key of the manual or module to query")
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tA repos", required=True)

    args = parser.parse_args(sys.argv[1:])

    tac = taCollection(args.inpath)
    if args.module:
        print getattr(tac.manualDict[args.manual].moduleDict[args.module], args.key)
    else:
        print getattr(tac.manualDict[args.manual], args.key)
    sys.exit()
