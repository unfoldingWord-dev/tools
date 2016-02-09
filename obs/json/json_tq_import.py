#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Imports an OBS tQ json file into Door43 and commits it to Github
'''

import os
import re
import sys
import json
import codecs
import argparse

gen_tools = '/var/www/vhosts/door43.org/tools/general_tools'
sys.path.append(gen_tools)

try:
    from git_wrapper import *
except ImportError:
    print "Please ensure that {0} exists.".format(gen_tools)
    sys.exit(1)
try:
    from github import Github
    from github import GithubException
except:
    print "Please install PyGithub with pip"
    sys.exit(1)

pages = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages'
langnames = os.path.join('/var/www/vhosts/door43.org',
                  'httpdocs/lib/plugins/door43translation/lang/langnames.txt')

reload(sys)
sys.setdefaultencoding('utf8')

def loadLangStrings(path):
    langdict = {}
    if not os.path.isfile(path):
        return langdict
    for line in codecs.open(path, 'r', encoding='utf-8').readlines():
        if ( line.startswith(u'#') or line.startswith(u'\n')
                                                  or line.startswith(u'\r') ):
            continue
        code,string = line.split(None, 1)
        langdict[code.strip()] = string.strip()
    return langdict

def main(lang, json_file):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);

    langpath = os.path.join(pages, lang)
    obspath = os.path.join(langpath, 'obs')
    qpath = os.path.join(obspath, 'notes', 'questions')

    if not os.path.isdir(langpath):
        print '{0} has not yet been set up on Door43'.format(lang)
        sys.exit(1)

    if not os.path.isdir(obspath):
        print 'OBS has not configured in Door43 for {0}'.format(lang)
        sys.exit(1)

    if not os.path.isdir(qpath):
        print 'OBS Questions has not configured in Door43 for {0}'.format(lang)
        sys.exit(1)

    langdict = loadLangStrings(langnames)

    try:
        langstr = langdict[lang]
    except KeyError:
        print "Configuration for language {0} missing in {1}.".format(lang, langnames)
        sys.exit(1)

    langname = langdict[lang]

    # Parse the json file
    try:
        json_array = json.load(codecs.open(json_file, 'r', 'utf8'))
    except IOError,e:
        print str(e)
        sys.exit(1)

    # INJECT THE NOTES INTO NOTE PAGES FROM JSON
    pageRe = re.compile(ur'^.*?(======.*?\n)[\n\s]*(=====.*?\n)(.*?)\n(\*\*.*?\*\*)[\n\s]*$', re.UNICODE | re.DOTALL)

    for chapter in json_array:
        if 'id' in chapter and 'cq' in chapter and chapter['cq']:
            filepath = os.path.join(qpath, chapter['id']+".txt")

            try:
                page = codecs.open(filepath, 'r', encoding='utf-8').read()

                if not pageRe.match(page):
                    print "{0} is malformed and thus can't inject the questions from the JSON. Please fix, such as by copying the English (en) counterpart. Exiting...".format(filepath)
                    sys.exit(1)

                result = pageRe.search(page)
                story_title = result.group(1)
                question_title = result.group(2)
                footer = result.group(4)

                with codecs.open(filepath, 'w', encoding='utf8') as f:
                    try:
                        f.write(story_title + u"\n")
                        f.write(question_title + u"\n")

                        for cq in chapter['cq']:
                            f.write(u"  - **{0}**\n".format(cq['q']))
                            f.write(u"      * //{0} {1}//\n".format(cq['a'], u', '.join(u'[{0}]'.format(ref) for ref in cq['ref'])))

                        f.write(u"\n"+footer+u"\n")
                    finally:
                        f.close()
            except IOError,e:
                print str(e)
                sys.exit(1)

    try:
        gitCommit(langpath, "Imported OBS tQ from JSON file")
        gitPush(langpath)
    except e:
        print str(e)
        sys.exit(1)

    print "Successfully imported {0} for {1} ({2}) to {3}.".format(json_file, langname, lang, qpath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="jsonfile",
        required=True, help="Input JSON file")
    parser.add_argument('-l', '--language', dest="lang",
        required=True, help="Language code")
    args = parser.parse_args(sys.argv[1:])

    main(args.lang, args.jsonfile)
