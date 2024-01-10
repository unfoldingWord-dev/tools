# -*- coding: utf-8 -*-
# substitutions module, used by usfm_cleanup.py.
# An ordered list of tuples to be used for string substitutions.

# Some UTF-8 special characters
# E2 80 8B = \u200b - zero width space. See https://en.wikipedia.org/wiki/Zero-width_space
# E2 80 8C = \u200c - zero width non-joiner. See https://en.wikipedia.org/wiki/Zero-width_non-joiner
# E2 80 8D = \u200d - zero width joiner

subs = [
    # Temporary subs
    #("Ye sus", "Yesus"),
    #("Yes us", "Yesus"),
    #("Yesu s", "Yesus"),
    #("Pet rus", "Petrus"),
    #("Petr us", "Petrus"),
    #("Patrus", "Petrus"),
    #("Kris tus", "Kristus"),
    #("Krist us", "Kristus"),
    #("Kristu s", "Kristus"),
    #("Yeru salem", "Yerusalem"),
    #("Yerusa lem", "Yerusalem"),
    #("Ma ria", "Maria"),
    #("Mar ia", "Maria"),
    #("Mari a", "Maria"),
    #("Tuha n", "Tuhan"),
    #("Yohani s", "Yohanis"),
    #("Pau lus", "Paulus"),
    #("Paul us", "Paulus"),
    #("Paulu s", "Paulus"),
    #("Sau lus", "Saulus"),
    #("Saul us", "Saulus"),
    #("Saulu s", "Saulus"),
    #("Is rael", "Israel"),
    #("", ""),

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

# Fix some quote marks
    ("''''", "'\""),
    ("'''", "'\""),
    ("''", "\""),
    ("’’", "”"),
    ("‘‘", "“"),
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

	("?.\n", "?\n"),
	(".?", "?"),
	(".!", "!"),
	("!.", "!"),
	("?\".", "?\""),
	("\".\n", ".\"\n"),
	("'.\n", ".'\n"),

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