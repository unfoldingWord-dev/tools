#!/usr/bin/env python3
#
# submit_one_Door43_test.py
#       Written: Jan 2019
#       Last modified: 2019-12-09 RJH
#

# Python imports
import os
import sys
import json
import logging
import subprocess


# ======================================================================

# User settings
USE_LOCALCOMPOSE_URL = True
LOAD_FROM_DISK_FILE = False
OVERWRITE = False

REVIEW_FLAG = True # Shows all the URLs again at the end
AUTO_OPEN_IN_BROWSER = True

# Choose one of the following
# TEST_PREFIXES = ('',)
TEST_PREFIXES = ('dev-',)
# TEST_PREFIXES = ('', 'dev-',)

TEST_FILENAME = 'ru_gl--ru_tn_1lv' # .json will be appended to this

LOCAL_FILEPATH = '/mnt/SSD/uW/Software/'

# ======================================================================


if USE_LOCALCOMPOSE_URL: assert TEST_PREFIXES == ('dev-',)

LOCAL_COMPOSE_URL = 'http://127.0.0.1:8080/'


TEST_FOLDER = f'{LOCAL_FILEPATH}/testPayloads/JSON/Door43/'
TEST_FILENAME = TEST_FILENAME.replace('/','--')
filepath = os.path.join(TEST_FOLDER, TEST_FILENAME+'.json')
test_json = None
if LOAD_FROM_DISK_FILE:
    if os.path.isfile(filepath):
        print(f"Loading '{filepath}'…")
        with open(filepath, 'rt') as jf:
            test_json = jf.read()
    else:
      logging.critical(f"LOAD_FROM_DISK_FILE was specified but '{filepath}' doesn't exist")
if not test_json:
    print("Using locally pasted JSON string…")
    test_json = """
{'secret': '', 'ref': 'refs/heads/master', 'before': '6d7f2812885cb872d649c191084433dfd5bee4b6', 'after': '210b544c3e051f83af3bbebdb0f0bf5a0976f26b', 'compare_url': 'https://git.door43.org/ru_gl/ru_tn_1lv/compare/6d7f2812885cb872d649c191084433dfd5bee4b6...210b544c3e051f83af3bbebdb0f0bf5a0976f26b', 'commits': [{'id': '210b544c3e051f83af3bbebdb0f0bf5a0976f26b', 'message': "Изменить 'jer/05/28.md'\n", 'url': 'https://git.door43.org/ru_gl/ru_tn_1lv/commit/210b544c3e051f83af3bbebdb0f0bf5a0976f26b', 'author': {'name': 'Parviz', 'email': 'parviz@noreply.door43.org', 'username': 'Parviz'}, 'committer': {'name': 'Parviz', 'email': 'parviz@noreply.door43.org', 'username': 'Parviz'}, 'verification': None, 'timestamp': '2019-11-19T08:34:31Z', 'added': None, 'removed': None, 'modified': None}], 'head_commit': None, 'repository': {'id': 25031, 'owner': {'id': 7140, 'login': 'ru_gl', 'full_name': '', 'email': '', 'avatar_url': 'https://git.door43.org/avatars/7140', 'language': '', 'is_admin': False, 'last_login': '1970-01-01T00:00:00Z', 'created': '2018-02-08T08:16:16Z', 'username': 'ru_gl'}, 'name': 'ru_tn_1lv', 'full_name': 'ru_gl/ru_tn_1lv', 'description': 'Source for Russian translationNotes', 'empty': False, 'private': False, 'fork': True, 'parent': {'id': 24194, 'owner': {'id': 6, 'login': 'WycliffeAssociates', 'full_name': 'WycliffeAssociates', 'email': 'wycliffeassociates@noreply.door43.org', 'avatar_url': 'https://git.door43.org/avatars/bf3cc4e96ae6c7a77e8e90a8dce075b2', 'language': 'en-US', 'is_admin': False, 'last_login': '2019-08-22T14:19:22Z', 'created': '2016-02-04T12:55:33Z', 'username': 'WycliffeAssociates'}, 'name': 'en_tn', 'full_name': 'WycliffeAssociates/en_tn', 'description': 'Source for English translationNotes', 'empty': False, 'private': False, 'fork': True, 'parent': None, 'mirror': False, 'size': 98139, 'html_url': 'https://git.door43.org/WycliffeAssociates/en_tn', 'ssh_url': 'git@git.door43.org:WycliffeAssociates/en_tn.git', 'clone_url': 'https://git.door43.org/WycliffeAssociates/en_tn.git', 'website': '', 'stars_count': 2, 'forks_count': 3, 'watchers_count': 8, 'open_issues_count': 11, 'default_branch': 'master', 'archived': False, 'created_at': '2018-04-11T20:08:08Z', 'updated_at': '2019-10-01T21:30:17Z', 'permissions': {'admin': False, 'push': False, 'pull': False}, 'has_issues': True, 'has_wiki': True, 'has_pull_requests': False, 'ignore_whitespace_conflicts': False, 'allow_merge_commits': False, 'allow_rebase': False, 'allow_rebase_explicit': False, 'allow_squash_merge': False, 'avatar_url': ''}, 'mirror': False, 'size': 105256, 'html_url': 'https://git.door43.org/ru_gl/ru_tn_1lv', 'ssh_url': 'git@git.door43.org:ru_gl/ru_tn_1lv.git', 'clone_url': 'https://git.door43.org/ru_gl/ru_tn_1lv.git', 'website': '', 'stars_count': 0, 'forks_count': 0, 'watchers_count': 5, 'open_issues_count': 0, 'default_branch': 'master', 'archived': False, 'created_at': '2018-05-28T09:49:08Z', 'updated_at': '2019-11-19T08:34:32Z', 'permissions': {'admin': False, 'push': False, 'pull': False}, 'has_issues': True, 'has_wiki': True, 'has_pull_requests': True, 'ignore_whitespace_conflicts': False, 'allow_merge_commits': False, 'allow_rebase': False, 'allow_rebase_explicit': True, 'allow_squash_merge': False, 'avatar_url': ''}, 'pusher': {'id': 8019, 'login': 'Parviz', 'full_name': '', 'email': 'parviz@noreply.door43.org', 'avatar_url': 'https://secure.gravatar.com/avatar/9279dbd416821bde3f2b7eb884d33a3a?d=identicon', 'language': 'ru-RU', 'is_admin': False, 'last_login': '2019-11-19T07:16:11Z', 'created': '2018-05-15T20:44:35Z', 'username': 'Parviz'}, 'sender': {'id': 8019, 'login': 'Parviz', 'full_name': '', 'email': 'parviz@noreply.door43.org', 'avatar_url': 'https://secure.gravatar.com/avatar/9279dbd416821bde3f2b7eb884d33a3a?d=identicon', 'language': 'ru-RU', 'is_admin': False, 'last_login': '2019-11-19T07:16:11Z', 'created': '2018-05-15T20:44:35Z', 'username': 'Parviz'}, 'DCS_event': 'push', 'door43_webhook_retry_count': 0, 'door43_webhook_received_at': '2019-11-19T08:34:32Z'}""" \
  .replace('\\n','').replace('\n','') \
  .replace("{'", '{"').replace("': ", '": ').replace(": '", ': "').replace("', ", '", ').replace(", '", ', "').replace("'}", '"}') \
  .replace(': True,', ': true,').replace(': False,', ': false,').replace(': None,', ': null,') \
  .replace(': True}', ': true}').replace(': False}', ': false}').replace(': None}', ': null}')
