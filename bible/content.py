from __future__ import print_function, unicode_literals
import json
from future.builtins import chr
import re
from general_tools.print_utils import print_error
from general_tools.url_utils import get_url
import bible_classes


class Book(object):

    # TODO: change these to point to the API when it is available
    api_root = 'https://raw.githubusercontent.com/unfoldingWord-dev/uw-api/develop/static'
    vrs_file = api_root + '/versification/ufw/ufw.vrs'
    book_file = api_root + '/versification/ufw/books.json'
    chunk_url = api_root + '/versification/ufw/chunks/{0}.json'

    verse_re = re.compile(r'(\\v[\u00A0 ][0-9-\u2013\u2014]*\s+)', re.UNICODE)
    chapter_re = re.compile(r'(\\c[\u00A0 ][0-9]+\s*\n)', re.UNICODE)

    # chapter tag with other characters following the chapter number
    bad_chapter_re = re.compile(r'\\c[\u00A0 ][0-9]+([^0-9\n]+)', re.UNICODE)

    # back-slash with no tag character following it
    empty_tag_re = re.compile(r'\n(.*?\\[\u00A0 ]*?\n.*?)\n', re.UNICODE)

    # chapter or verse with missing number
    missing_num_re = re.compile(r'(\\[cv][\u00A0 ][^0-9]+?)[\u00A0\s]+?', re.UNICODE)

    # verse with no text
    missing_verse_text_re = re.compile(r'(\\v[\u00A0 ][0-9-\u2013\u2014]*[\u00A0 ]*[\r\n])', re.UNICODE)

    # git merge conflicts
    git_conflict_re = re.compile(r'<<<<<<<.*?=======.*?>>>>>>>', re.UNICODE | re.DOTALL)

    tag_re = re.compile(r'\s(\\\S+)\s', re.UNICODE)
    bad_tag_re = re.compile(r'(\S\\\S+)\s', re.UNICODE)
    tag_exceptions = ('\\f*', '\\fe*', '\\fqa*', '\\qs*')
    nbsp_re = re.compile(r'(\\[a-z0-9]+)([\u00A0])', re.UNICODE)

    # clean-up usfm
    s5_re = re.compile(r'\\s5\s*')
    nl_re = re.compile(r'\n{2,}')

    # initialization
    book_skeletons = None  # type: list<Book>

    def __init__(self, book_id, name, number):
        """
        :type book_id: str|unicode
        :type name: str|unicode
        :type number: int
        """
        self.book_id = book_id       # type: str
        self.name = name             # type: str
        self.number = number         # type int
        self.chapters = []           # type: list<Chapter>
        self.chunks = []             # type: list<Chunk>
        self.dir_name = str(number).zfill(2) + '-' + book_id  # type: str
        self.usfm = None             # type: str
        self.validation_errors = []  # type: list<str>
        self.header_usfm = ''        # type: str

    def number_string(self):
        return str(self.number).zfill(2)

    def get_chapter(self, num):
        return next((chapter for chapter in self.chapters if chapter.number == num), None)

    def set_usfm(self, new_usfm):

        # remove Windows line endings
        temp = new_usfm.replace('\r\n', '\n')

        # replace nbsp in USFM tags with normal space (32)
        temp = self.nbsp_re.sub(r'\1 ', temp)

        self.usfm = temp

    def build_usfm_from_chapters(self):
        self.usfm = self.header_usfm

        self.chapters.sort(key=lambda c: c.number)
        for chapter in self.chapters:
            self.usfm += "\n\n\\c {0}\n{1}".format(chapter.number, chapter.usfm)

    def clean_usfm(self):

        # remove superfluous line breaks
        self.usfm = self.nl_re.sub('\n', self.usfm)

        # remove \s5 lines
        self.usfm = self.s5_re.sub('', self.usfm)

    def verify_chapters_and_verses(self, same_line=False):

        if same_line:
            print('Verifying ' + self.book_id + '... ', end=' ')
        else:
            print('Verifying ' + self.book_id)

        # check for git conflicts
        conflicts = self.git_conflict_re.findall(self.usfm)
        if conflicts:
            if len(conflicts) == 1:
                self.append_error('There is 1 Git conflict in {0}'.format(self.book_id))
            else:
                self.append_error('There are {0} Git conflicts in {1}'.format(len(conflicts), self.book_id))

        # check for bad chapter tags
        for bad_chapter in self.bad_chapter_re.finditer(self.usfm):
            if bad_chapter.group(1).strip():
                self.append_error('Invalid chapter marker: "{0}"'.format(bad_chapter.group(0)))

        # check for empty tags
        for bad_tag in self.empty_tag_re.finditer(self.usfm):
            if bad_tag.group(1).strip():
                self.append_error('Empty USFM marker: "{0}"'.format(bad_tag.group(1)))

        # check for chapter or verse tags without numbers
        for no_num in self.missing_num_re.finditer(self.usfm):
            self.append_error('Chapter or verse tag without a number: "{0}"'.format(no_num.group(1)))

        # split into chapters
        self.check_chapters(self.chapter_re.split(self.usfm))

    def verify_usfm_tags(self, same_line=False):

        if same_line:
            print('Checking USFM in ' + self.book_id + '... ', end=' ')
        else:
            print('Checking USFM in ' + self.book_id)

        # split into chapters
        chapters_usfm = self.chapter_re.split(self.usfm)
        current_chapter = '\c 0'

        for chapter_usfm in chapters_usfm:
            if chapter_usfm[0:2] == '\c':
                current_chapter = chapter_usfm.strip()
            else:
                # get all tags
                matches = re.findall(self.tag_re, chapter_usfm)
                for match in matches:
                    if not bible_classes.USFM.is_valid_tag(match):

                        # check the exceptions
                        if not match.startswith(self.tag_exceptions):
                            self.append_error('Invalid USFM tag in ' + current_chapter + ': ' + match)

                # check for bad tags
                matches = re.findall(self.bad_tag_re, chapter_usfm)
                for match in matches:

                    # check the exceptions
                    if not match.endswith(self.tag_exceptions):
                        self.append_error('Invalid USFM tag in ' + current_chapter + ': ' + match)

                # check for verses with no text
                for no_text in self.missing_verse_text_re.finditer(chapter_usfm):
                    self.append_error('Verse tag without text in {0}: "{1}"'.format(current_chapter,
                                                                                    no_text.group(1).strip()))

    def check_chapters(self, blocks):

        self.header_usfm = ''

        # find the first chapter marker, should be the second block
        # the first block should be everything before the first chapter marker
        current_index = 0
        while blocks[current_index][:2] != '\c':
            self.header_usfm += blocks[current_index].rstrip()
            current_index += 1

        # loop through the blocks
        while current_index < len(blocks):

            # parse the chapter number
            test_num = blocks[current_index][3:].strip()
            if not test_num.isdigit():
                self.append_error('Invalid chapter number, ' + self.book_id + ' "' + test_num + '"')

            # compare this chapter number to the numbers from the bible file
            try:
                chapter_num = int(test_num)
            except ValueError:
                self.append_error('Invalid chapter number, ' + self.book_id + ' "' + blocks[current_index] + '"')
                continue

            found_chapter = next((c for c in self.chapters if c.number == chapter_num), None)  # type: Chapter
            if not found_chapter:
                self.append_error('Invalid chapter number, ' + self.book_id + ' "' + test_num + '"')

            else:
                found_chapter.found = True

                # make sure there is a chapter body
                if current_index + 1 >= len(blocks):
                    self.append_error('No verses found in ' + self.book_id + ' ' + str(found_chapter.number))

                else:
                    # split the chapter text into verses
                    self.check_verses(found_chapter, self.verse_re.split(blocks[current_index + 1]))

                    # remember for later
                    found_chapter.usfm = blocks[current_index] + '\n' + blocks[current_index + 1] + '\n'

            # increment the counter
            current_index += 2

    def check_verses(self, found_chapter, verse_blocks):

        last_verse = 0
        processed_verses = []

        # go to the first verse marker
        current_cv_index = 0
        while current_cv_index < len(verse_blocks) and verse_blocks[current_cv_index][:2] != '\\v':
            current_cv_index += 1

        # are all the verse markers missing?
        if current_cv_index >= len(verse_blocks):
            self.append_error('All verse markers are missing for ' + self.book_id + ' ' + str(found_chapter.number))
            return

        # verses should be sequential, starting at 1 and ending at found_chapter.num_verses
        while current_cv_index < len(verse_blocks):

            # parse the verse number
            test_num = verse_blocks[current_cv_index][3:].strip()

            bridge_marker = None  # type: str

            # check for invalid dash characters in verse bridge
            # en dash = \u2013, 8211
            # em dash = \u2014, 8212
            if chr(8211) in test_num:
                bridge_marker = chr(8211)
                self.append_error('Invalid verse bridge (en dash used), ' + self.book_id + ' ' +
                                  str(found_chapter.number) + ':' + test_num)

            elif chr(8212) in test_num:
                bridge_marker = chr(8212)
                self.append_error('Invalid verse bridge (em dash used), ' + self.book_id + ' ' +
                                  str(found_chapter.number) + ':' + test_num)

            # is this a verse bridge?
            elif '-' in test_num:
                bridge_marker = '-'

            if bridge_marker:
                nums = test_num.split(bridge_marker)
                if len(nums) != 2 or not nums[0].strip().isdigit() or not nums[1].strip().isdigit():
                    self.append_error('Invalid verse bridge, ' + self.book_id + ' ' +
                                      str(found_chapter.number) + ':' + test_num)

                else:
                    for bridge_num in range(int(nums[0].strip()), int(nums[1].strip()) + 1):
                        last_verse = self.check_this_verse(found_chapter, bridge_num, last_verse, processed_verses)

            else:
                if not test_num.isdigit():

                    # the verse number isn't a number
                    self.append_error('Invalid verse number, ' + self.book_id + ' ' +
                                      str(found_chapter.number) + ':' + test_num)

                else:
                    verse_num = int(test_num)
                    last_verse = self.check_this_verse(found_chapter, verse_num, last_verse, processed_verses)

            current_cv_index += 2

        # are there verses missing from the end
        if last_verse < found_chapter.expected_max_verse_number:
            self.append_error('Verses ' + str(last_verse + 1) + ' through ' +
                              str(found_chapter.expected_max_verse_number) + ' for ' + self.book_id + ' ' +
                              str(found_chapter.number) + ' are missing.')

    def check_this_verse(self, found_chapter, verse_num, last_verse, processed_verses):

        # is this verse number too large?
        if verse_num > found_chapter.expected_max_verse_number:
            self.append_error('Invalid verse number, ' + self.book_id + ' ' +
                              str(found_chapter.number) + ':' + str(verse_num))

        # look for gaps in the verse numbers
        while verse_num > last_verse + 1 and last_verse < found_chapter.expected_max_verse_number:
            # there is a verse missing
            self.append_error('Verse not found, ' + self.book_id + ' ' +
                              str(found_chapter.number) + ':' + str(last_verse + 1))
            last_verse += 1

        # look for out-of-order verse numbers
        if verse_num < last_verse:
            self.append_error('Verse out-of-order, ' + self.book_id + ' ' +
                              str(found_chapter.number) + ':' + str(verse_num))

        # look for duplicate verse numbers
        if verse_num == last_verse or verse_num in processed_verses:
            self.append_error('Duplicate verse, ' + self.book_id + ' ' +
                              str(found_chapter.number) + ':' + str(verse_num))

        # remember for next time
        if verse_num > last_verse:
            last_verse = verse_num

        processed_verses.append(verse_num)

        return last_verse

    def append_error(self, message, prefix='** '):

        print_error(prefix + message)
        self.validation_errors.append(message)

    def get_chunks(self):

        chunk_str = get_url(self.chunk_url.format(self.book_id.lower()))
        if not chunk_str:
            raise Exception('Could not load chunks for ' + self.book_id)

        chunks_obj = json.loads(chunk_str)

        # chunk it
        for chapter in chunks_obj:
            for first_verse in chapter['first_verses']:
                self.chunks.append(Chunk(chapter['chapter'], first_verse))
        self.chunks = sorted(self.chunks, key=lambda c: '{0}-{1}'.format(str(c.chapter_num).zfill(3),
                                                                         str(c.first_verse).zfill(3)))
        return self.chunks

    def apply_chunks(self):

        if not self.chunks:
            self.get_chunks()

        for chap in self.chapters:
            chap.apply_chunks([c for c in self.chunks if c.chapter_num == chap.number])

        new_usfm = ''
        for chap in self.chapters:
            new_usfm += chap.usfm + '\n'

        # extra space between header and first chapter
        self.usfm = self.header_usfm + '\n\n' + new_usfm

    @staticmethod
    def create_book(book_key):
        """
        Returns the requested initialized Book object
        :param str|unicode book_key: Either the 3 letter USFM code or a 6 character repo directory name, like 01-GEN.
        :return: Book|None
        """
        if not Book.book_skeletons:

            # get the list of books
            books = json.loads(get_url(Book.book_file))

            # get the bible file
            raw = get_url(Book.vrs_file)
            lines = [l for l in raw.replace('\r', '').split('\n') if l and l[0:1] != '#']

            scheme = []

            for key, value in iter(books.items()):

                book = Book(key, value[0], int(value[1]))

                # find the key in the lines
                line = [line for line in lines if line[0:3] == key]
                if not line:
                    raise Exception('Could not load chapter information for ' + key)

                chapters = line[0][4:].split()
                for chapter in chapters:
                    parts = chapter.split(':')
                    book.chapters.append(Chapter(int(parts[0]), int(parts[1])))
                scheme.append(book)

            Book.book_skeletons = scheme

        # is the book_key a directory name?
        if len(book_key) == 3:
            found = [book for book in Book.book_skeletons if book.book_id == book_key]
        else:
            found = [book for book in Book.book_skeletons if book.dir_name == book_key]

        return found[0] if found else None


