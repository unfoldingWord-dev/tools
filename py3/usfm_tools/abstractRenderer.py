import logging

from .books import loadBooks, silNames
from .parseUsfm import parseString



class AbstractRenderer:

    booksUsfm = None

    chapterLabel = 'Chapter'

    def writeLog(self, s):
        # logging.info(s)
        pass


    def loadUSFM(self, usfmDir):
        # logging.debug(f"abstractRenderer.loadUSFM({usfmDir}) is loading ALL USFM books…")
        self.booksUsfm = loadBooks(usfmDir)


    def run(self):
        # logging.debug(f"AbstractRenderer.run() to convert {len(self.booksUsfm)} books…")
        self.unknowns = []
        warning_list = []
        try:
            # logging.debug("AbstractRenderer.run() try using renderBook…")
            bookName = self.renderBook # This gives an AttributeError for USFM
            if bookName in self.booksUsfm:
                self.writeLog('     (' + bookName + ')')
                tokens = parseString(self.booksUsfm[bookName])
                for t in tokens:
                    try:
                        t.renderOn(self)
                    except Exception as e:
                        warning_list.append(f"Unable to render '{t.type}' token due to {e}")
        except AttributeError:
            # logging.debug("AbstractRenderer.run() now using silNames…")
            for bookName in silNames:
                if bookName in self.booksUsfm:
                    # logging.debug(f"AbstractRenderer.run() converting {bookName}…")
                    self.writeLog('     (' + bookName + ')')
                    tokens = parseString(self.booksUsfm[bookName])
                    for t in tokens:
                        try:
                            t.renderOn(self)
                        except Exception as e:
                            warning_list.append(f"Unable to render '{t.type}' token due to {e}")
        if self.unknowns:
            unknownsSet = set(self.unknowns)
            msg = f"Renderer skipped {len(self.unknowns)} total, {len(unknownsSet)} unique unknown USFM tokens: {', '.join(unknownsSet)}"
            logging.error(msg)
            # warning_list.append(msg)
        return set(warning_list) # Remove duplicates
    # end of run()


    # Added here May 2019 so they applied to all derived renderers
    # TODO: Should make this list extensive (from USFM 3 spec)
    # TODO: How do we remove the linter warnings
    def renderMT(self, token): self.renderMT1(token)
    def render_imt(self, token): self.render_imt1(token)
    def render_is(self, token): self.render_is1(token)
    def renderLI(self, token): self.renderLI1(token)
    def renderQ(self, token): self.renderQ1(token)
    def renderS(self, token): self.renderS1(token)
    def renderMS(self, token): self.renderMS1(token)
    def renderPI(self, token): self.renderPI1(token)
    # def renderLI(self, token): self.renderLI1(token)


    # Commented out RJH, May 2019 as we want to know
    #   which renderers are missing in the derived classes
    #   rather than silently omitting text
    # def renderID(self, token):      pass
    # def renderIDE(self, token):     pass
    # def renderSTS(self, token):     pass
    # def renderH(self, token):       pass

    # def renderM(self, token):       pass
    # def renderTOC1(self, token):      pass
    # def renderTOC2(self, token):      pass
    # def renderTOC3(self, token):      pass
    # def renderMT(self, token):      pass
    # def renderMT2(self, token):     pass
    # def renderMT3(self, token):     pass
    # def renderMS(self, token):      pass
    # def renderMS1(self, token):     pass
    # def renderMS2(self, token):     pass
    # def renderMR(self, token):      pass
    # def renderMI(self, token):      pass

    # def renderP(self, token):       pass
    # def renderSP(self, token):      pass

    # def renderS(self, token):       pass
    # def renderS2(self, token):      pass
    # def renderS3(self, token):      pass

    # def renderC(self, token):       pass
    # def renderV(self, token):       pass

    # def renderWJS(self, token):     pass
    # def renderWJE(self, token):     pass

    # def renderText(self, token):    pass

    # def renderQ(self, token):       pass
    # def renderQ1(self, token):      pass
    # def renderQ2(self, token):      pass
    # def renderQ3(self, token):      pass

    # def renderNB(self, token):      pass
    # def renderB(self, token):       pass
    # def renderQTS(self, token):     pass
    # def renderQTE(self, token):     pass
    # def renderR(self, token):       pass

    # def renderFS(self, token):      pass
    # def renderFE(self, token):      pass
    # def renderFR(self, token):      pass
    # def renderFRE(self, token):     pass
    # def renderFK(self, token):      pass
    # def renderFT(self, token):      pass
    # def renderFQ(self, token):      pass
    # def renderFP(self, token):      pass

    # def renderIS(self, token):      pass
    # def renderIE(self, token):      pass

    # def renderNDS(self, token):     pass
    # def renderNDE(self, token):     pass

    # def renderPBR(self, token):     pass
    # def renderD(self, token):       pass
    # def renderREM(self, token):     pass
    # def renderPI(self, token):      pass
    # def renderPI2(self, token):     pass
    # def renderLI(self, token):      pass

    # def renderXS(self, token):      pass
    # def renderXE(self, token):      pass
    # def renderXO(self, token):      pass
    # def renderXT(self, token):      pass
    # def renderXTS(self, token):      pass
    # def renderXTE(self, token):      pass
    # def renderXDCS(self, token):    pass
    # def renderXDCE(self, token):    pass

    # def renderTLS(self, token):     pass
    # def renderTLE(self, token):     pass

    # def renderADDS(self, token):    pass
    # def renderADDE(self, token):    pass

    # def render_is1(self, token):    pass
    # def render_is2(self, token):    pass
    # def render_is3(self, token):    pass
    # def render_imt1(self, token):   pass
    # def render_imt2(self, token):   pass
    # def render_imt3(self, token):   pass
    # def render_ip(self, token):     pass
    # def render_iot(self, token):    pass
    # def render_io1(self, token):    pass
    # def render_io2(self, token):    pass
    # def render_ior_s(self, token):  pass
    # def render_ior_e(self, token):  pass

    # def render_bk_s(self, token):   pass
    # def render_bk_e(self, token):   pass

    # def renderSCS(self, token):     pass
    # def renderSCE(self, token):     pass

    # def renderBDS(self, token):     pass
    # def renderBDE(self, token):     pass
    # def renderBDITS(self, token):   pass
    # def renderBDITE(self, token):   pass


    # Add unknown tokens to list
    def renderUnknown(self, token):
        # logging.debug(f"renderUnkown({token.value})")
        self.unknowns.append(token.value)
# end of AbstractRenderer class
