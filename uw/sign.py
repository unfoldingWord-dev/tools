#!/usr/bin/env python2
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
import time
import shlex
import codecs
import shutil
import urllib
import urllib2
import argparse
import requests
from subprocess import *
from base64 import b64encode, b64decode


catalog_url = u'https://api.unfoldingword.org/ts/txt/2/catalog.json'
source_keys = [u'usfm', u'terms', u'source', u'notes']
sign_com = '/usr/local/bin/openssl dgst -sha384 -sign /etc/pki/uw/uW-sk.pem'
api = u'http://api.unfoldingword.org:9098/'
working_dir = '/dev/shm/check_sig'
pki_base = 'https://pki.unfoldingword.org'
verbose = False


def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return False

def getContent(cat):
    global verbose

    content = []
    for x in cat:

        if verbose:
            print u'Retrieving {0}'.format(x['lang_catalog'])

        lang_cat = json.loads(getURL(x['lang_catalog']))
        for y in lang_cat:
            res_cat = json.loads(getURL(y['res_catalog']))
            for key in source_keys:
                for i in res_cat:
                    if key in i:
                        if i[key] not in content:

                            if verbose:
                                print u'Found {0}'.format(i[key])

                            content.append(i[key])
                            # if '/obs-' in i[key]:
                            #     pdf = u'{0}-v{1}.pdf'.format(i[key]
                            #                                  .split('.json')[0], i['status']['version']
                            #                                  .replace(u'.', u'_'))
                            #     #content.append(pdf)
    return content

def sign(content):
    command = shlex.split(sign_com)
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate(content)
    return b64encode(out)

def upload(sig, content, si):
    payload = { 'data': { 'content': content,
                          'sig': sig,
                          'slug': si
                        }
              }
    r = requests.post(api, data=json.dumps(payload),
                                 headers={'Content-Type': 'application/json'})
    if 'ok' not in r.text:
        print content
        print u'-> {0}'.format(r.text)

def checkSig(content, sig, slug):
    # Based on https://github.com/unfoldingWord-dev/sigadd/blob/master/index.py
    '''
    Checks if a signature is valid
    :param path: the path to the content that was signed
    :param sig: the signature that will be validated
    :param slug: the SI slug
    :return:
    '''
    ts = time.time()
    vk_url = '{0}/si/{1}-vk.pem'.format(pki_base, slug)
    if slug == 'uW':
        vk_url = '{0}/{1}-vk.pem'.format(pki_base, slug)

    # download the si
    vk_path = '{0}/{1}.pem'.format(working_dir, ts)
    if not os.path.exists(vk_path):
        try:
            f = urllib.URLopener()
            f.retrieve(vk_url, vk_path)
            f.close()
        except Exception as e:
            print e
            return False

    # prepare the content sig
    sig_path = '{0}/{1}.sig'.format(working_dir, ts)
    uw_sig = [x['sig'] for x in sig if x['si'] == 'uW']
    sigf = open(sig_path, 'w')
    sigf.write(b64decode(uw_sig[0]))
    sigf.close()

    # write content to file so OpenSSL can check it
    content_path = '{0}/{1}.content'.format(working_dir, ts)
    try:
        f = codecs.open(content_path, 'w', 'utf-8')
        f.write(content.decode('utf-8'))
        f.close()
    except Exception as e:
        print e
        return False

    # Use openssl to verify signature
    command_str = 'openssl dgst -sha384 -verify '+vk_path+' -signature '+sig_path+' '+content_path
    command = shlex.split(command_str)
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate()

    return out.strip() == 'Verified OK'


def main(test):
    global verbose

    if verbose:
        print u'Getting the catalog...'

    cat = json.loads(getURL(catalog_url))

    if verbose:
        print u'Getting the list of files to sign...'

    content_list = getContent(cat)

    if test:
        print u'Testing'
    else:
        print u'Signing...'

    for x in content_list:
        if verbose:
            print u'Retrieving {0}'.format(x)
        content = getURL(x)
        if not content:
            continue

        if verbose:
            print u'Retrieving .sig file'
        existing_sig = getURL('{0}.sig'.format(x.rsplit('.', 1)[0]))
        if existing_sig:

            if verbose:
                print u'Found .sig file'

            if checkSig(content, json.loads(existing_sig), 'uW'):
                if verbose:
                    print u'Valid .sig file'
                else:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                continue
            else:
                if verbose:
                    print u'Invalid .sig file'

        else:
            if verbose:
                print u'Did not find .sig file'

        if test:
            print "!! SIG FAILURE: {0}".format(x)
            continue

        sig = sign(content)
        upload(sig, x, 'uW')
        print "Signed: {0}".format(x)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t', '--test', dest="test", default=False,
        action='store_true', help="Test signatures only.")
    parser.add_argument('-v', '--verbose', dest="verbose", default=False,
                        action='store_true', help="More verbose output for debugging.")

    args = parser.parse_args(sys.argv[1:])
    verbose = args.verbose

    # init working dir
    if not os.path.exists(working_dir):
        print 'initializing working directory in '+working_dir
        os.makedirs(working_dir)

    main(args.test)

    print 'Done'
    shutil.rmtree(working_dir)
