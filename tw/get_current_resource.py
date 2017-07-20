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
This script queries the UW Catalog to get the latest resource specified and downloads the files
"""

import sys
import argparse
from catalog.v3.catalog import UWCatalog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='langcode', default=None, required=True, help="Language Code")
    parser.add_argument('-r', '--resource', dest='resource', default=None, required=True, help="Resource")
    parser.add_argument('-v', '--version', dest='version', default=None, required=False, help="Version")

    args = parser.parse_args(sys.argv[1:])

    uwc = UWCatalog()

    lang_code = args.langcode
    res_code = args.resource
    version = args.version

    resource = uwc.get_resource(lang_code, res_code)

    if version:
        ver = ""
        try:
            ver = resource['version']
        except:
            pass

        print ver

    else:
        url = ""
        try:
            projects = resource['projects']
            project = projects[0]
            formats = project['formats']
            format = formats[0]
            url = format['url']
        except:
            pass

        print url

    sys.exit()
