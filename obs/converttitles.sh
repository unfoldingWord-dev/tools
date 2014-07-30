#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

PROGNAME="${0##*/}"

ROOT=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages
ROOT=~/vcs/door43-pages/

TITLES="01-the-creation 02-sin-enters-the-world 03-the-flood 04-gods-covenant-with-abraham 05-the-son-of-promise 06-god-provides-for-isaac 07-god-blesses-jacob 08-god-saves-joseph-and-his-family 09-god-calls-moses 10-the-ten-plagues 11-the-passover 12-the-exodus 13-gods-covenant-with-israel 14-wandering-in-the-wilderness 15-the-promised-land 16-the-deliverers 17-gods-covenant-with-david 18-the-divided-kingdom 19-the-prophets 20-the-exile-and-return 21-god-promises-the-messiah 22-the-birth-of-john 23-the-birth-of-jesus 24-john-baptizes-jesus 25-satan-tempts-jesus 26-jesus-starts-his-ministry 27-the-story-of-the-good-samaritan 28-the-rich-young-ruler 29-the-story-of-the-unmerciful-servant 30-jesus-feeds-five-thousand-people 31-jesus-walks-on-water 32-jesus-heals-a-demon-possessed-man 33-the-story-of-the-farmer 34-jesus-teaches-other-stories 35-the-story-of-the-compassionate-father 36-the-transfiguration 37-jesus-raises-lazarus-from-the-dead 38-jesus-is-betrayed 39-jesus-is-put-on-trial 40-jesus-is-crucified 41-god-raises-jesus-from-the-dead 42-jesus-returns-to-heaven 43-the-church-begins 44-peter-and-john-heal-a-beggar 45-philip-and-the-ethiopian-official 46-paul-becomes-a-christian 47-paul-and-silas-in-philippi 48-jesus-is-the-promised-messiah 49-gods-new-covenant 50-jesus-returns"

changefiles () {
    for f in `find "$1" -type f -maxdepth 1 -name '[0-9][0-9]-*.txt'`; do
        mv "$f" "${f%%-[a-zA-Z]*}.txt"
    done
}

for l in `find $ROOT -type d -name 'obs'`; do
    # change files $l
done

# Update links
for x in `find $ROOT -type f`; do

    sed title

done

#tg/obs/stories.txt:  - [[tg:obs:08-god-saves-joseph-and-his-family|God Saves Joseph and His Family]]

