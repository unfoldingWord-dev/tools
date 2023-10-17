# -*- coding: utf-8 -*-
# Script initialization via config file.

import configparser
import os
import sys

# Gets location of config file from argv.
# Prompts for location of config file if necessary.
# Ensures that specified section exists.
# Validates source_dir in specified section.
# Returns configparser config object, or None if any errors.
def get_config(argv, section):
    if len(argv) > 1:
        config_path = argv[1]
    else:
        # -------------------------------------------------------
        # ----- Hard code a permanent config file path here -----
        # -------------------------------------------------------
        config_path = r'C:\DCS\config.ini'

    while not os.path.exists(config_path):
        config_path = input("Enter the full path of your configuration file: ")

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        source_dir = config[section]['source_dir']
        if not os.path.isdir(source_dir):
            sys.stderr.write(f"{source_dir} is not a valid directory name.\n")
            config = None
        elif not os.listdir(source_dir):
            sys.stderr.write(f"{source_dir} is an empty folder!\n")
            config = None
    except KeyError as e:
        sys.stderr.write(f"No {section} section is found in your config file, or no value is found there for source_dir!\n")
        config = None

    return config[section]
