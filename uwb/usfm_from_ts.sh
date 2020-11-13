#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

set -e

: ${DEBUG:=false}

# Process command line options
while getopts l:v:b:s:o:w opt; do
    case $opt in
        l) LANGUAGE=$OPTARG;;
        s) SPECIAL_FONT=$OPTARG;;
        v) VERSION=$OPTARG;;
        b) BOOK=$OPTARG;;
        o) OUTPUT_FILE=$OPTARG;;
        w) WORKING_DIR=$OPTARG;;
    esac
done

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

: ${LANGUAGE:=en}
: ${VERSION:=udb}

case $VERSION in
  udb) VERSION_TITLE="Unlocked Dynamic Bible";;
  ulb) VERSION_TITLE="Unlocked Literal Bible";;
  *) VERSION_TITLE=${VERSION^^}
esac

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "${LANGUAGE}-${VERSION}-usfm.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

TS_REPO_DIR="/var/lib/deployed_repositories/tS"
TOOLS_DIR="/home/rmahn/tools"

BASENAME="${LANGUAGE}-${VERSION}-${BOOK}"
COMPILED_DIR="$WORKING_DIR/${BASENAME}-tS"
USFM_DIR="$WORKING_DIR/${BASENAME}-USFM"
USFM_FILE="$USFM_DIR/${BASENAME}.usfm"

: ${OUTPUT_FILE:=$(pwd)/$BASENAME.usfm}

# Gets us an associative array called $BOOK_NAMES
source "$TOOLS_DIR/general_tools/bible_books.sh"

mkdir -p $COMPILED_DIR
mkdir -p $USFM_DIR 

title_file="$COMPILED_DIR/title.txt"
for tsdir in `find $TS_REPO_DIR -type d -name uw-${BOOK}-${LANGUAGE}`
do
  echo $tsdir

  new_title_file="$tsdir/title.txt"
  if ([ -s $new_title_file ]) && ([ ! -e "$title_file" ] || ([ $title_file -ot $new_title_file ]));
  then
    cp -p $new_title_file $title_file
  fi

  for dir in `ls -d $tsdir/[01234567890]*`
  do
    echo $dir
    chapter=$(basename "$dir")
    mkdir -p "$COMPILED_DIR/$chapter"
    for file in `ls $dir/[01234567890]*.txt`
    do
      chunk=$(basename "$file")
      new_file="$COMPILED_DIR/$chapter/$chunk"
      fs=`wc -c $file | cut -d' ' -f1`
      if [ -e $new_file ];
      then
        new_fs=`wc -c $new_file | cut -d' ' -f1`
      else
        new_fs=0
      fi
      if ([ -s $file ]) && ([ ! -e "$new_file" ] || ([ $new_file -ot $file ] && [ $fs -ge $new_fs ]));
      then
        cp -p $file $new_file
        ls -l $file
        ls -l $new_file
      fi
    done
  done
done

rm -f "$USFM_FILE"
touch "$USFM_FILE" 


if [ -e $USFM_DIR/title.txt ];
then
  : ${BOOK_TITLE=$(cat $USFM_DIR/title.txt)}
else
  : ${BOOK_TITLE:=${BOOK_NAMES[$BOOK]}}
fi

echo "\\id ${BOOK^^} $VERSION_TITLE" >> "$USFM_FILE"
echo "\\ide UTF-8" >> "$USFM_FILE"
echo "\\h $BOOK_TITLE" >> "$USFM_FILE"
echo "\\toc1 $BOOK_TITLE" >> "$USFM_FILE"
echo "\\mt $BOOK_TITLE" >> "$USFM_FILE"

for dir in `ls -d ${COMPILED_DIR}/[01234567890]*`
do
  chapter=$((10#$(basename "$dir")))
  start=true
  
  echo >> "$USFM_FILE"
  echo '\s5' >> "$USFM_FILE"
  echo "\\c $chapter" >> "$USFM_FILE"
 
  for file in `ls $dir/[01234567890]*.txt`
  do
    filename=$(basename "$file")
    chunk=${filename%.*}
    
    if ! $start;
    then
      echo >> "$USFM_FILE"
      echo '\s5' >> "$USFM_FILE"
    else
      start=false
    fi  

    echo '\p' >> "$USFM_FILE"
    cat $file >> "$USFM_FILE"
    echo >> "$USFM_FILE"
  done
done

sed -i -e 's/\s*<verse number="\([0-9]\+\)"[^>]*>\s*/ \\v \1 /g' "$USFM_FILE"
sed -i -e 's/\s*\/v\([0-9]\+\)\s*/ \\v \1 /g' "$USFM_FILE"
sed -i -e 's/^ \\v /\\v /' "$USFM_FILE"

install -Dm 0644 "$USFM_FILE" "$OUTPUT_FILE"

echo INSTALL FILE: $OUTPUT_FILE
echo DONE!
