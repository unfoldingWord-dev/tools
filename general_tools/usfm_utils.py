# coding=utf-8

from __future__ import unicode_literals
import re

class tWPhrase:
    """
    A utility for building a tW phrase while parsing USFM with mapped tW links.
    Phrases are consecutive usfm words that have multiple tW links with at least one common tW link
    """

    def __init__(self, index):
        """
        :param index: the starting index of the phrase
        """
        self.__index = index
        # all the lines that make up this phrase
        self.__lines = []
        # a set of unique links that are common between all words in this phrase
        self.__link_set = set()

    def isLineValid(self, line):
        """
        Checks if a line is a valid addition to this phrase.
        Must have links and strong number.
        Must have at least one common link with the rest of the phrase
        :param line:
        :return:
        """
        links = get_usfm3_word_links(line)
        strong = get_usfm3_word_strongs(line)
        if strong and links:
            # TRICKY: empty phrases are valid
            if not len(self.__link_set) > 0 or len(self.__link_set.intersection(set(links))) > 0:
                return True
        return False

    def isComplete(self):
        """
        Checks if the phrase is theoretically complete.
        You should still manually check if any more lines can be added to the phrase.
        This only checks of the link set has been reduced to 1.
        A link set greater than 1 is a sure indicator that it is missing words.
        :return:
        """
        return len(self.__link_set) == 1 and len(self.__lines) > 1


    def addLine(self, line):
        """
        Adds a new line to the phrase
        :param line:
        :return:
        """
        links = get_usfm3_word_links(line)
        if len(self.__link_set):
            self.__link_set = self.__link_set.intersection(set(links))
        else:
            self.__link_set = set(links)
        self.__lines.append(line)

    def startIndex(self):
        """
        Returns the index of the starting line in this phrase
        :return:
        """
        return self.__index

    def endIndex(self):
        """
        Returns the calculated index of the ending line in this phrase
        :return:
        """
        return self.__index + len(self.__lines)

    def lines(self):
        """
        Returns a list of lines that make up this phrase
        :return:
        """
        return self.__lines

    def links(self):
        """
        Returns a list of common links within the phrase
        :return:
        """
        return list(self.__link_set)

    def __str__(self):
        """
        Returns the formatted usfm milestone.
        Note: if the phrase is not complete this may produce multiple links on the milestone.
        :return:
        """
        if not self.__lines or not len(self.__link_set):
            return ''

        formatted_links = list(map((lambda l: 'x-tw="{}"'.format(l)), self.__link_set))
        milestone = ['\k-s | {}'.format(' '.join(formatted_links))]
        for line in self.__lines:
            milestone.append(strip_tw_links(line, self.__link_set))
        closing = '\k-e\*'
        # TRICKY: move punctuation to end of milestone
        punctuation = re.findall(r'\\w\*(.*)$', milestone[-1])
        milestone[-1] = re.sub(r'(\\w\*).*$', r'\g<1>', milestone[-1])
        if punctuation:
            try:
                closing = '{}{}'.format(closing, punctuation[0].encode('utf8'))
            except Exception as e:
                print(u'Failed to move punctuation "{}" from {} at index: {}'.format(punctuation[0], milestone[-1], self.__index))
                raise e

        milestone.append(closing.decode('utf8'))

        return '\n'.join(milestone)

