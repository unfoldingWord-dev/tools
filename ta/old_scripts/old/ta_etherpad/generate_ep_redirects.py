#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

import sys
from etherpad_lite import EtherpadLiteClient

def main():
    try:
        pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                api_version='1.2.10')
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)

    all_pads = ep.listAllPads()
    ver_pads = [x for x in all_pads['padIDs'] if x.startswith(u'ta-')]
    ver_pads.sort()

    redirects = []
    for p in ver_pads:
        content = ep.getText(padID=p)['text']
        if 'Welcome to Etherpad!' in content:
            continue
        redirects.append(u'rewrite /p/{0} /p/{1} permanent;'.format(p, ep.getReadOnlyID(padID=p)['readOnlyID']))
    print u'\n'.join(sorted(redirects))

if __name__ == '__main__':
    main()
