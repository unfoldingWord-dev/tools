#!/usr/bin/env python
# -*- coding: utf8 -*-
#  Copyright (c) 2013 Jesse Griffin
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#
#  Requires PyGithub for unfoldingWord export.

import os
import sys
import json
import codecs
import shlex
import datetime
from subprocess import *


root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
exportdir = os.path.join(root, 'media/exports')
unfoldingWorddir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
digits = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
rtl = ['he', 'ar']
langnames = os.path.join('/var/www/vhosts/door43.org',
                        'httpdocs/lib/plugins/translation/lang/langnames.txt')


def getChapter(chapterpath, jsonchapter):
    i = 0
    chapter = codecs.open(chapterpath, 'r', encoding='utf-8').readlines()
    for line in chapter:
        i += 1
        if line.startswith((u'\n', u'\ufeff')) or line == u'':
            continue
        if u'======' in line:
            jsonchapter['title'] = line.replace(u'======', u'').strip()
            continue
        elif line.startswith(u'//'):
            jsonchapter['ref'] = line.replace(u'//', u'').strip()
            continue
        elif line.startswith('{{'):
            if 'Program Files' in line:
                continue
            frame = { 'id': line.split('.jpg')[0].split('obs-')[1],
                      'img': line.strip()
                    }
        else:
            if 'No translation' in line:
                frame = { 'id': None,
                          'img': None,
                          'text': 'No translation'
                        }
                jsonchapter['frames'].append(frame)
                break
            try:
                frame['text'] = line.strip()
                jsonchapter['frames'].append(frame)
            except UnboundLocalError, e:
                error = 'Problem parsing line {0} in {1}: {2}'.format(i,
                                                               chapterpath, e)
                print error
                frame = { 'id': None,
                          'img': None,
                          'text': 'Invalid format.'
                        }
                jsonchapter['frames'].append(frame)
                break
    jsonchapter['frames'].sort(key=lambda frame: frame['id'])
    return jsonchapter

def writePage(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile.replace('.txt', '.json'), 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getDump(j):
    return json.dumps(j, sort_keys=True, indent=2)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def loadLangStrings(path):
    langdict = {}
    if not os.path.isfile(path):
        return langdict
    for line in codecs.open(path, 'r', encoding='utf-8').readlines():
        if ( line.startswith(u'#') or line.startswith(u'\n')
                                                  or line.startswith(u'\r') ):
            continue
        code,string = line.split(None, 1)
        langdict[code.strip()] = string.strip()
    return langdict

def getStatus(statfile):
    status = {}
    if os.path.isfile(statfile):
        for line in open(statfile):
            if ( line.startswith('#') or line.startswith('\n')
                                                         or ':' not in line ):
                continue
            k, v = line.split(':')
            status[k.strip().lower()] = v.strip().lower()
    return status

def exportunfoldingWord(status, gitdir, json, lang, githuborg):
    '''
    Exports JSON data for each language into its own Github repo.
    '''
    if status.has_key('checking level') and status.has_key('publish date'):
        if ( status['checking level'] in ['1', '2', '3'] and 
                       status['publish date'] == str(datetime.date.today()) ):
            print "Exporting to unfoldingWord: {0}".format(lang)
            makeDir(gitdir)
            writePage(os.path.join(gitdir, 'obs-{0}.json'.format(lang)), json)
            statjson = getDump(status)
            writePage(os.path.join(gitdir, 'status-{0}.json'.format(lang)),
                                                                     statjson)
            gitCreate(gitdir)
            githubCreate(gitdir, lang, githuborg)
            gitCommit(gitdir, statjson)
            gitPush(gitdir)

def gitCreate(d):
    '''
    Creates local GIT repo and pushes to Github.
    '''
    if os.path.exists(os.path.join(d, '.git')):
        return
    os.chdir(d)
    out, ret = runCommand('git init .')
    if ret > 0:
        print 'Failed to create a GIT repo in: {0}'.format(d)
        sys.exit(1)

def githubCreate(d, lang, org):
    '''
    Creates a Github repo for lang unless it already exists.
    '''
    rname = 'obs-{0}'.format(lang)
    try:
        repo = org.get_repo(rname)
        return
    except GithubException:
        try:
            repo = org.create_repo(rname,
                            'Open Bible Stories for {0}'.format(lang),
                            'http://unfoldingword.org/{0}/'.format(lang),
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
    Pushes local repository to github.
    '''
    os.chdir(d)
    out, ret = runCommand('git push origin master')
    if ret > 0:
        print out
        print 'Failed to push repo to Github in: {0}'.format(d)

def runCommand(c):
    command = shlex.split(c)
    com = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate()).strip()
    return comout, com.returncode

def getGithubOrg(orgname):
    user = raw_input('Github username: ').strip()
    pw = raw_input('Github password: ').strip()
    g = Github(user, pw)
    return g.get_organization(orgname)


if __name__ == '__main__':
    unfoldingwordexport = False
    if len(sys.argv) > 1:
        if sys.argv[1] == '--unfoldingwordexport':
            try:
                from github import Github
                from github import GithubException
            except:
                print "Please install PyGithub with pip"
                sys.exit(1)
            unfoldingwordexport = True
            try:
                githuborg = getGithubOrg('unfoldingword')
            except:
                print 'Could not login to Github'
                sys.exit(1)
        else:
            print 'Unknown argument: {0}'.format(sys.argv[1])
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    langdict = loadLangStrings(langnames)
    catpath = os.path.join(exportdir, 'obs-catalog.json')
    catalog = loadJSON(catpath, 'l')
    for lang in os.listdir(pages):
        if ( os.path.isfile(os.path.join(pages, lang)) or
             'obs' not in os.listdir(os.path.join(pages, lang)) ):
            continue
        jsonlang = { 'language': lang,
                     'chapters': [],
                     'date_modified': today,
                   }
        for page in os.listdir(os.path.join(pages, lang, 'obs')):
            if not page.startswith(digits): continue
            jsonchapter = { 'number': page.split('-')[0],
                            'frames': [],
                          }
            chapterpath = os.path.join(pages, lang, 'obs', page)
            jsonlang['chapters'].append(getChapter(chapterpath, jsonchapter))
        jsonlang['chapters'].sort(key=lambda frame: frame['number'])
        jsonlangfilepath = os.path.join(exportdir, lang, 'obs',
                                            'obs-{0}.json'.format(lang))
        prevjsonlang = loadJSON(jsonlangfilepath, 'd')
        curjson = getDump(jsonlang)
        prevjson = getDump(prevjsonlang)
        try:
            langstr = langdict[lang]
        except KeyError:
            print "Configuration for language {0} missing in {1}.".format(lang,
                                                                     langnames)
            continue
        if not lang in [x['language'] for x in catalog]:
            langcat =  { 'language': lang,
                         'string': langstr,
                         'date_modified': today
                       }
            catalog.append(langcat)
        # Maybe fix this to do a full string comparison
        if len(str(curjson)) != len(str(prevjson)):
            ( [x for x in catalog if x['language'] ==
                                            lang][0]['date_modified']) = today
            writePage(jsonlangfilepath, curjson)
        if unfoldingwordexport:
            status = getStatus(os.path.join(pages, lang, 'obs/status.txt'))
            unfoldingWordlangdir = os.path.join(unfoldingWorddir, lang)
            exportunfoldingWord(status, unfoldingWordlangdir, curjson,
                                                              lang, githuborg)
    catjson = getDump(catalog)
    writePage(catpath, catjson)
