#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>
#

'''
Creates token in Gogs through the API
'''

import sys
import gogs
import config

api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password, config.admin_token)

def create(username, token_name):
    user = gogs.GogsUser(username, config.new_user_password)
    token = gogs.GogsToken(user, token_name)
    return api.createToken(token)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: create_token.py <username> <token name>"
        exit(1)

    username = sys.argv[1]
    token_name = sys.argv[2]
    result = create(username, token_name)
    if result == api.STATUS_TOKEN_CREATED:
        print "Token {0} created successfully for {1}.".format(token_name, username)
        exit(0)
    elif result == api.STATUS_TOKEN_EXISTS:
        print "Token {0} already exists for user {1}.".format(token_name, username)
        exit(1)
    else:
        print "Error: unable to create token {0} for {1}.".format(token_name, username)
        exit(1)
