# coding: latin-1

# This script produces a set of .usx files in resource container format from
# a USFM source text.
# Chunk division and paragraph locations are based on an English resource container of the same Bible book.
# Uses parseUsfm module.
# This script was originally written for converting Guarani translated text in USFM format to RC format
# so that the existing Guarani translation could be used as a source text in tStudio.

# The location of the English RC is hard-coded in the script and must be changed for each book processed.
# The input file should be verified, correct USFM.
# The output, target language RC is also hard-coded and may need to be changed for each run of this script.
# Both content folders must exist before the script will run.

import sys
import os

# Set Path for files in support/
rootdiroftools = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(rootdiroftools,'support'))

import parseUsfm
import io
import codecs
import re

# Global variables
en_content_dir = r'C:\Users\Larry\AppData\Local\translationstudio\library\resource_containers\en_mrk_ulb\content'
target_content_dir = r'C:\Users\Larry\Documents\GitHub\Spanish\es-419_mrk_ulb\content'
target_book_name = u'Marcos'
package_json_template_dir = r'C:\Users\Larry\Documents\GitHub\Spanish\es-419_mat_ulb'   # Can be from a different book
lastToken = parseUsfm.UsfmToken(None)
vv_re = re.compile(r'([0-9]+)-([0-9]+)')

class State:
    ID = u""
    chapter = 0
    chapterPad = "00"
    verse = 0
    lastVerse = 0
    versePad = "00"
    needingVerseText = False
    pendingVerse = 0
    sectionPending = u""
    pendingEndpp = False
    reference = u""
    lastRef = u""
    en_chapter_dir = ""
    usxTemplate = u""
    usxTemplatePtr = 0
    # usxOutput = io.open(os.path.join(target_content_dir, "temp.txt"), "tw")
    usxOutput = 0
    
    def addID(self, id):
        State.ID = id
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.needingVerseText = False
        State.lastRef = State.reference
        State.reference = id
        
    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        # Will need a different padding algorithm for Psalms
        if len(c) == 1:
            State.chapterPad = "0" + c
        else:
            State.chapterPad = c
        State.lastVerse = 0
        State.verse = 0
        State.versePad = ""
        State.needingVerseText = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c
    
    # Reports if vv is a range of verses, e.g. 3-4. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        if vv.find('-') > 0:
            sys.stderr.write("Range of verses encountered at " + State.reference + "\n")
            vv_range = vv_re.search(vv)
            self.addVerse(vv_range.group(1))
            self.addVerse(vv_range.group(2))
        else:
            self.addVerse(vv)

    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        # Will need a different padding algorithm for Psalms
        if len(v) == 1:
            State.versePad = "0" + v
        else:
            State.versePad = v
        State.needingVerseText = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v
        
    def setPendingVerse(self, v):
        if v:
            State.pendingVerse = int(v)
        else:
            State.pendingVerse = 0
            
    def setPendingEndpp(self, endpp):
        State.pendingEndpp = endpp

    def needVerseText(self):
        return State.needingVerseText
        
    def addText(self):
        State.needingVerseText = False

    def saveSection(self, s):
        State.sectionPending = s
    
    def setUsxTemplate(self, s):
        State.usxTemplate = s
        State.usxTemplatePtr = 0
        
#     def getTemplatePtr(self):
#         return State.usxTemplatePtr

    def advanceTemplate(self, n):
        State.usxTemplatePtr += n
        
    def clearSource(self):
        State.usxTemplate = u""
        State.usxTemplatePtr = 0
            
    def openUsxOutput(self, filename):
        if State.usxOutput:
            State.usxOutput.close()
        target_chapter_dir = os.path.join(target_content_dir, State.chapterPad)
        target_usx_path = os.path.join(target_chapter_dir, filename)
        State.usxOutput = io.open(target_usx_path, "tw", encoding="utf-8", newline='\n')
        
    def closeUsxOutput(self):
        if State.usxOutput:
            State.usxOutput.close()
            State.usxOutput = 0

    def writeUsx(self, t):
        if State.usxOutput:
            State.usxOutput.write(t)
    
    
