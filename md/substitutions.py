# -*- coding: utf-8 -*-
# substitutions module, used by translate.py.
# An ordered list of tuples to be used for string substitutions.
# The first element is a regular express, the second is a string to replace it with
#

subs = [
	("http://ufw.io/[[rc://", "[[rc://"),
	("rc://en/", "rc://*/"),
	(" \( ", " (")
]