#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

"""
This class parses information in the UW catalog.
"""

import os
import re
import sys
import json
import codecs
import urllib2
import base64
import config

from urllib2 import Request, urlopen, URLError, HTTPError

class GogsToken:
    def __init__(self, owner, name, sha1 = None):
        self.name = name
        self.sha1 = sha1
        self.owner = owner

class GogsUser:
    def __init__(self, username, password = None):
        self.id = None
        self.username = username
        if password:
            self.password = password
        else:
            self.password = config.new_user_password
        self.token = None
        self.full_name = None
        self.email = None
        self.avatar_url = None
        self.tokens = []
        self.repos = []

class GogsRepo:
    def __init__(self, name, owner):
        self.id = None
        self.name = name
        self.owner = owner
        self.description = None
        self.full_name = None
        self.private = False
        self.fork = False
        self.html_url = None
        self.clone_url = None
        self.ssh_url = None
        self.permissions = {
            "admin": True,
            "push": True,
            "pull": True
        }
        self.auto_init = False
        self.gitignores = None
        self.license = 'Creative Commons CC0 1.0 Universal'
        self.readme = 'Default'

class GogsAPI:
    STATUS_USER_CREATED = 1
    STATUS_USER_EXISTS = 2
    STATUS_ERROR_CREATING_USER = 3
    STATUS_USER_DELETED = 4
    STATUS_USER_DOES_NOT_EXIST = 5
    STATUS_ERROR_DELETING_USER = 6
    STATUS_REPO_CREATED = 7
    STATUS_REPO_EXISTS = 8
    STATUS_ERROR_CREATING_REPO = 9
    STATUS_REPO_DELETED = 10
    STATUS_REPO_DOES_NOT_EXIST = 11
    STATUS_ERROR_DELETING_REPO = 12
    STATUS_USER_STILL_HAS_REPOS = 13
    STATUS_CONNECTION_ERROR = 14
    STATUS_TOKEN_CREATED = 15
    STATUS_TOKEN_EXISTS = 16
    STATUS_ERROR_CREATING_TOKEN = 17
    STATUS_TOKEN_DELETED = 18
    STATUS_TOKEN_DOES_NOT_EXIST = 19
    STATUS_ERROR_DELETING_TOKEN = 20

    catalog = None

    adminUser = None
    api_base_url = None

    def __init__(self, api_base_url, admin_username, admin_password):
        sys.stdout = codecs.getwriter('utf8')(sys.stdout);
        self.api_base_url = api_base_url
        self.adminUser = GogsUser(admin_username, admin_password)

    def connectToGogs(self, partialUrl, authUser=None, data=None, delete=False):
        url = self.api_base_url.format(partialUrl)

        req = urllib2.Request(url)
        if delete:
            req.get_method = lambda: 'DELETE'
        if data:
            req.add_header('Content-Type', 'application/json')
        if authUser:
            base64string = base64.encodestring('%s:%s' % (authUser.username, authUser.password)).replace('\n', '')
            req.add_header("Authorization", "Basic %s" % base64string)
        if data:
            return urllib2.urlopen(req, json.dumps(data))
        else:
            return urllib2.urlopen(req)

    def createUser(self, user, populateIfExists=False):
        data = {
            'username': user.username,
            'password': user.password,
            'email': user.email,
            'full_name': user.full_name,
            'send_notify': False
        }
        if not data['email']:
            data['email'] = '{0}@door43.org'.format(data['username'])
        try:
            response = self.connectToGogs('admin/users', self.adminUser, data)
        except HTTPError as e:
            if e.code == 422: # user already exists
                if populateIfExists:
                    self.populateUser(user)
                return self.STATUS_USER_EXISTS
            else:
                print 'The system rejected this request.'
                print 'Reason: ', e.reason
                return self.STATUS_ERROR_CREATING_USER
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return self.STATUS_ERROR_CREATING_USER
        else:
            self.populateUser(user, json.load(response))
            return self.STATUS_USER_CREATED

    def populateUser(self, user, data=None):
        if not data:
            try:
                response = self.connectToGogs('users/{0}'.format(user.username), self.adminUser)
            except HTTPError as e:
                if e.code == 404: # user doesn't exists
                    return self.STATUS_USER_DOES_NOT_EXIST
                else:
                    print 'The system rejected this request.'
                    print 'Reason: ', e.reason
                    return self.STATUS_CONNECTION_ERROR
            except URLError as e:
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
                return self.STATUS_CONNECTION_ERROR
            else:
                data = json.load(response)

        if not data or 'id' not in data:
            return self.STATUS_USER_DOES_NOT_EXIST

        user.id = data['id']
        user.username = data['username']
        user.email = data['email']
        user.full_name = data['full_name']
        user.avatar_url = data['avatar_url']
        self.populateTokens(user)
        self.populateRepos(user)

    def deleteUser(self, user, alsoDeleteRepos=False):
        url = 'admin/users/{0}'.format(user.username)
        try:
            response = self.connectToGogs(url, self.adminUser, None, True)
        except HTTPError as e:
            if e.code == 422: # user still has content, such as repos
                if alsoDeleteRepos:
                    if not user.id:
                        self.populateUser(user)
                    for repo in user.repos:
                        self.deleteRepo(repo)
                    return self.deleteUser(user, False)
                else:
                    return self.STATUS_USER_STILL_HAS_REPOS
            if e.code == 404: # repo doesn't exist
                return self.STATUS_USER_DOES_NOT_EXIST
            else:
                print 'The system rejected this request.'
                print 'Reason: ', e.reason
                print 'Code: ', e.code
                return self.STATUS_ERROR_DELETING_USER
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return self.STATUS_ERROR_DELETING_USER
        else:
            return self.STATUS_USER_DELETED

    def populateTokens(self, user):
        url = 'users/{0}/tokens'.format(user.username)
        response = self.connectToGogs(url, user)
        tokens = json.load(response)
        for token in tokens:
            user.tokens.append(GogsToken(user, token['name'], token['sha1']))

    def populateToken(self, token, data):
        token.name = data['name']
        token.sha1 = data['sha1']

    def createToken(self, token, populateIfExists = False):
        url = 'users/{0}/tokens'.format(token.owner.username)
        data = {
            'name': token.name,
        }
        try:
            response = self.connectToGogs(url, token.owner, data)
        except HTTPError as e:
            if e.code == 422: # token already exists
                if populateIfExists:
                    self.populateToken(token)
                return self.STATUS_TOKEN_EXISTS
            else:
                print 'The system rejected this request.'
                print e.reason
                return self.STATUS_ERROR_CREATING_TOKEN
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return self.STATUS_ERROR_CREATING_TOKEN
        else:
            self.populateToken(token, json.load(response))
            return self.STATUS_TOKEN_CREATED

    def createRepo(self, repo, populateIfExists=False):
        data = {
            'name': repo.name,
            'description': repo.description,
            'private': repo.private,
            'auto_init': repo.auto_init,
            'gitignores': repo.gitignores,
            'license': repo.license,
            'readme': repo.readme
        }

        try:
            response = self.connectToGogs('user/repos', repo.owner, data)
        except HTTPError as e:
            if e.code == 422: # repo already exists
                if populateIfExists:
                    self.populateRepo(repo)
                return self.STATUS_REPO_EXISTS
            else:
                print 'The system rejected this request.'
                print e.reason
                return self.STATUS_ERROR_CREATING_REPO
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return self.STATUS_ERROR_CREATING_REPO
        else:
            self.populateRepo(repo, json.load(response))
            return self.STATUS_REPO_CREATED

    def populateRepo(self, repo, data=None):
        if not data:
            try:
                response = self.connectToGogs('repos/{0}/{1}'.format(repo.owner.username, repo.name), repo.owner)
            except HTTPError as e:
                if e.code == 404: # repo doesn't exists
                    return self.STATUS_REPO_DOES_NOT_EXIST
                else:
                    print 'The system rejected this request.'
                    print 'Reason: ', e.reason
                    return self.STATUS_CONNECTION_ERROR
            except URLError as e:
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
                return self.STATUS_CONNECTION_ERROR
            else:
                data = json.load(response)

        if not data or 'full_name' not in data:
            return self.STATUS_USER_DOES_NOT_EXIST

        repo.id = data['id']
        repo.full_name = data['full_name']
        repo.private = data['private']
        repo.fork = data['fork']
        repo.html_url = data['html_url']
        repo.clone_url = data['clone_url']
        repo.ssh_url = data['ssh_url']
        repo.permissions = data['permissions']

    def populateRepos(self, user):
        url = 'user/repos'
        response = self.connectToGogs(url, user)
        repos = json.load(response)
        for repo_data in repos:
            repo_name = repo_data['full_name'].split('/').pop()
            repo = GogsRepo(repo_name, user)
            self.populateRepo(repo, repo_data)
            user.repos.append(repo)

    def deleteRepo(self, repo):
        url = 'repos/{0}/{1}'.format(repo.owner.username, repo.name)
        try:
            response = self.connectToGogs(url, repo.owner, None, True)
        except HTTPError as e:
            if e.code == 404: # repo doesn't exist
                return self.STATUS_REPO_DOES_NOT_EXIST
            else:
                print 'The system rejected this request.'
                print 'Reason: ', e.reason
                print 'Code: ', e.code
                return self.STATUS_ERROR_DELETING_REPO
        except URLError as e:
            print 'We failed to reach a server.'
            print 'Reason: ', e.reason
            return self.STATUS_ERROR_DELETING_REPO
        else:
            return self.STATUS_REPO_DELETED

