#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2018 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#
#  Copies the Bible references from one set of tW files to another (copy between two repos)
#
#  Usage: copy_bible_references.py -i <input tw repo> -o <output tw repo>
#

import os
import re
import sys
import json
import codecs
import argparse
import glob

reload(sys)
sys.setdefaultencoding('utf8')

def main(inpath, outpath):
    inBibleDir = os.path.join(inpath, 'bible')
    outBibleDir = os.path.join(outpath, 'bible')
    groupDirs = glob.glob(os.path.join(inBibleDir, '*'))
    for groupDir in groupDirs:
        if os.path.isdir(groupDir):
            group = os.path.basename(groupDir)
            articles = glob.glob(os.path.join(groupDir, '*'))
            for articlePath in articles:
                article = os.path.basename(articlePath)
                outPath = os.path.join(outBibleDir, group, article)
                if os.path.exists(outPath):
                    print "Reading from " + articlePath
                    f = codecs.open(articlePath, 'r', encoding='utf-8')
                    lines = f.readlines()
                    inRef = False
                    found = False
                    refs = ''
                    for line in lines:
                        if 'Bible References' in line:
                            inRef = True
                            found = True
                        elif '#' in line:
                            inRef = False
                        elif inRef:
                            refs += line
                    f.close()

                    if '=' in refs:
                        print 'BAD REFS: '+refs

                    if not found:
                        print "WARNING! No Bible References section found in " + articlePath
                    else:
                        found = False
                        f = codecs.open(outPath, 'r', encoding='utf-8')
                        lines = f.readlines()
                        inRef = False
                        after = False
                        newContent = ''
                        for line in lines:
                            if 'Bible References' in line:
                                inRef = True
                                found = True
                                newContent += line
                                newContent += refs
                            elif '#' in line:
                                inRef = False
                                after = True
                                newContent += line
                            elif not inRef:
                                newContent += line
                        f.close()
                        if not found:
                            print "WARNING! No Bible References sectionf oudn in " + outPath
                        else:
                            print "Writing to "+outPath
                            f = codecs.open(outPath, 'w', encoding='utf-8')
                            f.write(newContent)
                            f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="inpath",
        help="Directory of the tW with correct Bible references", required=True)
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=True, help="Directory of the repo with files to update")
    args = parser.parse_args(sys.argv[1:])
    main(args.inpath, args.outpath)
