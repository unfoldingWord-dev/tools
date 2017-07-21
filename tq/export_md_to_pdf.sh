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

if [[ -z $WORKING_DIR ]]; then
    WORKING_DIR=$(mktemp -d -t "export_md_to_pdf.XXXXXX")
    $DEBUG || trap 'popd > /dev/null; rm -rf "$WORKING_DIR"' EXIT SIGHUP SIGTERM
elif [[ ! -d $WORKING_DIR ]]; then
    mkdir -p "$WORKING_DIR"
fi

source "$MY_DIR/../general_tools/bible_books.sh"

echo $WORKING_DIR

# Change to our own temp dir but note our current dir so we can get back to it
pushd "$WORKING_DIR" > /dev/null

# link tools folder
ln -s $MY_DIR/.. ./tools

ls .

URL=$(python -m tools.general_tools.get_current_resource -l $LANGUAGE -r $RESOURCE);
VERSION=$(python -m tools.general_tools.get_current_resource -l $LANGUAGE -r $RESOURCE -v 1);

repo="${LANGUAGE}_${RESOURCE}"

echo "Current '$repo' Resource is at: $URL"
echo "Current '$repo' Version is at: $VERSION"

# If running in DEBUG mode, output information about every command being run
$DEBUG && set -x

mkdir files

wget $URL -O ./file.zip

unzip -q ./file.zip -d files

echo "Unzipped files:"
ls files/$repo

rm -f $OUTPUT_DIR/html/*
rm -f $OUTPUT_DIR/pdf/*

mkdir -p "$OUTPUT_DIR/html"
cp "$MY_DIR/style.css" "$OUTPUT_DIR/html"
cp "$MY_DIR/header.html" "$OUTPUT_DIR/html"

book_export () {
    book=$1

    echo "GENERATING Tempfile: $OUTPUT_DIR/html/${book}.html"
    python -m tools.tq.md_to_html_export -i "$WORKING_DIR/files/$repo" -o "$OUTPUT_DIR/html" -v "$VERSION" -b $book

    headerfile="file://$OUTPUT_DIR/html/header.html"
    coverfile="file://$OUTPUT_DIR/html/cover.html"
    licensefile="file://$OUTPUT_DIR/html/license.html"
    bodyfile="file://$OUTPUT_DIR/html/$book.html"
    if [[ $book != "all" ]]; then
        outfile="$OUTPUT_DIR/pdf/tq_${BOOK_NUMBERS[$book]}-${book^^}_v${VERSION}.pdf"
    else
        outfile="$OUTPUT_DIR/pdf/tq_v${VERSION}.pdf"
    fi
    mkdir -p "$OUTPUT_DIR/pdf"
    echo "GENERATING $outfile"
    wkhtmltopdf --encoding utf-8 --outline-depth 3 -O portrait -L 15 -R 15 -T 15 -B 15  --header-html "$headerfile" --header-spacing 2 --footer-center '[page]' cover "$coverfile" cover "$licensefile" toc --disable-dotted-lines --enable-external-links --xsl-style-sheet "$TEMPLATE" "$bodyfile" "$outfile"
}

if [[ -z $1 ]]; then
  for book in "${!BOOK_NAMES[@]}"
  do
      book_export $book
  done
  book_export 'all'
else
  book_export $1
fi

cd $OUTPUT_DIR
zip ${repo}.zip ./pdf/*

