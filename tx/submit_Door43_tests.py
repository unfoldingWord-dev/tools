#!/usr/bin/env python3
#
# submit_Door43_tests.py
#       Written: Oct 2018
#       Last modified: 2019-12-09 RJH
#

# Python imports
import sys
import json
import subprocess


# ======================================================================

# User settings
USE_LOCALCOMPOSE_URL = True
MAX_JOBS_TO_SUBMIT = 1
# (There are 12 'line's, then 5 'new's, and 35 'test's = 52 total)

# Can also choose ONE or NONE of the following
# The following list is for a basic system test
OPTIONAL_JOB_LIST = [
                    'line03_OBS','line08_OBS_tn','line09_OBS_tq',
                        'uW--en_OBS-sq', 'uW--en_OBS-sn',
                    'line10_TN','line11_TQ','line12_TW','line13_TA',
                    'new1_ULT',
                    'uW--el-x-koine_ugnt','uW--hbo_uhb',
                    'new6_uW--en_ugl', 'new7_uW--en_uhal',
                    ] # 14 entries
OPTIONAL_JOB_LIST = ['uW--hbo_uhb']
# OPTIONAL_JOB_LIST = ['WycliffeAssociates--en_ta--yamlProblem']
# OPTIONAL_JOB_LIST = ['one_off.tx-manager-test-data--en_ugl_mini',
#                      'one_off.tx-manager-test-data--en_uhal_mini']

# The following field can either be a single string or a collection of strings
# OPTIONAL_JOB_STARTSWITH = ['line01','line02','line03','line08','line09','line1',]

REVIEW_FLAG = True # Shows all the URLs again at the end
AUTO_OPEN_IN_BROWSER = True


# Choose one of the following
TEST_PREFIXES = ('dev-',)
# TEST_PREFIXES = ('',)
# TEST_PREFIXES = ('', 'dev-',)

LOCAL_FILEPATH = '/mnt/SSD/uW/Software/'

# ======================================================================


if USE_LOCALCOMPOSE_URL: assert TEST_PREFIXES == ('dev-',)

