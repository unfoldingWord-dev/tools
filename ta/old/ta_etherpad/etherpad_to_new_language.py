#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#
import argparse
import codecs
from datetime import datetime
from etherpad_lite import EtherpadLiteClient, EtherpadException
import os
import re
import sys

NEW_LANGUAGE_CODE = ''
CONTINUE_ON_ERROR = 0
DELETE_EXISTING = -1
ERROR_COUNT = 0

LOGFILE = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/ta_copy.log.txt'

VOLUMEREGEX = re.compile(r".*(volume:\s*[1]+).*", re.DOTALL | re.MULTILINE | re.UNICODE)

# YAML file heading data format:
#
# ---
# title: Test tA Module 1
# question: What is Module 1 all about?
# manual: Section_Name(?)
# volume: 1
# slug: testmod1 - unique in all tA
# dependencies: ["intro", "howdy"] - slugs
# status: finished
# ---
#
# Derived URL = en/ta/vol1/section_name/testmod1



# enable logging for this script
log_dir = os.path.dirname(LOGFILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, 0755)

if os.path.exists(LOGFILE):
    os.remove(LOGFILE)


class SelfClosingEtherpad(EtherpadLiteClient):
    """
    This class is here to enable with...as functionality for the EtherpadLiteClient
    """

    def __init__(self):
        super(SelfClosingEtherpad, self).__init__()

        # noinspection PyBroadException
        try:
            # ep_api_key.door43 indicates this is a remote connection
            if os.path.exists('/usr/share/httpd/.ssh/ep_api_key.door43'):
                key_file = '/usr/share/httpd/.ssh/ep_api_key.door43'
                base_url = 'https://pad.door43.org/api'

            else:
                key_file = '/usr/share/httpd/.ssh/ep_api_key'
                base_url = 'http://localhost:9001/api'

            pw = open(key_file, 'r').read().strip()
            self.base_params = {'apikey': pw}
            self.base_url = base_url

        except:
            e1 = sys.exc_info()[0]
            print 'Problem logging into Etherpad via API: {0}'.format(e1)
            sys.exit(1)

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exception_type, exception_val, trace):
        return


class SectionData(object):
    def __init__(self, name, page_list=None):
        if not page_list:
            page_list = []
        self.name = self.get_name(name)
        self.page_list = page_list

    @staticmethod
    def get_name(name):
        if name.lower().startswith('intro'):
            return 'Introduction'

        if name.lower().startswith('transla'):
            return 'Translation'

        if name.lower().startswith('check'):
            return 'Checking'

        if name.lower().startswith('tech'):
            return 'Technology'

        if name.lower().startswith('proc'):
            return 'Process'

        return name


def log_this(string_to_log, top_level=False):
    if string_to_log == '':
        return

    print string_to_log
    if top_level:
        msg = u'\n=== {0} ==='.format(string_to_log)
    else:
        msg = u'\n  * {0}'.format(string_to_log)

    with codecs.open(LOGFILE, 'a', 'utf-8') as file_out:
        file_out.write(msg)


def log_error(string_to_log):
    global ERROR_COUNT
    global CONTINUE_ON_ERROR

    ERROR_COUNT += 1
    log_this(string_to_log)

    # prompt user to continue or exit
    if CONTINUE_ON_ERROR == 1:
        return

    user_input = raw_input('Continue after error (y|N|a): ')

    if user_input == 'y':
        return

    if user_input == 'a':
        CONTINUE_ON_ERROR = 1
        return

    # if we get here we should exit
    sys.exit(1)


def parse_ta_modules(raw_text):
    """
    Returns a dictionary containing the URLs in each major section
    :param raw_text: str
    :rtype: SectionData[]
    """

    returnval = []

    # remove everything before the first ======
    pos = raw_text.find("\n======")
    tmpstr = raw_text[pos + 7:]

    # break at "\n======" for major sections
    arr = tmpstr.split("\n======")
    for itm in arr:

        # split section at line breaks
        lines = filter(None, itm.splitlines())

        # section name is the first item
        section_name = lines[0].replace('=', '').strip()

        # remove section name from the list
        del lines[0]
        urls = []

        # process remaining lines
        for i in range(0, len(lines)):

            # find the URL, just the first one
            match = re.search(r"(https://[\w\./-]+)", lines[i])
            if match:
                pos = match.group(1).rfind("/")
                if pos > -1:
                    urls.append(match.group(1)[pos + 1:])
                else:
                    urls.append(match.group(1))

        # remove duplicates
        no_dupes = set(urls)

        # add the list of URLs to the dictionary
        returnval.append(SectionData(section_name, no_dupes))

    return returnval


