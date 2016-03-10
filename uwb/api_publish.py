#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>


"""
This script publishes the Unlocked Bible into the tS v2 API.

Requires that https://github.com/Door43/USFM-Tools be checked out to
/var/www/vhosts/door43.org/USFM-Tools or be on the path
"""

import os
import re
import sys
import json
import codecs
import shutil
import argparse
import datetime
# Import USFM-Tools
USFMTools='/var/www/vhosts/door43.org/USFM-Tools'
sys.path.append(USFMTools)
try:
    import transform
except ImportError:
    print "Please ensure that {0} exists.".format(USFMTools)
    sys.exit(1)

ULBSource = '/var/www/vhosts/api.unfoldingword.org/httpdocs/ulb/txt/1/'
UDBSource = '/var/www/vhosts/api.unfoldingword.org/httpdocs/udb/txt/1/'
api_v2 = '/var/www/vhosts/api.unfoldingword.org/httpdocs/ts/txt/2/'
versere = re.compile(ur'<verse number="([0-9]*)', re.UNICODE)


def makeDir(d):
    '''
    Simple wrapper to make a directory if it does not exist.
    '''
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def writeJSON(outfile, p):
    '''
    Simple wrapper to write a file as JSON.
    '''
    makeDir(outfile.rsplit('/', 1)[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(json.dumps(p, sort_keys=True))
    f.close()

def parse(usx):
    '''
    Iterates through the source and splits it into frames based on the
    s5 markers.
    '''
    chapters = []
    chp = ''
    frid = 0
    chp_num = 0
    fr_list = []
    for line in usx:
        if line.startswith(u'\n'): continue
        if 'chapter number' in line:
            if chp:
                if fr_list:
                    fr_text = u'\n'.join(fr_list)
                    try:
                        firstvs = versere.search(fr_text).group(1)
                    except AttributeError:
                        print u'myError, chp {0}'.format(chp_num)
                        print u'Text: {0}'.format(fr_text)
                        sys.exit(1)
                    chp['frames'].append({ u'id': u'{0}-{1}'.format(
                                     str(chp_num).zfill(2), firstvs.zfill(2)),
                                       u'img': u'',
                                       u'format': u'usx',
                                       u'text': fr_text
                                      })
                chapters.append(chp)
            chp_num += 1
            chp = { u'number': str(chp_num).zfill(2),
                    u'ref': u'',
                    u'title': u'',
                    u'frames': []
                  }
            fr_list = []
            continue
        if 'para style="s5"' in line:
            if chp_num == 0:
                continue
            if fr_list:
                fr_text = u'\n'.join(fr_list)
                try:
                    firstvs = versere.search(fr_text).group(1)
                except AttributeError:
                    print u'Error, chp {0}'.format(chp_num)
                    print u'Text: {0}'.format(fr_text)
                    sys.exit(1)
                chp['frames'].append({ u'id': u'{0}-{1}'.format(
                                     str(chp_num).zfill(2), firstvs.zfill(2)),
                                       u'img': u'',
                                       u'format': u'usx',
                                       u'text': fr_text
                                      })
                fr_list = []
                continue
        fr_list.append(line)

    # Append the last frame and the last chapter
    chp['frames'].append({ u'id': u'{0}-{1}'.format(
                                   str(chp_num).zfill(2), str(frid).zfill(2)),
                           u'img': u'',
                           u'format': u'usx',
                           u'text': u'\n'.join(fr_list)
                          })
    chapters.append(chp)
    return chapters

def getChunks(book):
    chunks = []
    for c in book:
        for frame in c['frames']:
            chunks.append({ 'id': frame['id'],
                            'firstvs': versere.search(frame['text']).group(1)
                          })
    return chunks

def main(source):
    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    dirs = []
    if source:
        dirs.append(source)
    else:
        udbd = [os.path.join(UDBSource, x) for x in os.listdir(UDBSource)]
        dirs += udbd
        ulbd = [os.path.join(ULBSource, x) for x in os.listdir(ULBSource)]
        dirs += ulbd
    for d in dirs:
        ver, lang = d.rsplit('/', 1)[1].split('-', 1)
        tmpdir = '/tmp/{0}-{1}'.format(ver, lang)
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
        transform.buildUSX(d, tmpdir, '', True)
        print "#### Chunking..."
        for f in os.listdir(tmpdir):
            usx = codecs.open(os.path.join(tmpdir, f), 'r', encoding='utf-8'
                                                                 ).readlines()
            slug = f.split('.')[0].lower()
            print '     ({0})'.format(slug.upper())
            book = parse(usx)
            payload = { 'chapters': book,
                        'date_modified': today
                      }
            writeJSON(os.path.join(api_v2, slug, lang, ver, 'source.json'),
                                                                     payload)
            chunks = getChunks(book)
            writeJSON(os.path.join(api_v2, slug, lang, ver, 'chunks.json'),
                                                                       chunks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--sourceDir', dest="sourcedir", default=False,
                                                     help="Source directory.")
    args = parser.parse_args(sys.argv[1:])
    main(args.sourcedir)
    ### chown -R syncthing:syncthing /var/www/vhosts/api.unfoldingword.org/httpdocs/
