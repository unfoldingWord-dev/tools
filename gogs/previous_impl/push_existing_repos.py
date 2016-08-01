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
Goes through all tS users and repos on the gitolite server and creates a user
and mirrors the repo in Gogs
'''

import sys
import os
import json
import urllib2
import paramiko
import base64
import gogs
import config
import push_repo
import delete_user

def main():
    api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password)
    key = paramiko.RSAKey.from_private_key_file(config.pkey_file)
    client = paramiko.SSHClient()
    client.get_host_keys().add('git.door43.org', 'ssh-rsa', key)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print "connecting"
    client.connect( hostname = "us.door43.org", username = "gitolite3", port=9299, pkey = key )
    print "connected"
    stdin, stdout, stderr = client.exec_command('info -json')
    json_data = json.load(stdout)

    sys.setrecursionlimit(2000)
    for repo_path in json_data['repos']:
        parts = repo_path.split('/')
        if len(parts) == 3:
            org = parts[0]
            username = parts[1]
            repo_name = parts[2]

            if org == 'tS' and repo_name.startswith('uw-') and len(username) >= 10:
                os.system('rm -rf /tmp/{0}'.format(repo_path))
                os.system('git clone gitolite3@us.door43.org:{0} /tmp/{0}'.format(repo_path))
                push_repo.push('/tmp/{0}'.format(repo_path), username)

if __name__ == '__main__':
    main()
