#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

import os
import json
import base64

root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
imagesdir = os.path.join(root, 'media/en/obs')
exportdir = os.path.join(root, 'media/exports/img')

def b64_encode(f):
    jpg = open(f, 'rb')
    return base64.b64encode(jpg.read())

def writeJSON(outfile, jsonjpg):
    makeDir(outfile.rpartition('/')[0])
    f = open(outfile.replace('jpg', 'json'), 'wb')
    f.write(jsonjpg)
    f.close()
    os.chown(outfile.replace('jpg', 'json'), 48, 502)

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)


if __name__ == '__main__':
    for jpgfile in os.listdir(imagesdir):
        if not jpgfile.endswith('.jpg'):
            continue
        jpgparts = jpgfile.split('-')
        chapter = jpgparts[1]
        number = jpgparts[2].split('.')[0]
        base64img = b64_encode(os.path.join(imagesdir, jpgfile))
        jsonimg = json.dumps( { 'chapter': chapter,
                                'number': number,
                                'img': base64img,
                              } )
        writeJSON(os.path.join(exportdir, jpgfile), jsonimg)
