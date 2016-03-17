#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#    Copyright (c) 2014 - 2016 unfoldingWord
#    http://creativecommons.org/licenses/MIT/
#    See LICENSE file for details.
#
#    Contributors:
#    Jesse Griffin <jesse@distantshores.org>
#    Phil Hopper <phillip_hopper@wycliffeassociates.org>


"""
This script imports USFM files from a zip file and prepares them for use in
translationStudio.
"""

import os
import re
import sys
import glob
import json
import codecs
import shutil
import urllib2
import zipfile
import argparse
# noinspection PyUnresolvedReferences
import datetime

# remember these so we can delete them
downloaded_file = ''
unzipped_dir = ''

chunk_url = u'https://api.unfoldingword.org/ts/txt/2/{0}/en/ulb/chunks.json'
out_template = '/var/www/vhosts/api.unfoldingword.org/httpdocs/{0}/txt/1/{0}-{1}'

id_re = re.compile(ur'\\id (\w+)', re.UNICODE)
chapter_re = re.compile(ur'\\c [0-9]* ', re.UNICODE)
book_name_re = re.compile(ur'\\h (.*)', re.UNICODE)
s5_re = re.compile(ur'\\s5\s*')

books = {u'GEN': [u'Genesis', '01'],
         u'EXO': [u'Exodus', '02'],
         u'LEV': [u'Leviticus', '03'],
         u'NUM': [u'Numbers', '04'],
         u'DEU': [u'Deuteronomy', '05'],
         u'JOS': [u'Joshua', '06'],
         u'JDG': [u'Judges', '07'],
         u'RUT': [u'Ruth', '08'],
         u'1SA': [u'1 Samuel', '09'],
         u'2SA': [u'2 Samuel', '10'],
         u'1KI': [u'1 Kings', '11'],
         u'2KI': [u'2 Kings', '12'],
         u'1CH': [u'1 Chronicles', '13'],
         u'2CH': [u'2 Chronicles', '14'],
         u'EZR': [u'Ezra', '15'],
         u'NEH': [u'Nehemiah', '16'],
         u'EST': [u'Esther', '17'],
         u'JOB': [u'Job', '18'],
         u'PSA': [u'Psalms', '19'],
         u'PRO': [u'Proverbs', '20'],
         u'ECC': [u'Ecclesiastes', '21'],
         u'SNG': [u'Song of Solomon', '22'],
         u'ISA': [u'Isaiah', '23'],
         u'JER': [u'Jeremiah', '24'],
         u'LAM': [u'Lamentations', '25'],
         u'EZK': [u'Ezekiel', '26'],
         u'DAN': [u'Daniel', '27'],
         u'HOS': [u'Hosea', '28'],
         u'JOL': [u'Joel', '29'],
         u'AMO': [u'Amos', '30'],
         u'OBA': [u'Obadiah', '31'],
         u'JON': [u'Jonah', '32'],
         u'MIC': [u'Micah', '33'],
         u'NAM': [u'Nahum', '34'],
         u'HAB': [u'Habakkuk', '35'],
         u'ZEP': [u'Zephaniah', '36'],
         u'HAG': [u'Haggai', '37'],
         u'ZEC': [u'Zechariah', '38'],
         u'MAL': [u'Malachi', '39'],
         u'MAT': [u'Matthew', '41'],
         u'MRK': [u'Mark', '42'],
         u'LUK': [u'Luke', '43'],
         u'JHN': [u'John', '44'],
         u'ACT': [u'Acts', '45'],
         u'ROM': [u'Romans', '46'],
         u'1CO': [u'1 Corinthians', '47'],
         u'2CO': [u'2 Corinthians', '48'],
         u'GAL': [u'Galatians', '49'],
         u'EPH': [u'Ephesians', '50'],
         u'PHP': [u'Philippians', '51'],
         u'COL': [u'Colossians', '52'],
         u'1TH': [u'1 Thessalonians', '53'],
         u'2TH': [u'2 Thessalonians', '54'],
         u'1TI': [u'1 Timothy', '55'],
         u'2TI': [u'2 Timothy', '56'],
         u'TIT': [u'Titus', '57'],
         u'PHM': [u'Philemon', '58'],
         u'HEB': [u'Hebrews', '59'],
         u'JAS': [u'James', '60'],
         u'1PE': [u'1 Peter', '61'],
         u'2PE': [u'2 Peter', '62'],
         u'1JN': [u'1 John', '63'],
         u'2JN': [u'2 John', '64'],
         u'3JN': [u'3 John', '65'],
         u'JUD': [u'Jude', '66'],
         u'REV': [u'Revelation', '67'],
         }


