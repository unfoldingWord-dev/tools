#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#    Copyright (c) 2016 unfoldingWord
#    http://creativecommons.org/licenses/MIT/
#    See LICENSE file for details.
#
#    Contributors:
#    Phil Hopper <phillip_hopper@wycliffeassociates.org>

"""
This script validates the English ULB and UDB USFM data
"""
import argparse
import codecs
import json
import os
import re
import sys
import shutil
import urllib2
import zipfile

# remember these so we can delete them
downloaded_file = ''
unzipped_dir = ''

# TODO: change these to point to the API when it is available
vrs_file = 'https://raw.githubusercontent.com/unfoldingWord-dev/uw-api/develop/static/bible/ufw/ufw.vrs'
book_file = 'https://raw.githubusercontent.com/unfoldingWord-dev/uw-api/develop/static/bible/ufw/books-en.json'

chapter_re = re.compile(ur'(\\c [0-9]*\s*\n)', re.UNICODE)
verse_re = re.compile(ur'(\\v [0-9\-]*\s+)', re.UNICODE)
s5_re = re.compile(ur'\\s5\s*')
nl_re = re.compile(ur'\n{2,}')

validation_errors = []


class Book(object):
    def __init__(self, book_id, name, number):
        """
        :type book_id: str
        :type name: str
        :type number: int
        """
        self.book_id = book_id  # type: str
        self.name = name  # type: str
        self.number = number  # type int
        self.chapters = []  # type: list<Chapter>
        self.dir_name = str(number).zfill(2) + '-' + book_id  # type: str
        self.usfm = None  # type: unicode

    def verify_chapters_and_verses(self):
        global chapter_re

        # split into chapters
        self.check_chapters(chapter_re.split(self.usfm))

    def check_chapters(self, blocks):

        # find the first chapter marker, should be the second block
        # the first block should be everything before the first chapter marker
        current_index = 0
        while blocks[current_index][:2] != u'\c':
            current_index += 1

        # loop through the blocks
        while current_index < len(blocks):

            # parse the chapter number
            test_num = blocks[current_index][3:].strip()
            if not test_num.isdigit():
                append_error(u'Invalid chapter number, ' + self.name + u' "' + test_num + u'"')

            # compare this chapter number to the numbers from the bible file
            chapter_num = int(test_num)
            found_chapter = next((c for c in self.chapters if c.number == chapter_num), None)  # type: Chapter
            if not found_chapter:
                append_error(u'Invalid chapter number, ' + self.name + u' "' + test_num + u'"')

            else:
                found_chapter.found = True

                # make sure there is a chapter body
                if current_index + 1 >= len(blocks):
                    append_error(u'No verses found in ' + self.name + u' ' + unicode(found_chapter.number))

                else:
                    # split the chapter text into verses
                    self.check_verses(found_chapter, verse_re.split(blocks[current_index + 1]))

            # increment the counter
            current_index += 2

    def check_verses(self, found_chapter, verse_blocks):

        last_verse = 0
        processed_verses = []

        # go to the first verse marker
        current_cv_index = 0
        while verse_blocks[current_cv_index][:2] != u'\\v':
            current_cv_index += 1

        # verses should be sequential, starting at 1 and ending at found_chapter.num_verses
        while current_cv_index < len(verse_blocks):

            # parse the verse number
            test_num = verse_blocks[current_cv_index][3:].strip()

            # is this a verse bridge?
            if u'-' in test_num:
                nums = test_num.split(u'-')
                if len(nums) != 2 or not nums[0].strip().isdigit() or not nums[1].strip().isdigit():
                    append_error(u'Invalid verse bridge, ' + self.name + u' ' +
                                 unicode(found_chapter.number) + u':' + test_num)

                else:
                    for bridge_num in range(int(nums[0].strip()), int(nums[1].strip()) + 1):
                        last_verse = self.check_this_verse(found_chapter, bridge_num, last_verse, processed_verses)

                    current_cv_index += 2
            else:
                if not test_num.isdigit():

                    # the verse number isn't a number
                    append_error(u'Invalid verse number, ' + self.name + u' ' +
                                 unicode(found_chapter.number) + u':' + test_num)

                else:
                    verse_num = int(test_num)
                    last_verse = self.check_this_verse(found_chapter, verse_num, last_verse, processed_verses)

                current_cv_index += 2

    def check_this_verse(self, found_chapter, verse_num, last_verse, processed_verses):

        # is this verse number too large?
        if verse_num > found_chapter.expected_max_verse_number:
            append_error(u'Invalid verse number, ' + self.name + u' ' +
                         unicode(found_chapter.number) + u':' + unicode(verse_num))

        # look for gaps in the verse numbers
        while verse_num > last_verse + 1 and last_verse < found_chapter.expected_max_verse_number:
            # there is a verse missing
            append_error(u'Verse not found, ' + self.name + u' ' +
                         unicode(found_chapter.number) + u':' + unicode(last_verse + 1))
            last_verse += 1

        # look for out-of-order verse numbers
        if verse_num < last_verse:
            append_error(u'Verse out-of-order, ' + self.name + u' ' +
                         unicode(found_chapter.number) + u':' + unicode(verse_num))

        # look for duplicate verse numbers
        if verse_num == last_verse or verse_num in processed_verses:
            append_error(u'Duplicate verse, ' + self.name + u' ' +
                         unicode(found_chapter.number) + u':' + unicode(verse_num))

        # remember for next time
        if verse_num > last_verse:
            last_verse = verse_num

        processed_verses.append(verse_num)

        return last_verse


