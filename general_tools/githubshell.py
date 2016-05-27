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
This provides easy access to the PyGithub API for testing and development.
'''

import sys
from general_tools.git_wrapper import *

sys.path.append('/var/www/vhosts/door43.org/tools/general_tools')
try:
    from github import Github
    from github import GithubException
except:
    print "Please install PyGithub with pip"
    sys.exit(1)


if __name__ == '__main__':
    # Log in to Github via API
    try:
        pw = open('/root/.github_pass', 'r').read().strip()
        guser = githubLogin('dsm-git', pw)
        githuborg = getGithubOrg('door43', guser)
    except GithubException as e:
        print 'Problem logging into Github: {0}'.format(e)
        sys.exit(1)
