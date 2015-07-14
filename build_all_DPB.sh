#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  dboerschlein
#  Caleb Maclennan <caleb@alerque.com>
set -e

# Setup a temp directory for doing out processing in, and clean up after
# ourselves when the script ends or otherwise dies
BASE_DIR=$(cd $(dirname "$0")/../../ && pwd)
TMPDIR=$(mktemp -d --tmpdir)
trap 'cd $BASE_DIR; rm -rf $TMPDIR' EXIT SIGHUP SIGTERM

# Set defaults (may be overridden at runtime with environment variables)
: ${tagver:=3dpbTEST}
: ${yyyymmdd:=$(date +%Y%m%d)}
: ${langlist:=am ru tr fr pt-br en es}
: ${output:=$(pwd)}
: ${drafts:=}

# Pick an output file name based on whether the export script is doing a full
# run or a sample of X chapters for each language
MAX_CHAPTERS=$(sed -n '/^MAX_CHAPTERS/s/.*= *//p' obs/export.py)
[[ $MAX_CHAPTERS -eq 0 ]] && output_package=full || output_package=samples-first-$n-chapters

# Iterate over the language linst and generate PDFs
for lang in $langlist; do
    ./obs/book/publish_PDF.sh -l $lang -v $tagver -o $TMPDIR
    zip -9j $TMPDIR/$output_package $TMPDIR/*${lang}*json.tmp
    # If drafts diretory specified place a dated copy of each PDF there
    [[ -d $drafts ]] && install -Dm 0644 $TMPDIR/OBS-${lang}-v${tagver}.pdf \
                            $drafts/OBS-${lang}-v${tagver}-${yyyymmdd}.pdf
done

# Package up everything that got generated
zip -9rj $TMPDIR/$output_package $TMPDIR/[A-Za-z]*$tagver*[a-z]

# Generate and add a report to the package
for lang in $langlist; do
{
    formatA="%-10s%-30s%s\n"
    formatD="%-10s%-10s%-10s%-10s%s\n"
    printf "$formatA" "language" "link-counts-each-matter-part  possibly-rogue-links-in-JSON-files"
    printf "$formatA" "--------" "----------------------------  --------------------------------------------------------"
    for lang in $langlist; do
        cat $TMPDIR/OBS-${lang}*${tagver}*tex \
            | egrep 'start.*matter|goto' \
            | sed -e 's/goto/~goto~/g' \
            | tr '~' '\n' \
            | egrep 'matter|\.com|goto' \
            | tee $TMPDIR/part \
            | egrep 'matter|goto' \
	    | tee $TMPDIR/matter-goto \
            | awk 'BEGIN{tag="none"}
                {
                    if (sub("^.*start","",$0) && sub("matter.*$","",$0)) {tag = $0 }
                    if ($0 ~ goto) { count[tag]++ }
                }
                END { for (g in count) { printf "%s=%d\n", g, count[g]; } }' \
            | sort -ru \
            > $TMPDIR/tmp
        cat $TMPDIR/part \
            | sed -e 's/[^ ]*https*:[^ ]*]//' \
            | tr ' ()' '\n' \
            | egrep 'http|\.com' \
            > $TMPDIR/bad
        printf "$formatD" "$lang" $(cat $TMPDIR/tmp) "$(echo $(cat $TMPDIR/bad))"
    done
} | tee -a $TMPDIR/OBS-${tagver}-report.txt
done
zip -9j $TMPDIR/$output_package $TMPDIR/OBS-${tagver}-report.txt

# Copy the final package to the requested output location
install -Dm 0644 $TMPDIR/$output_package.* $output/
