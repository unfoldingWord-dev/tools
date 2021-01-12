#!/usr/bin/env python3
#
# tigger_DCS_webhooks.py
#       Written: Nov 2019
#       Last modified: 2019-12-09 RJH
#
# See Gitea documentation at https://try.gitea.io/api/swagger
#
# Assumes a valid Gitea access token saved as an environment variable: GITEA_USER_TOKEN
#   (This token will require administrator permission if wanting to access webhooks for other users.)
#

# Python imports
from typing import Dict, List, Optional, Any, Union
import sys
from os import environ
import re
import logging

# PyPI imports
import requests


# ======================================================================

# User settings
# Choose one of the following
TEST_PREFIXES = ('',)
TEST_PREFIXES = ('dev-',)
# TEST_PREFIXES = ('', 'dev-',)

REPO_LIST_DOCUMENT = """
https://git.door43.org/bcs-exegetical/hi_tn
https://git.door43.org/door43-catalog/hi_tn
https://git.door43.org/str/hi_tn
"""

MAX_WEBHOOKS_TO_TRIGGER = None # Set to None for no-limit or to an integer for testing

# ======================================================================


# Permanent settings
DOOR43_BASE_URL = 'git.door43.org/api/v1' # No protocol and no trailing slash
# TEST_BASE_URL = 'try.gitea.io/api/v1'
BASE_URL = DOOR43_BASE_URL
ACCESS_TOKEN = environ['GITEA_USER_TOKEN'] # We need a Gitea access token from the environment

OUR_NAME = 'Trigger Webhook'



uW_ORIGINALS_LIST = """
https://git.door43.org/unfoldingWord/hbo_uhb
https://git.door43.org/unfoldingWord/el-x-koine_ugnt
"""

uW_ENGLISH_LIST = """
https://git.door43.org/unfoldingWord/en_obs
https://git.door43.org/unfoldingWord/en_obs-tn
https://git.door43.org/unfoldingWord/en_obs-tq
https://git.door43.org/unfoldingWord/en_obs-sn
https://git.door43.org/unfoldingWord/en_obs-sq

https://git.door43.org/unfoldingWord/en_ta
https://git.door43.org/unfoldingWord/en_tn
https://git.door43.org/unfoldingWord/en_tq
https://git.door43.org/unfoldingWord/en_tw

https://git.door43.org/unfoldingWord/en_ult
https://git.door43.org/unfoldingWord/en_ust

https://git.door43.org/unfoldingWord/en_ugl
https://git.door43.org/unfoldingWord/en_uhal

https://git.door43.org/unfoldingWord/en_ugg # Doesn't have standard webhooks (uses readthedocs)
https://git.door43.org/unfoldingWord/en_uhg # Doesn't have standard webhooks (uses readthedocs)
"""



def get_result(command:str, parameters:Optional[str]=None) -> Optional[Dict[str,Any]]:
    """
    Compiles and submits the GET command to GITEA
        and hopefully returns the result.

    Returns None if there was an error,
            otherwise the returned result.
    """
    assert command and command[0]!='/'
    full_url = f'https://{BASE_URL}/{command}?access_token={ACCESS_TOKEN}'
    if parameters:
        full_url = f'{full_url}&{parameters}'
    requests_result = requests.get(full_url)
    logging.debug(f"Requests result = {requests_result}")
    if requests_result.status_code == 200:
        try:
            result_json = requests_result.json()
            result_json_string = str(result_json)
            if len(result_json_string) > 800:
                result_json_string = f'{result_json_string[:600]} ……… {result_json_string[-200:]}'
            logging.debug(f"Got result_json = ({len(result_json):,}) {result_json_string}")
            return result_json
        except Exception as err:
            logging.error(f"JSON decoding error: {err}")
            return None
    elif requests_result.status_code == 401:
        logging.critical("Need to authorize first! (Code 401)")
        return None
    elif requests_result.status_code == 403:
        logging.critical("You don't have authorisation to trigger this webhook! (Code 403)")
        return None
    else:
        logging.error(f"Received {requests_result.status_code} error from '{full_url}': {requests_result.headers}")
        return None
# end of get_result function


