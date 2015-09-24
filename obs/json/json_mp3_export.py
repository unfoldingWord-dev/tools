#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@unfoldingword.org>
#
#  Requires mutagen for reading mp3 information

import os
import re
import sys
import json
import glob
import codecs
import argparse
from mutagen.mp3 import MP3

api_base = u'https://api.unfoldingword.org'
api_abs = '/var/www/vhosts/api.unfoldingword.org/httpdocs/'
chpre = re.compile(ur'([0-5][0-9]).mp3', re.UNICODE)


def audio_stat(directory, lang, contrib, txt_ver, rev, slug):
    audio = { 'contributors': contrib,
              'txt_ver': txt_ver,
              'rev': rev,
              'src_list': [],
              'slug': slug,
            }
    for f in glob.glob('{0}/*[0-5][0-9].mp3'.format(directory)):
        chp_entry = {}
        chp = chpre.search(f).group(1)

        # Get MP3 info
        mp3_info = MP3(f).info
        chp_entry['br'] = mp3_info.bitrate / 1000
        chp_entry['length'] = int(MP3(f).info.length)

        # Get file info
        f_stat = os.stat(f)
        chp_entry['size'] = f_stat.st_size
        chp_entry['mod'] = int(f_stat.st_mtime)

        # Set src URLs
        chp_entry['src'] = '{0}/{1}'.format(api_base, f.split(api_abs)[1])
        chp_entry['src_sig'] = chp_entry['src'].replace('.mp3', '.sig')
        audio['src_list'].append({chp: chp_entry})
    audio['src_list'].sort()
    return audio




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest="lang", default=False,
        required=True, help="Language code of resource.")
    parser.add_argument('-s', '--slug', dest="slug", default=False,
        required=True, help="Slug of resource (e.g. obs-en).")
    parser.add_argument('-r', '--rev', dest="rev", default=False,
        required=True, help="Revision of audio.")
    parser.add_argument('-v', '--ver', dest="ver", default=False,
        required=True, help="Version of text.")
    parser.add_argument('-c', '--contrib', dest="contrib", default=False,
        required=True, help="Contributors to audio.")
    parser.add_argument('-d', '--directory', dest="directory", default=False,
        required=True, help="Directory of audio.")

    args = parser.parse_args(sys.argv[1:])
    status_info = audio_stat(args.directory, args.lang, args.contrib,
                             args.ver, args.rev, args.slug)
    stat_f = codecs.open('{0}/status.json'.format(args.directory), 'w',
                         encoding='utf-8')
    stat_f.write(json.dumps(status_info, sort_keys=True))
    stat_f.close()
