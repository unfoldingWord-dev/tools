#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#    Copyright (c) 2014 unfoldingWord
#    http://creativecommons.org/licenses/MIT/
#    See LICENSE file for details.
#
#    Contributors:
#    Jesse Griffin <jesse@distantshores.org>


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
import datetime


chunkurl = u'https://api.unfoldingword.org/ts/txt/2/{0}/en/ulb/chunks.json'
outtmp = '/var/www/vhosts/api.unfoldingword.org/httpdocs/{0}/txt/1/{0}-{1}'
idre = re.compile(ur'\\id (\w+)', re.UNICODE)
chpre = re.compile(ur'\\c [0-9]* ', re.UNICODE)
bknmre = re.compile(ur'\\h (.*)', re.UNICODE)
books = { u'GEN': [ u'Genesis', '01' ],
          u'EXO': [ u'Exodus', '02' ],
          u'LEV': [ u'Leviticus', '03' ],
          u'NUM': [ u'Numbers', '04' ],
          u'DEU': [ u'Deuteronomy', '05' ],
          u'JOS': [ u'Joshua', '06' ],
          u'JDG': [ u'Judges', '07' ],
          u'RUT': [ u'Ruth', '08' ],
          u'1SA': [ u'1 Samuel', '09' ],
          u'2SA': [ u'2 Samuel', '10' ],
          u'1KI': [ u'1 Kings', '11' ],
          u'2KI': [ u'2 Kings', '12' ],
          u'1CH': [ u'1 Chronicles', '13' ],
          u'2CH': [ u'2 Chronicles', '14' ],
          u'EZR': [ u'Ezra', '15' ],
          u'NEH': [ u'Nehemiah', '16' ],
          u'EST': [ u'Esther', '17' ],
          u'JOB': [ u'Job', '18' ],
          u'PSA': [ u'Psalms', '19' ],
          u'PRO': [ u'Proverbs', '20' ],
          u'ECC': [ u'Ecclesiastes', '21' ],
          u'SNG': [ u'Song of Solomon', '22' ],
          u'ISA': [ u'Isaiah', '23' ],
          u'JER': [ u'Jeremiah', '24' ],
          u'LAM': [ u'Lamentations', '25' ],
          u'EZK': [ u'Ezekiel', '26' ],
          u'DAN': [ u'Daniel', '27' ],
          u'HOS': [ u'Hosea', '28' ],
          u'JOL': [ u'Joel', '29' ],
          u'AMO': [ u'Amos', '30' ],
          u'OBA': [ u'Obadiah', '31' ],
          u'JON': [ u'Jonah', '32' ],
          u'MIC': [ u'Micah', '33' ],
          u'NAM': [ u'Nahum', '34' ],
          u'HAB': [ u'Habakkuk', '35' ],
          u'ZEP': [ u'Zephaniah', '36' ],
          u'HAG': [ u'Haggai', '37' ],
          u'ZEC': [ u'Zechariah', '38' ],
          u'MAL': [ u'Malachi', '39' ],
          u'MAT': [ u'Matthew', '41' ],
          u'MRK': [ u'Mark', '42' ],
          u'LUK': [ u'Luke', '43' ],
          u'JHN': [ u'John', '44' ],
          u'ACT': [ u'Acts', '45' ],
          u'ROM': [ u'Romans', '46' ],
          u'1CO': [ u'1 Corinthians', '47' ],
          u'2CO': [ u'2 Corinthians', '48' ],
          u'GAL': [ u'Galatians', '49' ],
          u'EPH': [ u'Ephesians', '50' ],
          u'PHP': [ u'Philippians', '51' ],
          u'COL': [ u'Colossians', '52' ],
          u'1TH': [ u'1 Thessalonians', '53' ],
          u'2TH': [ u'2 Thessalonians', '54' ],
          u'1TI': [ u'1 Timothy', '55' ],
          u'2TI': [ u'2 Timothy', '56' ],
          u'TIT': [ u'Titus', '57' ],
          u'PHM': [ u'Philemon', '58' ],
          u'HEB': [ u'Hebrews', '59' ],
          u'JAS': [ u'James', '60' ],
          u'1PE': [ u'1 Peter', '61' ],
          u'2PE': [ u'2 Peter', '62' ],
          u'1JN': [ u'1 John', '63' ],
          u'2JN': [ u'2 John', '64' ],
          u'3JN': [ u'3 John', '65' ],
          u'JUD': [ u'Jude', '66' ],
          u'REV': [ u'Revelation', '67' ],
}



