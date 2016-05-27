#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

'''
This script exports the ULB and UDB from Etherpad by each book into given directory.
'''

import os
import re
import sys
import json
import codecs
import datetime
import argparse
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException

def main():
    try:
        pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                api_version='1.2.10')
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    namespace = u'ta-'

    all_pads = ep.listAllPads()
    ver_pads = [x for x in all_pads['padIDs'] if x.startswith(namespace)]
    ver_pads.sort()

    for p in ver_pads:
        content = []
        # Skips pad that WA uses for communication (e.g. 'en-ulb-1ti')
        content = ep.getText(padID=p)['text']
        if 'Welcome to Etherpad!' in content:
            continue
        print u"rewrite /p/"+p+""

if __name__ == '__main__':
    main()
