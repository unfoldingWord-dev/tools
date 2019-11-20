import logging
import re

from .abstractRenderer import AbstractRenderer
from .books import bookKeys, bookNames, silNames, readerNames, bookKeyForIdValue
from .parseUsfm import UsfmToken

#
#   Simplest renderer. Ignores everything except ascii text.
#

class SingleHTMLRenderer(AbstractRenderer):
    def __init__(self, inputDir, outputFilename):
        # logging.debug(f"SingleHTMLRenderer.__init__( {inputDir}, {outputFilename} ) …")
        # Unset
        self.f = None  # output file stream
        # IO
        self.outputFilename = outputFilename
        self.inputDir = inputDir
        # Position
        self.cb = ''    # Current Book
        self.cc = '001'    # Current Chapter
        self.cv = '001'    # Current Verse
        self.inParagraph = False
        self.indentFlag = False
        self.bookName = ''
        self.chapterLabel = 'Chapter'
        self.listItemLevel = 0

        self.footnoteFlag = False
        self.fqaFlag = False
        self.footnotes = {}
        self.footnote_id = ''
        self.footnote_num = 1
        self.footnote_text = ''

        # TODO: This isn't finished
        self.crossReferenceFlag = False
        self.crossReferences = {}
        self.crossReference_id = ''
        self.crossReference_num = 1
        self.crossReference_origin = ''
        self.crossReference_text = ''


    def render(self):
        # logging.debug("SingleHTMLRenderer.render() …")
        self.loadUSFM(self.inputDir) # Result is in self.booksUsfm
        #print(f"About to render USFM ({len(self.booksUsfm)} books): {str(self.booksUsfm)[:300]} …")
        with open(self.outputFilename, 'wt', encoding='utf-8') as self.f:
            warning_list = self.run()
            self.writeFootnotes()
            self.writeCrossReferences()
            self.f.write('\n    </body>\n</html>\n')
        return warning_list


    def writeHeader(self):
        h = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="content-type" content="text/html; charset=utf-8"></meta>
    <title>""" + self.bookName + """</title>
    <style media="all" type="text/css">
    .indent-0 {
        margin-left:0em;
        margin-bottom:0em;
        margin-top:0em;
    }
    .indent-1 {
        margin-left:0em;
        margin-bottom:0em;
        margin-top:0em;
    }
    .indent-2 {
        margin-left:1em;
        margin-bottom:0em;
        margin-top:0em;
    }
    .indent-3 {
        margin-left:2em;
        margin-bottom:0em;
        margin-top:0em;
    }
    .c-num {
        color:gray;
    }
    .v-num {
        color:gray;
    }
    .tetragrammaton {
        font-variant: small-caps;
    }
    .d {
        font-style: italic;
    }
    .footnotes {
        font-size: 0.8em;
    }
    .footnotes-hr {
        width: 90%;
    }
    </style>

