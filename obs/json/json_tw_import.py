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

obsframeset = set([
    "01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07", "01-08", "01-09", "01-10", "01-11", "01-12", "01-13", "01-14", "01-15", "01-16", "02-01", "02-02", "02-03", "02-04", "02-05", "02-06", "02-07", "02-08", "02-09", "02-10", "02-11", "02-12", "03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10", "03-11", "03-12", "03-13", "03-14", "03-15", "03-16", "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09", "05-01", "05-02", "05-03", "05-04", "05-05", "05-06", "05-07", "05-08", "05-09", "05-10", "06-01", "06-02", "06-03", "06-04", "06-05", "06-06", "06-07", "07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07", "07-08", "07-09", "07-10", "08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08", "08-09", "08-10", "08-11", "08-12", "08-13", "08-14", "08-15", "09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07", "09-08", "09-09", "09-10", "09-11", "09-12", "09-13", "09-14", "09-15", "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07", "10-08", "10-09", "10-10", "10-11", "10-12", "11-01", "11-02", "11-03", "11-04", "11-05", "11-06", "11-07", "11-08", "12-01", "12-02", "12-03", "12-04", "12-05", "12-06", "12-07", "12-08", "12-09", "12-10", "12-11", "12-12", "12-13", "12-14", "13-01", "13-02", "13-03", "13-04", "13-05", "13-06", "13-07", "13-08", "13-09", "13-10", "13-11", "13-12", "13-13", "13-14", "13-15", "14-01", "14-02", "14-03", "14-04", "14-05", "14-06", "14-07", "14-08", "14-09", "14-10", "14-11", "14-12", "14-13", "14-14", "14-15", "15-01", "15-02", "15-03", "15-04", "15-05", "15-06", "15-07", "15-08", "15-09", "15-10", "15-11", "15-12", "15-13", "16-01", "16-02", "16-03", "16-04", "16-05", "16-06", "16-07", "16-08", "16-09", "16-10", "16-11", "16-12", "16-13", "16-14", "16-15", "16-16", "16-17", "16-18", "17-01", "17-02", "17-03", "17-04", "17-05", "17-06", "17-07", "17-08", "17-09", "17-10", "17-11", "17-12", "17-13", "17-14", "18-01", "18-02", "18-03", "18-04", "18-05", "18-06", "18-07", "18-08", "18-09", "18-10", "18-11", "18-12", "18-13", "19-01", "19-02", "19-03", "19-04", "19-05", "19-06", "19-07", "19-08", "19-09", "19-10", "19-11", "19-12", "19-13", "19-14", "19-15", "19-16", "19-17", "19-18", "20-01", "20-02", "20-03", "20-04", "20-05", "20-06", "20-07", "20-08", "20-09", "20-10", "20-11", "20-12", "20-13", "21-01", "21-02", "21-03", "21-04", "21-05", "21-06", "21-07", "21-08", "21-09", "21-10", "21-11", "21-12", "21-13", "21-14", "21-15", "22-01", "22-02", "22-03", "22-04", "22-05", "22-06", "22-07", "23-01", "23-02", "23-03", "23-04", "23-05", "23-06", "23-07", "23-08", "23-09", "23-10", "24-01", "24-02", "24-03", "24-04", "24-05", "24-06", "24-07", "24-08", "24-09", "25-01", "25-02", "25-03", "25-04", "25-05", "25-06", "25-07", "25-08", "26-01", "26-02", "26-03", "26-04", "26-05", "26-06", "26-07", "26-08", "26-09", "26-10", "27-01", "27-02", "27-03", "27-04", "27-05", "27-06", "27-07", "27-08", "27-09", "27-10", "27-11", "28-01", "28-02", "28-03", "28-04", "28-05", "28-06", "28-07", "28-08", "28-09", "28-10", "29-01", "29-02", "29-03", "29-04", "29-05", "29-06", "29-07", "29-08", "29-09", "30-01", "30-02", "30-03", "30-04", "30-05", "30-06", "30-07", "30-08", "30-09", "31-01", "31-02", "31-03", "31-04", "31-05", "31-06", "31-07", "31-08", "32-01", "32-02", "32-03", "32-04", "32-05", "32-06", "32-07", "32-08", "32-09", "32-10", "32-11", "32-12", "32-13", "32-14", "32-15", "32-16", "33-01", "33-02", "33-03", "33-04", "33-05", "33-06", "33-07", "33-08", "33-09", "34-01", "34-02", "34-03", "34-04", "34-05", "34-06", "34-07", "34-08", "34-09", "34-10", "35-01", "35-02", "35-03", "35-04", "35-05", "35-06", "35-07", "35-08", "35-09", "35-10", "35-11", "35-12", "35-13", "36-01", "36-02", "36-03", "36-04", "36-05", "36-06", "36-07", "37-01", "37-02", "37-03", "37-04", "37-05", "37-06", "37-07", "37-08", "37-09", "37-10", "37-11", "38-01", "38-02", "38-03", "38-04", "38-05", "38-06", "38-07", "38-08", "38-09", "38-10", "38-11", "38-12", "38-13", "38-14", "38-15", "39-01", "39-02", "39-03", "39-04", "39-05", "39-06", "39-07", "39-08", "39-09", "39-10", "39-11", "39-12", "40-01", "40-02", "40-03", "40-04", "40-05", "40-06", "40-07", "40-08", "40-09", "41-01", "41-02", "41-03", "41-04", "41-05", "41-06", "41-07", "41-08", "42-01", "42-02", "42-03", "42-04", "42-05", "42-06", "42-07", "42-08", "42-09", "42-10", "42-11", "43-01", "43-02", "43-03", "43-04", "43-05", "43-06", "43-07", "43-08", "43-09", "43-10", "43-11", "43-12", "43-13", "44-01", "44-02", "44-03", "44-04", "44-05", "44-06", "44-07", "44-08", "44-09", "45-01", "45-02", "45-03", "45-04", "45-05", "45-06", "45-07", "45-08", "45-09", "45-10", "45-11", "45-12", "45-13", "46-01", "46-02", "46-03", "46-04", "46-05", "46-06", "46-07", "46-08", "46-09", "46-10", "47-01", "47-02", "47-03", "47-04", "47-05", "47-06", "47-07", "47-08", "47-09", "47-10", "47-11", "47-12", "47-13", "47-14", "48-01", "48-02", "48-03", "48-04", "48-05", "48-06", "48-07", "48-08", "48-09", "48-10", "48-11", "48-12", "48-13", "48-14", "49-01", "49-02", "49-03", "49-04", "49-05", "49-06", "49-07", "49-08", "49-09", "49-10", "49-11", "49-12", "49-13", "49-14", "49-15", "49-16", "49-17", "49-18", "50-01", "50-02", "50-03", "50-04", "50-05", "50-06", "50-07", "50-08", "50-09", "50-10", "50-11", "50-12", "50-13", "50-14", "50-15", "50-16", "50-17"
])

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
        gitCommit(langpath, "Imported OBS tN from JSON file")
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
