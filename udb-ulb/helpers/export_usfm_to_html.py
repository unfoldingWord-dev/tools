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
This script exports a Bible into the given format from the API.

Requires that https://github.com/Door43/USFM-Tools be checked out to
/var/www/vhosts/door43.org/USFM-Tools or be on the path
"""

import os
import sys
import codecs
import shutil
import argparse
import urllib
import tempfile
from ...catalog.v3.catalog import UWCatalog
from usfm_tools.transform import UsfmTransform

CatalogJSON='https://api.door43.org/v3/catalog.json'


def main(lang_code, resource_id, books, outfile):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);

    catalog = UWCatalog(CatalogJSON)

    lang = catalog.get_language(lang_code)
    bible = catalog.get_resource(lang_code, resource_id)

    if lang is None:
        print("The language code {0} is not found in the catalog at {1}. Exiting...".format(lang_code, CatalogJSON))
        sys.exit(1)

    if bible is None:
        print("The Bible version {0} for language {1} is not found in the catalog at {2}. Exiting...".format(resource_id, lang_code, CatalogJSON))
        sys.exit(1)

    sources = []
    for p in bible['projects']:
        if books is None or p['identifier'] in books:
            if 'formats' in p:
                for f in p['formats']:
                    if f['format'] == 'text/usfm':
                        sources += [f['url']]

    if not sources:

        print("No sources were found for language {0} of version {1} in {2}. Exiting...".format(lang_code, resource_id, CatalogJSON))
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix='uwb-{0}-{1}-'.format(resource_id, lang_code))

    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir+"/sources")
    for source in sources:
        f = urllib.URLopener()
        f.retrieve(source, tmpdir+"/sources/"+os.path.basename(source))

    UsfmTransform.buildSingleHtml(tmpdir+"/sources", tmpdir, "bible")
    shutil.copyfile(tmpdir+'/bible.html', outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='langcode', default=False, required=True, help="Language Code")
    parser.add_argument('-r', '--resource', dest='resource_id', default=False, required=True, help="Bible Version")
    parser.add_argument('-b', '--book', dest='books', nargs='+', default=None, required=False, help="Bible Book(s)")
    parser.add_argument('-o', '--outfile', dest='outfile', default=False, required=True, help="Output file")

    args = parser.parse_args(sys.argv[1:])

    main(args.langcode, args.resource_id, args.books, args.outfile)
