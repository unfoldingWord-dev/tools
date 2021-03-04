# -*- coding: utf-8 -*-
# substitutions module, used by md_cleanup.py.
# An ordered list of tuples to be used for string substitutions.
# The first element is a regular express, the second is a string to replace it with
#

subs = [
	("http://ufw.io/[[rc://", "[[rc://"),
	("&nbsp;", " "),
	("<o:p>", ""),
	("</o:p>", ""),
	("rc://en/", "rc://*/"),
	("rc://*/obe/", "rc://*/tw/bible/"),
#  these next few lines are for Burmese, probably don't apply to other languages
#	(" figs-metaphor)", " [[rc://*/ta/man/translate/figs-metaphor]])"),
#	(" figs-metaphor )", " [[rc://*/ta/man/translate/figs-metaphor]])"),
#	(" figs-abstractnouns)", " [[rc://*/ta/man/translate/figs-abstractnouns]])"),
#	(" figs-abstractnouns )", " [[rc://*/ta/man/translate/figs-abstractnouns]])"),
#	(" figs-synecdoche)", " [[rc://*/ta/man/translate/figs-synecdoche]])"),
#	(" figs-synecdoche )", " [[rc://*/ta/man/translate/figs-synecdoche]])"),
 	("\\ [", "["),
 	("\\ ]", "]"),
 	("\\[", "["),
 	("\\]", "]"),
 	(" ]", "]"),
 	("]]]]", "]]"),
	(") [", "), ["),
	(" \( ", " ("),
	("/ )", "/)"),
	("____", "__"),
	("___", "__"),
	("..md", ".md"),
	(".jpg?direct&", ".jpg")    # OBS image links
]