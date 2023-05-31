# -*- coding: utf-8 -*-
# Used by usfm_cleanup.py.
# Substitutions in this file convert straight double quotes to curly double quotes.
# To be used in languages where the single quote (apostrophe) is a word-forming character.
# These substitutions are applied after some regular expressions replacements have been made.

# subs is a list of tuples to be used for string substitutions.
subs = [
# Convert open quote marks
	('"“', '““'),
	('“"', '““'),
# Convert closing quote marks
	('"”', "””"),
	('”"', "””"),
]

import re
quote0_re = re.compile(r'\s("+)[\w\']+("+)\s')     # a single word in quotes
quote1_re = re.compile(r' ("+)[\w\']')     # SPACE quotes word => open quotes
quote2_re = re.compile(r': ("+)')     # colon SPACE quotes => open quotes
quote3_re = re.compile(r'[,;]("+) ')     # comma/semicolon quotes SPACE => close quotes
quote4_re = re.compile(r'[\.!\?]("+)')     # period/bang/question quotes => close quotes
quote5_re = re.compile(r'[\w\']("+) *\n')        # word quotes EOL => close quotes
opentrans = str.maketrans('"', '“')
closetrans = str.maketrans('"', '”')

# Changes straight quotes to curly quotes where context suggests with very high confidence.
def promoteQuotes(str):
    pos = 0
    snippet = quote0_re.search(str, pos)
    while snippet:
        # if len(snippet.group(1)) == 1 and len(snippet.group(1)) == 1:       # TEMPORARY!!!!!!
        if snippet.group(1) == snippet.group(2) and len(snippet.group(1)) == 1:
            (i,j) = (snippet.start()+1, snippet.end()-1)
            str = str[0:i] + snippet.group(1).translate(opentrans) + str[i+1:j-1] + snippet.group(2).translate(closetrans) + str[j:]
        pos = snippet.end()
        snippet = quote0_re.search(str, pos)

    snippet = quote1_re.search(str)
    while snippet:
        (i,j) = (snippet.start()+1, snippet.end()-1)
        str = str[0:i] + snippet.group(1).translate(opentrans) + str[j:]
        snippet = quote1_re.search(str)

    snippet = quote2_re.search(str)
    while snippet:
        (i,j) = (snippet.start()+2, snippet.end())
        str = str[0:i] + snippet.group(1).translate(opentrans) + str[j:]
        snippet = quote2_re.search(str)

    snippet = quote3_re.search(str)
    while snippet:
        (i,j) = (snippet.start()+1, snippet.end()-1)
        str = str[0:i] + snippet.group(1).translate(closetrans) + str[j:]
        snippet = quote3_re.search(str)

    snippet = quote4_re.search(str)
    while snippet:
        (i,j) = (snippet.start()+1, snippet.end())
        str = str[0:i] + snippet.group(1).translate(closetrans) + str[j:]
        snippet = quote4_re.search(str)

    snippet = quote5_re.search(str)
    while snippet:
        (i,j) = (snippet.start()+1, snippet.start() + 1 + len(snippet.group(1)))
        str = str[0:i] + snippet.group(1).translate(closetrans) + str[j:]
        snippet = quote5_re.search(str)

    for pair in subs:
        str = str.replace(pair[0], pair[1])
    return str
