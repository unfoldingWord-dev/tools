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
#

import codecs
from datetime import datetime
from etherpad_lite import EtherpadLiteClient, EtherpadException
from itertools import ifilter
import os
import re
import sys
import yaml

NAMESPACES = ['hi', 'ru', 'tr']
LOGDIR = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground'
BADLINKREGEX = re.compile(r"(.*?)(\[\[?)(:?en:ta:?)(.*?)(]]?)(.*?)", re.DOTALL | re.MULTILINE | re.UNICODE)
YAMLREGEX = re.compile(r"(---\s*\n)(.+?)(^-{3}\s*\n)+?(.*)$", re.DOTALL | re.MULTILINE)

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
#


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

        if name.lower().startswith('proc'):
            return 'Process'

        return name


class PageData(object):
    def __init__(self, section_name, page_id, yaml_data, page_text):
        self.section_name = section_name
        self.page_id = page_id
        self.yaml_data = yaml_data
        self.page_text = page_text


class PageGenerator(object):
    def __init__(self, namespace, root_page_id):
        global LOGDIR

        self.namespace = namespace
        self.root_page_id = root_page_id

        self.question_label = 'This module answers the question:'
        self.recommend_label = 'Next we recommend you learn about:'
        self.depends_label = 'Before you start this module have you learned about:'
        self.error_count = 0
        self.process_volumes = [1, 2]

        self.log_file = LOGDIR + '/' + root_page_id + '_import.log.txt'
        if os.path.exists(self.log_file):
            os.remove(self.log_file)


    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_val, trace):
        return

    def log_this(self, string_to_log, top_level=False):
        print string_to_log
        if top_level:
            msg = u'\n=== {0} ==='.format(string_to_log)
        else:
            msg = u'\n  * {0}'.format(string_to_log)

        with codecs.open(self.log_file, 'a', 'utf-8') as file_out:
            file_out.write(msg)

    def log_error(self, string_to_log):

        self.error_count += 1
        self.log_this(u'<font inherit/inherit;;#bb0000;;inherit>{0}</font>'.format(string_to_log))

    def get_page_yaml_data(self, raw_yaml_text, skip_checks=False):

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
                self.log_error('Bad yaml format => ' + part)
                return None

            # try to parse
            # noinspection PyBroadException
            try:
                parsed = yaml.load(part)

            except:
                self.log_error('Not able to parse yaml value => ' + part)
                return None

            if not isinstance(parsed, dict):
                self.log_error('Yaml parse did not return the expected type => ' + part)
                return None

            # add the successfully parsed value to the dictionary
            for key in parsed.keys():
                returnval[key] = parsed[key]

        if not skip_checks and not self.check_yaml_values(returnval):
            returnval['invalid'] = True

        return returnval

    def get_ta_pages(self, e_pad, sections):
        """

        :param e_pad: SelfClosingEtherpad
        :param sections: SectionData[]
        :return: PageData[]
        """

        global YAMLREGEX

        pages = []

        for section in sections:
            section_key = section.name

            for pad_id in section.page_list:

                self.log_this('Retrieving page: ' + section_key.lower() + ':' + pad_id, True)

                # get the page
                try:
                    page_raw = e_pad.getText(padID=pad_id)
                    match = YAMLREGEX.match(page_raw['text'])
                    if match:

                        # check for valid yaml data
                        yaml_data = self.get_page_yaml_data(match.group(2))
                        if yaml_data is None:
                            continue

                        if yaml_data == {}:
                            self.log_error('No yaml data found for ' + pad_id)
                            continue

                        # check if we are processing this volume
                        if yaml_data['volume'] in self.process_volumes:
                            pages.append(PageData(section_key, pad_id, yaml_data, match.group(4)))

                    else:
                        self.log_error('Yaml header not found ' + pad_id)

                except EtherpadException as e:
                    self.log_error(e.message)

                except Exception as ex:
                    self.log_error(str(ex))

        return pages

    def check_yaml_values(self, yaml_data):

        returnval = True

        # check the required yaml values
        if not self.check_value_is_valid_int('volume', yaml_data):
            self.log_error('Volume value is not valid.')
            returnval = False

        if not self.check_value_is_valid_string('manual', yaml_data):
            self.log_error('Manual value is not valid.')
            returnval = False

        if not self.check_value_is_valid_string('slug', yaml_data):
            self.log_error('Volume value is not valid.')
            returnval = False
        else:
            # slug cannot contain a dash, only underscores
            test_slug = str(yaml_data['slug']).strip()
            if '-' in test_slug:
                self.log_error('Slug values cannot contain hyphen (dash).')
                returnval = False

        if not self.check_value_is_valid_string('title', yaml_data):
            returnval = False

        return returnval

    def check_value_is_valid_string(self, value_to_check, yaml_data):

        if value_to_check not in yaml_data:
            self.log_error('"' + value_to_check + '" data value for page is missing')
            return False

        if not yaml_data[value_to_check]:
            self.log_error('"' + value_to_check + '" data value for page is blank')
            return False

        data_value = yaml_data[value_to_check]

        if not isinstance(data_value, str) and not isinstance(data_value, unicode):
            self.log_error('"' + value_to_check + '" data value for page is not a string')
            return False

        if not data_value.strip():
            self.log_error('"' + value_to_check + '" data value for page is blank')
            return False

        return True

    def make_dependency_chart(self, sections, pages):

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
            self.log_this('Processing page ' + page.section_name.lower() + '/' + page.yaml_data['slug'])

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


            # noinspection PyBroadException

    # noinspection PyBroadException
    def check_value_is_valid_int(self, value_to_check, yaml_data):

        if value_to_check not in yaml_data:
            self.log_error('"' + value_to_check + '" data value for page is missing')
            return False

        if not yaml_data[value_to_check]:
            self.log_error('"' + value_to_check + '" data value for page is blank')
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

    def make_dokuwiki_pages(self, pages):

        pages_generated = 0

        # pages
        for page in pages:
            assert isinstance(page, PageData)

            # check for invalid yaml data
            if 'invalid' in page.yaml_data:
                continue

            try:
                # get the directory name from the yaml data
                page_dir = self.namespace + '/ta/vol' + str(page.yaml_data['volume']).strip()
                page_dir += '/' + str(page.yaml_data['manual']).strip()
                page_dir = page_dir.lower()

                actual_dir = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/' + page_dir
                if not os.path.exists(actual_dir):
                    os.makedirs(actual_dir, 0755)

                # get the file name from the yaml data
                page_file = str(page.yaml_data['slug']).strip().lower()

                self.log_this('Generating Dokuwiki page: [[https://door43.org/' + page_dir + '/' +
                              page_file + '|' + page_dir + '/' + page_file + '.txt]]')

                page_file = actual_dir + '/' + page_file + '.txt'

                # get the markdown
                question = get_yaml_string('question', page.yaml_data)
                dependencies = get_yaml_object('dependencies', page.yaml_data)
                recommended = get_yaml_object('recommended', page.yaml_data)
                page_credits = get_yaml_object('credits', page.yaml_data)

                md = '===== ' + page.yaml_data['title'] + " =====\n\n"

                if question:
                    md += self.question_label + ' ' + question + "\\\\\n"

                if dependencies:
                    md += self.depends_label
                    md += self.output_list(pages, dependencies)
                    md += "\n\n"

                md += page.page_text + "\n\n"
                self.check_bad_links(page.page_text)

                if page_credits:
                    md += '//Credits: ' + page_credits + "//\n\n"

                if recommended:
                    md += self.recommend_label
                    md += self.output_list(pages, recommended)
                    md += "\n\n"

                # write the file
                with codecs.open(page_file, 'w', 'utf-8') as file_out:
                    file_out.write(md)

                pages_generated += 1

            except Exception as ex:
                self.log_error(str(ex))

        self.log_this('Generated ' + str(pages_generated) + ' Dokuwiki pages.', True)

    def check_bad_links(self, page_text):
        matches = BADLINKREGEX.findall(u'{0}'.format(page_text).replace(u'–', u'-'))

        # check for vol1 or vol2
        for match in matches:
            if len(match[3]) > 3 and match[3][:3] != u'vol':
                self.log_error(u'Bad link => {0}{1}'.format(match[2], match[3]))


    def output_list(self, pages, option_list):
        md = ''

        if isinstance(option_list, list):
            for option in option_list:
                link = self.get_page_link_by_slug(pages, option)
                if link:
                    md += "\n  * " + link
                else:
                    self.log_error('Linked page not found: ' + option)
        else:
            link = self.get_page_link_by_slug(pages, option_list)
            if link:
                md += ' ' + link
            else:
                self.log_error('Linked page not found: ' + option_list)

        return md


    def get_page_url(self, page):

        page_dir = self.namespace + ':ta:vol' + str(page.yaml_data['volume']).strip()
        page_dir += ':' + str(page.yaml_data['manual']).strip()
        page_dir = page_dir.lower()

        page_file = str(page.yaml_data['slug']).strip().lower()

        return page_dir + ':' + page_file


    def get_page_link_by_slug(self, pages, slug):
        found = [page for page in pages if page.yaml_data['slug'].strip().lower() == slug.strip().lower()]
        if len(found) == 0:
            return ''

        return '[[' + self.get_page_url(found[0]) + '|' + found[0].yaml_data['title'] + ']]'


    def generate(self):

        self.log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)

        with SelfClosingEtherpad() as ep:
            text = ep.getText(padID=self.root_page_id)

            default_match = YAMLREGEX.match(text['text'])
            if default_match:

                # check for valid yaml data
                default_yaml_data = self.get_page_yaml_data(default_match.group(2), skip_checks=True)
                if default_yaml_data:

                    # get the target namespace
                    self.namespace = get_yaml_string('namespace', default_yaml_data)

                    # get the volumes to process
                    volumes = get_yaml_object('generate_volumes', default_yaml_data)
                    if volumes:
                        self.process_volumes = volumes

                    # get translated phrases
                    self.question_label = get_yaml_string('question_label', default_yaml_data, self.question_label)
                    self.depends_label = get_yaml_string('depends_label', default_yaml_data, self.depends_label)
                    self.recommend_label = get_yaml_string('recommend_label', default_yaml_data, self.recommend_label)

            # namespace is required
            if not self.namespace:
                self.log_error('FATAL ERROR: No namespace value found')
                self.log_this('Finished updating', True)
                return

            ta_sections = parse_ta_modules(text['text'])
            ta_pages = self.get_ta_pages(ep, ta_sections)

            # sort the pages in the order they appear in the contents file
        self.log_this('Sorting pages', True)
        ta_pages = sorted(ta_pages, cmp=compare_pages)

        # generate dependency chart for English
        if self.root_page_id == 'ta-modules':
            self.log_this('Generating dependency chart', True)
            self.make_dependency_chart(ta_sections, ta_pages)

        self.log_this('Generating Dokuwiki pages.', True)
        self.make_dokuwiki_pages(ta_pages)

        # remember last_checked for the next time
        if self.error_count == 0:
            self.log_this('Completed with no errors', True)
        elif self.error_count == 1:
            self.log_this('1 error has been logged', True)
        else:
            self.log_this(str(self.error_count) + ' errors have been logged', True)

        self.log_this('Finished updating', True)


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
        returnval.append(SectionData(section_name, no_dupes, colors[color_index]))
        color_index += 1

    return returnval


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