def main(resource, lang, slug, name, checking, contrib, ver):
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    local_res = '/tmp/{0}'.format(resource.rpartition('/')[2])
    sourceDir = '/tmp/{0}'.format(resource.rpartition('/')[2].strip('.zip'))
    outdir = outtmp.format(slug, lang)

    if not os.path.isfile(local_res):
        getZip(resource, local_res)
    unzip(local_res, sourceDir)

    books_published = {}
    files = glob.glob('{0}/{1}'.format(sourceDir, '*[Ss][Ff][Mm]'))
    for path in files:
        lines = codecs.open(path, encoding='utf-8').readlines()
        book = getRE('\n'.join(lines[:10]), idre)
        print book
        bookname = getRE('\n'.join(lines[:10]), bknmre)
        if not book:
            print "No book"
            continue
        verses = getVerses(book)
        if not verses:
            print "No verses"
            continue
        newlines = addSections(lines, verses)
        book_name = '{0}-{1}.usfm'.format(books[book][1], book)
        writeFile('{0}/{1}'.format(outdir, book_name), u''.join(newlines))
        meta = ['Bible: OT']
        if int(books[book][1]) > 39:
            meta = ['Bible: NT']
        books_published[book.lower()] = { 'name': bookname,
                                          'meta': meta,
                                          'sort': books[book][1],
                                          'desc': ''
                                        }
    del books_published['psa']
    del books_published['isa']
    status = { "slug": slug.lower(),
               "name": name,
               "lang": lang,
               "date_modified": today,
               "books_published": books_published,
               "status": { "checking_entity": checking,
                           "checking_level": "3",
                           "comments": "Original source text",
                           "contributors": contrib,
                           "publish_date": today,
                           "source_text": lang,
                           "source_text_version": ver,
                           "version": ver
                          }
             }
    writeJSON('{0}/status.json'.format(outdir), status)
    print "Check {0} and do a git push".format(outdir)

def getVerses(book):
    chunkstr = getURL(chunkurl.format(book.lower()))
    if not chunkstr: return False
    chunks = json.loads(chunkstr)
    return [x['firstvs'] for x in chunks]

def addSections(lines, verses):
    newlines = []
    i = 0
    for line in lines:
        if line in [u'', u' ', u'\n']: continue
        chpse = chpre.search(line)
        if chpse:
            newlines.append(u'\\s5\n')
            newlines.append(line)
            i += 1
            continue
        if i < len(verses):
            versese = re.search(ur'\\v {0} '.format(verses[i]), line)
            if versese:
                newlines.append(u'\\s5\n')
                i += 1
        newlines.append(line)
    return newlines

def getRE(text, regex):
    se = regex.search(text)
    if not se:
        return False
    return se.group(1).strip()

def writeJSON(outfile, p):
    '''
    Simple wrapper to write a file as JSON.
    '''
    makeDir(outfile.rsplit('/', 1)[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(json.dumps(p, sort_keys=True))
    f.close()

def writeFile(f, content):
    makeDir(f.rpartition('/')[0])
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()

def makeDir(d):
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
                if word in (os.curdir, os.pardir, ''): continue
                path = os.path.join(path, word)
            zf.extract(member, path)

def getZip(url, outfile):
    print "Getting ZIP"
    try:
        request = urllib2.urlopen(url)
    except:
        print "    => ERROR retrieving %s\nCheck the URL" % url
        sys.exit(1)
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)

def getURL(url):
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

    args = parser.parse_args(sys.argv[1:])
    main(args.resource, args.lang, args.slug, args.name, args.checking,
                                                   args.contrib, args.version)