</head>
<body>
<h1>""" + self.bookName + """</h1>
"""
        self.f.write(h)

    def startLI(self, level=1):
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} startLI({level})…")
        if self.listItemLevel:
            self.stopLI()
        assert self.listItemLevel == 0
        # self.listItemLevel = 0 # Should be superfluous I think
        while self.listItemLevel < level:
            self.f.write('<ul>')
            self.listItemLevel += 1

    def stopLI(self):
        # if 'NUM' in self.bookName and '00' in self.cc and self.listItemLevel: logging.debug(f"@{self.cc}:{self.cv} stopLI() from level {self.listItemLevel}…")
        while self.listItemLevel > 0:
            self.f.write('</ul>')
            self.listItemLevel -= 1
        assert self.listItemLevel == 0

    def escape(self, s):
        return s.replace('~', '&nbsp;')

    def write(self, unicodeString):
        self.f.write(unicodeString.replace('~', '&nbsp;'))

    def writeIndent(self, level):
        assert level > 0
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} writeIndent({level})…")
        # if self.indentFlag:
        self.closeParagraph()  # always close the last indent before starting a new one
        self.indentFlag = True
        self.write('\n<p class="indent-' + str(level) + '">\n')
        self.write('&nbsp;' * (level * 4))  # spaces for PDF since we can't style margin with css

    def closeParagraph(self):
        # if 'NUM' in self.bookName and '00' in self.cc and self.indentFlag: logging.debug(f"@{self.cc}:{self.cv} closeParagraph() from {self.indentFlag}…")
        if self.inParagraph:
            self.inParagraph = False
            self.f.write('</p>\n')
        if self.indentFlag:
            self.indentFlag = False
            self.f.write('</p>\n')

    def renderID(self, token):
        self.writeFootnotes()
        self.writeCrossReferences()
        self.cb = bookKeyForIdValue(token.value)
        self.chapterLabel = 'Chapter'
        self.closeParagraph()
        #self.write('\n\n<span id="' + self.cb + '"></span>\n')

    def renderIDE(self, token):
        pass # Ignore
    def renderUSFMV(self, token):
        pass # Ignore

    def renderREM(self, token):
        pass # Don't output these comments here

    def renderH(self, token):
        self.bookName = token.value
        self.writeHeader()

    def renderTOC1(self, token):
        pass # Ignore
    def renderTOC2(self, token):
        if not self.bookName: # i.e., there was no \h field in the USFM
            self.bookName = token.value
            self.writeHeader()
    def renderTOC3(self, token):
        pass # Ignore


    # def renderMT(self, token):
    #     return  #self.write('\n\n<h1>' + token.value + '</h1>') # removed to use TOC2
    def renderMT1(self, token):
        return  #self.write('\n\n<h1>' + token.value + '</h1>') # removed to use TOC2
    def renderMT2(self, token):
        self.write('\n\n<h2>' + token.value + '</h2>')
    def renderMT3(self, token):
        self.write('\n\n<h2>' + token.value + '</h2>')


    # def renderMS(self, token):
    #     self.write('\n\n<h3>' + token.value + '</h3>')
    def renderMS1(self, token):
        self.write('\n\n<h3>' + token.value + '</h3>')
    def renderMS2(self, token):
        self.write('\n\n<h4>' + token.value + '</h4>')


    def renderP(self, token):
        assert not token.value
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} renderP({token.value})…")
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    def renderPI1(self, token):
        assert not token.value
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} renderPI({token.value})…")
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(2)
    def renderPI2(self, token):
        assert not token.value
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} renderPI({token.value})…")
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(3)

    def renderM(self, token):
        assert not token.value
        # TODO: This should NOT be identical to renderP
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    def renderMI(self, token):
        assert not token.value
        # TODO: This should NOT be identical to renderP
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    # def renderS(self, token):
    #     self.stopLI()
    #     self.closeParagraph()
    #     self.write('\n\n<h4 style="text-align:center">' + token.getValue() + '</h4>')
    def renderS1(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h4 style="text-align:center">' + token.getValue() + '</h4>')
    def renderS2(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h5 style="text-align:center">' + token.getValue() + '</h5>')
    def renderS3(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h5">' + token.getValue() + '</h5>')
    def renderS4(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h5">' + token.getValue() + '</h5>')

    def renderS5(self, token):
        if token.value:
            logger = logging.warning if token.value==' ' else logging.error
            logger(f"pseudo-USFM 's5' marker will lose following text: '{token.value}'")
        # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} renderS5({token.value})…")
        self.write('\n<span class="chunk-break"></span>\n')

    def renderC(self, token):
        self.closeFootnote()
        if not self.bookName: # i.e., there was no \h or \toc2 field in the USFM
            # NOTE: The next line is not tested on New Testament -- may be out by one book
            self.bookName = bookNames[int(self.cb)-1]
            logging.warning(f"Used '{self.bookName}' as book name (due to missing \\h and \\toc2 fields)")
            self.writeHeader()
        self.stopLI()
        self.closeParagraph()
        self.writeFootnotes()
        self.writeCrossReferences()
        self.footnote_num = 1
        self.cc = token.value.zfill(3)
        self.write('\n\n<h2 id="{0}-ch-{1}" class="c-num">{2} {3}</h2>'
                   .format(self.cb, self.cc, self.chapterLabel, token.value))
    def renderCA_S(self, token):
        assert not token.value
        self.write('<span class="altChapter">')
    def renderCA_E(self, token):
        assert not token.value
        self.write('</span>')

    def renderV(self, token):
        self.stopLI()
        self.closeFootnote()
        self.cv = token.value.zfill(3)
        self.write(' <span id="{0}-ch-{1}-v-{2}" class="v-num"><sup><b>{3}</b></sup></span>'.
                   format(self.cb, self.cc, self.cv, token.value))
    def renderVA_S(self, token):
        assert not token.value
        self.write('<span class="altVerse"><sup> (')
    def renderVA_E(self, token):
        assert not token.value
        self.write(')</sup></span>')


    # def renderQ(self, token): # TODO: Can't this type of thing be in the abstractRenderer?
    #     assert not token.value
    #     self.renderQ1(token)
    def renderQ1(self, token):
        assert not token.value
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(1)
    def renderQ2(self, token):
        assert not token.value
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(2)
    def renderQ3(self, token):
        assert not token.value
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(3)

    def renderNB(self, token):
        assert not token.value
        self.closeParagraph()

    def renderB(self, token):
        assert not token.value
        self.stopLI()
        self.write('\n\n<p class="indent-0">&nbsp;</p>')

    def renderI_S(self, token):
        assert not token.value
        self.write('<i>')
    def renderI_E(self, token):
        assert not token.value
        self.write('</i>')

    def renderND_S(self, token):
        assert not token.value
        self.write('<span class="tetragrammaton">')
    def renderND_E(self, token):
        assert not token.value
        self.write('</span>')

    def render_bk_s(self, token):
        assert not token.value
        self.write('<span class="bookname">')
    def render_bk_e(self, token):
        assert not token.value
        self.write('</span>')

    def renderPBR(self, token):
        assert not token.value
        self.write('<br></br>')

    def renderSC_S(self, token):
        assert not token.value
        self.write('<b>')
    def renderSC_E(self, token):
        assert not token.value
        self.write('</b>')

    def renderQS_S(self, token):
        assert not token.value
        self.write('<i class="quote selah" style="float:right;">')
    def renderQS_E(self, token):
        assert not token.value
        self.write('</i>')

    def renderWJ_S(self, token):
        assert not token.value
        self.write('<span class="woc">')
    def renderWJ_E(self, token):
        assert not token.value
        self.write('</span>')

    def renderEM_S(self, token):
        assert not token.value
        self.write('<i class="emphasis">')
    def renderEM_E(self, token):
        assert not token.value
        self.write('</i>')

    def renderE(self, token):
        self.closeParagraph()
        self.write('\n\n<p>' + token.value + '</p>')

    def renderPB(self, token):
        pass

    def renderPERIPH(self, token):
        pass

    # def renderLI(self, token): # TODO: Can't this type of thing be in the abstractRenderer?
    #     assert not token.value
    #     # if 'NUM' in self.bookName and '00' in self.cc: logging.debug(f"@{self.cc}:{self.cv} renderLI({token.value})…")
    #     self.renderLI1(token)
    def renderLI1(self, token):
        assert not token.value
        self.startLI(1)
    def renderLI2(self, token):
        assert not token.value
        self.startLI(2)
    def renderLI3(self, token):
        assert not token.value
        self.startLI(3)

    def renderD(self, token):
        # logging.debug(f"singlehtmlRenderer.renderD( '{token.value}' at {self.cb} {self.cc}:{self.cv}")
        self.closeParagraph()
        self.write('<span class="d">' + token.value + '</span>')
    def renderSP(self, token):
        # logging.debug(f"singlehtmlRenderer.renderD( '{token.value}' at {self.cb} {self.cc}:{self.cv}")
        self.closeParagraph()
        self.write('<span class="sp">' + token.value + '</span>')

    # def render_imt(self, token):
    #     self.write('\n\n<h2>' + token.value + '</h2>')
    def render_imt1(self, token):
        self.write('\n\n<h2>' + token.value + '</h2>')
    def render_imt2(self, token):
        self.write('\n\n<h3>' + token.value + '</h3>')
    def render_imt3(self, token):
        self.write('\n\n<h4>' + token.value + '</h4>')

    # def render_is(self, token):
    #     self.stopLI()
    #     self.closeParagraph()
    #     self.write('\n\n<h4 style="text-align:center">' + token.getValue() + '</h4>')
    def render_is1(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h4 style="text-align:center">' + token.getValue() + '</h4>')
    def render_is2(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h5 style="text-align:center">' + token.getValue() + '</h5>')
    def render_is3(self, token):
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<h5">' + token.getValue() + '</h5>')

    def render_ip(self, token):
        assert not token.value
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    def render_ipi(self, token):
        assert not token.value
        self.stopLI()
        self.closeParagraph()
        self.writeIndent(2)

    def render_im(self, token):
        assert not token.value
        # TODO: This should NOT be identical to render_ip
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    def render_imi(self, token):
        assert not token.value
        # TODO: This should NOT be identical to render_ip
        self.stopLI()
        self.closeParagraph()
        self.write('\n\n<p>')
        self.inParagraph = True

    def render_ie(self, token):
        assert not token.value
        self.closeParagraph()

    def renderCL(self, token):
        self.chapterLabel = token.value

    def renderQR(self, token):
        self.write('<i class="quote right" style="display:block;float:right;">'+token.value+'</i>')


    def renderF_S(self, token):
        # print(f"renderF_S({token.value}) with {self.footnoteFlag} and '{self.footnote_text}'")
        self.closeFootnote() # If there's one currently open
        self.footnote_id = 'fn-{0}-{1}-{2}-{3}'.format(self.cb, self.cc, self.cv, self.footnote_num)
        self.write('<span id="ref-{0}"><sup><i>[<a href="#{0}">{1}</a>]</i></sup></span>'.format(self.footnote_id, self.footnote_num))
        self.footnoteFlag = True
        text = token.value
        if text.startswith('+ '):
            text = text[2:]
        elif text.startswith('+'):
            text = text[1:]
        self.footnote_text = text

    def renderFR(self, token):
        pass # We don't need these footnote reference fields to be rendered

    def renderFT(self, token):
        # print(f"renderFT({token.value}) with '{self.footnote_text}'")
        self.footnote_text += token.value
    def renderFT_E(self, token):
        assert not token.value

    def renderF_E(self, token):
        # print(f"renderF_E({token.value}) with '{self.footnote_text}'")
        assert not token.value
        self.closeFootnote()

    def renderFP(self, token):
        # print(f"renderFP({token.value}) with '{self.footnote_text}'")
        assert not token.value
        self.write('<br />')


    def renderFQA(self, token):
        # print(f"renderFQA({token.value}) with {self.fqaFlag} and '{self.footnote_text}'")
        self.footnote_text += '<i>' + token.value
        self.fqaFlag = True
    def renderFQA_E(self, token):
        # print(f"renderFQA_E({token.value}) with {self.fqaFlag} and '{self.footnote_text}'")
        if self.fqaFlag:
            self.footnote_text += '</i>' + token.value
        self.fqaFlag = False


    def closeFootnote(self):
        # if self.footnoteFlag or self.footnote_text:
        #     print(f"closeFootnote() with {self.footnoteFlag} and '{self.footnote_text}'")
        if self.footnoteFlag:
            self.footnoteFlag = False
            self.renderFQA_E(UsfmToken(''))
            self.footnotes[self.footnote_id] = {
                'text': self.footnote_text,
                'book': self.cb,
                'chapter': self.cc,
                'verse': self.cv,
                'fn_num': self.footnote_num
            }
            self.footnote_num += 1
            self.footnote_text = ''
            self.footnote_id = ''

    def writeFootnotes(self):
        fkeys = self.footnotes.keys()
        if fkeys:
            self.write('<div class="footnotes">')
            self.write('<hr class="footnotes-hr"/>')
            for fkey in sorted(fkeys):
                footnote = self.footnotes[fkey]
                self.write(f'<div id="{fkey}" class="footnote">{footnote["chapter"].lstrip("0")}:{footnote["verse"].lstrip("0")} <sup><i>[<a href="#ref-{fkey}">{footnote["fn_num"]}</a>]</i></sup> <span class="text">{footnote["text"]}</span></div>')
            self.write('</div>')
        self.footnotes = {}


    # TODO: render other \x fields
    def renderX_S(self, token):
        assert token.value == '+'
        self.closeCrossReference() # If there's one currently open
        self.crossReference_id = 'xr-{0}-{1}-{2}-{3}'.format(self.cb, self.cc, self.cv, self.crossReference_num)
        self.write('<span id="ref-{0}"><sup><i>[<a href="#{0}">{1}</a>]</i></sup></span>'.format(self.crossReference_id, self.crossReference_num))
        self.crossReferenceFlag = True
        text = token.value
        if text.startswith('+ '):
            text = text[2:]
        elif text.startswith('+'):
            text = text[1:]
        self.crossReference_text = text

    def renderXO(self, token):
        self.crossReference_origin = token.value

    def renderXT(self, token):
        if self.crossReferenceFlag:
            self.crossReference_text += token.value
        else: # Can occur not in a cross-reference
            self.write(token.value)
    def renderXT_E(self, token):
        assert not token.value

    def renderX_E(self, token):
        assert not token.value
        # self.write(')')
        self.closeCrossReference()


    def closeCrossReference(self):
        if self.crossReferenceFlag:
            self.crossReferenceFlag = False
            # self.renderFQA_E(UsfmToken(''))
            self.crossReferences[self.crossReference_id] = {
                'origin': self.crossReference_origin,
                'text': self.crossReference_text,
                'book': self.cb,
                'chapter': self.cc,
                'verse': self.cv,
                'xr_num': self.crossReference_num
            }
            self.crossReference_num += 1
            self.crossReference_origin = ''
            self.crossReference_text = ''
            self.crossReference_id = ''

    def writeCrossReferences(self):
        crKeys = self.crossReferences.keys()
        if crKeys:
            self.write('<div class="crossreferences">')
            self.write('<hr class="crossreferences-hr"/>')
            for crKey in sorted(crKeys):
                crossreference = self.crossReferences[crKey]
                liveCrossReferences = self.livenCrossReferences(crossreference['text'])
                origin_text = self.crossReference_origin if self.crossReference_origin \
                                else f'{crossreference["chapter"].lstrip("0")}:{crossreference["verse"].lstrip("0")}'
                self.write(f'<div id="{crKey}" class="crossreference">{origin_text} <sup><i>[<a href="#ref-{crKey}">{crossreference["xr_num"]}</a>]</i></sup> <span class="text">{liveCrossReferences}</span></div>')
            self.write('</div>')
        self.crossReferences = {}

    def livenCrossReferences(self, xr_text):
        """
        Convert cross-references (\\x....\\x*) to live links
        """
        # print(f"livenCrossReferences({xr_text})…")
        results = []
        # lastBookcode = lastBooknumber = None
        for individualXR in xr_text.split(';'):
            # print(f"  Processing '{individualXR}'…")
            strippedXR = individualXR.strip()
            xrBookcode = xrBooknumber = None
            xrLink = ''
            match = re.match(r'(\w{2,16}) (\d{1,3}):(\d{1,3})', strippedXR)
            if match:
                xrBookname, C, V = match.group(1), match.group(2), match.group(3)
                # print(f"    Have match '{xrBookname}' '{C}':'{V}'")
                try: ix = bookNames.index(xrBookname)
                except ValueError: ix = -1
                # print(f"      ix1={ix}")
                if ix == -1:
                    try: ix = readerNames.index(xrBookname)
                    except ValueError: ix = -1
                    # print(f"      ix2={ix}")
                if ix == -1:
                    for j,bookName in enumerate(bookNames):
                        if xrBookname in bookName:
                            ix = j; break
                    # print(f"      ix3={ix}")
                if ix == -1:
                    for j,bookName in enumerate(readerNames):
                        if xrBookname in bookName:
                            ix = j; break
                    # print(f"      ix4={ix}")
                if ix != -1:
                    xrBookcode = silNames[ix+1]
                    xrBooknumber = bookKeys[xrBookcode]
                    # print(f"      xrBookcode='{xrBookcode}'")
                    # print(f"      xrBooknumber='{xrBooknumber}'")
                    # TODO: This logic may not work for NT books (due to book numbering MAT=41)
                    xrLink = f'{str(ix+1).zfill(2)}-{xrBookcode}.html#{xrBooknumber}-ch-{C.zfill(3)}-v-{V.zfill(3)}'
                    # lastBookcode, lastBooknumber = xrBookcode, xrBooknumber
            # TODO: Handle other types of matches, e.g., book name not included, i.e., defaults to last book
            # print(f"    Got '{xrLink}'…")
            liveXR = f'<a href="{xrLink}">{individualXR}</a>'
            results.append(liveXR)

        live_text = ';'.join(results)
        # print(f"Returning '{live_text}'")
        return live_text


    def renderQA(self, token):
        self.write('<p class="quote acrostic heading" style="text-align:center;text-style:italic;">'+token.value+'</p>')

    def renderQAC(self, token):
        assert not token.value
        self.write('<i class="quote acrostic character">')
    def renderQAC_E(self,token):
        assert not token.value
        self.write('</i>')


    def renderText(self, token):
        """
        This is where unattached chunks of USFM text (e.g., contents of paragraphs)
            are written out.
        """
        # if "the best copies" in token.value:
        #     print(f"renderText({token.value})")
        if self.footnoteFlag:
            self.footnote_text += f' {self.escape(token.value)} '
        else:
            self.write(f' {token.value} ') # write function does escaping of non-break space
# end of class SingleHTMLRenderer
