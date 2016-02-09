#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

"""
Writes a JSON catalog of in progress OBS translations based on door43.org.
"""

import json
import shlex
import codecs
import urllib2
import datetime
from subprocess import *

pages = "/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages"
lang_names = u'http://td.unfoldingword.org/exports/langnames.json'
obs_cat = u'https://api.unfoldingword.org/obs/txt/1/obs-catalog.json'
obs_in_progress_file_name = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/obs-in-progress.json'


# noinspection PyBroadException
def get_url(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return


def run_command(c):
    """
    Runs a command in a shell.  Returns output and return code of command.
    :param c: str
    :return: str, int
    """
    command = shlex.split(c)
    com = Popen(command, shell=False, stdout=PIPE, stderr=PIPE)
    comout = ''.join(com.communicate()).strip()
    return comout, com.returncode


def write_json(object_to_store):
    """
    Stores an object in a json-formatted file
    :param object_to_store: object
    """
    f = codecs.open(obs_in_progress_file_name, 'w', encoding='utf-8')
    f.write(json.dumps(object_to_store, sort_keys=True))
    f.close()


def main(catalog, published_catalog):

    # get a list of the language codes already completed/published
    pub_list = [x['language'] for x in published_catalog]

    # get a list of the languages for which OBS has been initialized
    out, ret = run_command('find {0} -maxdepth 2 -type d -name obs'.format(pages))

    # start building the in-progress list
    in_progress_languages = []
    for line in out.split('\n'):

        # get the language code from the OBS namespace
        lc = line.split('/')[9]

        # skip this language if it is in the list of published languages
        if lc in pub_list:
            continue

        # make sure the language is in the official list of languages
        for x in catalog:
            if lc == x['lc']:
                in_progress_languages.append({'lc': lc, 'ln': x['ln']})
                break

    # now that we have the list of in-progress languages, sort it by language code
    in_progress_languages.sort(key=lambda item: item['lc'])

    # add a date-stamp
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    in_progress_languages.append({'date_modified': today})

    # save the results to a file
    write_json(in_progress_languages)


if __name__ == '__main__':
    cat = json.loads(get_url(lang_names))
    pub_cat = json.loads(get_url(obs_cat))
    main(cat, pub_cat)