def compare_pages(page_a, page_b):
    """
    Function used to compare and sort PageData objects
    :param page_a: PageData
    :param page_b: PageData
    :return: int
    """

    test1 = page_a.section_name + '/' + page_a.yaml_data['slug']
    test2 = page_b.section_name + '/' + page_b.yaml_data['slug']

    if test1 > test2:
        return 1

    if test2 > test1:
        return -1

    return 0


if __name__ == '__main__':

    # enable logging for this script
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR, 0755)

    # start with English
    with PageGenerator('en', 'ta-modules') as generator:
        generator.generate()
    log_link = u'ta-modules_import.log'
    log_text = u'[[https://door43.org/playground/' + log_link + u'|' + log_link + u']]\n\n'

    for ns in NAMESPACES:
        with PageGenerator(ns, ns + '-ta-modules') as generator:
            generator.generate()
        log_link = ns + u'-ta-modules_import.log'
        log_text = log_text + u'[[https://door43.org/playground/' + log_link + u'|' + log_link + u']]\n\n'

    # write a log file
    log_text = u'=== Last run finished at: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + \
               u' UTC ===\n' + log_text
    with codecs.open(LOGDIR + '/ta_import.log.txt', 'w', 'utf-8') as log_file_out:
        log_file_out.write(log_text)
