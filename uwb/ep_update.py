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
This script makes updates to the Etherpad documents directly.
'''

import re
import sys
import argparse
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException


_digits = re.compile(ur'\d')
hyphenfixre = re.compile(ur'[ ]?--[ ]?')


def contains_digits(d):
    return bool(_digits.search(d))

def main(args):
    try:
        pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                                         api_version='1.2.10')

    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    all_pads = ep.listAllPads()
    ver_pads = [x for x in all_pads['padIDs'] if args.slug.lower() in x]
    ver_pads.sort()
    bk_pads = [x for x in ver_pads if contains_digits(x)]

    for p in bk_pads:
        if p != 'en-en-ulb-gen-01': continue
        # Get text
        p_orig = ep.getText(padID=p)['text']
        p_content = p_orig

        # Run transformations
        if args.hyphenfix:
            p_content = hyphenfixre.sub(u'—', p_content)
            p_content = p_content.replace(u' — ', u'—')
        #if args.versefix:
            #p_content = verseFix(p_content)
        #if args.smartquotes:
            #p_content = smartquotes(p_content)

        # save text
        if p_orig != p_content:
            print 'Updating {0}'.format(p)
            try:
                ep.setText(padID=p, text=p_content.encode('utf-8'))
            except EtherpadException as e:
                print '{0}: {1}'.format(e, p)
        break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-r', '--resource', dest="slug", default=False,
        required=True, help="Resource (UDB|ULB)")
    parser.add_argument('--hypen-fix', dest="hyphenfix", default=False,
        required=False, action='store_true', help="Fix hyphens.")
    parser.add_argument('--verse-fix', dest="versefix", default=False,
        required=False, action='store_true', help="Fix verse markers.")
    parser.add_argument('--smartquotes', dest="smartquotes", default=False,
        required=False, action='store_true',
        help="Change straight quotes to smart.")

    args = parser.parse_args(sys.argv[1:])

    main(args)
