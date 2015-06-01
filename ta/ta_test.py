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
import re
import sys
import yaml
from etherpad_lite import EtherpadLiteClient, EtherpadException


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


class PageData(object):
    def __init__(self, section_name, page_id, yaml_data, page_text):
        self.section_name = section_name
        self.page_id = page_id
        self.yaml_data = yaml_data
        self.page_text = page_text


def parse_ta_modules(raw_text):
    """
    Returns a dictionary containing the URLs in each major section
    :param raw_text: str
    :rtype: {}
    """

    returnval = {}

    # remove everything before the first ======
    pos = raw_text.find("\n======")
    tmpstr = raw_text[pos+7:]

    # break at "\n======" for major sections
    arr = tmpstr.split("\n======")
    for itm in arr:

        # split section at line breaks
        lines = filter(None, itm.splitlines())

        # section name is the first item
        section = lines[0].replace('=', '').strip()

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
        returnval[section] = no_dupes

    return returnval


def get_ta_pages(e_pad, sections):
    """

    :param e_pad: SelfClosingEtherpad
    :param sections: {}
    :return: []
    """

    regex = re.compile(r"(---\s*\n)(.+)(---\s*\n)(.*)$", re.DOTALL)

    pages = []

    for section_key in sections.keys():

        for pad_id in sections[section_key]:

            # get the page
            try:
                page_raw = e_pad.getText(padID=pad_id)
                match = regex.match(page_raw['text'])
                if match:
                    pages.append(PageData(section_key, pad_id, yaml.load(match.group(2)), match.group(4)))
                else:
                    print 'Not able to retrieve ' + pad_id

            except EtherpadException as e:
                print e.message + ': ' + pad_id

    return pages


def make_dependency_chart(sections, pages):

    chart_lines = []
    chart_file = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/en/ta/dependencies.txt'

    # header
    chart_lines.append("<graphviz dot right>\ndigraph finite_state_machine {\n")
    chart_lines.append("rankdir=BT;\n")
    chart_lines.append("size=\"9,5\";\n")

    # sections
    chart_lines.append("")
    for section_key in sections.keys():
        chart_lines.append(section_key)

    # pages
    for page in pages:
        chart_lines.append("")

    chart_lines.append("")
    chart_lines.append("")
    chart_lines.append("")

    chart_lines.append("}\n</graphviz>\n")
    chart_lines.append("~~NOCACHE~~\n")


if __name__ == '__main__':

    with SelfClosingEtherpad() as ep:

        text = ep.getText(padID='ta-modules')
        ta_sections = parse_ta_modules(text['text'])
        ta_pages = get_ta_pages(ep, ta_sections)
        make_dependency_chart(ta_sections, ta_pages)
