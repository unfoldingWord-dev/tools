#!/bin/bash

###############################################################################
#
#  `book_export` is a script that exports the complete text of Open
#  Bible Stories in every language on Door43 (in which it is available) as
#  a formatted ODT with images.
#
#  NOTE: this script needs to further development to enable the passing of a 
#  custom template, to better account for RTL languages, non-roman scripts,
#  and other custom rendering issues.
#
###############################################################################

ROOT=/var/www/vhosts/door43.org/httpdocs/data/gitrepo
DEST=$ROOT/media/exports
TEMPLATE=$ROOT/media/en/obs-templates/obs-book-template.odt
# for processing all available languages: LANGS=$ROOT/media/exports/meta/langcodes.txt
LANGS=$1

DATE=`date +%y%m%d%H%M`
PANDOC=/usr/bin/pandoc

# tmp vars
TMP=/tmp/tmpodt.txt

#
# process each language
#
for l in $LANGS
#DEBUG for l in "en" 
do

	#
	# does this language have an OBS file in the 'markdown' exports?
	# (if not, must run `export_markdown.sh`)
	#
	if [ -e $DEST/$l/obs/markdown/obs-$l.md ];
	then

		#
		# set source & export directories
		#
		SOURCEDIR=$DEST/$l/obs/markdown
		EXPORTDIR=$DEST/$l/obs/book

		#
		# create "obs/book" directories in "exports" directory 
		# for current language, if not exist yet
		# 
		if [ ! -d $EXPORTDIR ]
		then
			mkdir -p $EXPORTDIR
		else
			chmod +w $EXPORTDIR/*
		fi

	    #
	    # generate ODT
	    # pandoc -S -o fa/obs/book/obs-fa.odt --reference-odt=/home/timj/Data/Dev/tools/obs/book/obs-book-template.odt \
 		#     fa/obs/markdown/obs-fa.md
 		#

 		# FIXME: the "-V lang:____" option should be scripted so that it dynamically inserts the language based on the
 		# language subdirectory of the content being processed

 		pandoc -S -V lang:fa -o $EXPORTDIR/obs-$l.odt \
 		--reference-odt=$TEMPLATE \
 		$DEST/$l/obs/markdown/obs-$l.md

	    #
	    # revert all files to read-only (so cannot be deleted in 
	    # Door43 web interface)
		#
		chmod -w $EXPORTDIR/*

		echo "$l: $EXPORTDIR/obs-$l.odt"

	else

		echo "ERROR!"
		echo "Missing file: $DEST/$l/obs/markdown/obs-$l.md"
		echo "Run `export_markdown.sh $l` to generate."

	fi

	echo ""

done

exit 0
