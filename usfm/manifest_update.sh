#!/usr/bin/env bash
#
# Simple script to update the manifest.yaml file with a few things
# Should be safe to run multiple times on same project
# Should be safe to run on any type of project

# If running on Mac, we need gsed
SED=`which sed`
if [[ -f /usr/bin/sw_vers ]]; then
    if [[ ! -f /usr/local/bin/gsed ]]; then
        echo "Please install gsed"
        exit 1
    fi
    SED="/usr/local/bin/gsed"
fi

# Verifies that the files listed in the manifest are present in the cwd
echo "Ensure every file in manifest is present..."
for x in `grep -ow '[0-6][0-9].*.usfm' manifest.yaml`; do
    [[ -f $x ]] || echo "--> MISSING FILE: $x"
done

# Verifies any USFM files in the cwd are listed in the manifest
echo "Ensure every USFM file in repo is in manifest..."
# Also ensure ide line exists
for x in `ls *.usfm`; do
    grep -q $x manifest.yaml || echo "--> MANIFEST MISSING: $x"
    grep -q '\\ide UTF-8' $x || $SED -i '2i\\\ide UTF-8' $x
done

# Determine USFM3ness
USFM=2
grep -q '\\zaln-s' *.usfm && USFM=3

# If it is USFM 3, add the \usfm 3.0 line to the files and
# set format to usfm3 and subject to Aligned Bible
if [[ "$USFM" -eq 3 ]]; then
    $SED -i "s/  format.*/  format: 'text\/usfm3'/" manifest.yaml
    $SED -i "s/  subject.*/  subject: 'Aligned Bible'/" manifest.yaml
    for x in `ls *.usfm`; do
        grep -q '\\usfm 3.0' $x || $SED -i '2i\\\usfm 3.0' $x
    done
fi

# Today's date
DATE=`date +"%Y-%m-%d"`

$SED -i "s/  issued.*/  issued: \'$DATE\'/" manifest.yaml
$SED -i "s/  modified.*/  modified: \'$DATE\'/" manifest.yaml
echo "Updated issued and modified dates"
echo
echo "--> UPDATE VERSION"

# Run linter on yaml files
test -f manifest.yaml && yamllint *.yaml
