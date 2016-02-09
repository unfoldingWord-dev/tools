#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

import os
import sys
import codecs


td = { "01-the-creation.txt": "01",
       "02-sin-enters-the-world.txt": "02",
       "03-the-flood.txt": "03",
       "04-gods-covenant-with-abraham.txt": "04",
       "05-the-son-of-promise.txt": "05",
       "06-god-provides-for-isaac.txt": "06",
       "07-god-blesses-jacob.txt": "07",
       "08-god-saves-joseph-and-his-family.txt": "08",
       "09-god-calls-moses.txt": "09",
       "10-the-ten-plagues.txt": "10",
       "11-the-passover.txt": "11",
       "12-the-exodus.txt": "12",
       "13-gods-covenant-with-israel.txt": "13",
       "14-wandering-in-the-wilderness.txt": "14",
       "15-the-promised-land.txt": "15",
       "16-the-deliverers.txt": "16",
       "17-gods-covenant-with-david.txt": "17",
       "18-the-divided-kingdom.txt": "18",
       "19-the-prophets.txt": "19",
       "20-the-exile-and-return.txt": "20",
       "21-god-promises-the-messiah.txt": "21",
       "22-the-birth-of-john.txt": "22",
       "23-the-birth-of-jesus.txt": "23",
       "24-john-baptizes-jesus.txt": "24",
       "25-satan-tempts-jesus.txt": "25",
       "26-jesus-starts-his-ministry.txt": "26",
       "27-the-story-of-the-good-samaritan.txt": "27",
       "28-the-rich-young-ruler.txt": "28",
       "29-the-story-of-the-unmerciful-servant.txt": "29",
       "30-jesus-feeds-five-thousand-people.txt": "30",
       "31-jesus-walks-on-water.txt": "31",
       "32-jesus-heals-a-demon-possessed-man.txt": "32",
       "33-the-story-of-the-farmer.txt": "33",
       "34-jesus-teaches-other-stories.txt": "34",
       "35-the-story-of-the-compassionate-father.txt": "35",
       "36-the-transfiguration.txt": "36",
       "37-jesus-raises-lazarus-from-the-dead.txt": "37",
       "38-jesus-is-betrayed.txt": "38",
       "39-jesus-is-put-on-trial.txt": "39",
       "40-jesus-is-crucified.txt": "40",
       "41-god-raises-jesus-from-the-dead.txt": "41",
       "42-jesus-returns-to-heaven.txt": "42",
       "43-the-church-begins.txt": "43",
       "44-peter-and-john-heal-a-beggar.txt": "44",
       "45-philip-and-the-ethiopian-official.txt": "45",
       "46-paul-becomes-a-christian.txt": "46",
       "47-paul-and-silas-in-philippi.txt": "47",
       "48-jesus-is-the-promised-messiah.txt": "48",
       "49-gods-new-covenant.txt": "49",
       "50-jesus-returns.t": "50",
     }
tmpl = u'''#REDIRECT [[{0}:obs:{1}]]'''


def writeFile(f, content):
    out = codecs.open(f, encoding='utf-8', mode='w')
    out.write(content)
    out.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        lang = str(sys.argv[1]).strip()
        if not os.path.exists(lang):
            print 'Directory not found: {0}'.format(lang)
            sys.exit(1)
    else:
        print 'Please specify the language to fix.'
        sys.exit(1)
    for k,v in td.iteritems():
        writeFile('{0}/obs/{1}'.format(lang, k), tmpl.format(lang, v))

