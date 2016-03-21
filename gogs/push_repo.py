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
import codecs
import re
import inspect

# Let's include ../general_tools as a place we can import python files from
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../general_tools")))
if cmd_subfolder not in sys.path:
	sys.path.insert(0, cmd_subfolder)
import get_bible_book

def push(repo_path, username = None):
	api = gogs.GogsAPI(config.api_base_url, config.admin_username, config.admin_password)
	parts = repo_path.split('/')
	repo_name = parts.pop()
	project = re.sub(u'^.*/uw-([^-]+)-.*$', u'\\1', repo_path)
	language = re.sub(u'^.*/uw-[^-]+-(.*)$', u'\\1', repo_path)
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

			# Go through all files to update USFM in #.txt files
			for path, subdirs, files in os.walk('.'):
				if path.startswith('./.git'):
					continue
					
				for name in files:
					file_path = os.path.join(path, name)
					chunk = re.search(u'^(\d*).txt$', name)
					if not chunk or os.stat(file_path).st_size == 0:
						continue
					content = codecs.open(file_path, 'r', 'utf-8').read()
					if not content:
						continue
 					if project.upper() in get_bible_book.books:
						content = re.sub(u'/v(\d+)', ur'\\v \1', content) # change /v1 to \v 1
						content = re.sub(u'<verse number="(\d+)" style="v"\s*/>\s*', ur'\\v \1 ', content) # change <verse number="1" style="v" /> to \v 1
 						content = re.sub(u'^\\\\v (\d+)( \\\\v \d+)* \\\\v (\d+)', ur'\\v \1-\3', content) # change \v 1 \v 2 \v 3 to \v 1-3
 						content = re.sub(u'([^\s])\s*\\\\v\s*(\d+)\s*', ur'\1\n\\v \2 ', content) # put a new line before a \v if it isn't at the beginning of the line
 						if not '\p' in content:
							content = u"\n\p\n"+content # Prepend a \p line if there isn't a \p in the chunk
						if name == '01.txt' and not '\c ' in content:
							chapter = re.sub(u'^\.\/0*', u'', path) # gets the chapter # from the path without 0s
							content = u"\c {0}\n{1}".format(chapter, content) # Prepends a \c # to the chunk
					file = codecs.open(file_path, 'w', 'utf-8')
					file.write(content)
					file.close()
			cleanup_usfm_command = '''
				unset GIT_DIR;
				unset GIT_WORK_TREE;
				git commit -a -m "Cleanup of USFM";
			'''
			os.system(cleanup_usfm_command)

			scrub_file_command = '''
				unset GIT_DIR;
				unset GIT_WORK_TREE;
				git filter-branch --force --index-filter "git rm --cached --ignore-unmatch {0}" --prune-empty --tag-name-filter cat -- --all;
				rm -rf .git/refs/original/;
				git reflog expire --all;
				git gc --aggressive --prune;
			'''

			add_json_command = '''
				unset GIT_DIR;
				unset GIT_WORK_TREE;
				git add .;
				git commit -a -m "Adding new {0}";
			'''

			#Removes email and phone from 'translators' in manifest.json if package_version < 5:
			filename = 'manifest.json'
			if os.path.exists(filename) and os.stat(filename).st_size > 0:
				with open(filename) as data:
					data = json.load(data)

				if not 'package_version' in data or data['package_version'] < 5:
					os.system(scrub_file_command.format(filename))
					if 'translators' in data:
						for translator in data['translators']:
							if isinstance(translator,dict):
								if 'email' in translator:
									del translator['email']
								if 'phone' in translator:
									del translator['phone']
					json_text = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
					with open(filename, 'w') as file:
						print >> file, json_text
					file.close()
					os.system(add_json_command.format(filename))

			#Removes email and phone from 'translators' in project.json if package_version < 5:
			filename = 'project.json'
			if os.path.exists(filename) and os.stat(filename).st_size > 0:
				with open(filename) as data:
					data = json.load(data)
				if not 'package_version' in data or data['package_version'] < 5:
					os.system(scrub_file_command.format(filename))
					if 'translators' in data:
						for translator in data['translators']:
							if 'email' in translator:
								del translator['email']
							if 'phone' in translator:
								del translator['phone']
					json_text = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
					with open(filename, 'w') as file:
						print >> file, json_text
					file.close()
					os.system(add_json_command.format(filename))

			# Need to see if the api_port is not standard 80, if isn't we need to add :<port> to the remote URL, but empty if is 80
			api_port = ''
			if hasattr(config, 'api_port') and config.api_port and config.api_port != '80':
				api_port = ':{0}'.format(config.api_port)

			command = '''
				unset GIT_DIR;
				unset GIT_WORK_TREE;
				git remote add {2} {4}://{0}:{1}@{2}{5}/{0}/{3};
				git push --force --all -u {2};
				git push --force --tags -u {2};
			'''.format(username, urllib2.quote(user.password), config.api_domain, repo_name, config.api_protocol, api_port)
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

