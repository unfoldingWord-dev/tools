# This was taken from https://github.com/jboy/distil/blob/master/distil/unicode_string_utils.py - Richard Mahn
#
#
# unicode_string_utils.py: Utility functions for Unicode strings.
# coding=utf-8
#
# Copyright 2011 James Boyden <jboy@jboy.id.au>
#
# This file is part of Distil.
#
# Distil is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License, version 3, as
# published by the Free Software Foundation.
#
# Distil is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License,
# version 3, for more details.
#
# You should have received a copy of the GNU General Public License,
# version 3, along with this program; if not, see
# http://www.gnu.org/licenses/gpl-3.0.html


import codecs
import string
import sys
import types

import unidecode  # http://pypi.python.org/pypi/Unidecode/0.04.6

from collections import namedtuple


def open_file_read_unicode(fname, which_error_handler="replace-if-possible"):
  """Open and read the file named 'fname', returning a Unicode string.

  It will also try to gloss over any Unicode-decoding errors that may occur,
  such as:
    UnicodeDecodeError: 'utf8' codec can't decode byte 0x97 in position 867373: invalid start byte

  It will return the string read (as a Unicode string object), plus a boolean
  value of whether the string contains non-ASCII Unicode.  It will also return
  a list of objects describing any Unicode-decoding errors that occurred.

  (So IN SUMMARY, it returns a tuple of THREE ITEMS.  I HOPE THIS IS CLEAR.)
  """

  error_handler = codecs.lookup_error(which_error_handler)
  error_handler.reset()

  # Note that we open the file with the encoding "utf-8-sig", since this
  # encoding will remove the BOM (byte-order mark) if present.
  # See http://docs.python.org/library/codecs.html ; search for "-sig".
  f = codecs.open(fname, encoding="utf-8-sig", errors=which_error_handler)

  # 's' will be a Unicode string, which may or may not contain non-ASCII.
  s = f.read()

  return (s, contains_non_ascii_unicode(s), error_handler.errors)


ErrorDescription = namedtuple('ErrorDescription',
    'encoding reason start end bad_data result replacement preceding following')


class ReplaceErrorsIfPossible(object):
  """Provides an error-handling function to be supplied to 'codecs.register_error'.

  If possible, return a useful replacement for the malformed data and the
  position where decoding should continue; otherwise, raise the exception
  just to really mess with everyone.
  """

  def __init__(self, fallback_replacement='?', try_cp1252=True):
    self.fallback_replacement = fallback_replacement
    self.try_cp1252 = try_cp1252
    self.errors = []

  def reset(self):
    self.errors = []

  def __call__(self, e):
    """An error-handling function to be supplied to 'codecs.register_error'.

    'e' will be an instance of type UnicodeDecodeError (which is currently
    handled) or UnicodeTranslateError (which is currently NOT handled).

    See http://docs.python.org/library/codecs.html#codecs.register_error for
    more details.
    """

    # 1. Code-point 0x97 was causing an error:
    #   UnicodeDecodeError: 'utf8' codec can't decode byte 0x97 in position 867373: invalid start byte
    #
    # An explanation (Praise Be to Stack Overflow!):
    #
    # """In your case, fortunately, your error message makes it obvious. It's
    # almost sure bet that you are dealing with Microsoft's annoying cp1252,
    # due to the presence of a 0x97 character. In latin-1, this codepoint holds
    # a control character, "END OF GUARDED AREA" which is almost never used.
    # You will never see this precise error with utf-8 as 0x97 is not a valid
    # character-leading byte. In cp1252, on the other hand, it is the very
    # common emdash."""
    #  -- http://stackoverflow.com/questions/2508847/convert-or-strip-out-illegal-unicode-characters
    #
    # Also:
    #
    # """The confusion arises because character 151 is a dash in Windows code
    # page 1252 (Western European). Many people think cp1252 is the same thing
    # as ISO-8859-1, but in reality it's not: the characters in the C1 range
    # (128 to 159) are different."""
    #  -- http://stackoverflow.com/questions/631406/what-is-the-difference-between-em-dash-151-and-8212
    #
    # Note that 0x97 is 151 in decimal, and 0x2014 is 8212.
    #
    #
    # 2. Next, code-point 0x92 was causing an error:
    #   UnicodeDecodeError: 'utf8' codec can't decode byte 0x92 in position 882259: invalid start byte
    #
    # Also from Stack Overflow:
    #
    # """0x92 in CP-1252 (default Windows code page) is a backquote character,
    # which looks kinda like an apostrophe. This code isn't a valid ASCII
    # character, and it isn't valid in IS0-8859-1 either."""
    #
    #
    # 3. In summary, many of these problems seem to be caused by CP-1252
    # (the default MS Windows code page for Western Europe).
    #
    # Also, here are some tables and explanations of CP-1252:
    #  http://unicode.org/Public/MAPPINGS/VENDORS/MICSFT/WINDOWS/CP1252.TXT
    #  http://en.wikipedia.org/wiki/Windows-1252
    #

    # The error
    #   'utf8' codec can't decode byte 0x97 in position 867373: invalid start byte"
    # is stored in the UnicodeDecodeError instance as:
    #   (e.encoding, e.end, e.reason, e.start) =
    #   ('utf8', 867374, 'invalid start byte', 867373)
    # with the (whole) input string contained in 'e.object'.

    bad_data = e.object[e.start:e.end]
    if len(bad_data) > 1:
      # It's a string rather than a single code-point.
      raise e

    preceding = e.object[e.start-40:e.start]
    following = e.object[e.end:e.end+40]

    bad_code_point = ord(bad_data)
    if self.try_cp1252 and map_cp1252_to_unicode.has_key(bad_code_point):
      replacement = map_cp1252_to_unicode[bad_code_point]

      error = ErrorDescription(e.encoding, e.reason, e.start, e.end, bad_data,
          "replaced using CP-1252", replacement, preceding, following)
      self.errors.append(error)

      return (replacement, e.end)
    else:
      replacement = self.fallback_replacement

      error = ErrorDescription(e.encoding, e.reason, e.start, e.end, bad_data,
          "replaced using fallback replacement", replacement, preceding, following)
      self.errors.append(error)

      return (unicode(replacement), e.end)