def post(command:str, parameters:Optional[str]=None) -> Optional[Dict[str,Any]]:
    """
    Compiles and submits the POST command to GITEA
        and hopefully returns the result.

    Returns None if there was an error,
            True if the result was successful but no content returned,
            otherwise the returned result.
    """
    assert command and command[0]!='/'
    full_url = f'https://{BASE_URL}/{command}?access_token={ACCESS_TOKEN}'
    if parameters:
        full_url = f'{full_url}&{parameters}'
    requests_result = requests.post(full_url)
    logging.debug(f"Requests result = {requests_result}")
    if requests_result.status_code == 204: # Success but no content returned
        return True
    elif requests_result.status_code == 200:
        try:
            result_json = requests_result.json()
            result_json_string = str(result_json)
            if len(result_json_string) > 800:
                result_json_string = f'{result_json_string[:600]} ……… {result_json_string[-200:]}'
            logging.debug(f"Got result_json = ({len(result_json):,}) {result_json_string}")
            return result_json
        except Exception as err:
            logging.error(f"JSON decoding error: {err}")
            return None
    elif requests_result.status_code == 401:
        logging.critical("Need to authorize first!")
        return None
    else:
        logging.error(f"Received {requests_result.status_code} error from '{full_url}'")
        return None
# end of post function


def get_Gitea_version() -> Optional[str]:
    """
    """
    result_json = get_result('version')
    if result_json:
        Gitea_version = result_json['version']
        # logging.debug(f"Gitea version = '{Gitea_version}'")
        return Gitea_version
# end of get_Gitea_version()


def get_all_organizations() -> Optional[Dict[str,Any]]:
    """
    Seems to be around 20 organizations.
    """
    limit = 50 # This is the max according to the documentation
    result_json = get_result('admin/orgs', f'limit={limit}')
    if result_json:
        print("\nOrganization list:")
        for j,entry in enumerate(result_json, start=1):
            print(f"  {j:3}/ {entry['id']:5} '{entry['full_name']:30}' ({entry['username']})")
        if len(result_json) >= limit:
            logging.critical(f"Note: there may be other entries not received! (limit was {limit})")
        return result_json
# end of get_all_organizations()


def get_organization_webhook_list(org_username:str) -> Optional[Dict[str,Any]]:
    result_json = get_result(f'orgs/{org_username}/hooks')
    if result_json:
        print("\nWebhook list for organization '{org_username}':")
        for entry in result_json:
            print(f"  {entry}")
        return result_json
# end of get_organization_webhook_list function


def get_all_users() -> Optional[str]:
    """
    There's over 12,000 of them!
    """
    result_json = get_result('admin/users')
    if result_json:
        if 1:
            print(f"{len(result_json)} user entries received.")
        else:
            print("\nUser list:")
            for j,entry in enumerate(result_json, start=1):
                print(f"  {j:3}/ {entry['id']:5} '{entry['full_name']:25}' ({entry['username']})")
        return result_json
# end of get_all_users()


def get_repo_webhook_list(repo_owner_username:str, repo_name:str):
    """
    Get the list of webhooks for a given repo.
    """
    result_json = get_result(f'repos/{repo_owner_username}/{repo_name}/hooks')
    if result_json:
        logging.debug(f"  Received {len(result_json)} webhooks for {repo_owner_username}/{repo_name}")
        # print(f"\nWebhook list ({len(result_json)}) for repo {repo_owner_username}/{repo_name}:")
        # for entry in result_json:
        #     assert entry['config']['content_type'] == 'json'
        #     print(f"  {entry['id']} {entry['type']}  {entry['config']['url']}  active={entry['active']}")
        return result_json
# end of get_repo_webhook_list function


def trigger_repo_webhooks(repo_owner_username:str, repo_name:str, webhook_list:List[int]) -> Union[bool,int]:
    """
    Trigger the given Gitea webhooks for the given repo.

    Returns the number of webhooks triggered
        or False if there was an error.
    """
    assert repo_owner_username
    assert repo_name
    repo_trigger_count = 0
    logging.info(f"Triggering {repo_owner_username}/{repo_name} webhook{'' if len(webhook_list)==1 else 's'} {webhook_list[0] if len(webhook_list)==1 else webhook_list}…")
    for webhook_id in webhook_list:
        result = post(f'repos/{repo_owner_username}/{repo_name}/hooks/{webhook_id}/tests')
        if result == True:
            repo_trigger_count += 1
        else:
            logging.error(f"Trigger webhook {webhook_id} for {repo_owner_username}/{repo_name} failed!")
            return False
    return repo_trigger_count
# end of trigger_repo_webhooks function