def printToken(token):
        if token.isV():
            print "Verse number " + token.value
        elif token.isC():
            print "Chapter " + token.value
        elif token.isS():
            sys.stdout.write(u"Section heading: " + token.value)
        elif token.isTEXT():
            print "Text: <" + token.value + ">"
        else:
            print token

# Closes the previous output USX file.
# Opens the new ones, based on current state.
# Creates the new target chapter dir if needed.
def changeFiles():
    state = State()
#    if state.getUsxFile():
#        state.usxOutput.close

    en_chapter_dir = os.path.join(en_content_dir, state.chapterPad)
    if state.verse:
        filename = state.versePad + ".usx"
        en_usx_path = os.path.join(en_chapter_dir, filename)
        try:
            usxInput = io.open(en_usx_path, "tr", encoding="utf-8")
            src = usxInput.read()
            usxInput.close()
            state.setUsxTemplate(src)
        except IOError as e:
            sys.stderr.write("Invalid input file: " + en_usx_path + "\n")
        except WindowsError as e:
            sys.stderr.write("Invalid input file: " + en_usx_path + "\n")
    else:
        filename = "title.usx"
        state.setUsxTemplate(u"")

    state.openUsxOutput(filename)

    
endpp_re = re.compile('([^\n]*</para> *\n)')
# startpp_re = re.compile(r'(<para style="p">)')
# anotherverse_re = re.compile(r'(\n *<verse number=")')

# Copies everything from the template .usx to the target language .usx, up thru the current verse tag.
# Writes the verse.  Resets state.usxTemplate for the next verse.
# Handles ranges of verses in the template .usx by splitting them into separate verses in the target.
def writeVerse(t):
    written = False
    state = State()
    srcTemplate = state.usxTemplate[state.usxTemplatePtr:]
    pattern = '(<verse number="' + str(state.verse) + ')(-\d*)" *style="v" */>'
    pattern2 = '(<verse number="' + str(state.verse) + ')" *style="v" */>'
    match = re.search(pattern, srcTemplate)
    if match:
        pendingVerse = match.group(2)[1:]
        # print "DX: " + srcTemplate[0:match.end(1)] + ". pendingVerse: " + pendingVerse
    else:
        pendingVerse = ""
        match = re.search(pattern2, srcTemplate)

    if match:
        # First, take care of pending section heading
        if state.sectionPending:
            state.writeUsx(u'<para style="p">' + state.sectionPending + u'</para>\n\n')
            state.saveSection(u"")
        state.writeUsx(srcTemplate[0:match.end(1)] + u'" style="v" />' + t)
        written = True
        state.advanceTemplate(match.end())
        srcTemplate = srcTemplate[match.end():]
        state.setPendingVerse( pendingVerse )   # last verse of range; sets to 0 if no range
        endpp = endpp_re.match( srcTemplate )
#        startpp = startpp_re.search(srcTemplate)
#        next = anotherverse_re.search(srcTemplate)
        
        # End verse
        if endpp:
            if state.verse >= state.pendingVerse:
                state.writeUsx(u"</para>\n")
                state.setPendingEndpp(False)
            else:
                state.setPendingEndpp(True)
            state.advanceTemplate(endpp.end())
        else:
            match = re.search("(\n)", srcTemplate)
            if match:
                state.advanceTemplate(match.end())
            state.writeUsx(u"\n")
    elif state.pendingVerse >= state.verse:
        state.writeUsx(u'\n<verse number="' + str(state.verse) + '" style="v" />' + t)
        written = True
        if state.pendingEndpp:
            state.writeUsx(u"</para>\n")
            state.setPendingEndpp(False)
        
    return written


def takeID(id):
    state = State()
    state.addID(id[0:3])

# When a chapter marker is encountered in the USFM file, we close the current .usx files
# and change en_chapter_dir to the corresponding chapter directory under the English RC content folder.
# We also write a default title.usx for the chapter.
def takeC(c):
    state = State()
    state.addChapter(c)
    print "Starting chapter " + c
    target_chapter_dir = os.path.join(target_content_dir, state.chapterPad)
    if not os.path.isdir(target_chapter_dir):
        os.mkdir(target_chapter_dir)
    changeFiles()
    state.writeUsx( str(state.chapter) + u" - " )

# Append chapter title to the output .usx file
def takeS(s):
    state = State()
