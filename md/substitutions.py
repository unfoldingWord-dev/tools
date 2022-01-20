# -*- coding: utf-8 -*-
# substitutions module, used by md_cleanup.py.
# An ordered list of tuples to be used for string substitutions.
# The first element is a regular express, the second is a string to replace it with
#

subs = [
	("http://ufw.io/[[rc://", "[[rc://"),
	("****", ""),
	("*__", "* __"),

	# HTML / V-MAST section
	("</ ", "</"),      #malformed html
#	("< ", "<"),      # commented out because this is not always an issue of malformed html
	("&nbsp;", " "),
	("&#34;", "\""),
	("&#39;", "'"),
	("<o:p>", ""),
	("</o:p>", ""),
	("<p>", "\n\n"),
	("</p>", "\n"),
	("<h1>", "\n# "),
	("</h1>", "\n"),

#	("rc://en/", "rc://*/"),    now incorporated in md_cleanup.py

	("rc://*/obe/", "rc://*/tw/bible/"),
	("rc: // en / ta / man / translate / ", "rc://*/ta/man/translate/"),
#  these next few lines apply to a few languages
#	(" figs-metaphor)", " [[rc://*/ta/man/translate/figs-metaphor]])"),
#	(" figs-metaphor )", " [[rc://*/ta/man/translate/figs-metaphor]])"),
#	(" figs-abstractnouns)", " [[rc://*/ta/man/translate/figs-abstractnouns]])"),
#	(" figs-abstractnouns )", " [[rc://*/ta/man/translate/figs-abstractnouns]])"),
#	(" figs-synecdoche)", " [[rc://*/ta/man/translate/figs-synecdoche]])"),
#	(" figs-synecdoche )", " [[rc://*/ta/man/translate/figs-synecdoche]])"),

    ("# # # ", "# "),
    ("# # ", "# "),
    ("\\*", "*"),
 	("\\ [", "["),
 	("\\ ]", "]"),
 	("\\[", "["),
 	("\\]", "]"),
 	(" ]", "]"),
 	("]]]]", "]]"),
 	("]])]]", "]])"),
	(") [", "), ["),
	(" \( ", " ("),
	("/ )", "/)"),
#	("____", "__"),
#	("___", "__"),
	("..md", ".md"),
	(".jpg?direct&", ".jpg")    # OBS image links
]