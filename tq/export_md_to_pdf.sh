#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>
#
#  Execute export_md_to_pdf.sh to run
#  Set WORKING_DIR, otherwise will be a temp dir
#  Set OUTPUT_DIR, otherwise will be the current dir

set -e # die if errors

: ${DEBUG:=false}

: ${MY_DIR:=$(cd $(dirname "$0") && pwd)} # Tools dir relative to this script
: ${OUTPUT_DIR:=$(pwd)}
: ${TEMPLATE:="$MY_DIR/toc_template.xsl"}
: ${TEMPLATE_ALL:="$MY_DIR/toc_template_all.xsl"}
: ${LANGUAGE:="en"}
: ${RESOURCE:="tq"}
: ${TAG:="v11"}

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "export_md_to_pdf.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

source "$MY_DIR/../general_tools/bible_books.sh"

echo $WORKING_DIR

# Change to our own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR" > /dev/null

# link tools folder
if [[ ! -L ./tools ]]; then
  ln -sf $MY_DIR/.. ./tools
fi

repo="${LANGUAGE}_${RESOURCE}"
url="https://git.door43.org/Door43/${repo}/archive/${TAG}.zip"

if [[ ! -d $repo ]]; then
  wget $url -O "./${repo}.zip"
  unzip -qo "./${repo}.zip"
  echo "Checked out repo files:"
  ls "${repo}"
fi

version=`js-yaml "${repo}/manifest.yaml" | jq -r '.dublin_core.version'`
publisher=`js-yaml "${repo}/manifest.yaml" | jq -r '.dublin_core.publisher'`
issued_date=`js-yaml "${repo}/manifest.yaml" | jq -r '.dublin_core.issued'`
title=`js-yaml "${repo}/manifest.yaml" | jq -r '.dublin_core.title'`
checking_level=`js-yaml "${repo}/manifest.yaml" | jq -r '.checking.checking_level'`
contributors=$(echo `js-yaml "${repo}/manifest.yaml" | jq -c '.dublin_core.contributor[]'`)
contributors=${contributors//\" \"/; }
contributors=${contributors//\"/}

echo "Current '$repo' Resource is at: ${url}"
echo "Current '$repo' Version is at: ${version}"
echo "Current '$repo' Publisher is: ${publisher}"
echo "Current '$repo' Contributors are: ${contributors}"

# make sure old out files are gone
# rm -f $OUTPUT_DIR/html/*
# rm -f $OUTPUT_DIR/pdf/*

mkdir -p "$OUTPUT_DIR/html"
cp "$MY_DIR/style.css" "$OUTPUT_DIR/html"
cp "$MY_DIR/header.html" "$OUTPUT_DIR/html"

book_export () {
    book=$1

    htmlfile="$OUTPUT_DIR/html/${book}.html"
    if [[ ! -f $htmlfile ]]; then 
      echo "GENERATING HTML File: $htmlfile"
      python -m tools.tq.md_to_html_export -i "$WORKING_DIR/$repo" -o "$OUTPUT_DIR/html" -v "$version" -p "$publisher" -c "$contributors" -d "$issued_date" -b "$book" -t "$title"
    fi

    headerfile="file://$OUTPUT_DIR/html/header.html"
    coverfile="file://$OUTPUT_DIR/html/${book}_cover.html"
    licensefile="file://$OUTPUT_DIR/html/license.html"
    bodyfile="file://$OUTPUT_DIR/html/$book.html"
    if [[ $book != "all" ]]; then
        outfile="$OUTPUT_DIR/pdf/${repo}_${BOOK_NUMBERS[$book]}-${book^^}_v${version}.pdf"
    else
        outfile="$OUTPUT_DIR/pdf/${repo}_v${version}.pdf"
    fi
    mkdir -p "$OUTPUT_DIR/pdf"
    if [[ ! -f $outfile ]]; then
      echo "GENERATING $outfile"
      wkhtmltopdf --javascript-delay 2000 --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$bodyfile" "$outfile"
    fi
}

if [[ -z $1 ]]; then
  for book in "${ORDERED_BOOKS_LIST[@]}"
  do
      book_export $book
  done
  book_export 'all'
else
  book_export $1
fi