LOCAL_COMPOSE_URL = 'http://127.0.0.1:8080/'
TEST_FOLDER = f'{LOCAL_FILEPATH}/testPayloads/JSON/Door43/'
DATA_SET = [
    # First entry is a status flag
    #   currently 'matched', 'success', or 'test'
    # Second entry is main name of .json file containing test payload
    # Third entry is used to create the URL of the Door43 page for viewing

    # Matrix lines from https://github.com/unfoldingWord-dev/door43.org/wiki/tX-Conversion-Types
    ('success', 'line01_OBS', 'unfoldingWord/en_obs/2b3288a119'),
    ('matched', 'line02_OBS', 'RobH/tem_obs_text_obs'), # Only one story so runs quickly
    ('success', 'line03_OBS', 'unfoldingWord/en_obs'),
    ('matched', 'line04_BIBLE_mat_ulb', 'RobH/id_mat_text_ulb'),
    ('matched', 'line05_BIBLE_ne-ulb', 'RobH/ne-ulb'),
    ('matched', 'line06_BIBLE_ne_ulb', 'RobH/ne_ulb'),
    #line7 ???
    ('success', 'line08_OBS_tn', 'unfoldingWord/en_obs-tn'),
    ('test', 'line09_OBS_tq', 'unfoldingWord/en_obs-tq'),
    ('testNow', 'line10_TN', 'unfoldingWord/en_tn'),
    ('test', 'line11_TQ', 'unfoldingWord/en_tq'),
    ('test', 'line12_TW', 'unfoldingWord/en_tw'),
    ('matched', 'line13_TA', 'unfoldingWord/en_ta'),

    # Repositories that need to start working (from https://github.com/unfoldingWord-dev/door43.org/issues/835)
    ('test', 'new1_ULT', 'unfoldingWord/en_ult'),
    ('test', 'new2_UST', 'unfoldingWord/en_ust'),

    # ('test', 'new3_UGNT', 'unfoldingWord/UGNT'),
    # ('test', 'new4_UHB', 'unfoldingWord/UHB'),
    ('test', 'uW--el-x-koine_ugnt', 'unfoldingWord/el-x-koine_ugnt'),
    ('test', 'uW--hbo_uhb', 'unfoldingWord/hbo_uhb'),

    ('test', 'new5_tS_tN', 'RobH/plt_1co_tn'),
    ('test', 'new6_uW--en_ugl', 'unfoldingWord/en_ugl'),
    ('test', 'new7_uW--en_uhal', 'unfoldingWord/en_uhal'),
    ('test', 'one_off.tx-manager-test-data--en_ugl_mini', 'tx-manager-test-data/en_ugl_mini'),
    ('test', 'one_off.tx-manager-test-data--en_uhal_mini', 'tx-manager-test-data/en_uhal_mini'),
    ('test', 'uW--en_OBS-sq', 'unfoldingWord/en_obs-sq'),
    ('test', 'uW--en_OBS-sn', 'unfoldingWord/en_obs-sn'),
    # Intentional failure
    #('fail', 'fail_OBS', 'unfoldingWord/en_obs'),

    # Repositories from https://git.door43.org/tx-manager-test-data
    ('matched', 'test-en-obs-rc-0.2', 'tx-manager-test-data/en-obs-rc-0.2'),
    ('matched', 'test-en-obs-pre-rc', 'tx-manager-test-data/en-obs-pre-rc'),
    ('success', 'test-en-ulb', 'tx-manager-test-data/en-ulb'),
    ('matched', 'test-ceb_psa_text_ulb_L3', 'tx-manager-test-data/ceb_psa_text_ulb_L3'),
    ('test', 'test-bible_ru_short', 'tx-manager-test-data/bible_ru_short'),
    ('test', 'test-en_ta', 'tx-manager-test-data/en_ta'),
    ('test', 'test-en_tn_mat', 'tx-manager-test-data/en_tn_mat'),
    ('test', 'test-en_tw', 'tx-manager-test-data/en_tw'),
    ('test', 'test-en_tq', 'tx-manager-test-data/en_tq'),
    ('test', 'test-en_tn', 'tx-manager-test-data/en_tn'),
    ('test', 'test-en_tn_nt', 'tx-manager-test-data/en_tn_nt'),
    ('test', 'test-en_tq_two_books', 'tx-manager-test-data/en_tq_two_books'),
    ('test', 'test-AlignedUdt_en', 'tx-manager-test-data/AlignedUdt_en'),
    ('test', 'test-AlignedUlb_hi_test', 'tx-manager-test-data/AlignedUlb_hi_test'),
    ('test', 'test-fr_stuff_tit_book', 'tx-manager-test-data/fr_stuff_tit_book'),
    ('test', 'test-tem_obs_text_obs-ts', 'tx-manager-test-data/tem_obs_text_obs-ts'),
    ('matched', 'test-ne-ulb-RC-0.2-bundle', 'tx-manager-test-data/ne-ulb-RC-0.2-bundle'),
    ('test', 'test-en-obs-tn', 'tx-manager-test-data/en-obs-tn'),
    ('success', 'test-en-ulb-123-john', 'tx-manager-test-data/en-ulb-123-john'),
    ('success', 'test-en-ulb-jud', 'tx-manager-test-data/en-ulb-jud'),
    ('matched', 'test-awa_act_text_reg', 'tx-manager-test-data/awa_act_text_reg'),
    ('matched', 'test-kpb_mat_text_udb', 'tx-manager-test-data/kpb_mat_text_udb'),
    ('matched', 'test-kan-x-aruvu_act_text_udb', 'tx-manager-test-data/kan-x-aruvu_act_text_udb'),
    ('matched', 'test-bible_ru', 'tx-manager-test-data/bible_ru'),
    ('matched', 'test-hu_obs_text_obs', 'tx-manager-test-data/hu_obs_text_obs'),
    ('test', 'test-tl_psa_text_ulb_L3', 'tx-manager-test-data/tl_psa_text_ulb_L3'),
    ('matched', 'test-nt_ru', 'tx-manager-test-data/nt_ru'),
    ('matched', 'test-ot_ru', 'tx-manager-test-data/ot_ru'),
    ('test', 'test-en_udb', 'tx-manager-test-data/en_udb'),
    ('matched', 'test-en_ulb_full', 'tx-manager-test-data/en_ulb_full'),
    ('matched', 'test-id_mat_text_ulb-ts', 'tx-manager-test-data/id_mat_text_ulb-ts'),
    ('test', 'test-en_ult_rev_book', 'RobH/en_ult_rev_book'),
    ('test', 'test_WA_en_udb', 'RobH/en_udb'),
    ('test', 'test_hi_tq', 'tx-manager-test-data/d43_catalog_hi_tq'),
    ('test', 'test_mr_ta', 'tx-manager-test-data/d43_catalog_mr_ta'),
    ('test', 'test-pt-br_bible_tw', 'alexandre_brazil/pt-br_bible_tw'),
    ('test', 'test-hr_tn', 'STR/hr_tn'),
    ('test', 'test-es-419_luk_tn', 'wendyc/es-419_luk_tn'), # Contains conflict markers in json files
    ('test', 'plateaumalagasy--plt_1co_tq_l2', 'plateaumalagasy/plt_1co_tq_l2'),
    ]



