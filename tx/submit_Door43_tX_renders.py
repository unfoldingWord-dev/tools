#!/usr/bin/env python3
#
# submit_Door43_tX_renders.py
#       Written: Dec 2019
#       Last modified: 2019-12-09 RJH
#
# Uses CURL to generate and submit jobs to the Door43 tX (translationConverter) system
#   Can accept a Door43 username and repo name (down in main program at end)
#   or a list of repo URLS.
#
# NOTE: You must enter your Door43 user info
#           in your copy of the script before running it.
#       This is not a user-friendly program with command line parameters, etc.
#           -- it's just a raw script that you can make do what you need.
#

# Python imports
from typing import Dict, Any
import sys
import re
import json
import logging
import subprocess

# ======================================================================

# User settings
MY_NAME = '' # Put your full name in here
MY_USERNAME = '' # Put your Door43 username in here

# Choose ONE of the following lines
TEST_PREFIXES = ('',) # Render with prodn chain
# TEST_PREFIXES = ('dev-',) # Render with dev- chain
#TEST_PREFIXES = ('', 'dev-',) # Render on both chains

# Paste in a list of Door43 repo URLs here
REPO_LIST_DOCUMENT = """
https://git.door43.org/bcs-exegetical/hi_tn
https://git.door43.org/door43-catalog/hi_tn
https://git.door43.org/str/hi_tn
"""

MAX_JOBS_TO_SUBMIT = None # Use None for no limit, otherwise an integer
AUTO_OPEN_IN_BROWSER = True # True or False

# NOTE: You may also have to adjust the main program near the bottom
#           to make sure it's doing what you want.
#       (You can also paste in a single username and repo name there.)

# ======================================================================


# NOTE: No need to manually modify this
minimal_master_JSON = """
{
  "ref": "refs/heads/master",
  "after": "master",
  "commits": [
    {
      "id": "master",
      "message": "Script: submit_Door43_tX_renders",
      "url": "https://git.door43.org/REPO_OWNER_USERNAME/REPO_NAME/commit/master",
      "author": {
        "name": "MY_NAME",
        "username": "MY_USERNAME"
      }
    }
  ],
  "repository": {
    "owner": {
      "full_name": "REPO_OWNER_USERNAME",
      "username": "REPO_OWNER_USERNAME"
    },
    "name": "REPO_NAME",
    "full_name": "REPO_OWNER_USERNAME/REPO_NAME",
    "html_url": "https://git.door43.org/REPO_OWNER_USERNAME/REPO_NAME",
    "default_branch": "master"
  },
  "pusher": {
    "full_name": "MY_NAME",
    "username": "MY_USERNAME"
  },
  "sender": {
    "full_name": "MY_NAME",
    "username": "MY_USERNAME"
  }
}

"""

num_submitted_jobs = 0
submitted_list = []
def submit_render(repo_owner_username:str, repo_name:str, created_JSON:[Dict[str,Any]]) -> None:
    """
    """
    global num_submitted_jobs
    for prefix in TEST_PREFIXES:
        if MAX_JOBS_TO_SUBMIT \
        and num_submitted_jobs >= MAX_JOBS_TO_SUBMIT:
            print(f"Aborted -- already submitted {num_submitted_jobs} job(s).")
            break
        num_submitted_jobs += 1
        submitted_list.append( (prefix,repo_owner_username,repo_name) )
        webhook = f'https://{prefix}api.door43.org/client/webhook/'
        print( f"\n\n{num_submitted_jobs}/ {MY_USERNAME} ({MY_NAME}) submitting {'(dev) ' if prefix else ''}{repo_owner_username}/{repo_name} to {webhook}:" )

        # Use curl to actually POST the JSON to the given webhook URL
        parameters = ['curl', webhook,
                        '--data', created_JSON,
                        '--header', "Content-Type: application/json",
                        '--header', "X-Gitea-Event: push",
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

        url = f"https://{'dev.' if prefix else ''}door43.org/u/{repo_owner_username}/{repo_name}/master/"
        print(f"   Should become available at {url}")
        if AUTO_OPEN_IN_BROWSER:
            import webbrowser
            webbrowser.open(url, new=0, autoraise=True)
            #subprocess.Popen(['xdg-open', url])
# end of submit_render function


def create_JSON_and_submit_render(repo_owner_username:str, repo_name:str) -> None:
    """
    """
    assert ' ' not in repo_owner_username
    assert ' ' not in repo_name
    created_JSON = minimal_master_JSON \
                        .replace('MY_NAME', MY_NAME) \
                        .replace('MY_USERNAME', MY_USERNAME) \
                        .replace('REPO_OWNER_USERNAME', repo_owner_username) \
                        .replace('REPO_NAME', repo_name)
    submit_render(repo_owner_username, repo_name, created_JSON)
# end of create_JSON_and_submit_render function


def process_repo_list(repo_list_document:str) -> None:
    """
    Paste in a list of repos, one per line,
        e.g., https://git.door43.org/xyz/plt_nam_text_ult
    """
    # total_trigger_count = 0
    for line in repo_list_document.split('\n'):
        logging.debug(f"Checking supplied line {line!r}…")
        if 'git.door43.org' in line:
            if (match := re.search(r'door43\.org/([^/]+?)/([^/\. ]+?)$', line)):
                repo_owner_username = match.group(1)
                repo_name = match.group(2)
                if repo_owner_username and repo_name:
                    result = create_JSON_and_submit_render(repo_owner_username, repo_name)
                    # if isinstance(result, int):
                    #     total_trigger_count += result
                    #     if MAX_WEBHOOKS_TO_TRIGGER and total_trigger_count >= MAX_WEBHOOKS_TO_TRIGGER:
                    #         logging.info(f"Stopping as requested after triggering {total_trigger_count} webhooks.")
                    #         break
                else:
                    logging.error(f"Didn't find parameters: {repo_owner_username=!r} {repo_name=!r}")
    # print(f"{total_trigger_count} total webhooks activated.")
    # return total_trigger_count > 0
# end of process_repo_list function



if __name__ == '__main__':
    """
    Set desired logging level
        then choose which chain(s) to run the render(s) on
        then choose one of the following functions to execute.

    Submits JSON directly to Door43.org api endpoint.
    """
    logging.getLogger().setLevel(logging.INFO)

    print(f"Running submit_tX_tests.py v0.01")
    assert MY_USERNAME
    assert MY_NAME

    # Put the username and repo name in the parameters
    #   to render a single repo.
    this_repo_owner_username = 'tx-manager-test-data'
    this_repo_name = 'tl_psa_text_ulb_L3'
    # create_JSON_and_submit_render(this_repo_owner_username, this_repo_name); sys.exit()

    # process_repo_list(uW_ORIGINALS_LIST); sys.exit()
    # process_repo_list(uW_ENGLISH_LIST); sys.exit()

    process_repo_list(REPO_LIST_DOCUMENT); sys.exit()
# end of submit_Door43_tX_renders.py
