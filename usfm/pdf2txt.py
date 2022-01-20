# -*- coding: utf-8 -*-
# This script converts PDF files to plain text files.
# Converts multiple files from the source_dir, creating .txt files in the target_dir.

# Global variables
source_dir = r'C:\DCS\Tuvan\PDF\Jacob.pdf'
target_dir = r'C:\DCS\Tuvan\TEXT'

import io
import os
import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams

def shortname(longpath):
    shortname = longpath
    if source_dir in longpath:
        shortname = longpath[len(source_dir)+1:]
    return shortname

# Uses the old Python 2 pdfminer library to convert the pdf file to text.
# Returns path name of the new text file.
def pdf2txt(pdfPath):
    (root, ext) = os.path.splitext( os.path.basename(pdfPath) )
    txtPath = os.path.join(target_dir, root + ".txt")
    fTxt = io.open(txtPath, "tw", encoding='utf-8', newline='\n')
    rsrcmgr = PDFResourceManager(caching=False)
    laparams = LAParams()
    device = TextConverter(rsrcmgr, fTxt, laparams=laparams, imagewriter=None)
    pagenos = set()
    with io.open(pdfPath, 'rb') as pdf:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(pdf, pagenos, maxpages=0, password=b'', caching=False, check_extractable=True):
            # page.rotate = 0
            interpreter.process_page(page)
    device.close()
    fTxt.close()
    return txtPath

# This method is called to extract the text from the pdf file.
def convertFile(path):
    sys.stdout.write("Converting: " + shortname(path) + "\n")
    sys.stdout.flush()
    pdf2txt(path)

def convertFolder(folder):
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if os.path.isdir(path) and entry[0] != '.':
            convertFolder(path)
        elif os.path.isfile(path) and entry.endswith(".pdf"):
            convertFile(path)

# Processes each directory and its files one at a time
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    if os.path.isdir(source_dir):
        convertFolder(source_dir)
    elif os.path.isfile(source_dir) and source_dir.endswith(".pdf"):
        path = source_dir
        source_dir = os.path.dirname(source_dir)
        convertFile(path)
    print("\nDone.")
