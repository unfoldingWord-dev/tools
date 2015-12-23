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
import yaml


NEW_LANGUAGE_CODE = ''
CONTINUE_ON_ERROR = 0
ERROR_COUNT = 0

LOGFILE = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/ta_new_language_dokuwiki.log.txt'
DEPENDS_LABEL = u'Before you start this module have you learned about:'
QUESTION_LABEL = u'This module answers the question:'
RECOMMEND_LABEL = u'Next we recommend you learn about:'

ADDITIONAL_PAGES = [u'en:ta:vol1:toc']

VOLUMEREGEX = re.compile(r".*(volume:\s*[1]+).*", re.DOTALL | re.MULTILINE | re.UNICODE)
YAMLREGEX = re.compile(r"(---\s*\n)(.+?)(^-{3}\s*\n)+?(.*)$", re.DOTALL | re.MULTILINE)
BADLINKREGEX = re.compile(r"(.*?)(\[\[?)(:?en:ta:?)(.*?)(]]?)(.*?)", re.DOTALL | re.MULTILINE | re.UNICODE)

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


class PageData(object):
    def __init__(self, section_name, page_id, yaml_data, page_text):
        self.section_name = section_name
        self.page_id = page_id
        self.yaml_data = yaml_data
        self.page_text = page_text


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

    user_input = raw_input('Continue after error [y|N|a(yes to all)]: ')

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
                page_text = create_new_page(e_pad, pad_id)
                if page_text is None:
                    continue

                match = YAMLREGEX.match(page_text)
                if match:

                    # check for valid yaml data
                    yaml_data = get_page_yaml_data(match.group(2))
                    if yaml_data is None:
                        continue

                    if yaml_data == {}:
                        log_error('No yaml data found for ' + pad_id)
                        continue

                    pages.append(PageData(section_key, pad_id, yaml_data, match.group(4)))

                else:
                    log_error('Yaml header not found ' + pad_id)

            except EtherpadException as e:
                log_error(e.message)

            except Exception as ex:
                log_error(str(ex))

    return pages


def create_new_page(e_pad, original_page_name, force=False):

    new_text = None

    try:
        # create the new pad
        original_text = e_pad.getText(padID=original_page_name)

        # only do volume 1 at this time
        new_text = original_text['text']
        match = VOLUMEREGEX.match(new_text)
        if not force and not match:
            return None

        new_text = replace_language_code(new_text)

    except EtherpadException as e:
        log_error(e.message)

    except Exception as ex:
        log_error(str(ex))

    return new_text


def replace_language_code(page_text):
    global NEW_LANGUAGE_CODE

    new_text = page_text.replace(u'[[en:ta:', u'[[' + NEW_LANGUAGE_CODE + u':ta:')
    new_text = new_text.replace(u'[[:en:ta:', u'[[:' + NEW_LANGUAGE_CODE + u':ta:')
    new_text = new_text.replace(u'[[en:ta|', u'[[' + NEW_LANGUAGE_CODE + u':ta|')
    new_text = new_text.replace(u'[[:en:ta|', u'[[:' + NEW_LANGUAGE_CODE + u':ta|')
    new_text = new_text.replace(u'{{page>en:ta:', u'{{page>' + NEW_LANGUAGE_CODE + u':ta:')

    return new_text


def get_page_yaml_data(raw_yaml_text, skip_checks=False):

    returnval = {}

    # convert windows line endings
    cleaned = raw_yaml_text.replace("\r\n", "\n")

    # replace curly quotes
    cleaned = cleaned.replace(u'“', '"').replace(u'”', '"')

    # split into individual values, removing empty lines
    parts = filter(bool, cleaned.split("\n"))

    # check each value
    for part in parts:

        # split into name and value
        pieces = part.split(':', 1)

        # must be 2 pieces
        if len(pieces) != 2:
            log_error('Bad yaml format => ' + part)
            return None

        # try to parse
        # noinspection PyBroadException
        try:
            parsed = yaml.load(part)

        except:
            log_error('Not able to parse yaml value => ' + part)
            return None

        if not isinstance(parsed, dict):
            log_error('Yaml parse did not return the expected type => ' + part)
            return None

        # add the successfully parsed value to the dictionary
        for key in parsed.keys():
            returnval[key] = parsed[key]

    if not skip_checks and not check_yaml_values(returnval):
        returnval['invalid'] = True

    return returnval