class USFMWordReader:
    """
    A utility for reading words from a USFM file and writing changes to
    the words
    """
    def __init__(self, usfm):
        self.lines = usfm.splitlines()
        self.line = ''
        self.book = None
        self.chapter = None
        self.verse = None
        self.header = []
        self.read_lines = []

        # locate book id
        while not self.book and not self.line.startswith('\\c ') and self.lines:
            self.line = self.lines.pop(0)
            self.header.append(self.line)
            if self.line.startswith('\\id'):
                id = parse_book_id(self.line)
                if id:
                    self.book = id.lower()
                else:
                    raise Exception('Malformed USFM. Unable to parse book id: {}'.format(self.line))

        if not self.book:
            raise Exception('Malformed USFM. Could not find book id.')

    def __str__(self):
        return '\n'.join(self.header + self.read_lines + self.lines)

    def __iter__(self):
        return self

    # Python 3
    def __next__(self):
        return self.findNextWord()

    # Python 2
    def next(self):
        return self.findNextWord()

    def amendLine(self, newLine):
        """
        Amends the line that was last read
        :param newLine:
        :return:
        """
        self.read_lines[-1] = newLine

    def twLinks(self):
        """
        Returns a list of links found in the current line
        :return:
        """
        return get_usfm3_word_links(self.line)

    def location(self):
        """
        Returns the location of the current line
        :return:
        """
        return self.book, self.chapter, self.verse

    def findNextWord(self):
        """
        Returns the next word in the USFM.
        :return: line, strong, index
        """
        self.line = ''
        while (not self.line or not self.line.startswith('\\w ')) and self.lines:
            strong = None
            self.line = self.lines.pop(0)
            self.read_lines.append(self.line)

            # start chapter
            if re.match(r'\\c\b', self.line):
                match = re.findall(r'^\\c\s+(\d+)', self.line, flags=re.IGNORECASE | re.UNICODE)
                if match:
                    self.chapter = unzpad(match[0])
                    self.verse = None
                else:
                    raise Exception('Malformed USFM. Unable to parse chapter number: {}'.format(self.line))

            # start verse
            if re.match(r'\\v\b', self.line):
                match = re.findall(r'^\\v\s+(\d+)', self.line, flags=re.IGNORECASE | re.UNICODE)
                if match:
                    self.verse = unzpad(match[0])
                else:
                    raise Exception('Malformed USFM. Unable to parse verse number: {}'.format(self.line))

            # start original language word
            strong = get_usfm3_word_strongs(self.line)

            # validate
            if self.chapter and self.verse and strong:
                strong = simplify_strong(strong)
                return self.line, strong, len(self.read_lines) - 1
            elif self.line.startswith('\\w'):
                raise Exception('Malformed USFM. USFM tags appear to be out of order.')

        raise StopIteration

    def amendPhrase(self, phrase):
        """
        Amends a set of lines with a phrase.
        TRICKY: this changes the line count so don't reuse the index after calling this.
        :param phrase:
        :type phrase: tWPhrase
        :return:
        """
        new_lines = unicode(phrase).splitlines()
        if len(self.read_lines) > phrase.startIndex() and len(self.read_lines) > phrase.endIndex():
            self.read_lines = self.read_lines[:phrase.startIndex()] + new_lines + self.read_lines[phrase.endIndex():]
        else:
            raise Exception('Phrase indices out of range: {}'.format(phrase))

def parse_book_id(usfm_line):
    """
    Returns the book id from the usfm id flag
    :param usfm_line:
    :return:
    """
    match = re.findall('^\\\id\s+(\w+)(\s+.*)?', usfm_line, flags=re.IGNORECASE | re.UNICODE)
    if match:
        components = match[0]
        if type(components) is tuple:
            # id, name, etc.
            return components[0]
        else:
            # there was only an id
            return components
    return None

def get_usfm3_word_links(usfm3_line):
    """
    Retrieves the tW links from a usfm3 word
    :param usfm3_line:
    :return:
    """
    links = []
    if usfm3_line and re.match(r'.*x-tw=', usfm3_line):
        links = re.findall(r'x-tw="([^"]*)"', usfm3_line, flags=re.IGNORECASE | re.UNICODE)
    return links

def get_usfm3_word_strongs(usfm3_line):
    """
    Retrieves the strongs number from a usfm3 word.
    :param usfm3_line:
    :return:
    """
    strong = None
    if re.match(r'\\w\b', usfm3_line):
        match = re.findall(r'strong="([^"]+)"', usfm3_line, flags=re.IGNORECASE | re.UNICODE)
        if match:
            strong = match[0]
        else:
            print('Error parsing {}'.format(usfm3_line))
            raise Exception('Malformed USFM. Unable to parse strong number: {}'.format(usfm3_line))
    return strong

def simplify_strong(strong):
    """
    This removes the prefix and suffix from the strong number.
    e.g. c:H1961a will become H1961
    :param strong:
    :return:
    """
    simplified = re.sub(r'[a-z]+$', '', strong)
    parts = simplified.split(':')
    return parts[len(parts)-1]

