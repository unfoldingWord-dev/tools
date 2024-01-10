# Utility functions

import os
import re

# Returns a count of files in specifed folder matching file name pattern.
# Recursive
# Omits subfolders whose names start with '.'
def count_files(folder, pattern):
    n = 0
    for entry in os.listdir(folder):
        if entry[0] != '.':
            path = os.path.join(folder, entry)
            if os.path.isdir(path):
                n += count_files(path, pattern)
            elif re.match(pattern, entry.lower()):
                n += 1
    return n

# Returns a count of folders in path matching path name pattern.
# If the specified path itself is a folder matching the pattern, return 1.
# Omits subfolders whose names start with '.'
def count_folders(path, pattern):
    n = 0
    if os.path.isdir(path):
        if re.search(pattern, path):
            n = 1
        else:
            for entry in os.listdir(path):
                if entry[0] != '.':
                    subpath = os.path.join(path, entry)
                    n += count_folders(subpath, pattern)
    return n
