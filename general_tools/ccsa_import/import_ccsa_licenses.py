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
# RUN THIS SCRIPT IN: dokuwiki/data/gitrepo/pages/
#
import codecs
import httplib
import lxml.html as html
import re
import sys
from general_tools.git_wrapper import *


class SelfClosingConnection(httplib.HTTPConnection):
    """
    This class is here to enable with...as functionality for the HHTPConnection
    """

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exception_type, exception_val, trace):
        self.close()


def get_document(host, url):
    """
    :param host: str
    :param url: str
    :rtype: html.HtmlElement
    """
    with SelfClosingConnection(host, httplib.HTTP_PORT) as connection:

        connection.request('GET', url)
        response = connection.getresponse()

        # check the status
        if response.status != 200:
            return None

        return html.document_fromstring(response.read())


def get_translation(lang_code):

    url = '/licenses/by-sa/4.0/deed.' + lang_code
    lang_doc = get_document('creativecommons.org', url)

    if lang_doc is not None:

        returnval = "====== Copyrights & Licensing ======\n\n\n"
        returnval += "All content on Door43 is made available under a [[http://creativecommons.org" + url

        # get the title
        title = lang_doc.get_element_by_id('deed-license').text_content().replace('\n', ' ')
        title = re.sub(r"\s{2,}", ' ', title).strip()
        returnval += "|" + title + " License]], which means\n\n"

        # get 'You are free to'
        div = lang_doc.get_element_by_id('deed-rights')
        free_to = div.cssselect('h3')[0].text_content().strip()
        returnval += free_to + "\n\n"

        # get 'Share...'
        share = div.cssselect('ul li.share')[0].text_content().strip()
        returnval += '  * ' + share + "\n"

        # get 'Adapt...'
        adapt = div.cssselect('ul li.remix')[0].text_content().strip()
        adapt += ' ' + div.cssselect('ul li.commercial')[0].text_content().strip()
        returnval += '  * ' + adapt + "\n\n"

        # get 'Under the following...'
        div = lang_doc.get_element_by_id('deed-conditions')
        conditions = div.cssselect('h3')[0].text_content().strip()
        returnval += conditions + "\n\n"

        # get 'Attribution'
        attribution = div.cssselect('ul li.by')[0].cssselect('p')[0].text_content().strip()
        returnval += '  * ' + attribution + "\n"

        # get 'ShareAlike'
        share_alike = div.cssselect('ul li.sa')[0].cssselect('p')[0].text_content().strip()
        returnval += '  * ' + share_alike + "\n\n\n"

        # remainder
        returnval += "===== Attribution of Door43 Contributors =====\n\n\n"
        returnval += "When importing a resource (e.g. a book, Bible study, etc.) into Door43, the original work must be"
        returnval += " attributed as specified by the open license under which it is available. For example, the"
        returnval += " artwork used in Open Bible Stories is available under an open license and is clearly attributed"
        returnval += " on the project's [[:" + lang_code + ":obs|main page]].\n\n\n"

        returnval += "Contributors to projects on Door43 agree that **the attribution that occurs automatically in the"
        returnval += " revision history of every page is sufficient attribution for their work.**  That is, every"
        returnval += " contributor to a translation of Open Bible Stories into another language is listed as \"the"
        returnval += " Door43 World Missions Community\" or something to that effect. The individual contributions of"
        returnval += " each individual contributor are preserved in the revision history for that translation.\n"

        return returnval


if __name__ == '__main__':

    cwdir = os.curdir

    with open('import_ccsa_licenses.log', 'w') as log:

        os.chdir('/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages')  # production
        # os.chdir('/var/www/html/dokuwiki/data/gitrepo/pages/')            # developer debugging

        log.write("Beginning import.\n")

        # get the doc containing the list of links
        doc = get_document('creativecommons.org', '/licenses/by-sa/4.0/')

        # get the div containing the links
        langs = doc.get_element_by_id('languages')
        log.write("Languages retrieved.\n")

        # get the links
        links = langs.cssselect('a')
        for e in links:
            code = e.get('hreflang')

            if code != 'en':

                dw_code = code.replace('_', '-').lower()

                # get the new document
                log.write('Getting ' + code + " from creativecommons.org.\n")
                md = get_translation(code)

                # check for the namespace
                if not os.path.exists(dw_code):
                    log.write('Namespace ' + dw_code + " does not exist.\n")
                    print 'Namespace ' + dw_code + ' does not exist.'

                else:
                    # directory
                    dir_name = dw_code + '/legal'
                    if not os.path.exists(dir_name):
                        os.makedirs(dir_name)

                    # file
                    file_name = dir_name + '/license.txt'
                    exists = False
                    if os.path.exists(file_name):
                        exists = True

                        # DO NOT make a backup
                        # os.rename(file_name, file_name + '.bak')
                        # log.write('File ' + file_name + " backed up.\n")
                        # print 'File ' + file_name + ' backed up.'

                    with codecs.open(file_name, 'w', 'utf-8') as file_out:
                        file_out.write(md)

                        if exists:
                            log.write('File ' + file_name + " updated.\n")
                            print 'File ' + file_name + ' updated.'
                        else:
                            log.write('File ' + file_name + " created.\n")
                            print 'File ' + file_name + ' created.'

        # push to github
        log.write("Pushing to Github.\n")
        print 'Pushing to Github.'
        dokuwiki_dir = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/'
        gitCommit(dokuwiki_dir, u'Updated license.txt from creativecommons.org.')
        gitPush(dokuwiki_dir)

        log.write('Finished')
        os.chdir(cwdir)
