#!/bin/bash
#

SRC="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/en"
LANG="$1"

if [ -z "$LANG" ]; then
    echo "Please specify language to create links for."
    exit 1
fi

LANGDIR="/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/jpg/1/$LANG"

# Make directories
for d in `find $SRC -type d`; do 
    [ "$SRC" == "$d" ] && continue
    ld="${d##*/}"
    mkdir -p "$LANGDIR/$ld"
done

# Make symlinks
for x in `find $SRC -type f`; do 
    lf=`echo $x | sed "s/en/$LANG/g"`
    ln -s $x $lf
done
