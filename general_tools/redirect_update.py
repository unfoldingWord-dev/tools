#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#
#  Requires PyGithub.

'''
This script configures webhooks for the DokuWiki namespaces via their Github
repos.
'''

import os
import sys
import codecs
import urllib2
sys.path.append('/var/www/vhosts/door43.org/tools/general_tools')
try:
    from git_wrapper import *
except:
    print "Please verify that"
    print "/var/www/vhosts/door43.org/tools/general_tools exists."
    sys.exit(1)
try:
    from github import Github
    from github import GithubException
except:
    print "Please install PyGithub with pip"
    sys.exit(1)

redirecttmpl = 'rewrite ^/{0}/(.*)$ http://{1}/{0}/$1 permanent;'
lang_url = 'https://api.unfoldingword.org/obs/txt/1/langnames.json'
host_regions = { 'Europe': 'uk.door43.org',
                 'Pacific': 'jp.door43.org',
                 'Americas': 'us.door43.org',
                 'Africa': 'us.door43.org',
                 'Asia': 'us.door43.org',
               }


def getLangs(url):
    try:
        request = urllib2.urlopen(url).read()
    except:
        request = '{}'
    return json.loads(request)

def writeFile(outfile, p):
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()


if __name__ == '__main__':
    lang_info = getLangs(lang_url)
    redirects = []
    for l in lang_info:
        if l['lr'] == u'':
            reg = u'us.door43.org'
            print 'Region not configured for {0}'.format(l['lc'])
        else:
            reg = host_regions[l['lr']]
        redirects.append(redirecttmpl.format(l['lc'], reg))

    r_for_uk = [x for x in redirects if 'uk.door43.org' not in x]
    r_for_us = [x for x in redirects if 'us.door43.org' not in x]
    r_for_jp = [x for x in redirects if 'jp.door43.org' not in x]

    writeFile('/etc/puppet/modules/nginx/files/r_for_uk', '\n'.join(r_for_uk))
    writeFile('/etc/puppet/modules/nginx/files/r_for_us', '\n'.join(r_for_us))
    writeFile('/etc/puppet/modules/nginx/files/r_for_jp', '\n'.join(r_for_jp))

    print "Please review modified files in /etc/puppet."

