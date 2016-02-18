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

            os.chdir(repo_path)

            #Removes 'translators' from manifest.json:
            filename = 'manifest.json'
            if os.path.exists(filename) and os.stat(filename).st_size > 0:
                with open(filename) as data:
                    data = json.load(data)
                #Totally remove old file from repo
                os.system('git filter-branch --force --index-filter "git rm --cached --ignore-unmatch {0}" --prune-empty --tag-name-filter cat -- --all'.format(filename))
                if 'translators' in data:
                    for translator in data['translators']:
                        if 'email' in translator:
                            del translator['email']
                        if 'phone' in translator:
                            del translator['phone']
                json_text = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
                with open(filename+'2', 'w') as file:
                    print >> file, json_text
                os.system('git commit -a -m "Updated {0}"'.format(filename+'2'));

            #Removes 'translators' from project.json:
            filename = 'project.json'
            if os.path.exists(filename) and os.stat(filename).st_size > 0:
                with open(filename) as data:
                    data = json.load(data)
                #Totally remove old file from repo
                os.system('git filter-branch --force --index-filter "git rm --cached --ignore-unmatch {0}" --prune-empty --tag-name-filter cat -- --all'.format(filename))
                if 'translators' in data:
                    for translator in data['translators']:
                        if 'email' in translator:
                            del translator['email']
                        if 'phone' in translator:
                            del translator['phone']
                json_text = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
                with open(filename, 'w') as file:
                    print >> file, json_text
                os.system('git commit -a -m "Updated {0}"'.format(filename));

            command = '''
                unset GIT_DIR
                unset GIT_WORK_TREE
                git remote add {2} {4}://{0}:{1}@{2}/{0}/{3} &&
                git push --force --all -u {2} &&
                git push --force --tags -u {2}
            '''.format(username, urllib2.quote(user.password), config.api_domain, repo_name, config.api_protocol)
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

