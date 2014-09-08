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
#  Requires PyGithub for Github commands.

import os
import sys
import json
import shlex
from subprocess import *


def getGithubOrg(orgname, user):
    try:
        from github import Github
    except:
        print "Please install PyGithub with pip"
        sys.exit(1)
    return user.get_organization(orgname)

def githubLogin(user, pw):
    try:
        from github import Github
    except:
        print "Please install PyGithub with pip"
        sys.exit(1)
    return Github(user, pw)

def githubCreate(d, rname, rdesc, rurl, org):
    '''
    Creates a Github repo, unless it already exists.
    Accepts a local path, repo name, description, org name.
    '''
    try:
        from github import Github
        from github import GithubException
    except:
        print "Please install PyGithub with pip"
        sys.exit(1)
    try:
        repo = org.get_repo(rname)
        return
    except GithubException:
        try:
            repo = org.create_repo(rname, rdesc, rurl,
                                   has_issues=False,
                                   has_wiki=False,
                                   auto_init=False,
                                  )
        except GithubException as ghe:
            print(ghe)
            return
    os.chdir(d)
    out, ret = runCommand('git remote add origin {0}'.format(repo.ssh_url))
    if ret > 0:
        print 'Failed to add Github remote to repo in: {0}'.format(d)

def gitCreate(d):
    '''
    Creates local git repo, unless it already exists.
    Accepts a local path as the git repo.
    '''
    if os.path.exists(os.path.join(d, '.git')):
        return
    os.chdir(d)
    out, ret = runCommand('git init .')
    if ret > 0:
        print 'Failed to create a git repo in: {0}'.format(d)
        sys.exit(1)

def gitCommit(d, msg):
    '''
    Adds all files in d and commits with message m.
    '''
    os.chdir(d)
    out, ret = runCommand('git add *')
    out1, ret1= runCommand('''git commit -am '{0}' '''.format(msg))
    if ret > 0 or ret1 > 0:
        print 'Nothing to commit, or failed commit to repo in: {0}'.format(d)
        print out1

def gitPush(d):
    '''
    Pushes local repository to origin master.
    '''
    os.chdir(d)
    out, ret = runCommand('git push origin master')
    if ret > 0:
        print out
        print 'Failed to push repo to Github in: {0}'.format(d)

def runCommand(c):
    '''
    Runs a command in a shell.  Returns output and return code of command.
    '''
    command = shlex.split(c)
    com = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate()).strip()
    return comout, com.returncode

if __name__ == '__main__':
    pass