def main(resource, lang, slug, name, checking, contrib, ver, check_level,
         comments, source):

    global downloaded_file, unzipped_dir

    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    downloaded_file = '/tmp/{0}'.format(resource.rpartition('/')[2])
    unzipped_dir = '/tmp/{0}'.format(resource.rpartition('/')[2].strip('.zip'))
    out_dir = out_template.format(slug, lang)

    if not os.path.isfile(downloaded_file):
        get_zip(resource, downloaded_file)

    unzip(downloaded_file, unzipped_dir)

    books_published = {}
    files = glob.glob('{0}/{1}'.format(unzipped_dir, '*[Ss][Ff][Mm]'))
    file_dir = unzipped_dir

    # archives from GitHub will have the files in a sub-directory several layers deep
    while len(files) == 0:
        sub_directories = os.listdir(file_dir)
        if len(sub_directories) == 1:
            file_dir = os.path.join(file_dir, sub_directories[0])
            files = glob.glob('{0}/{1}'.format(file_dir, '*[Ss][Ff][Mm]'))
        else:
            raise Exception('Not able to find the USFM files in the archive.')

    for path in files:
        lines = codecs.open(path, encoding='utf-8').readlines()
        book = getRE('\n'.join(lines[:10]), id_re).upper()
        print book
        book_name = getRE('\n'.join(lines[:10]), book_name_re)
        if not book:
            print "No book"
            continue
        verses = get_verses(book)
        if not verses:
            print "No verses"
            continue
        newlines = add_sections(lines, verses)
        book_file_name = '{0}-{1}.usfm'.format(books[book][1], book)
        write_file('{0}/{1}'.format(out_dir, book_file_name), u''.join(newlines))
        meta = ['Bible: OT']
        if int(books[book][1]) > 39:
            meta = ['Bible: NT']
        books_published[book.lower()] = {'name': book_name,
                                         'meta': meta,
                                         'sort': books[book][1],
                                         'desc': ''
                                         }
    source_ver = ver
    if u'.' in ver:
        source_ver = ver.split(u'.')[0]
    status = {"slug": u'{0}-{1}'.format(slug.lower(), lang),
              "name": name,
              "lang": lang,
              "date_modified": today,
              "books_published": books_published,
              "status": {"checking_entity": checking,
                         "checking_level": check_level,
                         "comments": comments,
                         "contributors": contrib,
                         "publish_date": today,
                         "source_text": source,
                         "source_text_version": source_ver,
                         "version": ver
                         }
              }
    write_json('{0}/status.json'.format(out_dir), status)
    print "Check {0} and do a git push".format(out_dir)


def get_verses(book):
    chunk_str = get_url(chunk_url.format(book.lower()))
    if not chunk_str:
        return False
    chunks = json.loads(chunk_str)
    # noinspection SpellCheckingInspection
    return [x['firstvs'] for x in chunks]


def add_sections(lines, verses):
    previous_line = u''
    newlines = []
    i = 0
    for line in lines:
        if line in [u'', u' ', u'\n']:
            continue

        # skip existing \s5 lines since we put them in ourselves
        s5_search = s5_re.search(line)
        if s5_search:
            continue

        chapter_search = chapter_re.search(line)
        if chapter_search:
            newlines.append(u'\\s5\n')
            newlines.append(line)
            previous_line = line
            i += 1
            continue

        if i < len(verses):
            verse_search = re.search(ur'\\v {0} '.format(verses[i]), line)
            if verse_search:

                # insert before \p, not after
                if previous_line == u'\\p\n':
                    newlines.insert(len(newlines) - 1, u'\\s5\n')
                else:
                    newlines.append(u'\\s5\n')

                i += 1

        newlines.append(line)
        previous_line = line

    return newlines


# noinspection PyPep8Naming
def getRE(text, regex):
    se = regex.search(text)
    if not se:
        return False
    return se.group(1).strip()


def write_json(out_file, p):
    """
    Simple wrapper to write a file as JSON.
    :param out_file:
    :param p:
    """
    make_dir(out_file.rsplit('/', 1)[0])
    f = codecs.open(out_file, 'w', encoding='utf-8')
    f.write(json.dumps(p, sort_keys=True))
    f.close()


def write_file(f, content):
    make_dir(f.rpartition('/')[0])
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()


def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)


def unzip(source, dest):
    with zipfile.ZipFile(source) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''):
                    continue
                path = os.path.join(path, word)
            zf.extract(member, path)


def get_zip(url, outfile):
    print "Getting ZIP"
    # noinspection PyBroadException
    try:
        request = urllib2.urlopen(url)
    except:
        print "    => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)


def get_url(url):
    # noinspection PyBroadException
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return u''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-r', '--resource', dest="resource", default=False,
                        required=True, help="URL of zip file.")
    parser.add_argument('-l', '--lang', dest="lang", default=False,
                        required=True, help="Language code of resource.")
    parser.add_argument('-s', '--slug', dest="slug", default=False,
                        required=True, help="Slug of resource name (e.g. NIV).")
    parser.add_argument('-n', '--name', dest="name", default=False,
                        required=True, help="Name (e.g. 'New International Version').")
    parser.add_argument('-c', '--checking', dest="checking", default=False,
                        required=True, help="Checking entity.")
    parser.add_argument('-t', '--translators', dest="contrib", default=False,
                        required=True, help="Contributing translators.")
    parser.add_argument('-v', '--version', dest="version", default=False,
                        required=True, help="Version of resource.")
    parser.add_argument('-e', '--check_level', dest="check_level", default=3,
                        required=False, help="Checking level of the resource.")
    parser.add_argument('-m', '--comments', dest="comments", default="",
                        required=False, help="Comments on the resource.")
    parser.add_argument('-o', '--source', dest="source", default="en",
                        required=False, help="Source language code.")

    args = parser.parse_args(sys.argv[1:])

    try:
        main(args.resource, args.lang, args.slug, args.name, args.checking,
             args.contrib, args.version, args.check_level, args.comments, args.source)
    finally:
        # delete temp files
        if os.path.isfile(downloaded_file):
            os.remove(downloaded_file)

        if os.path.isdir(unzipped_dir):
            shutil.rmtree(unzipped_dir, ignore_errors=True)
