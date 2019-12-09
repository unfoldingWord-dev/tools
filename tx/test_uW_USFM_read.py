#!/usr/bin/env python3
#
# test_uW_USFM_read.py
#       Written: Dec 2019
#       Last modified: 2019-12-02 RJH
#
# Reads complex (e.g., aligned) USFM files
#   and extracts the actual Biblical text
#   with special emphasis on correctly handling whitespace.
#
# Currently there's no provision for saving the extracted text into a file
#   although this could be easily added.
#


# Python imports
from typing import Optional
import logging
import re

# PyPI imports
import requests



GENESIS_ORIGINAL_HEBREW_URL = 'https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master/01-GEN.usfm'
JOSHUA_ORIGINAL_HEBREW_URL = 'https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master/06-JOS.usfm'
RUTH_ORIGINAL_HEBREW_URL = 'https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master/08-RUT.usfm'

MATTHEW_ORIGINAL_GREEK_URL = 'https://git.door43.org/unfoldingWord/el-x-koine_ugnt/raw/branch/master/41-MAT.usfm'
TITUS_ORIGINAL_GREEK_URL = 'https://git.door43.org/unfoldingWord/el-x-koine_ugnt/raw/branch/master/57-TIT.usfm'

GENESIS_LITERAL_TRANSLATION_URL = 'https://git.door43.org/unfoldingWord/en_ult/raw/branch/master/01-GEN.usfm'
RUTH_LITERAL_TRANSLATION_URL = 'https://git.door43.org/unfoldingWord/en_ult/raw/branch/master/08-RUT.usfm'


# ======================================================================

# Here the user chooses which file will be downloaded and processed
TEST_URL = JOSHUA_ORIGINAL_HEBREW_URL

# ======================================================================



def first_and_last(full_text:str, display_length:int=200, divider_chars:str=' …… ') -> str:
    """
    Helper function to abbreviate long strings (e.g., USFM files) for display.
    """
    if not full_text \
    or len(full_text) <= display_length:
        return full_text
    # else, let's abbreviate it
    return f'{full_text[:display_length]}{divider_chars}{full_text[-display_length:]}'
# end of first_and_last function


def get_file(file_url:str) -> Optional[str]:
    """
    Download the file at the requested URL and return it
        or return None if there was an error.
    """
    logging.debug(f"get_file( {file_url} )")
    assert file_url.startswith('http')

    requests_result = requests.get(file_url)
    logging.debug(f"Requests result = {requests_result}")
    if requests_result.status_code == 200:
        downloaded_text = requests_result.text
        logging.debug(f"Got downloaded_text = ({len(downloaded_text):,} chars):\n{first_and_last(downloaded_text)}")
        return downloaded_text
    else:
        logging.error(f"Received {requests_result.status_code} error from '{file_url}': {requests_result.headers}")
        return None
# end of get_file function


zaln_s_re = re.compile(r'\\zaln-s ([^\n]+?)\\\*')
k_s_re = re.compile(r'\\k-s ([^\n]+?)\n') # Bad USFM3 -- should be self-closed
def remove_milestones(given_text:str) -> str:
    """
    Remove the various milestone markers from the given text.
    """
    # logging.debug(f"remove_milestones( ({len(given_text):,}) {first_and_last(given_text, display_length=20)} )")

    result_text = zaln_s_re.sub('', given_text) # Remove start milestones with all their contents
    result_text = result_text.replace('\\zaln-e\\*', '') # Remove simpler end milestones

    result_text = k_s_re.sub('', given_text) # Remove start milestones with all their contents
    result_text = result_text.replace('\\k-e\\*\n', '') # Remove simpler end milestones (on a line of their own)

    result_text = result_text.replace('\\s5\n', '') # Remove non-USFM chunk milestones
    result_text = result_text.replace('\n\\s5', '') # Handle failure of the above with trailing spaces

    # logging.debug(f"  Returning ({len(result_text):,}) {first_and_last(result_text)}")
    return result_text
# end of remove_milestones function


