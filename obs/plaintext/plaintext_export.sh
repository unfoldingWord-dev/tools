#!/bin/bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Tim Jore <tim@distantshores.org>

###############################################################################
#
#  `plaintext_export` is a script that exports the complete text of Open
#  Bible Stories in every language on Door43 (in which it is available) as
#  plain text and ODT.
#
#  It is intended to help facilitate the recording of the audio files for
#  Open Bible Stories
#
###############################################################################

ROOT=/var/www/vhosts/door43.org/httpdocs/data/gitrepo
PAGES=$ROOT/pages
DEST=$ROOT/media/exports
#DEBUG PAGES=/tmp/pages
#DEBUG DEST=/tmp/exports
# for processing all available languages: LANGS=$ROOT/media/exports/meta/langcodes.txt
LANGS=$1

DATE=`date +%y%m%d%H%M`
DOKU2HTML=/usr/local/bin/doku2html
PANDOC=/usr/bin/pandoc

# tmp vars
TMP=/tmp/tmpfile.txt

#
# process each language
#
for l in $LANGS
#DEBUG for l in "en" 
do

	#
	# does this language have an OBS project?
	#
	if [ -d $PAGES/$l/obs ];
	then

		echo -n "$l: "

		#
		# set source & export directories
		#
		SOURCEDIR=$PAGES/$l/obs
		EXPORTDIR=$DEST/$l/obs/plaintext

		#
		# create "obs/plaintext" directories in "exports" directory 
		# for current language, if not exist yet
		# 
		if [ ! -d $EXPORTDIR ]
		then
			mkdir -p $EXPORTDIR
		else
			sudo chmod +w $EXPORTDIR/*
		fi

	    #
	    # process the contents of the 'obs' directory,
	    # maintain sort order
	    #
	    for i in `ls $SOURCEDIR/[0-9][0-9]*.txt | sort`
	    do 
	    	echo -n "+"

	    	#
	    	# set the basename of the file
	    	#
	    	NAME=`basename $i .txt`

	    	#
	    	# $i is the dokuwiki text file to be processed;
	    	# remove image declarations from the file
	    	#
	    	cat $i | \
	    	grep -v ".jpg" > $TMP

	    	#
	    	# convert wiki text --> html --> markdown
	    	#
			$DOKU2HTML $TMP | \
			$PANDOC -f html -s -t markdown -o $EXPORTDIR/$NAME.md
			rm -f $TMP

	    done

	    #
	    # we now have all stories in language $l as Markdown in 
	    # $EXPORTDIR. we will now concatenate them...
	    #
	    COMBINED=obs-plaintext-$l.md
	    cat /dev/null > $EXPORTDIR/$COMBINED

	    for m in `ls $EXPORTDIR/[0-9][0-9]*.md | sort`
	    do

	    	#
	    	# combine markdown files into one
	    	#
	    	cat $m >> $EXPORTDIR/$COMBINED
	    	echo "" >> $EXPORTDIR/$COMBINED

	    done

	    #
	    # ...and create an ODT + DOCX
	    #
	    DOCUMENT=`basename $EXPORTDIR/$COMBINED .md`
	    $PANDOC -f markdown -S -t odt -o $EXPORTDIR/$DOCUMENT.odt $EXPORTDIR/$COMBINED
	    $PANDOC -f markdown -S -t docx -o $EXPORTDIR/$DOCUMENT.docx $EXPORTDIR/$COMBINED

	    #
	    # revert all files to read-only (so cannot be deleted in 
	    # Door43 web interface)
		#
		sudo chmod a-w $EXPORTDIR/*

	fi

	echo ""
	echo ""
	echo "check this out: $EXPORTDIR/$DOCUMENT.odt"
	echo "check this out: $EXPORTDIR/$DOCUMENT.docx"
	echo ""

done

exit 0
