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

TEST_FILENAME = 'Door43-Catalog--vi_ulb--fork' # .json will be appended to this

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
{
  "secret": "",
  "forkee": {
    "id": 22755,
    "owner": {
      "id": 4598,
      "login": "Door43-Catalog",
      "full_name": "Door43 Resource Catalog",
      "email": "door43-catalog@noreply.door43.org",
      "avatar_url": "https://git.door43.org/img/avatar_default.png",
      "language": "",
      "is_admin": false,
      "last_login": "1970-01-01T00:00:00Z",
      "created": "2016-10-18T19:03:36Z",
      "username": "Door43-Catalog"
    },
    "name": "vi_ulb",
    "full_name": "Door43-Catalog/vi_ulb",
    "description": "Vietnamese ULB.  STR https://git.door43.org/Door43/SourceTextRequestForm/issues/149\\r\\n\\r\\n",
    "empty": false,
    "private": false,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 5376,
    "html_url": "https://git.door43.org/Door43-Catalog/vi_ulb",
    "ssh_url": "git@git.door43.org:Door43-Catalog/vi_ulb.git",
    "clone_url": "https://git.door43.org/Door43-Catalog/vi_ulb.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 1,
    "watchers_count": 9,
    "open_issues_count": 0,
    "default_branch": "master",
    "archived": false,
    "created_at": "2018-02-12T18:13:00Z",
    "updated_at": "2020-08-24T04:10:55Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    },
    "has_issues": true,
    "has_wiki": false,
    "has_pull_requests": true,
    "ignore_whitespace_conflicts": false,
    "allow_merge_commits": true,
    "allow_rebase": true,
    "allow_rebase_explicit": true,
    "allow_squash_merge": true,
    "avatar_url": ""
  },
  "repository": {
    "id": 58265,
    "owner": {
      "id": 6221,
      "login": "STR",
      "full_name": "",
      "email": "",
      "avatar_url": "https://git.door43.org/avatars/6221",
      "language": "",
      "is_admin": false,
      "last_login": "1970-01-01T00:00:00Z",
      "created": "2017-08-15T15:24:51Z",
      "username": "STR"
    },
    "name": "vi_ulb",
    "full_name": "STR/vi_ulb",
    "description": "Vietnamese ULB.  STR https://git.door43.org/Door43/SourceTextRequestForm/issues/149\\r\\n\\r\\n",
    "empty": false,
    "private": false,
    "fork": true,
    "parent": {
      "id": 22755,
      "owner": {
        "id": 4598,
        "login": "Door43-Catalog",
        "full_name": "Door43 Resource Catalog",
        "email": "door43-catalog@noreply.door43.org",
        "avatar_url": "https://git.door43.org/img/avatar_default.png",
        "language": "",
        "is_admin": false,
        "last_login": "1970-01-01T00:00:00Z",
        "created": "2016-10-18T19:03:36Z",
        "username": "Door43-Catalog"
      },
      "name": "vi_ulb",
      "full_name": "Door43-Catalog/vi_ulb",
      "description": "Vietnamese ULB.  STR https://git.door43.org/Door43/SourceTextRequestForm/issues/149\\r\\n\\r\\n",
      "empty": false,
      "private": false,
      "fork": false,
      "parent": null,
      "mirror": false,
      "size": 5376,
      "html_url": "https://git.door43.org/Door43-Catalog/vi_ulb",
      "ssh_url": "git@git.door43.org:Door43-Catalog/vi_ulb.git",
      "clone_url": "https://git.door43.org/Door43-Catalog/vi_ulb.git",
      "website": "",
      "stars_count": 0,
      "forks_count": 2,
      "watchers_count": 9,
      "open_issues_count": 0,
      "default_branch": "master",
      "archived": false,
      "created_at": "2018-02-12T18:13:00Z",
      "updated_at": "2020-08-24T04:10:55Z",
      "permissions": {
        "admin": true,
        "push": true,
        "pull": true
      },
      "has_issues": true,
      "has_wiki": false,
      "has_pull_requests": true,
      "ignore_whitespace_conflicts": false,
      "allow_merge_commits": true,
      "allow_rebase": true,
      "allow_rebase_explicit": true,
      "allow_squash_merge": true,
      "avatar_url": ""
    },
    "mirror": false,
    "size": 0,
    "html_url": "https://git.door43.org/STR/vi_ulb",
    "ssh_url": "git@git.door43.org:STR/vi_ulb.git",
    "clone_url": "https://git.door43.org/STR/vi_ulb.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 0,
    "open_issues_count": 0,
    "default_branch": "master",
    "archived": false,
    "created_at": "2020-08-24T04:11:10Z",
    "updated_at": "2020-08-24T04:11:10Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    },
    "has_issues": true,
    "has_wiki": true,
    "has_pull_requests": true,
    "ignore_whitespace_conflicts": false,
    "allow_merge_commits": true,
    "allow_rebase": true,
    "allow_rebase_explicit": true,
    "allow_squash_merge": true,
    "avatar_url": ""
  },
  "sender": {
    "id": 6442,
    "login": "RobH",
    "full_name": "Robert Hunt",
    "email": "robh@noreply.door43.org",
    "avatar_url": "https://git.door43.org/avatars/f85d2867fead49449e89c6822dc77bc6",
    "language": "en-US",
    "is_admin": true,
    "last_login": "2020-08-11T23:22:24Z",
    "created": "2017-10-22T07:31:07Z",
    "username": "RobH"
  }
}
""" \
  .replace('\\n','').replace('\n','') \
  .replace("{'", '{"').replace("': ", '": ').replace(": '", ': "').replace("', ", '", ').replace(", '", ', "').replace("'}", '"}') \
  .replace(': True,', ': true,').replace(': False,', ': false,').replace(': None,', ': null,') \
  .replace(': True}', ': true}').replace(': False}', ': false}').replace(': None}', ': null}')
# print('test_json = ', test_json)

if 0 and TEST_FILENAME.replace('--','/') not in test_json:
    print(f"Seems '{TEST_FILENAME}' can't be found in the JSON -- is it correct?")
    print(f"  {test_json[:600]}…")
    sys.exit()
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
    long_prefix = 'develop' if prefix else 'git'
    webhook = LOCAL_COMPOSE_URL if USE_LOCALCOMPOSE_URL else f'https://{long_prefix}.door43.org/client/webhook/'
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
    elif 'forkee' in jsonDict:
        event = 'fork'
    # elif 'ref_type' in jsonDict and jsonDict['ref_type']=='branch' and 'ref' in jsonDict:
    #     event = 'create'
    else:
        logging.critical(f"Can't determine event (push/release/delete/fork, etc.) from JSON")
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