word_data_re = re.compile(r'\\w ([^ \n]+?)\|([^\n]+?)\\w\*')
def remove_word_data(given_text:str) -> str:
    """
    Remove all of the word data inside \w ... \w* fields
        except for the actual word itself.
    """
    # logging.debug(f"remove_word_data( ({len(given_text):,}) {first_and_last(given_text, display_length=20)} )")
    result_text = given_text
    while (match := word_data_re.search(result_text)):
        # logging.debug(f'{match.group(0)=}')
        # logging.debug(f'{match.group(1)=}')
        # logging.debug(f'{match.group(2)=}')
        result_text = f'{result_text[:match.start()]}{match.group(1)}{result_text[match.end():]}'
    # logging.debug(f"  Returning ({len(result_text):,}) {first_and_last(result_text)}")
    return result_text
# end of remove_word_data function


def extract_text(file_url:str) -> Optional[str]:
    """
    Download the text file from the given URL
        and extract the Bible text.
    """
    # logging.debug(f"extract_text( {file_url} )")
    received_text = get_file(file_url)
    for left_char, right_char in (('(',')'), ('[',']'), ('{','}'),
                                  ('\\w ','\\w*'), ('\\f ','\\f*')):
        left_count, right_count = received_text.count(left_char), received_text.count(right_char)
        if left_count != right_count:
            logging.error(f"Original file contains {left_count} '{left_char}' chars but {right_count} '{right_char}' chars!")

    adjusted_text = received_text
    adjusted_text = remove_milestones(adjusted_text)
    adjusted_text = adjusted_text.replace('\n\\w ', ' \\w ') # Append word lines to previous line with a space
    adjusted_text = adjusted_text.replace('\n\\f ', '\\f ') # Append footnote lines to previous line (WITHOUT a space)
    adjusted_text = remove_word_data(adjusted_text)
    return adjusted_text
# end of extract_text function



# This is the start of the main program
print("Running test_uW_USFM_read.py v1.01\n")
logging.getLogger().setLevel(logging.INFO)
print(f"Processing {TEST_URL}…")
extracted_text = extract_text(TEST_URL)
if (double_count := extracted_text.count('  ')):
    print(f"Contains {double_count} sets of double spaces (now)!")
if (leading_count := extracted_text.count('\n ')):
    print(f"Contains {leading_count} lines with leading spaces (now)!")
if (trailing_count := extracted_text.count(' \n')):
    print(f"Contains {trailing_count} lines with trailing spaces!")
if (blank_count := extracted_text.count('\n\n')):
    print(f"Contains {blank_count} (unnecessary) blank lines!")
if (NBS_count := extracted_text.count('\u00A0')):
    print(f"Contains {NBS_count} non-break spaces!")
if (WJ_count := extracted_text.count('\u2060')):
    print(f"Contains {WJ_count:,} word joiners!")
if (f1_count := extracted_text.count(' \\f ')):
    print(f"Contains {f1_count} footnotes following a space!")
if (f2_count := extracted_text.count('\\f* ')):
    print(f"Contains {f2_count} footnotes with a following space!")
if (ms_count := extracted_text.count('־ ')):
    print(f"Contains {ms_count} maqqefs with a following space!")
if (sm_count := extracted_text.count(' ־')):
    print(f"Contains {sm_count} maqqefs with a preceding space!")
for left_char, right_char in (('(',')'), ('[',']'), ('{','}'), ('\\f ','\\f*')):
    left_count, right_count = extracted_text.count(left_char), extracted_text.count(right_char)
    if left_count != right_count:
        print(f"Extracted text contains {left_count} '{left_char}' chars but {right_count} '{right_char}' chars!")

# Do a final tidy-up here in a "post-processing" phrase
postprocessed_text = extracted_text
while ' \n' in postprocessed_text:
    postprocessed_text = postprocessed_text.replace(' \n', '\n')
while '\n\n' in postprocessed_text:
    postprocessed_text = postprocessed_text.replace('\n\n', '\n')

display_text = postprocessed_text
print("\nSpaces are represented below as '·' middle-dots")
if NBS_count:
    print("  Non-break spaces are represented as '~'")
if WJ_count:
    print("  Word joiner characters are represented as '¦' broken bars")
display_text = display_text.replace(' ', '·') # Change ordinary spaces into middle dots so visible
display_text = display_text.replace('\u00A0', '~') # Change non-break spaces into squiggles so visible
display_text = display_text.replace('\u2060', '¦') # Change word joiners into broken bars so visible
display_text = first_and_last(display_text, display_length=8_000, divider_chars='……\n……\n……')
print(f"\nFinal result = ({len(display_text):,} chars):\n{display_text}")

print(f"Finished processing {TEST_URL}.")
# end of test_uW_USFM_read.py