def get_ta_pages(e_pad, sections):
    """

    :param e_pad: SelfClosingEtherpad
    :param sections: SectionData[]
    :return: PageData[]
    """

    pages = []

    for section in sections:
        section_key = section.name

        for pad_id in section.page_list:

            log_this('Retrieving page: ' + section_key.lower() + ':' + pad_id, True)

            # get the page
            try:
                create_new_page(e_pad, pad_id)

            except EtherpadException as e:
                log_error(e.message)

            except Exception as ex:
                log_error(str(ex))

    return pages


def create_new_page(e_pad, original_page_name, force=False):
    global NEW_LANGUAGE_CODE

    new_pad_name = NEW_LANGUAGE_CODE + '-' + original_page_name
    pad_exists = False

    # check if the new pad already exists
    try:
        e_pad.getText(padID=new_pad_name)

        # if you are here is exists
        pad_exists = True

    except EtherpadException:
        log_this('', True)

    except Exception as ex:
        log_error(str(ex))

    # delete existing pad
    try:
        if pad_exists and should_delete_existing():
            e_pad.deletePad(padID=new_pad_name)

    except EtherpadException as e:
        log_error(e.message)

    except Exception as ex:
        log_error(str(ex))


    try:
        # create the new pad
        original_text = e_pad.getText(padID=original_page_name)

        # only do volume 1 at this time
        test_text = original_text['text']
        match = VOLUMEREGEX.match(test_text)
        if not force and not match:
            return

        original_html = e_pad.getHTML(padID=original_page_name)

        # update intermal links to other tA pages in this namespace
        new_text = original_html['html'].replace(u'&#x2F;p&#x2F;ta-',
                                                 u'&#x2F;p&#x2F;' + NEW_LANGUAGE_CODE + u'-ta-')

        new_text = new_text.replace(u'[[en:ta:', u'[[' + NEW_LANGUAGE_CODE + u':ta:')
        new_text = new_text.replace(u'[[:en:ta:', u'[[:' + NEW_LANGUAGE_CODE + u':ta:')
        new_text = new_text.replace(u'[[en:ta|', u'[[' + NEW_LANGUAGE_CODE + u':ta|')
        new_text = new_text.replace(u'[[:en:ta|', u'[[:' + NEW_LANGUAGE_CODE + u':ta|')
        new_text = new_text.replace(u'<br><strong>namespace:</strong> en<br>', u'<br><strong>namespace:</strong> ' + NEW_LANGUAGE_CODE + u'<br>')

        # undo the change to hi-ta-modules-template
        new_text = new_text.replace(NEW_LANGUAGE_CODE + u'-ta-modules-template', u'ta-modules-template')

        e_pad.createPad(padID=new_pad_name)
        e_pad.setHTML(padID=new_pad_name, html=new_text)

    except EtherpadException as e:
        log_error(e.message)

    except Exception as ex:
        log_error(str(ex))

    return


def should_delete_existing():
    global DELETE_EXISTING

    # if instructed to not delete pages
    if DELETE_EXISTING == 0:
        return False

    if DELETE_EXISTING == 1:
        return True

    # prompt user to delete or not
    user_input = raw_input('Delete existing page (y|N): ')

    if user_input == 'y':

        # prompt to delete all existing and not ask again
        user_input = raw_input('Delete all existing pages without asking (y|N): ')

        if user_input == 'y':
            DELETE_EXISTING = 1

        return True

    else:

        # prompt user to not delete existing and not ask again
        user_input = raw_input('Do not delete any existing pages (y|N): ')

        if user_input == 'y':
            DELETE_EXISTING = 0

        return False


if __name__ == '__main__':

    log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)
    log_this('Opening Etherpad', True)

    # process input args
    parser = argparse.ArgumentParser(description='Copies English tA Etherpad pages to a new language')
    parser.add_argument('-l', '--lang', help='Language Code')
    parser.add_argument('-e', '--err', help='1=Continue on error, 0=Prompt on error', default=0, type=int)
    parser.add_argument('-d', '--delete', help='1=Delete existing pages, 0=Do not delete existing pages', type=int)
    args = parser.parse_args()

    # prompt user for language code if not supplied on the command line
    if not args.lang:
        lang_code = raw_input('Enter the target language code: ')
        if lang_code:
            args.lang = lang_code

    # if no language code supplied, exit
    if not args.lang:
        log_this('Exiting because no language code was supplied.', True)
        sys.exit(1)

    NEW_LANGUAGE_CODE = args.lang
    CONTINUE_ON_ERROR = args.err

    if args.delete is not None:
        DELETE_EXISTING = args.delete

    ta_pages = None

    with SelfClosingEtherpad() as ep:
        text = ep.getText(padID='ta-modules')
        create_new_page(ep, 'ta-modules', True)
        ta_sections = parse_ta_modules(text['text'])
        ta_pages = get_ta_pages(ep, ta_sections)

    # remember last_checked for the next time
    if ERROR_COUNT > 0:
        if ERROR_COUNT == 1:
            log_this('1 error has been logged', True)
        else:
            log_this(str(ERROR_COUNT) + ' errors have been logged', True)

    log_this('Finished copying', True)
