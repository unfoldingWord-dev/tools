#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>
#
#  Cleans out extra stories when doing a Demo publish

import sys
import json
import codecs

filename = sys.argv[1]

f=codecs.open(filename, 'r', encoding='utf-8')
me = json.loads(f.read())
f.close()

todel = []

for x in range(1,51):
    me['chapters'] = [x for x in me['chapters'] if x['number'] in ['24', '25', '27', '28', '29', '30', '31', '33', '34', '36', '40', '41', '35', '37', '39'] ]

f=codecs.open('output.json', 'w', encoding='utf-8')
f.write(json.dumps(me))
f.close()
