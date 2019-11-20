"""
Class for a pretty HTML parser for BeautifulSoup
"""
from html import escape
from html.parser import HTMLParser

class PrettyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.__t = 0
        self.lines = []
        self.__current_line = ''
        self.__current_tag = ''
        self.__prev_is_text = False

    @staticmethod
    def __attr_str(attrs):
        return ' '.join('{}="{}"'.format(name, escape(value)) for (name, value) in attrs)

    def handle_starttag(self, tag, attrs):
        if tag != self.__current_tag and (tag != 'a' or not self.__prev_is_text):
            self.lines += [self.__current_line]
            self.__current_line = '\t' * self.__t
            self.__t += 1
        self.__current_line += '<{}>'.format(tag + (' ' + self.__attr_str(attrs) if attrs else ''))
        self.__current_tag = tag
        self.__prev_is_text = False

    def handle_endtag(self, tag):
        self.__t -= 1
        if tag != self.__current_tag:
            self.lines += [self.__current_line]
            self.lines += ['\t' * self.__t + '</{}>'.format(tag)]
            self.__current_line = ''
        elif tag == 'a':
            self.__current_line += '</{}>'.format(tag)
        else:
            self.lines += [self.__current_line + '</{}>'.format(tag)]
            self.__current_line = ''

    def handle_data(self, data):
        self.__prev_is_text = True
        self.__current_line += data

    def get_parsed_string(self):
        return '\n'.join(l for l in self.lines if l)
