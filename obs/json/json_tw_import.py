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
Imports an OBS tW json file into Door43 and commits it to Github
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

def cleanText(text):
    # remove smart quotes
    text = text.replace(u"\u2018","'").replace(u"\u2019","'").replace(u"\u201c",'"').replace(u"\u201d",'"')

    return text

def htmlToMarkdown(text):
    return text.replace(u'<ul>', u"\n") \
    .replace(ur'<li>', u'  * ') \
    .replace(ur'</li>', u"\n") \
    .replace(ur'</ul>',u"\n") \
    .replace(ur'<h2>', u'===== ') \
    .replace(ur'</h2>', u" =====\n") \
    .replace(ur'<h3>', u"==== ") \
    .replace(ur'</h3>', u" ====\n") \
    .replace(ur'<b>', u'**') \
    .replace(ur'</b>', u'**')

def getAppWordKeys(file):
    keys = {}
    if os.path.isfile(file):
        for line in codecs.open(file, 'r', encoding='utf-8'):
            if ( line.startswith(u'#') or line.startswith(u'\n')
                              or line.startswith(u'{{') or u':' not in line ):
                continue
            k, v = line.split(u':', 1)
            keys[k.strip().lower().replace(u' ', u'_')] = k.strip()
    return keys

def main(lang, json_file):
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);

    langpath = os.path.join(pages, lang)
    obepath = os.path.join(langpath, 'obe')
    ktpath = os.path.join(obepath, 'kt')
    otherpath = os.path.join(obepath, 'other')

    if not os.path.isdir(langpath):
        print '{0} has not yet been set up on Door43'.format(lang)
        sys.exit(1)

    if not os.path.isdir(obepath) or not os.path.isdir(ktpath) or not os.path.isdir(otherpath):
        print 'OBE has not configured in Door43 for {0}'.format(lang)
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
    seeAlsoRe = re.compile(ur'\n(\(.*?\)\n)[\n\s]*===== Bible', re.UNICODE | re.DOTALL)
    bibleRefRe = re.compile(ur'(===== Bible References: =====.*?)===', re.UNICODE | re.DOTALL)
    footerRe = re.compile(ur'(~~DISCUSSION|\{\{tag>|~~NOCACHE).*', re.UNICODE | re.DOTALL)

    for term in json_array:
        if 'id' in term and 'def' in term and 'def_title' in term and 'term' in term:
            filename = "{0}.txt".format(term['id'])
            if os.path.exists(os.path.join(ktpath, filename)):
                filepath = os.path.join(ktpath, filename)
            elif os.path.exists(os.path.join(otherpath, filename)):
                filepath = os.path.join(otherpath, filename)
            else:
                print u"No file {0} for {1} exists in {2}. Please create file with proper sections and try again. Exiting...".format(filename, term['term'], obepath)
                sys.exit(1)

            try:
                page = codecs.open(filepath, 'r', encoding='utf-8').read()

                with codecs.open(filepath, 'w', encoding='utf8') as f:
                    try:
                        f.write(u"====== {0} ======\n\n".format(term['term']))
                        f.write(u"===== {0} =====\n\n".format(term['def_title']))
                        f.write(htmlToMarkdown(term['def']))

                        if seeAlsoRe.search(page):
                            f.write(seeAlsoRe.search(page).group(1))
                            f.write(u"\n")
                        elif 'cf' in term and term['cf']:
                            alsos = []
                            for cf in term['cf']:
                                cf = re.sub(ur'[\[\]\(\)]', '', cf).lower().strip()
                                term_filename = u"{0}.txt".format(cf)
                                term_path = None
                                if os.path.exists(os.path.join(ktpath, term_filename)):
                                    term_path = "kt"
                                elif os.path.exists(os.path.join(otherpath, filename)):
                                    term_path = "other"
                                if term_path:
                                    alsos.append(u"[[{0}:obe:{1}:{2}]]".format(lang, term_path, cf))
                            if alsos:
                                f.write(u"(See also: {0})\n\n".format(",".join(alsos)));

                        if bibleRefRe.search(page):
                            f.write(bibleRefRe.search(page).group(1))

                        if 'ex' in term and term['ex']:
                            f.write(u"===== Examples from the Bible stories: =====\n\n")
                            for ex in term['ex']:
                                f.write(u"  ***[[:{0}:obs:notes:frames:{1}|[{1}]]]** {2}\n".format(lang, ex['ref'], htmlToMarkdown(ex['text'])))
                            f.write(u"\n")

                        if footerRe.search(page):
                            f.write(footerRe.search(page).group(0))
                    finally:
                        f.close()
            except IOError,e:
                print str(e)
                sys.exit(1)

    try:
        gitCommit(langpath, "Imported OBS tW from JSON file")
        gitPush(langpath)
    except e:
        print str(e)
        sys.exit(1)

    print u"Successfully imported {0} for {1} ({2}) to {3}.".format(json_file, langname, lang, obepath)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--input', dest="jsonfile",
        required=True, help="Input JSON file")
    parser.add_argument('-l', '--language', dest="lang",
        required=True, help="Language code")
    args = parser.parse_args(sys.argv[1:])

    main(args.lang, args.jsonfile)
