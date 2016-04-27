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
Deletes a user in Gogs through the API
'''

import sys
import gogs
import config

api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password, config.admin_token)

def delete(username):
    user = gogs.GogsUser(username, config.new_user_password)
    api.populateUser(user)
    if user.id:
        if len(user.repos) > 0:
            for repo in user.repos:
                api.deleteRepo(repo)
        return api.deleteUser(user, True)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: delete_user.py <username>"
        exit(1)

    username = sys.argv[1]
    result = delete(username)
    if result == api.STATUS_USER_DELETED:
        print "User {0} deleted successfully.".format(username)
        exit(0)
    elif result == api.STATUS_USER_STILL_HAS_REPOS:
        print "Error: User {0} still has repositories. They need to be deleted first.".format(username)
        exit(1)
    elif result == api.STATUS_USER_DOES_NOT_EXIST:
        print "Error: User {0} doesn't exist.".format(username)
        exit(1)
    else:
        print "Error: Unable to delete {0}.".format(username)
        exit(1)