tested = set()
numSubmittedJobs = 0
try: job_list = OPTIONAL_JOB_LIST
except NameError: job_list = None
for n, (status,testType,webURL) in enumerate(DATA_SET):
    if numSubmittedJobs >= MAX_JOBS_TO_SUBMIT: break

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
            else:
                raise Exception("Logic error")
        else:
            # Adjust according to what status fields you want
            pass
            #if status in ('matched','success'): continue
            #if status != 'testNow': continue
            #if not testType.startswith('line'): continue

    # Skip any specified exception jobs
    try: exception_job_list = OPTIONAL_EXCEPTION_JOB_LIST
    except NameError: exception_job_list = []
    if testType in exception_job_list: continue # skip this one

    tested.add( webURL )
    numSubmittedJobs += 1
    for prefix in TEST_PREFIXES:
        webhook = LOCAL_COMPOSE_URL if USE_LOCALCOMPOSE_URL else f'https://{prefix}api.door43.org/client/webhook/'
        print( f"\n\n{n+1}/ {'(dev) ' if prefix else ''}'{testType}' to {webhook}:" )
        jsonFilename = f'@{TEST_FOLDER}{testType}.json'

        # Use curl to actually POST the JSON to the given webhook URL
        parameters = ['curl', webhook,
                        '--data', jsonFilename,
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

        url = f"https://{'dev.' if prefix else ''}door43.org/u/{webURL}/"
        print(f"View result at {url}")
        if AUTO_OPEN_IN_BROWSER:
            import webbrowser
            webbrowser.open(url, new=0, autoraise=True)
            #subprocess.Popen(['xdg-open', url])


if REVIEW_FLAG and len(tested)>1: # Don't bother if there's only one
    print(f"\n\nSUMMARY:{' (should automatically open in browser)' if AUTO_OPEN_IN_BROWSER else ''}")
    for n, webURL in enumerate(tested):
        if len(TEST_PREFIXES) > 1:
            print(f" {n+1}/"
                  f" View at https://{'dev.' if TEST_PREFIXES[0] else ''}door43.org/u/{webURL}/"
                  f" and at https://{'dev.' if TEST_PREFIXES[1] else ''}door43.org/u/{webURL}/")
        else:
            print(f"{n+1}/"
                  f" View at https://{'dev.' if TEST_PREFIXES[0] else ''}door43.org/u/{webURL}/")

if job_list and numSubmittedJobs<len(job_list):
    print(f"\n\nNOTE: {len(job_list) - numSubmittedJobs} jobs were unable to be submitted!")