#!/usr/bin/env python
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
from time import sleep
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

filepath = '/etc/puppet/modules/nginx/files/{0}'
urltmpl = 'http://{0}:9094'
hosts = ( ['us.door43.org', 'r_for_us'],
          ['uk.door43.org', 'r_for_uk'],
          ['jp.door43.org', 'r_for_jp'],
        )


if __name__ == '__main__':
    # Log in to Github via API
    try:
        pw = open('/root/.github_pass', 'r').read().strip()
        guser = githubLogin('dsm-git', pw)
        githuborg = getGithubOrg('door43', guser)
    except GithubException as e:
        print 'Problem logging into Github: {0}'.format(e)
        sys.exit(1)

    slave_info = {}
    for h in hosts:
        if not os.path.exists(filepath.format(h[1])):
            print 'Cannot access {0}'.format(filepath.format(h[1]))
            sys.exit(1)
        lines = open(filepath.format(h[1]), 'r').readlines()
        for l in lines:
            repo_name = 'd43-{0}'.format(l.split('/')[1])
            if not repo_name in slave_info:
                slave_info[repo_name] = []
            slave_info[repo_name].append(urltmpl.format(h[0]))

    repos = githuborg.get_repos(type="public")
    for r in repos:
        if 'd43-' not in r.name:
            continue
        if guser.get_rate_limit().rate.remaining < 1000:
            sleep(5)

        print 'Configuring {0}'.format(r.name)

        hooks = r.get_hooks()
        cur_hks = [x.config['url'] for x in hooks if x.name == 'web']

        # Create hooks if they don't exist
        for host in set(slave_info[r.name]) - set(cur_hks):
            r.create_hook('web', {u'url': host, u'insecure_ssl': u'0',
                                  u'secret': u'', u'content_type': u'json'})

        # Remove hooks if need be
        for host in set(cur_hks) - set(slave_info[r.name]):
            hk = [x for x in hooks if x.config['url'] == host]
            hk[0].delete()

        print 'Slave info {0}'.format(slave_info[r.name])
        print 'Original hooks {0}'.format(cur_hks)
        break