#    print u"takeS length " + str(len(s)) + u" while state.verse == " + str(state.verse)
    if state.verse == 0:    # section heading is at the start of the chapter
        state.writeUsx(s)
    else:
        state.saveSection(s)

# When a verse marker is encountered in the USFM file, we close the current .usx files and open new ones.
# We then copy any desirable tags in the new .usx file, up to the specified verse.
def takeV(v):
    state = State()
    state.addVerses(v)
#   changeFiles()
 
def takeText(t):
    state = State()
#    print u"takeText length " + str(len(t)) + u" while state.verse == " + str(state.verse)
    if state.verse > 0:
        if not writeVerse(t):
            changeFiles()
            writeVerse(t)
    state.addText()
 
def take(token):
    state = State()
    if state.needVerseText() and not token.isTEXT():
        print "Empty verse: " + state.reference
    if token.isC():
        takeC(token.value)
    elif token.isS():
        # printToken(token)   # temp
        takeS(token.value)
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    global lastToken
    lastToken = token
     
def convertFile(filename):
    # detect file encoding
    enc = detect_by_bom(filename, default="utf-8")
    input = io.open(filename, "tr", 1, encoding=enc)
    str = input.read(-1)
    input.close

    print "CONVERTING " + filename + ":"
    for token in parseUsfm.parseString(str):
        take(token)
    state = State()
    state.closeUsxOutput()
    print "FINISHED.\nAfter running this script, check the following:"
    print "  Investigate any errors reported by the script."
    print "  Edit content/front/title.usx."
    print "  Edit package.json, LICENSE.md in parent folder. Verify that package.json is encoded as UTF-8."
    print "  No <note> or <char> nodes from the English .usx files crept in to the target files. (grep '<note' ...)"
    print "  No English carried over to the target .usx files. (grep -i 'the ' ...)"
    print "  <para> and </para> nodes should be balanced in target .usx files."

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

# Verifies the global content directory variables.
# Prints error message if either directory does not exist or has other problems.
# Returns True or False
def content_dirs_ok():
    content_dirs_ok = True      # various error conditions will make it False
    en_book = en_content_dir[-15:-12]
    target_book = target_content_dir[-15:-12]
    if en_book != target_book:
        print "English book (" + en_book + ") and target language book (" + target_book + ") do not match."
        content_dirs_ok = False
    if not os.path.isdir(en_content_dir):
        print "English content folder does not exist: " + en_content_dir
        content_dirs_ok = False
    if not os.path.isdir(target_content_dir):
        basedir = os.path.dirname(target_content_dir)
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        os.mkdir(target_content_dir)

    if not os.path.isdir(target_content_dir):
        print "Can't create target language content folder: " + target_content_dir
       
    return content_dirs_ok

def cp(srcdir, filename, destdir):
    input = open(os.path.join(srcdir, filename), 'r')
    output = open(os.path.join(destdir, filename), 'w')
    output.write( input.read() )
    output.close()
    input.close()    

# Adds front folder with title.usx
# Copies config.yml and toc.yml from English template    
def buildOutContentFolder():
    frontFolder = os.path.join(target_content_dir, 'front')
    if not os.path.isdir(frontFolder):
        os.mkdir(frontFolder) 
    output = io.open(os.path.join(frontFolder, 'title.usx'), 'tw', encoding="utf-8")
    output.write( target_book_name )
    output.close()
    
    cp(en_content_dir, 'config.yml', target_content_dir)
    cp(en_content_dir, 'toc.yml', target_content_dir)
    cp(package_json_template_dir, 'LICENSE.md', os.path.dirname(target_content_dir))
    cp(package_json_template_dir, 'package.json', os.path.dirname(target_content_dir))

    
if __name__ == "__main__":
    if content_dirs_ok():
        if len(sys.argv) < 2:
            source = raw_input("Enter path to .usfm file: ")
        elif sys.argv[1] == 'hard-coded-path':
            source = r'C:\Users\Larry\Documents\GitHub\Spanish\es-419_mrk_level2wc_text_ulb\es-419_mrk_level2wc_text_ulb.usfm'
        else:
            source = sys.argv[1]

        if os.path.isfile(source):
            buildOutContentFolder()
            convertFile(source)
        else:
            print "USFM input file not found: " + source
