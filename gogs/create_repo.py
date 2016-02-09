#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Creates repo in Gogs through the API
'''

import sys
import gogs
import config

api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password)

def create(username, repo_name):
    user = gogs.GogsUser(username, config.new_user_password)
    repo = gogs.GogsRepo(repo_name, user)
    return api.createRepo(repo)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: create_repo.py <username> <repo name>"
        exit(1)

    username = sys.argv[1]
    repo_name = sys.argv[2]
    result = create(username, repo_name)
    if result == api.STATUS_REPO_CREATED:
        print "Repo {0} created successfully for {1}.".format(repo_name, username)
        exit(0)
    elif result == api.STATUS_REPO_EXISTS:
        print "Repo {0} already exists for user {1}.".format(repo_name, username)
        exit(1)
    else:
        print "Error: unable to create repo {0} for {1}.".format(repo_name, username)
        exit(1)