def check_yaml_values(yaml_data):

    returnval = True

    # check the required yaml values
    if not check_value_is_valid_int('volume', yaml_data):
        log_error('Volume value is not valid.')
        returnval = False

    if not check_value_is_valid_string('manual', yaml_data):
        log_error('Manual value is not valid.')
        returnval = False

    if not check_value_is_valid_string('slug', yaml_data):
        log_error('Volume value is not valid.')
        returnval = False
    else:
        # slug cannot contain a dash, only underscores
        test_slug = str(yaml_data['slug']).strip()
        if '-' in test_slug:
            log_error('Slug values cannot contain hyphen (dash).')
            returnval = False

    if not check_value_is_valid_string('title', yaml_data):
        returnval = False

    return returnval


def check_value_is_valid_string(value_to_check, yaml_data):

    if value_to_check not in yaml_data:
        log_error('"' + value_to_check + '" data value for page is missing')
        return False

    if not yaml_data[value_to_check]:
        log_error('"' + value_to_check + '" data value for page is blank')
        return False

    data_value = yaml_data[value_to_check]

    if not isinstance(data_value, str) and not isinstance(data_value, unicode):
        log_error('"' + value_to_check + '" data value for page is not a string')
        return False

    if not data_value.strip():
        log_error('"' + value_to_check + '" data value for page is blank')
        return False

    return True


# noinspection PyBroadException
def check_value_is_valid_int(value_to_check, yaml_data):

    if value_to_check not in yaml_data:
        log_error('"' + value_to_check + '" data value for page is missing')
        return False

    if not yaml_data[value_to_check]:
        log_error('"' + value_to_check + '" data value for page is blank')
        return False

    data_value = yaml_data[value_to_check]

    if not isinstance(data_value, int):
        try:
            data_value = int(data_value)
        except:
            try:
                data_value = int(float(data_value))
            except:
                return False

    return isinstance(data_value, int)


def make_dokuwiki_pages(pages):
    global NEW_LANGUAGE_CODE
    global DEPENDS_LABEL, QUESTION_LABEL, RECOMMEND_LABEL

    pages_generated = 0

    # pages
    for page in pages:
        assert isinstance(page, PageData)

        # check for invalid yaml data
        if 'invalid' in page.yaml_data:
            continue

        try:
            # get the directory name from the yaml data
            page_dir = NEW_LANGUAGE_CODE + '/ta/vol' + str(page.yaml_data['volume']).strip()
            page_dir += '/' + str(page.yaml_data['manual']).strip()
            page_dir = page_dir.lower()

            actual_dir = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/' + page_dir
            if not os.path.exists(actual_dir):
                os.makedirs(actual_dir, 0755)

            # get the file name from the yaml data
            page_file = str(page.yaml_data['slug']).strip().lower()

            log_this('Generating Dokuwiki page: [[https://door43.org/' + page_dir + '/' +
                     page_file + '|' + page_dir + '/' + page_file + '.txt]]')

            page_file = actual_dir + '/' + page_file + '.txt'

            # get the markdown
            question = get_yaml_string('question', page.yaml_data)
            dependencies = get_yaml_object('dependencies', page.yaml_data)
            recommended = get_yaml_object('recommended', page.yaml_data)
            page_credits = get_yaml_object('credits', page.yaml_data)

            md = '===== ' + page.yaml_data['title'] + " =====\n\n"

            if question:
                md += QUESTION_LABEL + ' ' + question + "\\\\\n"

            if dependencies:
                md += DEPENDS_LABEL
                md += output_list(pages, dependencies)
                md += "\n\n"

            md += page.page_text + "\n\n"
            check_bad_links(page.page_text)

            if page_credits:
                md += '//Credits: ' + page_credits + "//\n\n"

            if recommended:
                md += RECOMMEND_LABEL
                md += output_list(pages, recommended)
                md += "\n\n"

            # write the file
            with codecs.open(page_file, 'w', 'utf-8') as file_out:
                file_out.write(md)

            pages_generated += 1

        except Exception as ex:
            log_error(str(ex))

    pages_generated += copy_additional_pages()

    log_this('Generated ' + str(pages_generated) + ' Dokuwiki pages.', True)


