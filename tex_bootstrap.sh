#!/usr/bin/env bash

# If it doesn't exist, install minimal ConTeXt distribution locally
if [[ ! -d tex ]] && ! command -v context; then
    cd $(dirname "$0")
    sh <(curl -s -L http://minimals.contextgarden.net/setup/first-setup.sh)
else
    echo "You seem to have ConTeXt installed arleady. If it's not working"
    echo "right try removing it from your path and running this again."
fi