def find_and_trigger_repo_webhooks(repo_owner_username:str, repo_name:str) -> bool:
    """
    Get a list of webhooks for the given repo
        and then trigger either the main ones or the DEV- ones or both
            (depending on the TEST_PREFIXES global setting).

    Returns the number of webhooks triggered
        or False if there was an error.
    """
    assert repo_owner_username
    assert repo_name
    logging.info(f"Finding webhooks for {repo_name}/{repo_name}…")
    repo_webhook_list = get_repo_webhook_list(repo_owner_username, repo_name)
    if not repo_webhook_list:
        logging.error(f"No webhooks set for {repo_owner_username}/{repo_name}")
        return False
    hook_id_list = []
    for repo_webhook in repo_webhook_list:
        if '' in TEST_PREFIXES \
        and repo_webhook['config']['url'] in ('https://api.door43.org/client/webhook','https://git.door43.org/client/webhook'):
            hook_id_list.append(repo_webhook['id'])
            logging.debug(f"  Found matching {repo_webhook['config']['url']} ({repo_webhook['id']}) webhook")
        if 'dev-' in TEST_PREFIXES \
        and repo_webhook['config']['url'] in ('https://dev-api.door43.org/client/webhook','https://dev-git.door43.org/client/webhook'):
            hook_id_list.append(repo_webhook['id'])
            logging.debug(f"  Found matching {repo_webhook['config']['url']} ({repo_webhook['id']}) webhook")
    if not hook_id_list:
        logging.error(f"No valid {TEST_PREFIXES} webhooks found for {repo_owner_username}/{repo_name}")
        logging.debug(f"repo_webhook_list was {repo_webhook_list}")
        return False
    return trigger_repo_webhooks(repo_owner_username, repo_name, hook_id_list)
# end of find_and_trigger_repo_webhooks function


def demo():
    """
    Just a brief demo to show some of the Gitea functions working.
    """
    # get_all_organizations()
    # org_username = 'Door43'
    # organization_webhook_list = get_organization_webhook_list(org_username)

    # get_all_users()

    repo_owner_username = 'tx-manager-test-data'
    repo_name = 'en_tn_nt'
    find_and_tigger_DCS_webhooks(repo_owner_username, repo_name)
# end of demo()


def process_repo_list(repo_list_document:str) -> bool:
    """
    Paste in a list of repos, one per line,
        e.g., https://git.door43.org/plateaumalagasy/plt_nam_text_ulb_l3

    Gets the webhooks from Door43,
        discovers the right webhook(s) according to the TEST_PREFIXES global setting
        and then activates the webhook(s).
    """
    total_trigger_count = 0
    for line in repo_list_document.split('\n'):
        logging.debug(f"Checking supplied line {line!r}…")
        if 'git.door43.org' in line:
            if (match := re.search(r'door43\.org/([^/]+?)/([^/\. ]+?)$', line)):
                repo_owner_username = match.group(1)
                repo_name = match.group(2)
                if repo_owner_username and repo_name:
                    result = find_and_trigger_repo_webhooks(repo_owner_username, repo_name)
                    if isinstance(result, int):
                        total_trigger_count += result
                        if MAX_WEBHOOKS_TO_TRIGGER and total_trigger_count >= MAX_WEBHOOKS_TO_TRIGGER:
                            logging.info(f"Stopping as requested after triggering {total_trigger_count} webhooks.")
                            break
                else:
                    logging.error(f"Didn't find parameters: {repo_owner_username=!r} {repo_name=!r}")
    print(f"{total_trigger_count} total webhooks activated.")
    return total_trigger_count > 0
# end of process_repo_list function



if __name__ == '__main__':
    """
    Set desired logging level
        then choose which chain(s) to run the webhook(s) on
        then choose one of the following functions to execute.

    Note: This only triggers webhooks that are previously set-up in the system.
    """
    logging.getLogger().setLevel(logging.INFO)

    print(f"Communicating with {BASE_URL} running Gitea v{get_Gitea_version()}.")

    # demo()

    # Put the username and repo name in the parameters
    #   to trigger a single webhook.
    this_repo_owner_username = 'unfoldingWord'
    this_repo_name = 'en_ult'
    find_and_trigger_repo_webhooks(this_repo_owner_username, this_repo_name); sys.exit()

    # process_repo_list(uW_ORIGINALS_LIST); sys.exit()
    # process_repo_list(uW_ENGLISH_LIST); sys.exit()

    process_repo_list(REPO_LIST_DOCUMENT); sys.exit()
# end of tigger_DCS_webhooks.py