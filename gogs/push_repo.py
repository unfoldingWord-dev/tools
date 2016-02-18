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
Pushes a given repo to GOGs and creates the user of the repo if user doesn't exit
'''

import sys
import os
import json
import urllib2
import paramiko
import base64
import getpass
import gogs
import config

def push(repo_path, username = None):
    api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password)
    parts = repo_path.split('/')
    repo_name = parts.pop()
    if not username:
        username = parts.pop()
    user = gogs.GogsUser(username, config.new_user_password)
    result = api.createUser(user)
    if result != api.STATUS_ERROR_CREATING_USER:
        print "User result: ",username,' ',result
        repo = gogs.GogsRepo(repo_name, user)
        result = api.createRepo(repo)
        if result != api.STATUS_ERROR_CREATING_REPO:
            print "Repo result: ",repo_name,' ',result
            command = '''
                unset GIT_DIR
                unset GIT_WORK_TREE
                git remote add {2} {4}://{0}:{1}@{2}:3000/{0}/{3} &&
                git filter-branch --force --index-filter "git rm --cached --ignore-unmatch manifest.json project.json" --prune-empty --tag-name-filter cat -- --all &&
                git push --force --all -u {2} &&
                git push --force --tags -u {2} &&
                git checkout -f origin/master
            '''.format(username, urllib2.quote(user.password), config.api_domain, repo_name, config.api_protocol)
            os.chdir(repo_path)
            os.system('pwd')
            os.system(command)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: push_repo.py <absolute_path_to_repo> [username]"
        exit(1)

    repo_path = sys.argv[1]

    username = None
    if len(sys.argv) > 2:
        username = sys.argv[2]

    push(repo_path, username)

