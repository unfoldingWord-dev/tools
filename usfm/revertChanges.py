# -*- coding: utf-8 -*-
# The purpose of this program is to undo changes made by another program that
# at least provided backups of the original files.
# Use with caution as this overwrites files with correctExt extension.

import configmanager
import re       # regular expression module
import io
import os
import string
import sys

gui = None
config = None
maxChanged = 11111
nChanged = 0

# Detects whether file contains the string we are looking for.
# If there is a match, calls doConvert to do the conversion.
def undoFile(backupPath, backupExt, correctExt):
    global nChanged
    basePath = backupPath[:-len(backupExt)]
    correctPath = basePath + correctExt
    if os.path.isfile(correctPath):
        os.remove(correctPath)
    os.rename(backupPath, correctPath)
    nChanged += 1

# Recursive routine to restore all files under the specified folder
def undoFolder(folder, backupExt, correctExt):
    global nChanged
    if nChanged >= maxChanged:
        return
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path):
            undoFolder(path, backupExt, correctExt)
        elif backupExt in entry:
            undoFile(path, backupExt, correctExt)
        if nChanged >= maxChanged:
            break

def main(app = None):
    global gui
    global config
    global nChanged

    gui = app
    nChanged = 0
    config = configmanager.ToolsConfigManager().get_section('RevertChanges')   # configmanager version
    if config:
        source_dir = config['source_dir']
        backupExt = config['backupExt']
        correctExt = config['correctExt']
        undoFolder(source_dir, backupExt, correctExt)
        msg = "Done. Renamed " + str(nChanged) + " files."
        if nChanged == 1:
            msg = "Done. Renamed 1 file."
        if gui:
            with gui.progress_lock:
                gui.progress = msg
            gui.event_generate('<<ScriptEnd>>', when="tail")
        sys.stdout.write(msg + "\n")
    
# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    main()