# "Map CP1252-specific characters to their Unicode counterparts", from
#  http://effbot.org/zone/unicode-gremlins.htm
# Thanks Effbot!
map_cp1252_to_unicode = {
  # from http://www.microsoft.com/typography/unicode/1252.htm
  0x80: u"\u20AC",  # EURO SIGN
  0x82: u"\u201A",  # SINGLE LOW-9 QUOTATION MARK
  0x83: u"\u0192",  # LATIN SMALL LETTER F WITH HOOK
  0x84: u"\u201E",  # DOUBLE LOW-9 QUOTATION MARK
  0x85: u"\u2026",  # HORIZONTAL ELLIPSIS
  0x86: u"\u2020",  # DAGGER
  0x87: u"\u2021",  # DOUBLE DAGGER
  0x88: u"\u02C6",  # MODIFIER LETTER CIRCUMFLEX ACCENT
  0x89: u"\u2030",  # PER MILLE SIGN
  0x8A: u"\u0160",  # LATIN CAPITAL LETTER S WITH CARON
  0x8B: u"\u2039",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
  0x8C: u"\u0152",  # LATIN CAPITAL LIGATURE OE
  0x8E: u"\u017D",  # LATIN CAPITAL LETTER Z WITH CARON
  0x91: u"\u2018",  # LEFT SINGLE QUOTATION MARK
  0x92: u"\u2019",  # RIGHT SINGLE QUOTATION MARK
  0x93: u"\u201C",  # LEFT DOUBLE QUOTATION MARK
  0x94: u"\u201D",  # RIGHT DOUBLE QUOTATION MARK
  0x95: u"\u2022",  # BULLET
  0x96: u"\u2013",  # EN DASH
  0x97: u"\u2014",  # EM DASH
  0x98: u"\u02DC",  # SMALL TILDE
  0x99: u"\u2122",  # TRADE MARK SIGN
  0x9A: u"\u0161",  # LATIN SMALL LETTER S WITH CARON
  0x9B: u"\u203A",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
  0x9C: u"\u0153",  # LATIN SMALL LIGATURE OE
  0x9E: u"\u017E",  # LATIN SMALL LETTER Z WITH CARON
  0x9F: u"\u0178",  # LATIN CAPITAL LETTER Y WITH DIAERESIS
}


REPLACE_ERRORS_IF_POSSIBLE = ReplaceErrorsIfPossible('?')
codecs.register_error("replace-if-possible", REPLACE_ERRORS_IF_POSSIBLE)


