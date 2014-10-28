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
This script configures all of the DokuWiki namespaces for a new server
via their Github repos.
'''

import os
import sys
import codecs
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


pagesdir = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages'


if __name__ == '__main__':
    # Log in to Github via API
    try:
        pw = open('/root/.github_pass', 'r').read().strip()
        guser = githubLogin('dsm-git', pw)
        githuborg = getGithubOrg('door43', guser)
    except GithubException as e:
        print 'Problem logging into Github: {0}'.format(e)
        sys.exit(1)

    if not os.path.exists(pagesdir):
        os.makedirs(pagesdir, 0755)
    # Cycle through available repos and clone them
    repo_urls = []
    repos = githuborg.get_repos(type="public")
    for r in repos:
        ssh_url = r.ssh_url
        if 'd43-' in ssh_url:
            repo_urls.append(ssh_url)
    repo_urls.sort()
    for ssh_url in repo_urls:
        lang = ssh_url.split('/')[1].replace('.git', '').replace('d43-', '')
        d = os.path.join(pagesdir, lang)
        if os.path.exists(d):
            print 'Will not clone, path exists: {0}'.format(d)
            continue
        gitClone(d, ssh_url)
        os.chown(d, 48, 48)
