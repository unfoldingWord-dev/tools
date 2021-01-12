# -*- coding: utf-8 -*-
# substitutions module, used by tsv_cleanup.py.
# An ordered list of tuples to be used for string substitutions.

subs = [
 	("\\[\\[", "[["),
 	("\\]\\]", "]]"),
 	("# <br>", "# "),
 	("#   ", "# "),
 	("#  ", "# "),
 	("rc://en_ta/", "rc://kn/ta/"),
 	("rc://en/", "rc://kn/")
]

#	("rc://en/", "rc://hi/"),
# 	("//ro/t", "//*/t") # specific to Oriya tN
# 	("translate/writing-connectingwords", "translate/grammar-connect-words-phrases")
#   ("translate/grammar-connect-words-phrases", "translate/writing-connectingwords")
# The writing-connectingwords --> grammar-connect-words-phrases may well be incorrect for GLs that have their own tA resource.