def get_yaml_string(value_name, yaml_data, default_value=''):
    if value_name not in yaml_data:
        return default_value

    if not yaml_data[value_name]:
        return default_value

    data_value = yaml_data[value_name]

    if not isinstance(data_value, str) and not isinstance(data_value, unicode):
        data_value = str(data_value)

    return data_value.strip()


def get_yaml_object(value_name, yaml_data):
    if value_name not in yaml_data:
        return ''

    if not yaml_data[value_name]:
        return ''

    data_value = yaml_data[value_name]

    if not isinstance(data_value, str) and not isinstance(data_value, unicode):
        return data_value

    return data_value.strip()


def output_list(pages, option_list):
    md = ''

    if isinstance(option_list, list):
        for option in option_list:
            link = get_page_link_by_slug(pages, option)
            if link:
                md += "\n  * " + link
            else:
                log_error('Linked page not found: ' + option)
    else:
        link = get_page_link_by_slug(pages, option_list)
        if link:
            md += ' ' + link
        else:
            log_error('Linked page not found: ' + option_list)

    return md


def get_page_link_by_slug(pages, slug):
    found = [page for page in pages if page.yaml_data['slug'].strip().lower() == slug.strip().lower()]
    if len(found) == 0:
        return ''

    return '[[' + get_page_url(found[0]) + '|' + found[0].yaml_data['title'] + ']]'


def get_page_url(page):
    global NEW_LANGUAGE_CODE

    page_dir = NEW_LANGUAGE_CODE + ':ta:vol' + str(page.yaml_data['volume']).strip()
    page_dir += ':' + str(page.yaml_data['manual']).strip()
    page_dir = page_dir.lower()

    page_file = str(page.yaml_data['slug']).strip().lower()

    return page_dir + ':' + page_file


def check_bad_links(page_text):
    global BADLINKREGEX

    matches = BADLINKREGEX.findall(u'{0}'.format(page_text).replace(u'–', u'-'))

    # check for vol1 or vol2
    for match in matches:
        if len(match[3]) > 3 and match[3][:3] != u'vol':
            log_error(u'Bad link => {0}{1}'.format(match[2], match[3]))


def copy_additional_pages():
    global ADDITIONAL_PAGES, NEW_LANGUAGE_CODE

    base_dir = u'/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/'
    page_count = 0

    for page in ADDITIONAL_PAGES:

        source = base_dir + page.replace(u':', u'/') + u'.txt'

        if not os.path.isfile(source):
            log_this(u'File not found: ' + source, True)
            continue

        target = base_dir + NEW_LANGUAGE_CODE + page[2:].replace(u':', u'/') + u'.txt'

        with codecs.open(source, 'r') as myfile:
            source_text = myfile.read()

        target_text = replace_language_code(source_text)

        with codecs.open(target, 'w', 'utf-8') as file_out:
            file_out.write(target_text)

        page_count += 1

    return page_count


if __name__ == '__main__':

    log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)
    log_this('Opening Etherpad', True)

    # process input args
    parser = argparse.ArgumentParser(description='Copies English tA Etherpad pages to a new language')
    parser.add_argument('-l', '--lang', help='Language Code')
    parser.add_argument('-e', '--err', help='1=Continue on error, 0=Prompt on error', default=0, type=int)
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

    ta_pages = None

    # get the pages from etherpad
    with SelfClosingEtherpad() as ep:
        text = ep.getText(padID='ta-modules')
        create_new_page(ep, 'ta-modules', True)
        ta_sections = parse_ta_modules(text['text'])
        ta_pages = get_ta_pages(ep, ta_sections)

    # make dokuwiki pages for the new language
    make_dokuwiki_pages(ta_pages)

    # finish logging the results
    if ERROR_COUNT > 0:
        if ERROR_COUNT == 1:
            log_this('1 error has been logged', True)
        else:
            log_this(str(ERROR_COUNT) + ' errors have been logged', True)

    log_this('Finished copying', True)
    log_this('Log file: ' + LOGFILE, True)
