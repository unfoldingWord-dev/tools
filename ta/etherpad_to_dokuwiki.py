#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#
#
import atexit
import codecs
from datetime import datetime
from etherpad_lite import EtherpadLiteClient, EtherpadException
from itertools import ifilter
import logging
import os
import re
import sys
import time
import yaml

LOGFILE = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/ta_import.log.txt'

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

error_count = 0

# enable logging for this script
log_dir = os.path.dirname(LOGFILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, 0755)

if os.path.exists(LOGFILE):
    os.remove(LOGFILE)
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format="%(message)s")


@atexit.register
def exit_logger():
    logging.shutdown()


class SelfClosingEtherpad(EtherpadLiteClient):
    """
    This class is here to enable with...as functionality for the EtherpadLiteClient
    """
    def __init__(self):
        super(SelfClosingEtherpad, self).__init__()

        # noinspection PyBroadException
        try:
            pw = open('/usr/share/httpd/.ssh/ep_api_key', 'r').read().strip()
            self.base_params = {'apikey': pw}
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
    def __init__(self, name, page_list=None, color='yellow'):
        if not page_list:
            page_list = []
        self.name = self.get_name(name)
        self.color = color
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

        if name.lower().startswith('test'):
            return 'Test'

        return name


class PageData(object):
    def __init__(self, section_name, page_id, yaml_data, page_text):
        self.section_name = section_name
        self.page_id = page_id
        self.yaml_data = yaml_data
        self.page_text = page_text


def log_this(string_to_log, top_level=False):
    print string_to_log
    if top_level:
        msg = u'\n=== {0} ==='.format(string_to_log)
    else:
        msg = u'  * {0}'.format(string_to_log)

    logging.info(msg)


def log_error(string_to_log):

    global error_count
    error_count += 1
    log_this(string_to_log)


def quote_str(string_value):
    return '"' + string_value.replace('"', '') + '"'


def parse_ta_modules(raw_text):
    """
    Returns a dictionary containing the URLs in each major section
    :param raw_text: str
    :rtype: SectionData[]
    """

    returnval = []
    colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#99ffff', '#ff99ff', '#cccccc']
    color_index = 0

    # remove everything before the first ======
    pos = raw_text.find("\n======")
    tmpstr = raw_text[pos+7:]

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
        returnval.append(SectionData(section_name, no_dupes, colors[color_index]))
        color_index += 1

    return returnval


def get_last_changed(e_pad, sections):
    """

    :param e_pad: SelfClosingEtherpad
    :param sections: SectionData[]
    :return: int
    """

    last_change = 0

    for section in sections:

        for pad_id in section.page_list:

            # get last edited
            try:
                page_info = e_pad.getLastEdited(padID=pad_id)
                if page_info['lastEdited'] > last_change:
                    last_change = page_info['lastEdited']

            except EtherpadException as e:
                if e.message != 'padID does not exist':
                    log_error(e.message + ': ' + pad_id)

    # etherpad returns lastEdited in milliseconds
    return int(last_change / 1000)


def get_page_yaml_data(pad_id, raw_yaml_text):

    returnval = {}

    # convert windows line endings
    cleaned = raw_yaml_text.replace("\r\n", "\n")

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

    if not check_yaml_values(pad_id, returnval):
        returnval['invalid'] = True

    return returnval


def get_ta_pages(e_pad, sections):
    """

    :param e_pad: SelfClosingEtherpad
    :param sections: SectionData[]
    :return: PageData[]
    """

    regex = re.compile(r"(---\s*\n)(.+)(^-{3}\s*\n)+?(.*)$", re.DOTALL | re.MULTILINE)

    pages = []

    for section in sections:
        section_key = section.name

        for pad_id in section.page_list:

            log_this('Processing page: ' + pad_id, True)

            # get the page
            try:
                page_raw = e_pad.getText(padID=pad_id)
                match = regex.match(page_raw['text'])
                if match:

                    # check for valid yaml data
                    yaml_data = get_page_yaml_data(pad_id, match.group(2))
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


def make_dependency_chart(sections, pages):

    chart_lines = []
    dir_name = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ta'
    # dir_name = '/var/www/projects/dokuwiki/data/gitrepo/pages/en/ta'
    chart_file = dir_name + '/dependencies.txt'

    # header
    chart_lines.append('<graphviz dot right>\ndigraph finite_state_machine {')
    chart_lines.append('rankdir=BT;')
    chart_lines.append('graph [fontname="Arial"];')
    chart_lines.append('node [shape=oval, fontname="Arial", fontsize=12, style=filled, fillcolor="#dddddd"];')
    chart_lines.append('edge [arrowsize=1.4];')

    # sections
    for section in sections:
        chart_lines.append(quote_str(section.name) + ' [fillcolor="' + section.color + '"]')

    # pages
    for page in pages:
        assert isinstance(page, PageData)
        log_this('Processing page ' + page.page_id)

        # check for invalid yaml data
        if 'invalid' in page.yaml_data:
            continue

        # get the color for the section
        fill_color = next(ifilter(lambda sec: sec.name == page.section_name, sections), '#dddddd').color

        # create the node
        chart_lines.append(quote_str(page.yaml_data['slug']) + ' [fillcolor="' + fill_color + '"]')

        # dependency arrows
        if 'dependencies' in page.yaml_data:
            dependencies = page.yaml_data['dependencies']
            if isinstance(dependencies, list):
                for dependency in dependencies:
                    chart_lines.append(quote_str(dependency) + ' -> ' + quote_str(page.yaml_data['slug']))

            else:
                if isinstance(dependencies, str):
                    chart_lines.append(quote_str(dependencies) + ' -> ' + quote_str(page.yaml_data['slug']))

                else:
                    chart_lines.append(quote_str(page.section_name) + ' -> ' + quote_str(page.yaml_data['slug']))

        else:
            chart_lines.append(quote_str(page.section_name) + ' -> ' + quote_str(page.yaml_data['slug']))

    # footer
    chart_lines.append('}\n</graphviz>')
    chart_lines.append('~~NOCACHE~~')

    # join the lines
    file_text = "\n".join(chart_lines)

    # write the Graphviz file
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    with codecs.open(chart_file, 'w', 'utf-8') as file_out:
        file_out.write(file_text)


