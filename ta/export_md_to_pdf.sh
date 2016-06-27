#!/usr/bin/env bash
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wyciffeassociates.org>

WORKING_DIR=/home/rmahn/working-ta
OUT_DIR=/var/www/vhosts/api.unfoldingword.org/httpdocs/test/ta
repos=(en-ta-intro en-ta-process en-ta-translate-vol1 en-ta-translate-vol2)

for repo in "${repos[@]}"
do
    if [ ! -e "$WORKING_DIR/$repo" ]; then
        cd "$WORKING_DIR"
        git clone "https://git.door43.org/Door43/$repo.git"
    else
        cd "$WORKING_DIR/$repo"
        git pull
    fi
done

/home/rmahn/repos/tools/ta/md_to_pdf_export.py -i "$WORKING_DIR" -o "$OUT_DIR"

for repo in "${repos[@]}"
do
     echo /home/rmahn/working-ta/wkhtmltox/bin/wkhtmltopdf --encoding utf-8 -O portrait -L 15 -R 15 -T 15 -B 15 --header-left '[section]' --header-right '[subsection]' --header-line --header-spacing 5 --footer-center '[page]' cover "file://$OUT_DIR/${repo}-cover.html" toc --disable-dotted-lines --xsl-style-sheet "$WORKING_DIR/default.xsl" "file://$OUT_DIR/$repo.html" "$OUT_DIR/$repo.pdf"
     /home/rmahn/working-ta/wkhtmltox/bin/wkhtmltopdf --encoding utf-8 -O portrait -L 15 -R 15 -T 15 -B 15 --header-left '[section]' --header-right '[subsection]' --header-line --header-spacing 5 --footer-center '[page]' cover "file://$OUT_DIR/${repo}-cover.html" toc --disable-dotted-lines --xsl-style-sheet "$WORKING_DIR/default.xsl" "file://$OUT_DIR/$repo.html" "$OUT_DIR/$repo.pdf"
done
