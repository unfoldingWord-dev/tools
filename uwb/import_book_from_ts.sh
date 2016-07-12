#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

: ${TOOLS_DIR:=$(cd $(dirname "$0")/../ && pwd)}

FILE_TYPES=()
BOOKS_TO_PROCESS=()

VALID_FILE_TYPES=(pdf docx html tex txt text)

# Gets us an associative array called $bookS
source "$TOOLS_DIR/general_tools/bible_books.sh"

#gather command-line arguments
while [[ $# > 0 ]]
do
    arg="$1"
    case $arg in
        -o|--output)
            OUTPUT_DIR="$2"
            shift # past argument
        ;;
        -w|--working)
            WORKING_DIR="$2"
            shift # past argument
        ;;
        -l|--lang|-language)
            LANGUAGE="$2"
            shift # past argument
        ;;
        --debug)
            DEBUG=true
        ;;
        -t|--type)
            arg2=${2,,}

            if [ ! ${VALID_FILE_TYPES[$arg2]+_} ];
            then
                echo "Invalid type: $arg2"
                echo "Valid types: pdf, docx, html, tex, txt, text"
                exit 1
            fi

            FILE_TYPES+=("$arg2")

            shift # past argument
        ;;
        *)
            if [ ! ${BOOK_NAMES[${arg,,}]+_} ];
            then
                if [ ${arg,,} = "ot" ];
                then
                    BOOKS_TO_PROCESS+=(gen exo lev num deu jos jdg rut 1sa 2sa 1ki 2ki 1ch 2ch ezr neh est job psa pro ecc sng isa jer lam ezk dan hos jol amo oba jon mic nam hab zep hag zec mal)
                elif [ ${arg,,} = "nt" ];
                then
                    BOOKS_TO_PROCESS+=(mat mrk luk jhn act rom 1co 2co gal eph php col 1ti 2ti 1th 2th tit phm heb jas 1pe 2pe 1jn 2jn 3jn jud rev)
                else
                    echo "Invalid book given: $arg"
                    exit 1;
                fi
            else
                BOOKS_TO_PROCESS+=("$arg")
            fi
        ;;
    esac
    shift # past argument or value
done

: ${DEBUG:=false}
: ${LANGUAGE:=en}

: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:=$TOOLS_DIR/uwb/tex/uwb_template.tex}

ver='udb'
book='act'
VERSION_TITLE="Unlocked Dynamic Bible"
WORKING_DIR="/home/rmahn/india"
TOOLS_DIR="/home/rmahn/tools"
USFM_TOOLS_DIR="/home/rmahn/USFM-Tools"
TS_REPO_DIR="/var/lib/deployed_repositories/tS"
MAIN_FONT="Noto Sans Kannada"
compile_repo=true

COMPILED_DIR="$WORKING_DIR/${lang}-${ver}-${book}-tS"
USFM_DIR="$WORKING_DIR/${lang}-${ver}-${book}-USFM"
BOOK_TITLE=`cat $USFM_DIR/title.txt`
BASENAME="${lang}-${ver}-${book}"
USFM_FILE="${BASENAME}.usfm"

mkdir -p $COMPILED_DIR
mkdir -p $USFM_DIR 

if $compile_repo;
then

for tsdir in `find $TS_REPO_DIR -type d -name uw-${book}-${lang}`
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
      if ([ -s $file ]) && ([ ! -e "$new_file" ] || ([ $new_file -ot $file ] && [ $fs -ge $new_fs ]));
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
TEMPLATE="/home/rmahn/india/mr_template.tex"

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
        -V mainfont="Noto Sans Kannada" \
        -V sansfont="Noto Sans" \
        -o "${BASENAME}.pdf" "${USFM_DIR}/${BASENAME}.html"

