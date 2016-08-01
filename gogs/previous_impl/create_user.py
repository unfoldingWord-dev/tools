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
Creates users in Gogs through the API
'''

import sys
import gogs
import config

api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password, config.admin_token)

def create(username, passowrd=None, full_name=None):
    user = gogs.GogsUser(username, password, full_name)
    return api.createUser(user)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: create_user.py <username> [password]"
        exit(1)
        
    username = sys.argv[1]
    password = config.new_user_password
    if len(sys.argv) > 2:
        password = sys.argv[2]
    if len(sys.argv) > 3:
        full_name = ' '.join(sys.argv[3:])
    else:
        full_name = username
    result = create(username, password, full_name)
    if result == api.STATUS_USER_CREATED:
        print "User {0} created successfully.".format(username)
        exit(0)
    elif result == api.STATUS_USER_EXISTS:
        print "User {0} already exists.".format(username)
        exit(0)
    else:
        print "Error: unable to create user {0}.".format(username)
        exit(1)
