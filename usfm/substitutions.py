# -*- coding: utf-8 -*-
# substitutions module, used by translate.py.
# An ordered list of tuples to be used for string substitutions.

#import re

subs = [
# Remove \u200b and \u200c where they have no effect or don't belong.
    (" \u200b", " "),   # next to a space
    ("\u200b ", " "),
    (" \u200c", " "),
    ("\u200c ", " "),
    ("\"\u200b", "\""),   # next to quotes
    ("\u200b\"", "\""),
    ("\"\u200c", "\""),
    ("\u200c\"", "\""),
    ("'\u200b", "'"),
    ("\u200b'", "'"),
    ("'\u200c", "'"),
    ("\u200c'", "'"),
    ("\u200b\n", "\n"),   # before line break
    ("\u200c\n", "\n"),
    ("\u200c\u200c", "\u200c"),     #duplicates
    ("\u200b\u200b", "\u200b"),
    ("*​\u200b", "* "),    # (specific to Laotian)

    ("''''", "'\""),
    ("'''", "'\""),
    ("''", "\""),
    ("´", "'"),
    (" <<", " «"),
    (":<<", ": «"),
    (",<<", ", «"),
#    (",“", ", “"),     # unsafe because of improper use of commas and quotes
    (" >>", "»"),
    (">> ", "» "),
#    (" <", ", «"),
#    (">", "»"),

    # Doubled marks
	(",,", ","),
	(";;", ";"),
	("::", ":"),

#	("?.", "?"),
	(".?", "?"),
	(".!", "!"),
	("!.", "!"),

# Fix space before/after opening quote mark (but not straight quotes!)
	(", “ ", ", “"),
	("? “ ", "? “"),
	("! “ ", "! “"),
	(": “ ", ": “"),
	(". “ ", ". “"),
	(":«", ": «"),
	(":\"", ": \""),
	("« ", "«"),

# Fix space before closing quote mark
	(". \"\n", ".\"\n"),
	(". '\n", ".'\n"),
	(". \"\n", ".\"\n"),
	(". \"\n", ".\"\n"),
	(". \"\n", ".\"\n"),
	(". \"\n", ".\"\n"),
	("? \"\n", "?\"\n"),
	("! \"\n", "!\"\n"),
	(" »", "»"),
	(". ”", ".”"),
	(". ’", ".’"),
	("! ”", "!”"),
	("! ’", "!’"),
	("? ”", "?”"),
	("? ’", "?’"),

    ("( ", "("),
    (" )", ")"),
    ("\\f+", "\\f +"),
    ("+\\f", "+ \\f"),
    ("\\wj \\wj\*", " "),

# Remove space before phrase ending punctuation
	(" :", ":"),
	(" ,", ","),
	(" !", "!"),
	(" ?", "?"),
	(" . ", ". "),  # more carful with periods because of .. and ...
	(" .\n", ".\n"),
	(" .\"\n", ".\"\n"),
	(" .\" ", ".\" "),
	(" .'\n", ".'\n"),
	(" .' ", ".' "),
	(" .»", ".»"),
	(" .’", ".’"),
	(" .”", ".”")
]