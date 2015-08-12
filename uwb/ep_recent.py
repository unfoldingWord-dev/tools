#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

"""
Generates HTML page of recently edited pads.
"""

import os
import sys
import time
import codecs
from etherpad_lite import EtherpadLiteClient
from etherpad_lite import EtherpadException


path = '/var/www/vhosts/pad.door43.org/httpdocs/recent.html'
link = '''<tr>
<td><a href="https://pad.door43.org/p/{0}">{0}</a></td>
<td>{1}</td>
</tr>'''
page_template = '''<!DOCTYPE html>
<html lang="en">
<head>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/cs
s/bootstrap.min.css">
</head>
<body>
<div class="container">
<h1>unfoldingWord Recently Edited Pads</h1>
<div class="row"><div class="col-md-4">
<table class="table table-striped">
<th>Pad Name</th><th>Modified Time (EST)</th>
{0}
</table>
</div></div>
</div>
</body>
</html>'''


def writeFile(f, content):
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()


if __name__ == '__main__':
    try:
        pw = open('/root/.ep_api_key', 'r').read().strip()
        ep = EtherpadLiteClient(base_params={'apikey': pw},
                                                         api_version='1.2.10')
    except:
        e = sys.exc_info()[0]
        print 'Problem logging into Etherpad via API: {0}'.format(e)
        sys.exit(1)
    os.environ['TZ'] = 'US/Eastern'
    pads = ep.listAllPads()
    recent = []
    for p in pads['padIDs']:
        if not p:
            continue
        recent.append((p, ep.getLastEdited(padID=p)['lastEdited']))

    recent_sorted = sorted(recent, key=lambda p: p[1], reverse=True)
    recent_html = []
    for i in recent_sorted:
        t = time.strftime('%Y-%m-%d %H:%M:%S',
             time.localtime(int(str(i[1])[0:10])))
        recent_html.append(link.format(i[0], t))

    writeFile(path, page_template.format('\n'.join(recent_html)))
