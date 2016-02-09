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
This script exports a Bible into the given format in chunks from the chunk API
(e.g. https://api.unfoldingword.org/ts/txt/2/1ch/en/udb/source.json).

Requires that https://github.com/Door43/USFM-Tools be checked out to
/var/www/vhosts/door43.org/USFM-Tools or be on the path
"""

import os
import re
import sys
import json
import codecs
import shutil
import argparse
import datetime
import urllib2

sourceJSON='https://api.unfoldingword.org/ts/txt/2/{0}/{1}/{2}/source.json'

# Import USFM-Tools
USFMTools='/var/www/vhosts/door43.org/USFM-Tools'
sys.path.append(USFMTools)
try:
    import transform
except ImportError:
    print "Please ensure that {0} exists.".format(USFMTools)
    sys.exit(1)

def main(book, lang, ver, format, outfile):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);

    # Get the JSON
    data = json.load(urllib2.urlopen(sourceJSON.format(book, lang, ver)))

    tmpdir = '/tmp/uwb-{0}-{1}-{2}'.format(book, lang, ver)

    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir+"/sources")

    for chapter in data['chapters']:
        for frame in chapter.frames:
            f = open(tmpdir+"/sources/{0}/{1}.usfm".format(book,frame['id']), 'w')
            f.write(frame['text']

    if format == 'html':
        transform.buildSingleHtml(tmpdir+"/sources", tmpdir, "bible")
        shutil.copyfile(tmpdir+'/bible.html', outfile);
    if format == 'tex':
        transform.buildConTeXt(tmpdir+"/sources", tmpdir, "bible")
        shutil.copyfile(tmpdir+'/working/tex/bible.tex', outfile);

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='langcode', default=False, required=True, help="Language Code")
    parser.add_argument('-v', '--version', dest='ver', default='udb', required=True, help="Bible Version")
    parser.add_argument('-b', '--book', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-f', '--format', dest='format', default='html', required=False, help='Format')
    parser.add_argument('-o', '--outfile', dest='outfile', default=False, required=True, help="Output file")

    args = parser.parse_args(sys.argv[1:])

    main(args.langcode, args.ver, args.books, args.format, args.outfile)
    ### chown -R syncthing:syncthing /var/www/vhosts/api.unfoldingword.org/httpdocs/