# print('test_json = ', test_json)
if OVERWRITE or not LOAD_FROM_DISK_FILE: # Write the json file
    print(f"Writing '{filepath}'…")
    with open(filepath, 'wt') as jf:
        jf.write(test_json)
else:
    print("(Not saving JSON file)")
if not os.path.isfile(filepath):
    logging.critical(f"Unable to proceed coz '{filepath}' doesn't exist")
    sys.exit()


webURL = ''
for prefix in TEST_PREFIXES:
    webhook = LOCAL_COMPOSE_URL if USE_LOCALCOMPOSE_URL else f'https://{prefix}api.door43.org/client/webhook/'
    print( f"\n{'(dev) ' if prefix else ''}'{TEST_FILENAME}' to {webhook}:" )
    jsonFilename = f'{TEST_FOLDER}{TEST_FILENAME}.json'

    with open(jsonFilename, 'rt') as jsonFile:
      jsonString = jsonFile.read()
    jsonDict = json.loads(jsonString)
    if 'pusher' in jsonDict:
        event = 'push'
    elif 'release' in jsonDict:
        event = 'release'
    elif 'pull_request' in jsonDict:
        event = 'pull_request'
    elif 'ref_type' in jsonDict and jsonDict['ref_type']=='branch' and 'pusher_type' in jsonDict:
        event = 'delete'
    # elif 'ref_type' in jsonDict and jsonDict['ref_type']=='branch' and 'ref' in jsonDict:
    #     event = 'create'
    else:
        logging.critical(f"Can't determine event (push/release/delete, etc.) from JSON")
        halt


    # Use curl to actually POST the JSON to the given webhook URL
    parameters = ['curl', webhook,
                    '--data', f'@{jsonFilename}',
                    '--header', "Content-Type: application/json",
                    '--header', f"X-Gitea-Event: {event}",
                ]
    myProcess = subprocess.Popen( parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    programOutputBytes, programErrorOutputBytes = myProcess.communicate()

    # Process the output from curl
    if programOutputBytes:
        programOutputString = programOutputBytes.decode(encoding='utf-8', errors='replace')
        #programOutputString = programOutputString.replace( baseFolder + ('' if baseFolder[-1]=='/' else '/'), '' ) # Remove long file paths to make it easier for the user to read
        #with open( os.path.join( outputFolder, 'ScriptOutput.txt" ), 'wt', encoding='utf-8' ) as myFile: myFile.write( programOutputString )
        #print( f"Response = {programOutputString!r}" )
        if programOutputString.startswith('{'): # Assume it's a json dict
            responseDict = json.loads(programOutputString)
            if responseDict['status'] == 'queued':
                print( "      Job successfully queued" )
            else:
                print( f"Response dict = {responseDict}" )
        else:
            print( f"Response = {programOutputString!r}" )
    if programErrorOutputBytes:
        programErrorOutputString = programErrorOutputBytes.decode(encoding='utf-8', errors='replace')
        #with open( os.path.join( outputFolder, 'ScriptErrorOutput.txt" ), 'wt', encoding='utf-8' ) as myFile: myFile.write( programErrorOutputString )
        if not programErrorOutputString.startswith('  % Total'):
            print( f"pEOS = {programErrorOutputString!r}" )

    if webURL:
      url = f"https://{'dev.' if prefix else ''}door43.org/u/{webURL}/"
      print(f"View result at {url}")
      if AUTO_OPEN_IN_BROWSER:
          import webbrowser
          webbrowser.open(url, new=0, autoraise=True)
          #subprocess.Popen(['xdg-open', url])
