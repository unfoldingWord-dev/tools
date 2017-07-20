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
This script queries the UW Catalog
"""
import sys
import argparse
from catalog import UWCatalog


def main(langcode=None, resource_id=None, project_id=None, key=None):
    uwc = UWCatalog()

    if not langcode:
        if key:
            print(uwc.catalog[key])
        else:
            print(uwc.catalog)
        return

    if not resource_id:
        lang = uwc.get_language(langcode)
        if key:
            print(lang[key])
        else:
            print(lang)
        return

    if not project_id:
        resource = uwc.get_resource(langcode, resource_id)
        if key:
            print(resource[key])
        else:
            print(resource)
            return

    project = uwc.get_project(langcode, resource_id, project_id)
    if key:
        print(project[key])
    else:
        print(project)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='langcode', default=None, required=False, help="Language Code")
    parser.add_argument('-r', '--resource', dest='resource_id', default=None, required=False, help="Resource")
    parser.add_argument('-p', '--project', dest='project_id', default=None, required=False, help="Project")
    parser.add_argument('-k', '--key', dest='key', default=None, help="Key of the catalog to query")

    args = parser.parse_args(sys.argv[1:])

    main(args.langcode, args.resource_id, args.project_id, args.key)
