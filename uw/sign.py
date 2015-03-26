#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

'''
Signs all content in tS catalog.
'''

import os
import sys
import json
import shlex
import urllib2
from subprocess import *
from urllib import urlencode
from base64 import b64encode


catalog_url = u'https://api.unfoldingword.org/ts/txt/2/catalog.json'
source_keys = [u'usfm', u'terms', u'source', u'notes']
sign_com = '/usr/local/bin/openssl dgst -sha384 -sign /etc/pki/uw/uW-sk.pem'
api = u'http://api.unfoldingword.org:9098/'


def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return False

def getContent(cat):
    content = []
    for x in cat:
        lang_cat = json.loads(getURL(x['lang_catalog']))
        for y in lang_cat:
            res_cat = json.loads(getURL(y['res_catalog']))
            for key in source_keys:
                for i in res_cat:
                    if key in i:
                        if i[key] not in content:
                            content.append(i[key])
    return content

def sign(content):
    command = shlex.split(sign_com)
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate(content)
    return b64encode(out)

def upload(sig, content, si):
    payload = json.dumps({ 'content': content,
                           'sig': sig,
                           'slug': si
                        })
    req = urllib2.Request(api, payload, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    response = f.read()
    f.close()
    print response

def main():
    cat = json.loads(getURL(catalog_url))
    content_list = getContent(cat)
    for x in content_list:
        content = getURL(x)
        if not content:
            print 'skipped {0}'.format(x)
            continue
        sig = sign(content)
        print x
        print sig
        upload(sig, x, 'uW')
        break


if __name__ == '__main__':
    main()
