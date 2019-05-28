#!/bin/bash
#
# Expects argument of repo path (like https://git.door43.org/shojojohn/bn_irv_1th_book)
# Convert that path to filename for download (like https://git.door43.org/shojojohn/bn_irv_1th_book/raw/branch/master/bn_irv_1th_book.usfm)
# Downloads and properly names file in cwd
#
# Must have get_bible_book.py in ~/bin/ directory

TCBOOKNAME="${1##*/}"
GETURL="$1/raw/branch/master/$TCBOOKNAME.usfm"
CODE=`echo $1 | cut -d '_' -f 3`
USFMBOOK=`python ~/bin/get_bible_book.py $CODE`

wget "$GETURL" -O "$USFMBOOK"

