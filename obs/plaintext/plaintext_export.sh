#!/bin/bash

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
#PAGES=$ROOT/pages
PAGES=/tmp/pages
#DEST=$ROOT/media/exports
DEST=/tmp/exports
LANGS=$ROOT/media/exports/meta/langcodes.txt

DATE=`date +%y%m%d%H%M`
DOKU2HTML=/usr/local/bin/doku2html
PANDOC=/usr/bin/pandoc

# tmp vars
#FILE=$PAGES/en/obs/01-the-creation.txt
TMP=/tmp/tmpfile.txt

#
# process each language
#
for l in `cat $LANGS`
do
	echo -n "$l: "

	#
	# does this language have an OBS project?
	#
	if [ -d $PAGES/$l/obs ];
	then

		#
		# set source & export directories
		#
		SOURCEDIR=$PAGES/$l/obs
		EXPORTDIR=$DEST/$l/obs

		#
		# create "obs/plaintext" directories in "exports" directory 
		# for current language, if not exist yet
		# 
		if [ ! -d $EXPORTDIR/plaintext ]
		then
			mkdir -p $EXPORTDIR/plaintext
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
	    COMBINED=$EXPORTDIR/obs-$l_$DATE.md
	    cat /dev/null > $COMBINED

	    for m in `ls $EXPORTDIR/[0-9][0-9]*.md | sort`
	    do

	    	#
	    	# combine markdown files into one
	    	#
	    	cat $EXPORTDIR/$m >> $COMBINED

	    done

	    #
	    # ...and create an ODT + DOCX
	    #
	    DOCUMENT=`basename $EXPORTDIR/$COMBINED .md`
	    $PANDOC -f markdown -S -t odt -o $EXPORTDIR/$DOCUMENT.odt $EXPORTDIR/$COMBINED
	    $PANDOC -f markdown -S -t docx -o $EXPORTDIR/$DOCUMENT.docx $EXPORTDIR/$COMBINED

	fi

	echo ""

done

exit 0
