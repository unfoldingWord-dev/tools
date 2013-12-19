#!/usr/bin/env python
# -*- coding: utf8 -*-
#  Copyright (c) 2013 Jesse Griffin
#  http://creativecommons.org/licenses/MIT/
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

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