class Chapter(object):
    def __init__(self, number, expected_max_verse_number):
        """
        :type number: int
        :type expected_max_verse_number: int
        """
        self.number = number  # type: int
        self.expected_max_verse_number = expected_max_verse_number  # type: int
        self.missing_verses = []  # type: list<int>
        self.found = False  # type: bool


def get_versification():
    """
    Get the bible file and parse it into book, chapter and verse information
    :return: list<Book>
    """
    global vrs_file

    # get the list of books
    request = urllib2.urlopen(book_file)
    raw = request.read()
    request.close()
    books = json.loads(raw)

    # get the bible file
    request = urllib2.urlopen(vrs_file)
    raw = request.read()
    request.close()
    lines = [l for l in raw.replace('\r', '').split('\n') if l and l[0:1] != '#']

    scheme = []
    for key, value in books.iteritems():

        book = Book(key, value[0], int(value[1]))

        # find the key in the lines
        for line in lines:
            if line[0:3] == key:
                chapters = line[4:].split()
                for chapter in chapters:
                    parts = chapter.split(':')
                    book.chapters.append(Chapter(int(parts[0]), int(parts[1])))
                scheme.append(book)
                break

    return scheme


def main(resource):
    """
    Get the repo and walk through the files
    """
    vrs = get_versification()  # type: list<Book>

    global downloaded_file, unzipped_dir

    # today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    downloaded_file = '/tmp/{0}'.format(resource.rpartition('/')[2])
    unzipped_dir = '/tmp/{0}'.format(resource.rpartition('/')[2].strip('.zip'))

    if not os.path.isfile(downloaded_file):
        get_zip(resource, downloaded_file)

    unzip(downloaded_file, unzipped_dir)

    for root, dirs, files in os.walk(unzipped_dir):

        # only usfm files
        files = [f for f in files if f[-3:].lower() == 'sfm']

        if not len(files):
            continue

        # there are usfm files, which book is this?
        test_dir = root.rpartition('/')[2]
        book = next((b for b in vrs if b.dir_name == test_dir), None)

        if book:
            book_text = u''
            files.sort()

            for usfm_file in files:
                with codecs.open(os.path.join(root, usfm_file), 'r', 'utf-8') as in_file:
                    book_text += in_file.read() + u'\n'

            # remove superfluous line breaks
            book_text = nl_re.sub(u'\n', book_text)

            # remove \s5 lines
            book_text = s5_re.sub(u'', book_text)

            book.usfm = book_text
            book.verify_chapters_and_verses()


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


def unzip(source, dest):
    with zipfile.ZipFile(source) as zf:
        zf.extractall(dest)


def append_error(message):
    global validation_errors

    print message
    validation_errors.append(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-r', '--resource', dest="resource", default=False,
                        required=True, help="URL of repository zip file.")

    args = parser.parse_args(sys.argv[1:])

    try:
        # initialize
        validation_errors = []
        main(args.resource)

    finally:
        # delete temp files
        if os.path.isfile(downloaded_file):
            os.remove(downloaded_file)

        if os.path.isdir(unzipped_dir):
            shutil.rmtree(unzipped_dir, ignore_errors=True)
