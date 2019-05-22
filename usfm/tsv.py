# -*- coding: utf-8 -*-
# This module consists of some functions useful for processing .tsv (tab-separated value) files.
# The tsvRead function imports all data from a .tsv file into a Python list of lists of strings.
# The data consists of a list of rows. Each row is a list of field values.
# Strips leading and trailing spaces from field values.
# This module also has a tsvWrite function that writes a list of list of strings to a specified file.
# The list2Dict function converts a list to a Python dictionary mapping.
# make_key() generates keys used in the dictionary.

# import re
import io
# import os
# import sys
# import json
import codecs


def tsvRead(inputPath):
    enc = detect_by_bom(inputPath, default="utf-8")
    f = io.open(inputPath, "tr", 1, encoding=enc)
    data = []
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        fields = line.split(u'\t')
        fields = [field.strip() for field in fields]
        data.append(fields)
    f.close()
    return data

def tsvWrite(data, tsvPath):
    tsvFile = io.open(tsvPath, "tw", buffering=1, encoding='utf-8', newline='\n')
    ustr = u""
    for row in data:
        ustr = u'\t'.join(row)
        tsvFile.write(ustr + u'\n')
    tsvFile.close()

# Maps each element of the list to a dictionary key, based on values in the key columns of the list.
# The list of strings in each element of the list become the values of the dictionary.
# Returns this dictionary object.
def list2Dict(list, keycolumns):
    dict = {}
    for row in list:
        key = make_key(row, keycolumns)
        dict[key] = row
    return dict

def make_key(list, keycolumns):
    key = u""
    for col in keycolumns:
        key += list[col]
        key += u'.'
    return key[:-1]

def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default
