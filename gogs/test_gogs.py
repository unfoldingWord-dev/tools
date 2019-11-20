#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2017 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#
import time
from gogs_client import GogsApi, UsernamePassword, Token

api = GogsApi('http://test.door43.org:3000')
admin_token = 'ff5729520a4a0c6a892419d2bafffd3f54e252ec'
username = 'user{0}'.format(int(time.time()))

admin_auth = Token(admin_token)
user_auth = UsernamePassword(username, username)

user = api.create_user(admin_auth, username, username, '{0}@door43.org'.format(username), username)
repo = api.create_repo(user_auth, 'testrepo')
repo2 = api.get_repo(user_auth,'testrepo')
repos = api.get_user_repos(user_auth)
deleted = api.delete_repo(user_auth, 'testrepo')

print(user)
print(repo)
print(repo2)