class Chapter(object):

    # lines that are just a \q tag
    q_alone_re = re.compile(r'^\\q[0-9a-z]*\s*$', re.UNICODE)

    def __init__(self, number, num_verses):
        """
        :type number: int
        :type num_verses: int
        """
        self.number = number  # type: int
        self.num_verses = num_verses  # type: int
        self.missing_verses = []  # type: list<int>
        self.found = False  # type: bool
        self.usfm = ''

    def apply_chunks(self, chunks):
        """

        :type chunks: list<Chunk>
        """
        previous_line = ''

        # insert the first marker now
        newlines = ['\n\\s5', ]
        i = 0

        for line in self.usfm.splitlines():
            if line in ['', ' ', '\n']:
                continue

            if i < len(chunks):

                # we already inserted the beginning marker
                if chunks[i].first_verse == 1:
                    i += 1

                if i < len(chunks):
                    verse_search = re.search(r'\\v[\u00A0\s]{0}[\s-]'.format(chunks[i].first_verse), line)
                    if verse_search:

                        # insert before \p and \q, not after
                        if previous_line == '\\p':
                            newlines.insert(len(newlines) - 1, '\n\\s5')
                        elif self.q_alone_re.search(previous_line):
                            newlines.insert(len(newlines) - 1, '\n\\s5')
                        else:
                            newlines.append('\n\\s5')

                        i += 1

            newlines.append(line)
            previous_line = line

        self.usfm = '\n'.join(newlines)


class Chunk(object):
    def __init__(self, chapter, first_verse):
        self.chunk_id = str(chapter).zfill(2) + '-' + str(first_verse).zfill(2)
        self.chapter_num = chapter
        self.first_verse = first_verse

    def __str__(self):
        return self.chunk_id
