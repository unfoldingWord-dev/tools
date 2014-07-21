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
		EXPORTDIR=$DEST/$l/obs/markdown

		#
		# create "obs/markdown" directories in "exports" directory 
		# for current language, if not exist yet
		# 
		if [ ! -d $EXPORTDIR ]
		then
			mkdir -p $EXPORTDIR
		else
			sudo chmod ug+w $EXPORTDIR/*
		fi

	    #
	    # process the contents of the 'obs' directory,
	    # maintain sort order
	    #
	    for i in "$SOURCEDIR/front-matter.txt" `ls $SOURCEDIR/[0-9][0-9]*.txt | sort` "$SOURCEDIR/back-matter.txt" 
	    do 
	    	echo -n "+"
	    	#echo "+ $i"

	    	#
	    	# set the basename of the file
	    	#
	    	NAME=`basename $i .txt`


	    	#
	    	# convert wiki text --> html --> tmp markdown --> clean up --> final markdown
	    	#
			#$DOKU2HTML $i | \
			#$PANDOC -f html -s -t markdown -o $EXPORTDIR/$NAME.md

			$DOKU2HTML $i | \
			$PANDOC -f html -s -t markdown -o $TMP

			cat $TMP | sed 's/?w=640&h=360&tok=[a-z0-9][a-z0-9][a-z0-9][a-z0-9][a-z0-9][a-z0-9]//' | sed 's:_media:var/www/vhosts/door43.org/httpdocs/data/gitrepo/media:' > $EXPORTDIR/$NAME.md

			rm -f $TMP

	    done

	    #
	    # we now have all stories in language $l as Markdown in 
	    # $EXPORTDIR. we will now concatenate them...
	    #
	    COMBINED=obs-$l.md
	    cat /dev/null > $EXPORTDIR/$COMBINED


	    for m in "$EXPORTDIR/front-matter.md" `ls $EXPORTDIR/[0-9][0-9]*.md | sort` "$EXPORTDIR/back-matter.md"
	    do

		#echo "+ $m"
	    	#
	    	# combine markdown files into one
	    	#
	    	cat $m >> $EXPORTDIR/$COMBINED
	    	echo "" >> $EXPORTDIR/$COMBINED

	    done

	    #
	    # ...and create an ODT + DOCX
	    #
	    #DOCUMENT=`basename $EXPORTDIR/$COMBINED .md`
	    #$PANDOC -f markdown -S -t odt -o $EXPORTDIR/$DOCUMENT.odt $EXPORTDIR/$COMBINED
	    #$PANDOC -f markdown -S -t docx -o $EXPORTDIR/$DOCUMENT.docx $EXPORTDIR/$COMBINED

	    #
	    # revert all files to read-only (so cannot be deleted in 
	    # Door43 web interface)
		#
		sudo chmod a-w $EXPORTDIR/*

	fi

	echo ""
	echo "Check this out: $EXPORTDIR/$COMBINED"

done

exit 0