def check_yaml_values(pad_id, yaml_data):

    returnval = True

    # check the required yaml values
    if not check_value_is_valid_int('volume', yaml_data):
        returnval = False

    if not check_value_is_valid_string('manual', yaml_data):
        returnval = False

    if not check_value_is_valid_string('slug', yaml_data):
        returnval = False
    else:
        # slug cannot contain a dash, only underscores
        test_slug = str(yaml_data['slug']).strip()
        if '-' in test_slug:
            log_error('Slug values cannot contain hyphen (dash): ' + pad_id)
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


def get_yaml_string(value_name, yaml_data):

    if value_name not in yaml_data:
        return ''

    if not yaml_data[value_name]:
        return ''

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


def make_dokuwiki_pages(pages):

    pages_generated = 0

    # pages
    for page in pages:
        assert isinstance(page, PageData)

        # check for invalid yaml data
        if 'invalid' in page.yaml_data:
            continue

        try:
            # get the directory name from the yaml data
            page_dir = 'en/ta/vol' + str(page.yaml_data['volume']).strip()
            page_dir += '/' + str(page.yaml_data['manual']).strip()
            page_dir = page_dir.lower()

            actual_dir = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/' + page_dir
            if not os.path.exists(actual_dir):
                os.makedirs(actual_dir, 0755)

            # get the file name from the yaml data
            page_file = str(page.yaml_data['slug']).strip().lower()

            log_this('Generating Dokuwiki page: [[https://door43.org/' + page_dir
                     + '/' + page_file + '|' + page_dir + '/' + page_file + '.txt]]')

            page_file = actual_dir + '/' + page_file + '.txt'

            # get the markdown
            question = get_yaml_string('question', page.yaml_data)
            dependencies = get_yaml_object('dependencies', page.yaml_data)
            recommended = get_yaml_object('recommended', page.yaml_data)

            md = '===== ' + page.yaml_data['title'] + " =====\n\n"

            if question:
                md += 'This module answers the question: ' + question + "\\\\\n"

            if dependencies:
                md += 'Before you start this module have you learned about:'
                md += output_list(pages, dependencies)
                md += "\n\n"

            md += page.page_text + "\n\n"

            if recommended:
                md += 'Next we recommend you learn about:'
                md += output_list(pages, recommended)
                md += "\n\n"

            # write the file
            with codecs.open(page_file, 'w', 'utf-8') as file_out:
                file_out.write(md)

            pages_generated += 1

        except Exception as ex:
            log_error(str(ex))

    log_this('Generated ' + str(pages_generated) + ' Dokuwiki pages.', True)


def output_list(pages, option_list):

    md = ''

    if isinstance(option_list, list):
        if len(option_list) == 1:
            link = get_page_link_by_slug(pages, option_list[0])
            if link:
                md += ' ' + link
            else:
                log_error('Linked page not found: ' + option_list[0])
        else:
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
    found = [page for page in pages if page.yaml_data['slug'].strip().lower() == slug]
    if len(found) == 0:
        return ''

    return '[[' + get_page_url(found[0]) + '|' + found[0].yaml_data['title'] + ']]'


def get_page_url(page):
    page_dir = 'en/ta/vol' + str(page.yaml_data['volume']).strip()
    page_dir += '/' + str(page.yaml_data['manual']).strip()
    page_dir = page_dir.lower()

    page_file = str(page.yaml_data['slug']).strip().lower()

    return 'https://door43.org/' + page_dir + '/' + page_file


if __name__ == '__main__':

    log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)
    log_this('Checking for changes in Etherpad', True)

    # get the last run time
    last_checked = 0
    last_file = '.lastEpToDwRun'
    if os.path.isfile(last_file):
        with open(last_file, 'r') as f:
            last_checked = int(float(f.read()))

    has_changed = False
    ta_pages = None

    with SelfClosingEtherpad() as ep:

        text = ep.getText(padID='ta-modules')
        ta_sections = parse_ta_modules(text['text'])
        if get_last_changed(ep, ta_sections) > last_checked:
            has_changed = True
            log_this('Changes found')

        if has_changed:
            ta_pages = get_ta_pages(ep, ta_sections)

    if has_changed:
        log_this('Generating dependency chart', True)
        make_dependency_chart(ta_sections, ta_pages)
        log_this('Generating Dokuwiki pages.', True)
        make_dokuwiki_pages(ta_pages)

    # remember last_checked for the next time
    if error_count == 0:
        with open(last_file, 'w') as f:
            f.write(str(time.time()))
    else:
        log_this(str(error_count) + ' errors have been logged', True)

    if has_changed:
        log_this('Finished updating', True)
    else:
        log_this('No changes found', True)
