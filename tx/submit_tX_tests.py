#!/usr/bin/env python3
#
# submit_tX_tests.py
#       Written: Nov 2018
#       Last modified: 2019-11-09 RJH
#

# Python imports
from os import getenv
import sys
import json
import logging
import subprocess


# ======================================================================

# User settings
USE_LOCALCOMPOSE_URL = True
MAX_JOBS_TO_SUBMIT = 1
# Can also choose ONE or NONE of the following
# OPTIONAL_JOB_LIST = ['test_WA_en_udb']
# The following field can either be a single string or a collection of strings
# OPTIONAL_JOB_STARTSWITH = 'line1'

# REVIEW_FLAG = True # Shows all the URLs again at the end
# AUTO_OPEN_IN_BROWSER = True


# Choose one of the following
#TEST_PREFIXES = ('',)
TEST_PREFIXES = ('dev-',)
#TEST_PREFIXES = ('', 'dev-',)

LOCAL_FILEPATH = '/mnt/SSD/uW/Software/'

# ======================================================================


if USE_LOCALCOMPOSE_URL: assert TEST_PREFIXES == ('dev-',)

LOCAL_COMPOSE_URL = 'http://127.0.0.1:8090/'
TEST_FOLDER = f'{LOCAL_FILEPATH}/testPayloads/JSON/tX/'
DATA_SET = [
    # First entry is a status flag
    #   currently 'matched', 'success', or 'test'
    # Second entry is main name of .json file containing test payload
    ('PDF', 'test_tX.OBS-PDF.uW--kn_obs--master'),
    ('PDF', 'test_tX.OBS-PDF.uW--en_obs--master--no_created_from'),
    ('PDF', 'test_tX.OBS-PDF.uW--en_obs--master'),
    ('PDF', 'test_tX.OBS-PDF.Catalog--rmy-x-vwa_obs--master'),
    ('PDF', 'test_tX.OBS-PDF.Catalog--sr-Latn_obs--master'), # Fails -- might be a case problem
    # ('max', 'test_tX.HTML.maximum'),
    # ('min', 'test_tX.HTML.minimum'),
    ]



tested = set()
numSubmittedJobs = 0
for n, (status,testType) in enumerate(DATA_SET):
    if numSubmittedJobs >= MAX_JOBS_TO_SUBMIT: break

    try: job_list = OPTIONAL_JOB_LIST
    except NameError: job_list = None
    if job_list:
        if testType not in job_list: continue
    else:
        try: job_startswith = OPTIONAL_JOB_STARTSWITH
        except NameError: job_startswith = ''
        if job_startswith:
            if isinstance(job_startswith, str):
                if not testType.startswith(job_startswith): continue
            elif isinstance(job_startswith, (list,set,tuple)):
                ok = False
                for this_job_startswith_string in job_startswith:
                    if testType.startswith(this_job_startswith_string): ok = True; break
                if not ok: continue
            else: halt # fault
        else:
            # Adjust according to what status fields you want
            #if status in ('matched','success'): continue
            #if status != 'testNow': continue
            #if not testType.startswith('line'): continue
            pass

    tested.add( testType )
    numSubmittedJobs += 1
    for prefix in TEST_PREFIXES:
        long_prefix = 'develop' if prefix else 'git'
        webhook = LOCAL_COMPOSE_URL if USE_LOCALCOMPOSE_URL else f'https://{long_prefix}.door43.org/tx/'
        print( f"\n\n{n+1}/ {'(dev) ' if prefix else ''}{testType} to {webhook}:" )
        jsonFilename = f'@{TEST_FOLDER}{testType}.json'

        # Use curl to actually POST the JSON to the given webhook URL
        parameters = ['curl', webhook, '-d', jsonFilename,
                '--header', "Content-Type: application/json", '--header', "X-Gogs-Event: push",]
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
                # else:
                print( f"Response dict = {responseDict}" )
            else:
                print( f"Response = {programOutputString!r}" )
        if programErrorOutputBytes:
            programErrorOutputString = programErrorOutputBytes.decode(encoding='utf-8', errors='replace')
            #with open( os.path.join( outputFolder, 'ScriptErrorOutput.txt" ), 'wt', encoding='utf-8' ) as myFile: myFile.write( programErrorOutputString )
            if not programErrorOutputString.startswith('  % Total'):
                print( f"pEOS = {programErrorOutputString!r}" )

        # url = f"https://{'dev.' if prefix else ''}door43.org/u/{webURL}/"
        # print(f"View result at {url}")
        # if AUTO_OPEN_IN_BROWSER:
        #     import webbrowser
        #     webbrowser.open(url, new=0, autoraise=True)
        #     #subprocess.Popen(['xdg-open', url])


# if REVIEW_FLAG and len(tested)>1: # Don't bother if there's only one
#     print(f"\n\nSUMMARY:{' (should automatically open in browser)' if AUTO_OPEN_IN_BROWSER else ''}")
#     for n, webURL in enumerate(tested):
#         if len(TEST_PREFIXES) > 1:
#             print(f" {n+1}/"
#                   f" View at https://{'dev.' if TEST_PREFIXES[0] else ''}door43.org/u/{webURL}/"
#                   f" and at https://{'dev.' if TEST_PREFIXES[1] else ''}door43.org/u/{webURL}/")
#         else:
#             print(f"{n+1}/"
#                   f" View at https://{'dev.' if TEST_PREFIXES[0] else ''}door43.org/u/{webURL}/")