def strip_tw_links(usfm, links=None):
    """
    Removes tW links from a usfm string for backwards compatibility with the legacy tS api.

    :param usfm:
    :param links: only remove these links. If left None all links will be removed. Milestones are always removed.
    :return:
    """
    updated_usfm=usfm
    # remove milestones
    updated_usfm = re.sub(r'\\k-[es].*\n*', '', updated_usfm)
    # remove links
    if links:
        for link in links:
            updated_usfm = re.sub(r'x-tw="' + re.escape(link) + '"\s*', '', updated_usfm)
    else:
        updated_usfm = re.sub(r'x-tw="([^"]*)"\s*', '', updated_usfm)
    return updated_usfm

def strip_word_data(usfm3):
    """
    Removes word data from a USFM 3 string for backwards compatibility with USFM 2
    :param usfm3:
    :return:
    """
    # remove empty word markers
    usfm = re.sub(r'\\w\s*(\|[^\\]*)?\\w\*', r'', usfm3, flags=re.UNICODE)

    # usfm = re.sub(r'\n(?!\\v|\\w|\\zaln-e\\\*.+).*', r'', usfm, flags=re.UNICODE)
    # usfm = re.sub(r'\\w ([^|]+).*', r'\g<1>', usfm, flags=re.UNICODE)    
    # usfm = re.sub(r'\n(?!\\v)', ' ', usfm, flags=re.UNICODE)
    # usfm = re.sub(r' \\zaln-e\\\*', '', usfm, flags=re.UNICODE)
    # usmf = re.sub(r'\\zaln-s.*?(\\w ([^|]+).*?\\w\*[\s\n]*)+(\\zaln-e\\\*\s*)+', r'\g<1>', usfm, flags=re.UNICODE | re.MULTILINE | re.DOTALL)

    # place words on their own lines so regex doesn't break
    usfm = re.sub(r'(\\w\s+)', r'\n\g<1>', usfm, flags=re.UNICODE)
    # remove words
    usfm = re.sub(r'\\w\s+([^|\\]*).*\\w\*', r'\g<1>', usfm, flags=re.UNICODE)
    # group words onto single line
    usfm = re.sub(r'(\n+)([^\\\n +])', r' \g<2>', usfm, flags=re.UNICODE)
    # stick text without markup on previous line
    usfm = re.sub(r'\n^(?![\\])(.*)', ' \g<1>', usfm, flags=re.UNICODE | re.MULTILINE)
    # clean whitespace
    usfm = re.sub(r'^[ \t]*', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'[ \t]*$', '', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r'^\n{2,}', '\n\n', usfm, flags=re.UNICODE | re.MULTILINE)
    usfm = re.sub(r' {2,}', ' ', usfm, flags=re.UNICODE)
    # put spaces back between chapters and verses
    usfm = re.sub(r'(\\s5)', '\n\g<1>', usfm, flags=re.UNICODE | re.MULTILINE)

    # remove the zaln markup but keep the punctuation after zaln-e
    usfm = re.sub(r'\\zaln-[se].*["\*]\n', r'', usfm, flags=re.UNICODE)
    usfm = re.sub(r'\\zaln-s.*" ([^"]+)\n', r'\g<1>\n', usfm, flags=re.UNICODE)
    usfm = re.sub(r'\n\\zaln-e\\\*(.+)', r'\g<1>', usfm, flags=re.UNICODE)
    usfm = re.sub(r'\n(?!\\)', r' ', usfm, flags=re.UNICODE)

    # Move punctuation away from other tags as the case is for `\q2-` in Hebrews 8:10
    usfm = re.sub(r'\\([\w]+)([^\w\s])', r'\1 \2', usfm, flags=re.UNICODE | re.IGNORECASE)
    usfm = re.sub(r'([^\n\s])\\([\w]+)', r'\1 \\\2', usfm, flags=re.UNICODE | re.IGNORECASE | re.MULTILINE)

    return usfm.strip()

def convert_chunk_markers(str):
    """
    Replaces \ts chunk markers to \s5 for backwards compatibility with the legacy tS api
    :param str:
    :return: the converted string
    """
    return re.sub(r'\\ts\b', '\\s5', str)

def usfm3_to_usfm2(usfm3):
    """
    Converts a USFM 3 string to a USFM 2 compatible string
    :param usfm3:
    :return: the USFM 2 version of the string
    """
    return strip_word_data(strip_tw_links(usfm3))

def unzpad(strint):
    """
    Removes zpadding from an integer string
    :param strint: a string that contains an integer value
    :return:
    """
    return '{}'.format(int(strint))
