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
# noinspection PyUnresolvedReferences
import datetime

# Import USFM-Tools
USFMTools = '/var/www/vhosts/door43.org/USFM-Tools'
sys.path.append(USFMTools)
try:
    # noinspection PyUnresolvedReferences
    import transform
except ImportError as e:
    print e.message
    print "Please ensure that {0} exists.".format(USFMTools)
    sys.exit(1)

ULBSource = '/var/www/vhosts/api.unfoldingword.org/httpdocs/ulb/txt/1/'
UDBSource = '/var/www/vhosts/api.unfoldingword.org/httpdocs/udb/txt/1/'
api_v2 = '/var/www/vhosts/api.unfoldingword.org/httpdocs/ts/txt/2/'
verse_re = re.compile(ur'<verse number="([0-9]*)', re.UNICODE)

# remember these so we can delete them
temp_dir = ''


def make_dir(d):
    """
    Simple wrapper to make a directory if it does not exist.
    :param d:
    """
    if not os.path.exists(d):
        os.makedirs(d, 0755)


def write_json(outfile, p):
    """
    Simple wrapper to write a file as JSON.
    :param outfile:
    :param p:
    """
    make_dir(outfile.rsplit('/', 1)[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(json.dumps(p, sort_keys=True))
    f.close()


def parse(usx):
    """
    Iterates through the source and splits it into frames based on the
    s5 markers.
    :param usx:
    """
    chunk_marker = u'<note caller="u" style="s5"></note>'
    chapters = []
    chp = ''
    fr_id = 0
    chp_num = 0
    fr_list = []
    current_vs = -1
    for line in usx:
        if line.startswith(u'\n'):
            continue

        if "verse number" in line:
            current_vs = verse_re.search(line).group(1)

        if 'chapter number' in line:
            if chp:
                if fr_list:
                    fr_text = u'\n'.join(fr_list)
                    try:
                        first_vs = verse_re.search(fr_text).group(1)
                    except AttributeError:
                        print u'myError, chp {0}'.format(chp_num)
                        print u'Text: {0}'.format(fr_text)
                        sys.exit(1)
                    chp['frames'].append({u'id': u'{0}-{1}'.format(
                            str(chp_num).zfill(2), first_vs.zfill(2)),
                        u'img': u'',
                        u'format': u'usx',
                        u'text': fr_text,
                        u'lastvs': current_vs
                    })
                chapters.append(chp)
            chp_num += 1
            chp = {u'number': str(chp_num).zfill(2),
                   u'ref': u'',
                   u'title': u'',
                   u'frames': []
                   }
            fr_list = []
            continue

        if chunk_marker in line:
            if chp_num == 0:
                continue

            # is there something else on the line with it? (probably an end-of-paragraph marker)
            if len(line.strip()) > len(chunk_marker):

                # get the text following the chunk marker
                rest_of_line = line.replace(chunk_marker, '')

                # append the text to the previous line, removing the unnecessary \n
                fr_list[-1] = fr_list[-1][:-1] + rest_of_line

            if fr_list:
                fr_text = u'\n'.join(fr_list)
                try:
                    first_vs = verse_re.search(fr_text).group(1)
                except AttributeError:
                    print u'Error, chp {0}'.format(chp_num)
                    print u'Text: {0}'.format(fr_text)
                    sys.exit(1)

                chp['frames'].append({u'id': u'{0}-{1}'.format(
                        str(chp_num).zfill(2), first_vs.zfill(2)),
                    u'img': u'',
                    u'format': u'usx',
                    u'text': fr_text,
                    u'lastvs': current_vs
                })
                fr_list = []

            continue

        fr_list.append(line)

    # Append the last frame and the last chapter
    chp['frames'].append({u'id': u'{0}-{1}'.format(
            str(chp_num).zfill(2), str(fr_id).zfill(2)),
        u'img': u'',
        u'format': u'usx',
        u'text': u'\n'.join(fr_list),
        u'lastvs': current_vs
    })
    chapters.append(chp)
    return chapters


def get_chunks(book):
    chunks = []
    for c in book:
        for frame in c['frames']:
            chunks.append({'id': frame['id'],
                           'firstvs': verse_re.search(frame['text']).group(1),
                           'lastvs': frame["lastvs"]
                           })
    return chunks


def main(source):
    global temp_dir

    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    dirs = []
    if source:
        dirs.append(source)
    else:
        udb_dir = [os.path.join(UDBSource, x) for x in os.listdir(UDBSource)]
        dirs += udb_dir
        ulb_dir = [os.path.join(ULBSource, x) for x in os.listdir(ULBSource)]
        dirs += ulb_dir
    for d in dirs:
        ver, lang = d.rsplit('/', 1)[1].split('-', 1)
        temp_dir = '/tmp/{0}-{1}'.format(ver, lang)
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        transform.buildUSX(d, temp_dir, '', True)
        print "#### Chunking..."
        for f in os.listdir(temp_dir):

            # use utf-8-sig to remove the byte order mark
            usx = codecs.open(os.path.join(temp_dir, f), 'r', encoding='utf-8-sig'
                              ).readlines()
            slug = f.split('.')[0].lower()
            print '     ({0})'.format(slug.upper())
            book = parse(usx)
            payload = {'chapters': book,
                       'date_modified': today
                       }
            write_json(os.path.join(api_v2, slug, lang, ver, 'source.json'),
                       payload)
            chunks = get_chunks(book)
            write_json(os.path.join(api_v2, slug, lang, ver, 'chunks.json'),
                       chunks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-s', '--sourceDir', dest="sourcedir", default=False,
                        help="Source directory.")
    args = parser.parse_args(sys.argv[1:])

    # noinspection SpellCheckingInspection
    try:
        main(args.sourcedir)
        # chown -R syncthing:syncthing /var/www/vhosts/api.unfoldingword.org/httpdocs/
    finally:
        # delete temp files
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
