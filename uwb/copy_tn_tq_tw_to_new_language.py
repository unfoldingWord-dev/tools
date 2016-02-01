#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
# Copies tN, tQ and tW from the en namespace to a selected namespace
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
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'general_tools'))
# noinspection PyBroadException
try:
    from git_wrapper import *
except:
    print "Please verify that"
    print "tools/general_tools exists."
    sys.exit(1)


DIRECTORIES = [u'en:bible:notes', u'en:bible:questions', u'en:obe']
FILES = [u'en:bible:team-info:training:topics:kt-yes-no',
         u'en:bible:team-info:training:topics:common-words',
         u'en:bible:admin-reports:obe-admin:obe-reject']
LOGFILE = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/playground/new_tn_tq_tw.log.txt'

NEW_LANGUAGE_CODE = ''
CONTINUE_ON_ERROR = 0
ERROR_COUNT = 0
PAGE_COUNT = 0

# enable logging for this script
log_dir = os.path.dirname(LOGFILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, 0755)

if os.path.exists(LOGFILE):
    os.remove(LOGFILE)

# console codes
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

PAGE_MSG = "\r" + OKGREEN + BOLD + '%i' + ENDC + ' pages copied'


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


def replace_language_code(page_text):
    global NEW_LANGUAGE_CODE

    new_text = page_text.replace(u'[[en:', u'[[' + NEW_LANGUAGE_CODE + u':')
    new_text = new_text.replace(u'[[:en:', u'[[:' + NEW_LANGUAGE_CODE + u':')
    new_text = new_text.replace(u'{{page>en:', u'{{page>' + NEW_LANGUAGE_CODE + u':')
    new_text = new_text.replace(u' en:', u' ' + NEW_LANGUAGE_CODE + u':')
    new_text = new_text.replace(u' :en:', u' :' + NEW_LANGUAGE_CODE + u':')

    return new_text


def increment_page_count():
    global PAGE_COUNT, PAGE_MSG

    PAGE_COUNT += 1

    sys.stdout.write(PAGE_MSG % PAGE_COUNT)
    sys.stdout.flush()


def process_directory(rootdir):

    for subdir, dirs, files in os.walk(rootdir):
        for file_name in files:
            process_file(os.path.join(subdir, file_name))

        for subsubdir in dirs:
            process_directory(os.path.join(subdir, subsubdir))


def process_file(source_file_name):
    global NEW_LANGUAGE_CODE

    with codecs.open(source_file_name, 'r', 'utf-8') as in_file:
        source_text = in_file.read()

    target_file_name = source_file_name.replace(u'/en/', u'/' + NEW_LANGUAGE_CODE + u'/')

    # make sure the target directory exists
    target_dir = os.path.dirname(target_file_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, 0755)

    with codecs.open(target_file_name, 'w', 'utf-8') as file_out:
        file_out.write(replace_language_code(source_text))

    increment_page_count()


def add_to_sidebar(rootdir):
    global NEW_LANGUAGE_CODE

    # get the existing sidebar
    sidebar_file = os.path.join(rootdir, NEW_LANGUAGE_CODE, u'sidebar.txt')
    if os.path.isfile(sidebar_file):
        with codecs.open(sidebar_file, 'r', 'utf-8') as in_file:
            sidebar_text = in_file.read()
    else:
        increment_page_count()
        sidebar_text = u''

    # check for **Resources**
    pos = sidebar_text.find(u'**Resources**\n\n')
    if pos == -1:
        if not sidebar_text:
            sidebar_text = u'**Resources**\n\n\n'
        else:
            sidebar_text += u'\n\n**Resources**\n\n\n'

        pos = sidebar_text.find(u'**Resources**\n\n')

    pos += 15  # length of **Resources**\n\n

    # check for * [[:en:ta:vol1:toc|translationAcademy Vol 1]]
    pos2 = sidebar_text.find(u':obe:home|', pos)
    if pos2 == -1:
        sidebar_text = sidebar_text[0:pos] + u'  * [[:' + NEW_LANGUAGE_CODE + \
                       u':ta:vol1:toc|translationAcademy Vol 1]]\n' + sidebar_text[pos:]

    # check for * [[:en:obe:home|translationWords]]
    pos2 = sidebar_text.find(u':obe:home|', pos)
    if pos2 == -1:
        sidebar_text = sidebar_text[0:pos] + u'  * [[:' + NEW_LANGUAGE_CODE + \
                       u':obe:home|translationWords]]\n' + sidebar_text[pos:]

    # check for * [[en:bible:questions:comprehension:home|translationQuestions]]
    pos2 = sidebar_text.find(u':bible:questions:comprehension:home|', pos)
    if pos2 == -1:
        sidebar_text = sidebar_text[0:pos] + u'  * [[:' + NEW_LANGUAGE_CODE + \
                       u':bible:questions:comprehension:home|translationQuestions]]\n' + sidebar_text[pos:]

    # check for * [[:en:bible:notes:home|translationNotes]]
    pos2 = sidebar_text.find(u':bible:notes:home|', pos)
    if pos2 == -1:
        sidebar_text = sidebar_text[0:pos] + u'  * [[:' + NEW_LANGUAGE_CODE + \
                       u':bible:notes:home|translationNotes]]\n' + sidebar_text[pos:]

    # save the changes
    with codecs.open(sidebar_file, 'w', 'utf-8') as file_out:
        file_out.write(sidebar_text)


if __name__ == '__main__':

    log_this('Most recent run: ' + datetime.utcnow().strftime('%Y-%m-%d %H:%M') + ' UTC', True)

    # process input args
    parser = argparse.ArgumentParser(description='Copies English tN, tQ and tW pages to a new language')
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

    # loop through the list of directories to copy
    base_dir = u'/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages/'
    for some_dir in DIRECTORIES:
        process_directory(base_dir + some_dir.replace(u':', u'/'))

    # loop through the list of additional files
    for some_file in FILES:
        process_file(os.path.join(base_dir, some_file.replace(u':', u'/') + u'.txt'))

    # add to sidebar
    add_to_sidebar(base_dir)

    # force new line after finished with file counter
    print ''

    # push to github
    push_to_git = raw_input('Push to Github now? [y|N]: ')
    if push_to_git == 'y':
        log_this('Pushing to Github')
        dokuwiki_dir = os.path.join(base_dir, NEW_LANGUAGE_CODE)
        gitCommit(dokuwiki_dir, u'Generated tN, tQ and tW.')
        gitPush(dokuwiki_dir)

    # finish logging the results
    if ERROR_COUNT > 0:
        if ERROR_COUNT == 1:
            log_this('1 error has been logged', True)
        else:
            log_this(str(ERROR_COUNT) + ' errors have been logged', True)

    log_this('Finished copying', True)
    print 'Log file: ' + OKBLUE + LOGFILE + ENDC
