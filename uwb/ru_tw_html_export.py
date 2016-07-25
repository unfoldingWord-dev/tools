#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

'''
Exports tA for ru from json to html
'''

import os
import re
import sys
import json
import codecs
import operator

reload(sys)
sys.setdefaultencoding('utf8')

def main():
    filepath = u'/home/rich/Downloads/ru/tw-ru.json'

    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    # Parse the body
    with open(filepath) as data:
        everything = json.load(data)

    terms = dict()
    for item in everything:
        if 'term' in item:
            terms[item['id'].lower()] = item

    output = u''
    for id, term in sorted(terms.items(), key=lambda x: x[1]['term']):
        output += u'<div class="page break" id="'+id+u'">'
        output += u'<h1>'+term['term']+u'</h1>'
        output += u'<h2>'+term['def_title']+u'</h2>'
        output += u'<p>'+term['def']+u'</p>'
        if 'aliases' in term and term['aliases']:
            if isinstance(term['aliases'], basestring):
                term['aliases'] = [term['aliases']]
            output += u'<p><b>Aliases:</b> '+', '.join(term['aliases'])+u'</p>'
        if 'cf' in term and term['cf']:
            if isinstance(term['cf'], basestring):
                term['cf'] = [term['cf']]
            output += u'<p><b>Смотрите также:</b> '
            for idx, cf in enumerate(term['cf']):
                output += u'<a href="#'+cf.lower()+u'">'+(terms[cf.lower()]['term'] if cf.lower() in terms else cf)+u'</a>'
                if idx < len(term['cf']) - 1:
                    output += u'; '
            output += u'</p>'

    f = codecs.open('tw-ru.html', 'w', encoding='utf-8')
    f.write(output)
    f.close()

if __name__ == '__main__':
    main()
