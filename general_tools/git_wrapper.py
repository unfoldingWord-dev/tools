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

def gitCommit(d, msg, files='*'):
    '''
    Adds all files in d and commits with message m.
    '''
    os.chdir(d)
    out, ret = runCommand('git add {0}'.format(files))
    out1, ret1= runCommand('''git commit -am "{0}" '''.format(msg))
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
        print 'Failed to push repo to origin master in: {0}'.format(d)

def gitPull(d):
    '''
    Pulls from origin master to local repository.
    '''
    os.chdir(d)
    out, ret = runCommand('git pull --no-edit origin master')
    if ret > 0:
        print out
        print 'Failed to pull from origin master in: {0}'.format(d)

def gitClone(d, remote):
    '''
    Clones a repo from remote into d.  Directory d should not exist or be
    empty.
    '''
    out, ret = runCommand('git clone {0} {1}'.format(remote, d))
    if ret > 0:
        print out
        print 'Failed to clone from {0} to {1}'.format(remote, d)

def createHallHook(repo, roomid):
    '''
    Creates a hall hook for the given repository to the given room.
    '''
    config = { u'room_token': unicode(roomid) }
    hook = repo.create_hook(u'hall', config)

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
