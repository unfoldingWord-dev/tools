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
This script publishes the Unlocked Bible into PDF from the API.

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

CatalogJSON='https://api.unfoldingword.org/uw/txt/2/catalog.json'

# Import USFM-Tools
#USFMTools='/var/www/vhosts/door43.org/USFM-Tools'
USFMTools='/home/rmahn/USFM-Tools'
sys.path.append(USFMTools)
try:
    import transform
except ImportError:
    print "Please ensure that {0} exists.".format(USFMTools)
    sys.exit(1)

def main(langcode, ver, books, format, outfile):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);

    # Get the JSON
    catalog = json.load(urllib2.urlopen(CatalogJSON))

    bible=None
    for item in catalog['cat']:
        if item['slug'] == 'bible':
            bible = item
            break

    lang=None
    for language in bible['langs']:
        if language['lc'] == langcode:
            lang=language
            break

    if lang is None:
        print "The language code {0} is not found in the catalog at {1}. Exiting...".format(langcode, CatalogJSON)
        sys.exit(1)

    bible=None
    for version in lang['vers']:
        if version['slug'] == ver:
            bible=version
            break

    if bible is None:
        print "The Bible version {0} for language {1} is not found in the catalog at {2}. Exiting...".format(ver, langcode, CatalogJSON)
        sys.exit(1)

    sources = []
    for source in bible['toc']:
        if books is None or source['slug'] in books:
            sources += [source['src']]

    if not sources:
        print "No sources were found for langage {0} of version {1} in {2}. Exiting...".format(langcode, ver, CatalogJSON)
        sys.exit(1)

    tmpdir = '/tmp/uwb-{0}-{1}'.format(ver, langcode)

    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir+"/sources")
    for source in sources:
        f = urllib2.urlopen(source)
        with open(tmpdir+"/sources/"+os.path.basename(source), "wb") as local_file:
            local_file.write(f.read())

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
