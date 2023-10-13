# -*- coding: utf-8 -*-
# Renames Paratext .SFM files to our standard naming convention.
# Set these config values in the GENERAL section of config.ini before running this script.
#   source_dir
#   target_dir


import configparser
import os
from pathlib import Path
import shutil
import sys
import usfm_verses

# Generates our standard name for usfm file
def makeUsfmFilename(bookId):
    num = usfm_verses.verseCounts[bookId]['usfm_number']
    return num + '-' + bookId + '.usfm'

def convert(source_dir, target_dir):
    count = 0
    sourcepath = Path(source_dir)
    for path in sourcepath.glob('*.SFM'):
        bookid = path.name[2:5]
        newpath = os.path.join(target_dir, makeUsfmFilename(bookid))
        shutil.copyfile(str(path), str(newpath))
        count += 1
    if count == 0:
        sys.stderr.write(f"There are no .SFM files in {source_dir}.\n")
    return count

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = r'C:\DCS\config.ini'
    while not os.path.exists(config_path):
        config_path = input("Enter the path of your configuration file: ")

    config = configparser.ConfigParser()
    config.read(config_path)
    try:
        general = config['GENERAL']
        source_dir = general['source_dir']
        target_dir = general['target_dir']

        if os.path.isdir(source_dir):
            Path(target_dir).mkdir(exist_ok=True)
            count = convert(source_dir, target_dir)
            print(f"Copied and renamed {count} files.")
        else:
            print("Invalid source_dir folder: " + source_dir + '\n')
    except:
        sys.stderr.write(f"Set these config values in the GENERAL section of config.ini: source_dir and target_dir\n")

