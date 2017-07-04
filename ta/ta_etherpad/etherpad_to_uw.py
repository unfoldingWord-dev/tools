#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
# This script gets the latest translationAcademy documents from etherpad and creates an HTML fragment for the
# unfoldingword.org website
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Phil Hopper <phillip_hopper@wycliffeassociates.org>
#
#
import atexit
import codecs
from datetime import datetime
from functools import partial
from etherpad_lite import EtherpadLiteClient, EtherpadException
import logging
import os
import re
import shlex
from subprocess import Popen, PIPE
import sys
import yaml

LOGFILE = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/ta_uw_export.log.txt'
HTMLFILE = '/var/www/projects/unfoldingWord.github.io/_includes/ta_body.html'

H1REGEX = re.compile(r"(.*?)((?:<p>)?======\s*)(.*?)(\s*======(?:</p>)?)(.*?)", re.DOTALL | re.MULTILINE)
H2REGEX = re.compile(r"(.*?)((?:<p>)?=====\s*)(.*?)(\s*=====(?:</p>)?)(.*?)", re.DOTALL | re.MULTILINE)
H3REGEX = re.compile(r"(.*?)((?:<p>)?====\s*)(.*?)(\s*====(?:</p>)?)(.*?)", re.DOTALL | re.MULTILINE)
H4REGEX = re.compile(r"(.*?)((?:<p>)?===\s*)(.*?)(\s*===(?:</p>)?)(.*?)", re.DOTALL | re.MULTILINE)
H5REGEX = re.compile(r"(.*?)((?:<p>)?==\s*)(.*?)(\s*==(?:</p>)?)(.*?)", re.DOTALL | re.MULTILINE)
LINKREGEX = re.compile(r"(.*?)(\[{2}?)(.*?)(\]{2}?)(.*?)", re.DOTALL | re.MULTILINE)
ITALICREGEX = re.compile(r"(.*?)(?<!:)(//)(.*?)(?<!http:|ttps:)(//)(.*?)", re.DOTALL | re.MULTILINE)
BOLDREGEX = re.compile(r"(.*?)(\*\*)(.*?)(\*\*)(.*?)", re.DOTALL | re.MULTILINE)
NLNLREGEX = re.compile(r"(.*?)(\\\\\s*\n\\\\\s*\n)(.*?)", re.DOTALL | re.MULTILINE)
NLREGEX = re.compile(r"(.*?)(\\\\\s*\n)(.*?)", re.DOTALL | re.MULTILINE)
ULREGEX = re.compile(r"(.*?)(?<!\n)(\n\s\s\*)(.+)(?!\n\s\s\*)(.*?)", re.DOTALL | re.MULTILINE)
UL2REGEX = re.compile(r"(.*?)(\n\s\s\*)(.+\n)(?!\s\s)(.*?)", re.DOTALL | re.MULTILINE)
PNGREGEX = re.compile(r"(.*?)(\{\{)(.*?)(\.png)(.*?)(\}\})(.*?)", re.DOTALL | re.MULTILINE)
COLONREGEX = re.compile(r"(.*?)(:[ ]*\n)(?!\n)(.*?)", re.DOTALL | re.MULTILINE)
QUOTEREGEX = re.compile(r"(>)(.*)(\n)")

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

        if name.lower().startswith('proces'):
            return 'Process'

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
                    test_url = match.group(1)[pos + 1:]
                    urls.append(match.group(1)[pos + 1:])
                else:
                    test_url = match.group(1)
                    urls.append(match.group(1))

                # do not add a duplicate
                if test_url not in urls:
                    urls.append(test_url)

        # add the list of URLs to the dictionary
        returnval.append(SectionData(section_name, urls))

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

    if not check_yaml_values(pad_id, returnval):
        returnval['invalid'] = True

    return returnval


def get_vol1_pages(e_pad, sections):
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

                    if not check_value_is_valid_int('volume', yaml_data):
                        continue

                    if int(yaml_data['volume']) != 1:
                        continue

                    pages.append(PageData(section_key, pad_id, yaml_data, match.group(4)))
                else:
                    log_error('Yaml header not found ' + pad_id)

            except EtherpadException as e:
                log_error(e.message)

            except Exception as ex:
                log_error(str(ex))

    return pages


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