REPLACE_ALL_ERRORS = ReplaceErrorsIfPossible('?', False)
codecs.register_error("replace-all", REPLACE_ALL_ERRORS)


def contains_non_ascii_unicode(s):
  """Determine whether the Unicode string 's' contains non-ASCII code-points."""

  # Surely there must be a better way to do this?  There's nothing I can see in
  # the stdlib 'unicodedata' module:
  #  http://docs.python.org/library/unicodedata.html
  #
  # Note that list comprehensions are faster than 'map' invocations, when
  # the 'map' invocation would involve a lambda:
  #  http://stackoverflow.com/questions/1247486/python-list-comprehension-vs-map
  #
  # A generator expression will be more memory-efficient than a list comp:
  #  http://www.python.org/dev/peps/pep-0289/
  #
  # I assume the use of 'any' (a built-in "in C" function) will be very fast
  # in terms of iteration and minimal in memory usage; hopefully it will also
  # short-circuit the evaluation of the generator expr, so only as many
  # iterations of the generator expr will be performed as are necessary to find
  # the first non-ASCII code point.

  #return any(((ord(c) > 127) for c in s))

  # Update:  According to Stack Overflow,
  #  http://stackoverflow.com/questions/196345/how-to-check-if-a-string-in-python-is-in-ascii
  # the above approach is inefficient and unPythonic.
  # Instead...
  try:
    s.decode('ascii')
  except UnicodeEncodeError:
    return True
  else:
    return False


def replace_non_ascii_unicode(s, replacement='?'):
  return "".join([(c if (ord(c) < 128) else replacement) for c in s])


def transliterate_to_ascii(s):
  """Convert any non-ASCII Unicode code points to their closest equivalents in ASCII.

  The argument is assumed to be a Unicode string; a Unicode string will be returned.
  """

  # Note that 'unidecode' expects its argument to be a Unicode string;
  # if the argument is a regular string, the wrong transformations will occur.
  # For example:
  #
  # >>> s = 'Don\xe2\x80\x99t'
  # >>> s
  # 'Don\xe2\x80\x99t'
  # >>> print s
  # Don't
  # >>> unidecode.unidecode(s)
  # 'Donat'
  # >>> s.decode('utf8')
  # u'Don\u2019t'
  # >>> unidecode.unidecode(s.decode('utf8'))
  # u"Don't"
  if type(s) != types.UnicodeType:
    # Assume that it's a regular string in UTF-8 encoding.
    s = s.decode('utf8')

  # Note also that we must wrap the return-value of 'unidecode' in a call to 'unicode',
  # since 'unidecode' will return a *regular* string (rather than a Unicode string)
  # if all the code points were non-ASCII in the string that was supplied.
  return unicode(unidecode.unidecode(s))


class StripPunctuationAndWhitespace(object):
  """Remove all punctuation and whitespace other than that which is explicitly allowed."""

  def __init__(self, chars_to_allow=""):
    """Initialise the object to remove all punctuation and whitespace other than
    the characters in the string 'chars_to_allow'.
    """

    # Define a translation table suitable to be supplied to the Unicode String
    # method 'translate'.
    #  http://docs.python.org/library/stdtypes.html#str.translate
    # We want this to remove all punctuation and whitespace.
    #
    # A similar approach is recommended at
    #  http://stackoverflow.com/questions/1324067/how-do-i-get-str-translate-to-work-with-unicode-strings
    #
    # A non-Unicode version, with timings for four different approaches
    # (sets, regex, translate, replace) is described at
    #  http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    # Basically, translate is the fastest; regex takes 3x as long as translate;
    # sets takes 3x as long as regex; replace takes 4x as long as regex.
    #
    # Note: List comprehensions are faster than 'map' when the 'map' expression
    # would involve a lambda expression:
    #  http://stackoverflow.com/questions/1247486/python-list-comprehension-vs-map
    # See also:
    #  http://www.python.org/doc/essays/list2str.html

    self.translation_table = dict(
        (ord(c), None) for c in
            (set(string.punctuation + string.whitespace) - set(chars_to_allow)))

  def __call__(self, s):
    """Remove punctuation and whitespace from Unicode String 's'.

    Note that 's' must be a *Unicode* string, not just a regular string.
    """
    return s.translate(self.translation_table)
