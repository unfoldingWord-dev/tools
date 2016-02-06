#!/usr/bin/env sh
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

help() {
    echo
    echo "Creates a torrent file for the given apk. App should match the name"
    echo "of the directory on api.unfoldingword.org."
    echo
    echo "Usage:"
    echo "   $PROGNAME -f <APK file> -v <Version of APK> -a <App>]"
    echo "   $PROGNAME --help"
    echo
    exit 1
}

if [ $# -lt 1 ]; then
    help
fi
while test -n "$1"; do
    case "$1" in
        --help|-h)
            help
            ;;
        --file|-f)
            APK="$2"
            shift
            ;;
        --app|-a)
            APP="$2"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            help
            ;;
    esac
    shift
done

[ ! -f "$APK" ] && echo "Please specify apk file." && exit 1

APKNAME="${APK%%.apk}"

mktorrent -c "$APKNAME" -n "$APKNAME" \
    -a http://torrent.tracker/announce,http://tracker.prq.to/announce,http://open.tracker.thepiratebay.org/announce,http://www.sumotracker.com/announce \
       -w "https://api.unfoldingword.org/$APP/apk/$APK" \
       "$APK"