def make_docx(pages):
    divs = make_html(pages)
    regex = re.compile(r"^(.*<body>)(.*?)(</body>.*)$", re.DOTALL | re.MULTILINE)

    # pages
    body = u"<div class=\"row\">\n"
    for div in divs:
        body += div + u"\n"

    body += u"</div>\n"

    with codecs.open(HTMLFILE, 'w', 'utf-8') as out_file:
        out_file.write(body)


def markdown_to_html(dokuwiki):
    """
    Runs markdown through pandoc to convert to html
    """

    markdown = dokuwiki_to_markdown(dokuwiki)
    markdown = NLNLREGEX.sub(r'\1\n\n\3', markdown)
    markdown = NLREGEX.sub(r'\1\n\n\3', markdown)
    markdown = ULREGEX.sub(r'\1\n\2\3\4', markdown)
    markdown = UL2REGEX.sub(r'\1\2\3\n\4', markdown)
    markdown = COLONREGEX.sub(r'\1:\n\n\3', markdown)
    markdown = QUOTEREGEX.sub(r'\1\2<br>\3', markdown)

    command = shlex.split('/usr/bin/pandoc -f markdown_phpextra -t html')
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate(markdown.encode('utf-8'))
    html = out.decode('utf-8')

    # fix some things pandoc doesn't convert
    # html = re.sub(LINKREGEX, convert_link, html)
    html = ITALICREGEX.sub(r'\1<em>\3</em>\5', html)
    html = BOLDREGEX.sub(r'\1<strong>\3</strong>\5', html)

    return html


def dokuwiki_to_markdown(dokuwiki):

    markdown = H1REGEX.sub(r'\1# \3 #\5', dokuwiki)
    markdown = H2REGEX.sub(r'\1## \3 ##\5', markdown)
    markdown = H3REGEX.sub(r'\1### \3 ###\5', markdown)
    markdown = H4REGEX.sub(r'\1#### \3 ####\5', markdown)
    markdown = H5REGEX.sub(r'\1##### \3 #####\5', markdown)

    # {{:en:ta:tech:translating_in_ts_-_obs_v2.mp4|Resources Video}}
    # {{:en:ta:ol2sl2sl2tl_small_600-174.png?nolink&600x174}}
    markdown = re.sub(PNGREGEX, convert_png_link, markdown)

    return markdown


def convert_link(match, pages):

    # get_page_link_by_slug
    try:
        parts = match.group(3).split('|')
        if isinstance(parts, list):
            if len(parts) > 1:
                return match.group(1) + '<a href="' + dokuwiki_to_html_link(parts[0]) + '">' + parts[1] + '</a>' + \
                    match.group(5)
            else:
                link_text = parts[0]

        else:
            link_text = parts

        href = dokuwiki_to_html_link(link_text)

        if href[:1] == '#':
            found = [page for page in pages if page.yaml_data['slug'].strip().lower() == href[1:].strip().lower()]
            if len(found) > 0:
                link_text = found[0].yaml_data['title']

        return match.group(1) + '<a href="' + href + '">' + link_text + '</a>' + match.group(5)

    except Exception as ex:
        log_error(str(ex))


def convert_png_link(match):
    # "![{$frame['id']}]({$image_file})\\"
    try:
        parts = match.group(3).split('|')
        if isinstance(parts, list):
            return match.group(1) + '![Image](https://door43.org/_media' + parts[0].replace(':', '/') + '.png)'\
                + match.group(7)
        else:
            return match.group(1) + '![Image](https://door43.org/_media' + parts.replace(':', '/') + '.png)'\
                + match.group(7)

    except Exception as ex:
        log_error(str(ex))


def dokuwiki_to_html_link(dokuwiki_link):

    # if this is already a valid URL, return it unchanged
    if dokuwiki_link[:4].lower() == 'http':
        return dokuwiki_link

    # if this is a dokuwiki link, convert it
    if ':' in dokuwiki_link:
        if dokuwiki_link[:1] == ':':
            dokuwiki_link = dokuwiki_link[1:]

        if 'en:ta:' in dokuwiki_link:
            parts = dokuwiki_link.split(':')
            return u'#' + parts[len(parts) - 1]

        else:
            return 'https://door43.org/' + dokuwiki_link.replace(':', '/')

    return dokuwiki_link


