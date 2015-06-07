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
from etherpad_lite import EtherpadLiteClient, EtherpadException
from itertools import ifilter
import logging
import os
import re
import sys
import time
import yaml

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
logging.basicConfig(filename='event.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

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


def log_this(string_to_log, is_error=False):
    print string_to_log

    if is_error:
        logging.error(string_to_log)
    else:
        logging.info(string_to_log)


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
                    log_this(e.message + ': ' + pad_id, True)

    # etherpad returns lastEdited in milliseconds
    return int(last_change / 1000)


def get_ta_pages(e_pad, sections):
    """

    :param e_pad: SelfClosingEtherpad
    :param sections: SectionData[]
    :return: PageData[]
    """

    regex = re.compile(r"(---\s*\n)(.+)(---\s*\n)(.*)$", re.DOTALL)

    pages = []

    for section in sections:
        section_key = section.name

        for pad_id in section.page_list:

            # get the page
            try:
                page_raw = e_pad.getText(padID=pad_id)
                match = regex.match(page_raw['text'])
                if match:
                    pages.append(PageData(section_key, pad_id, yaml.load(match.group(2)), match.group(4)))
                else:
                    log_this('Not able to retrieve ' + pad_id)

            except EtherpadException as e:
                log_this(e.message + ': ' + pad_id, True)

    return pages


def make_dependency_chart(sections, pages):

    chart_lines = []
    dir_name = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ta'
    # dir_name = '/var/www/projects/dokuwiki/data//gitrepo/pages/en/ta'
    chart_file = dir_name + '/dependencies.txt'

    # header
    chart_lines.append('<graphviz dot right>\ndigraph finite_state_machine {')
    chart_lines.append('rankdir=BT;')
    # chart_lines.append('size="9,11";')
    chart_lines.append('graph [fontname="Arial"];')
    chart_lines.append('node [shape=oval, fontname="Arial", fontsize=12, style=filled, fillcolor="#dddddd"];')
    chart_lines.append('edge [arrowsize=1.4];')

    # sections
    for section in sections:
        chart_lines.append(quote_str(section.name) + ' [fillcolor="' + section.color + '"]')

    # pages
    for page in pages:
        assert isinstance(page, PageData)
        print 'Processing page: ' + page.page_id

        if 'slug' in page.yaml_data:

            # get the color for the section
            fill_color = next(ifilter(lambda sec: sec.name == page.section_name, sections), None).color

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


def make_dokuwiki_pages(pages):

    # pages
    for page in pages:
        assert isinstance(page, PageData)

        page_file = ''
        data_good = False

        # get the file name from the yaml data
        if 'volume' in page.yaml_data and page.yaml_data['volume'] and str(page.yaml_data['volume']).strip():
            page_file = 'en/ta/vol' + str(page.yaml_data['volume']).strip()

            if 'manual' in page.yaml_data and page.yaml_data['manual'] and str(page.yaml_data['manual']).strip():
                page_file += '/' + str(page.yaml_data['manual']).strip()

                if 'slug' in page.yaml_data and page.yaml_data['slug'] and str(page.yaml_data['slug']).strip():
                    page_file += '/' + str(page.yaml_data['slug']).strip()
                    data_good = True

        if data_good:
            print 'Generating Dokuwiki page: ' + page_file
        else:
            log_this('Yaml data for page is incomplete: ' + page.page_id)


if __name__ == '__main__':

    log_this('Checking for changes in Etherpad.')

    # get the last run time
    last_checked = 0
    last_file = '.lastEpToDwRun'
    if os.path.isfile(last_file):
        with open(last_file, 'r') as f:
            last_checked = int(float(f.read()))

    haschanged = False
    ta_pages = None

    with SelfClosingEtherpad() as ep:

        text = ep.getText(padID='ta-modules')
        ta_sections = parse_ta_modules(text['text'])
        if get_last_changed(ep, ta_sections) > last_checked:
            haschanged = True

        if haschanged:
            ta_pages = get_ta_pages(ep, ta_sections)

    if haschanged:
        log_this('Generating dependency chart.')
        make_dependency_chart(ta_sections, ta_pages)
        log_this('Generating Dokuwiki pages.')
        make_dokuwiki_pages(ta_pages)

    # remember last_checked for the next time
    with open(last_file, 'w') as f:
        f.write(str(time.time()))

    if haschanged:
        log_this('Finished updating.')
    else:
        log_this('No changes found.')
