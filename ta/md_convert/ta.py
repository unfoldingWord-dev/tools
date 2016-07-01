#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

"""
This class parses information in tA Manual.
"""

import os
import re
import sys
import json
import codecs
import markdown2
import yaml
import glob
import ntpath

class taCollection:
    academyUrl = u'https://test.unfoldingword.org/academy/'
    manualUrls = {
      'en-ta-intro': academyUrl+u'ta-intro.html',
      'en-ta-process': academyUrl+u'ta-process.html',
      'en-ta-translate-vol1': academyUrl+u'ta-translation-1.html',
      'en-ta-translate-vol2': academyUrl+u'ta-translation-2.html',
      'en-ta-checking-vol1': academyUrl+u'ta-checking-1.html',
      'en-ta-checking-vol2': academyUrl+u'ta-checking-2.html',
      'en-ta-audio': academyUrl+u'ta-audio.html',
      'en-ta-gl': academyUrl+u'ta-gateway-language.html',
    }

    def __init__(self, taRoot):
        self.taRoot = taRoot
        # Populate the taMaual
        self.manuals = next(os.walk(self.taRoot))[1]
        self.manuals[:] = [manual for manual in self.manuals if os.path.isdir(taRoot+os.path.sep+manual+os.path.sep+"content") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"toc.yaml") and os.path.exists(taRoot+os.path.sep+manual+os.path.sep+"meta.yaml")]
        self.manualDict = {}
        for manual in self.manuals:
            print "MANUAL: "+manual
            self.manualDict[manual] = taManual(taRoot, manual)

class taManual:

    def __init__(self, taRoot, manual):
        self.taRoot = taRoot
        self.manual = manual
        self.manualDir = taRoot+os.path.sep+manual+os.path.sep
        self.moduleDict = {}
        metaFile = open(self.manualDir+'meta.yaml', 'r')
        meta = yaml.load(metaFile)
        metaFile.close()
        for key, value in meta.iteritems():
            setattr(self, key, value)
        self.slug = u'vol'+meta['volume']+u'_'+meta['manual']
        tocFile = open(self.manualDir+'toc.yaml', 'r')
        self.toc = yaml.load(tocFile)
        tocFile.close()
        self.modules = []
        for filepath in glob.iglob(self.manualDir+os.path.sep+u'content'+os.path.sep+u'*.md'):
            path, filename = ntpath.split(filepath)
            module, ext = os.path.splitext(filename)
            self.modules.append(module)
            self.moduleDict[module] = taModule(filepath)

class taModule:

    def __init__(self, filepath):
        self.filepath = filepath
        self.content = open(filepath).read()
        self.html = markdown2.markdown(self.content, extras=["tables", "metadata"])
        for key, value in self.html.metadata.iteritems():
            setattr(self, key, value)
