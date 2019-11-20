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
#set -x

compile_repo=false

# Process command line options
while getopts "dcl:v:b:s:o:w:" opt; do
    case $opt in
        d) DEBUG=true;;
        c) compile_repo=true;;
        l) lang=$OPTARG;;
        v) ver=$OPTARG;;
        b) book=$OPTARG;;
        s) SPECIAL_FONT=$OPTARG;;
        o) OUTPUT_DIR=$OPTARG;;
        w) WORKING_DIR=$OPTARG;;
    esac
done

$DEBUG && set -x

case $ver in
  udb) VERSION_TITLE="Unlocked Dynamic Bible";;
  ulb) VERSION_TITLE="Unlocked Literal Bible";;
  *) VERSION_TITLE=${ver^^}
esac

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../.. && pwd)}

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "ubw_pdf_create.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

: ${USFM_TOOLS_DIR:=$(cd $TOOLS_DIR/../USFM-Tools && pwd)}

: ${TS_REPO_DIR:="/var/lib/deployed_repositories/tS"}

COMPILED_DIR="$WORKING_DIR/${lang}-${ver}-${book}-tS"
USFM_DIR="$WORKING_DIR/${lang}-${ver}-${book}-USFM"
BASENAME="${lang}-${ver}-${book}"
USFM_FILE="${BASENAME}.usfm"

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

if [ -e $USFM_DIR/title.txt ];
then
  BOOK_TITLE=$(cat $USFM_DIR/title.txt)
else
echo $book
echo $BOOK_NAMES
  BOOK_TITLE=${BOOK_NAMES[$book]}
fi

mkdir -p $COMPILED_DIR
mkdir -p $USFM_DIR 

if $compile_repo;
then

for tsdir in `find $TS_REPO_DIR -type d -name uw-${book}-${lang} -or -name uw-${book}_${ver}-${lang}`
do
  echo $tsdir
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
      if [ -s $file ] && ([ ! -e "$new_file" ] || ([ $fs -ge $new_fs ] && [ $fs -eq $new_fs ]) || [ $new_file -ot $file ]);
      then
        cp -p $file $new_file
        ls -l $file
        ls -l $new_file
      fi
    done
  done
done

cd $USFM_DIR
rm -f "$USFM_FILE"
touch "$USFM_FILE" 

echo "\\id ${book^^} $VERSION_TITLE" >> "$USFM_FILE"
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

fi

cd $USFM_DIR

python ${USFM_TOOLS_DIR}/transform.py --target=singlehtml --usfmDir=${USFM_DIR} --builtDir=${USFM_DIR} --name=${BASENAME}

PUBLISH_DATE=$(date +"%Y-%m-%d")
VERSION=1
CHECKING_LEVEL=1
TOC_DEPTH=2
TEMPLATE="/home/rmahn/india/uwb_template.tex"

# Generate PDF with PANDOC
curl -o "logo.png" "https://unfoldingword.org/assets/img/icon-${ver}.png"
curl -o "checking.png" "https://api.unfoldingword.org/obs/jpg/1/checkinglevels/uW-Level${CHECKING_LEVEL}-128px.png"

    # Create PDF
    pandoc \
        -S \
        --latex-engine="xelatex" \
        --template="$TEMPLATE" \
        --toc \
        --toc-depth="$TOC_DEPTH" \
        -V documentclass="scrartcl" \
        -V classoption="oneside" \
        -V geometry='hmargin=2cm' \
        -V geometry='vmargin=3cm' \
        -V logo="logo.png" \
        -V title="$VERSION_TITLE" \
        -V subtitle="$BOOK_TITLE" \
        -V checking_level="$CHECKING_LEVEL" \
        -V version="$VERSION" \
        -V publish_date="$PUBLISH_DATE" \
        -V mainfont="Noto Serif" \
        -V sansfont="Noto Sans" \
        -V specialfont="$SPECIAL_FONT" \
        -o "${BASENAME}.pdf" "${USFM_DIR}/${BASENAME}.html"

