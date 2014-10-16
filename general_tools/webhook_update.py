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

lang_url = 'https://api.unfoldingword.org/obs/txt/1/langnames.json'
host_regions = { 'us.door43.org': ['Americas', 'Europe', 'Africa', 'Asia'],
                 'jp.door43.org': ['Pacific'],
               }


def getLangs(url):
    try:
        request = urllib2.urlopen(url).read()
    except:
        request = '{}'
    return json.loads(request)



if __name__ == '__main__':
    # Log in to Github via API
    try:
        pw = open('/root/.github_pass', 'r').read().strip()
        guser = githubLogin('dsm-git', pw)
        githuborg = getGithubOrg('door43', guser)
    except GithubException as e:
        print 'Problem logging into Github: {0}'.format(e)
        sys.exit(1)

    lang_info = getLangs(lang_url)

    hostname = os.environ.get('HOSTNAME')
    if hostname not in host_regions:
        print 'Hostname not configured for a region'
        sys.exit(1)
    regions = host_regions[hostname]

    # Cycle through available repos and set hooks

    repo_name = 'd43-en'
    repo = githuborg.get_repo(repo_name)
    for hook in repo.get_hooks():
        #Check to see if hooks are correct
        pass

    hook_name = 'jp-updates'
    hook_config = { u'url': u'http://jp.door43.org:9094',
                    u'insecure_ssl': u'0', u'secret': u'',
                    u'content_type': u'json'
                  }

    repo.create_hook(hook_name, hook_config)