def make_html(pages):
    pages_generated = 0
    slugs = []

    # pages
    for page in pages:
        assert isinstance(page, PageData)

        # check for invalid yaml data
        if 'invalid' in page.yaml_data:
            continue

        try:
            # get the slug from the yaml data
            slug = str(page.yaml_data['slug']).strip().lower()

            log_this('Generating page: ' + slug)

            # get the markdown
            question = get_yaml_string('question', page.yaml_data)
            dependencies = get_yaml_object('dependencies', page.yaml_data)
            recommended = get_yaml_object('recommended', page.yaml_data)

            dw = u'# ' + page.yaml_data['title'] + u'# {#' + slug + u"}\n\n"

            if question:
                dw += u'This module answers the question: ' + question + u"\\\\\n"

            if dependencies:
                dw += u'Before you start this module have you learned about:'
                dw += output_list(pages, dependencies)
                dw += u"\n\n"

            dw += re.sub(LINKREGEX, partial(convert_link, pages=pages), page.page_text) + u"\n\n"

            if recommended:
                dw += u'Next we recommend you learn about:'
                dw += output_list(pages, recommended)
                dw += u"\n\n"

            div = markdown_to_html(dw) + u"\n"

            slugs.append([SectionData.get_name(page.yaml_data['manual']), slug, page.yaml_data['title'], div])

            pages_generated += 1

        except Exception as ex:
            log_error(str(ex))

    # the slugs div
    slugs_div = u'<div class="col-md-3" role="complementary">' + u"\n"
    slugs_div += u'  <nav class="bs-docs-sidebar hidden-print hidden-xs hidden-sm">' + u"\n"
    slugs_div += u'    <ul class="nav bs-docs-sidenav">' + u"\n"

    # the content div
    content_div = u'<div class="col-md-9" role="main">' + u"\n" + u'<a id="top"></a>' + u"\n"

    # build the side nav menu
    #   slug_data[0] = section
    #   slug_data[1] = slug
    #   slug_data[2] = title
    #   slug_data[3] = content
    current_section = ''
    for slug_data in slugs:

        # has the top-level item changed?
        if slug_data[0] != current_section:

            # close the previous top-level item
            if current_section:
                slugs_div += u"          </ul>\n        </li>\n"
                content_div += u"  </div>\n"

            current_section = slug_data[0]
            slugs_div += u"      <li>\n        <a href=\"#" + slug_data[1] + u"\">" + slug_data[0]\
                         + u"</a>\n        <ul class=\"nav\">\n"

            content_div += u"<div class=\"bs-docs-section\">\n"

        # add the current item
        slugs_div += u"          <li><a href=\"#" + slug_data[1] + u"\">" + slug_data[2] + u"</a></li>\n"

        content_div += slug_data[3] + u"\n"

    # close the last top-level item
    slugs_div += u"        </ul>\n      </li>\n      <li><a class=\"back-to-top\" href=\"#top\">Back to top</a></li>"
    slugs_div += u"    </ul>\n  </nav>\n</div>"

    content_div += u"</div>\n</div>"

    log_this('Generated ' + str(pages_generated) + ' pages.', True)

    return [content_div, slugs_div]


def output_list(pages, option_list):
    md = u""

    if isinstance(option_list, list):
        if len(option_list) == 1:
            link = get_page_link_by_slug(pages, option_list[0])
            if link:
                md += u' ' + link
            else:
                log_error('Linked page not found: ' + option_list[0])
        else:
            for option in option_list:
                link = get_page_link_by_slug(pages, option)
                if link:
                    md += u"\n  * " + link
                else:
                    log_error('Linked page not found: ' + option)
    else:
        link = get_page_link_by_slug(pages, option_list)
        if link:
            md += u' ' + link
        else:
            log_error('Linked page not found: ' + option_list)

    return md


def get_page_link_by_slug(pages, slug):
    found = [page for page in pages if page.yaml_data['slug'].strip().lower() == slug.strip().lower()]
    if len(found) == 0:
        return ''

    return '<a href="#' + found[0].yaml_data['slug'].lower() + '">' + found[0].yaml_data['title'] + '</a>'


if __name__ == '__main__':

    log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)

    has_changed = False
    ta_pages = None

    with SelfClosingEtherpad() as ep:

        text = ep.getText(padID='ta-modules')
        ta_sections = parse_ta_modules(text['text'])
        ta_pages = get_vol1_pages(ep, ta_sections)

    log_this('Generating Word document.', True)
    make_docx(ta_pages)

    if error_count != 0:
        log_this(str(error_count) + ' errors have been logged', True)

    log_this('Finished generating docx', True)
