# -*- coding: utf-8 -*-
# This module consists of some functions useful for processing .tsv (tab-separated value) files.
# The tsvRead function imports all data from a .tsv file into a Python list of lists of strings.
# The data consists of a list of rows. Each row is a list of field values.
# Strips leading and trailing spaces from field values.
# This module also has a tsvWrite function that writes a list of list of strings to a specified file.
# The list2Dict function converts a list to a Python dictionary mapping.
# make_key() generates keys used in the dictionary.

import io
import codecs

# Each row becomes a list of strings
# The entire file is returned as a list of lists of strings (rows).
def tsvRead(inputPath):
#    enc = detect_by_bom(inputPath, default="utf-8")
    f = io.open(inputPath, "tr", 1, encoding="utf-8-sig")
    data = []
    lines = f.readlines()
    for line in lines:
        line = line.strip(' \n')
        fields = line.split('\t')
        fields = [field.strip() for field in fields]
        data.append(fields)
    f.close()
    return data

def tsvWrite(data, tsvPath):
    tsvFile = io.open(tsvPath, "tw", buffering=1, encoding='utf-8', newline='\n')
    ustr = ""
    tab = "\t"
    for row in data:
        ustr = tab.join(row)
        tsvFile.write(ustr + '\n')
    tsvFile.close()

# Maps each element of the list to a dictionary key, based on values in the key columns of the list.
# keycolumns is a list of column numbers which will serve as the unique key for all rows.
# The list of strings in each element of the list become the values of the dictionary.
# Returns this dictionary object.
def list2Dict(list, keycolumns):
    dict = {}
    for row in list:
        key = make_key(row, keycolumns)
        dict[key] = row
    return dict

# Returns a string made up of the keycolumn values separated by dots.
# Example: "r582.11.7"
# The caller must ensure the keycolumn numbers are valid, or an IndexError might occur.
def make_key(list, keycolumns):
    key = ""
    for col in keycolumns:
        if len(list[col]) > 10:
            key += list[col][0:10]
        else:
            key += list[col]
        key += '.'
    return key[:-1]     # remove final period
    