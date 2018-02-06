# -*- coding: utf-8 -*-
#

import sys

from pyparsing import Word, alphas, OneOrMore, nums, Literal, White, Group, Suppress, Empty, NoMatch, Optional, CharsNotIn, unicodeString, MatchFirst

def usfmToken(key):
    return Group(Suppress(backslash) + Literal( key ) + Suppress(White()))
def usfmBackslashToken(key):
    return Group(Literal(key))
def usfmEndToken(key):
    return Group(Suppress(backslash) + Literal( key +  u"*"))
def usfmTokenValue(key, value):
    return Group(Suppress(backslash) + Literal( key ) + Suppress(White()) + Optional(value) )
def usfmTokenNumber(key):
    return Group(Suppress(backslash) + Literal( key ) + Suppress(White()) + Word (nums + '-()') + Suppress(White()))


# define grammar
#phrase      = Word( alphas + u"-.,!? —–‘“”’;:()'\"[]/&%=*…{}" + nums )
phrase      = CharsNotIn( u"\n\\"  )
backslash   = Literal(u"\\")
plus        = Literal(u"+")

textBlock   = Group(Optional(NoMatch(), u"text") + phrase )
unknown     = Group(Optional(NoMatch(), u"unknown") + Suppress(backslash) + CharsNotIn(u' \n\t\\') )

id      = usfmTokenValue( u"id", phrase )
ide     = usfmTokenValue( u"ide", phrase )
h       = usfmTokenValue( u"h", phrase )
toc     = usfmTokenValue( u"toc", phrase )
toc1    = usfmTokenValue( u"toc1", phrase )
toc2    = usfmTokenValue( u"toc2", phrase )
toc3    = usfmTokenValue( u"toc3", phrase )
mt      = usfmTokenValue( u"mt", phrase )
mt1     = usfmTokenValue( u"mt1", phrase )
mt2     = usfmTokenValue( u"mt2", phrase )
mt3     = usfmTokenValue( u"mt3", phrase )
mte     = usfmTokenValue( u"mte", phrase )
imt     = usfmTokenValue( u"imt", phrase )
imt1    = usfmTokenValue( u"imt1", phrase )
ms      = usfmTokenValue( u"ms", phrase )
ms1     = usfmTokenValue( u"ms1", phrase )
ms2     = usfmTokenValue( u"ms2", phrase )
mr      = usfmTokenValue( u"mr", phrase )
s       = usfmTokenValue( u"s", phrase )
s1      = usfmTokenValue( u"s1", phrase )
s2      = usfmTokenValue( u"s2", phrase )
s3      = usfmTokenValue( u"s3", phrase )
s4      = usfmTokenValue( u"s4", phrase )
s5      = usfmTokenValue( u"s5", phrase )
sr      = usfmTokenValue( u"sr", phrase )
sts     = usfmTokenValue( u"sts", phrase )
r       = usfmTokenValue( u"r", phrase )
p       = usfmToken(u"p")
pi      = usfmToken(u"pi")
pc      = usfmToken(u"pc")
b       = usfmToken(u"b")
c       = usfmTokenNumber(u"c")
cas     = usfmToken(u"ca")
cae     = usfmEndToken(u"ca")
cl      = usfmTokenValue(u"cl", phrase)
v       = usfmTokenNumber(u"v")
wjs     = usfmToken(u"wj")
wje     = usfmEndToken(u"wj")
q       = usfmToken(u"q")
q1      = usfmToken(u"q1")
q2      = usfmToken(u"q2")
q3      = usfmToken(u"q3")
q4      = usfmToken(u"q4")
qa      = usfmToken(u"qa")
qac     = usfmToken(u"qac")
qc      = usfmToken(u"qc")
qm      = usfmToken(u"qm")
qm1     = usfmToken(u"qm1")
qm2     = usfmToken(u"qm2")
qm3     = usfmToken(u"qm3")
qr      = usfmToken(u"qr")
qss     = usfmToken(u"qs")
qse     = usfmEndToken(u"qs")
qts     = usfmToken(u"qt")
qte     = usfmEndToken(u"qt")
nb      = usfmToken(u"nb")
m       = usfmToken(u"m")

# Footnotes
fs      = usfmTokenValue(u"f", plus)
fr      = usfmTokenValue( u"fr", phrase )
fre     = usfmEndToken( u"fr" )
fk      = usfmTokenValue( u"fk", phrase )
ft      = usfmTokenValue( u"ft", phrase )
fp      = usfmTokenValue( u"fp", phrase )
fq      = usfmTokenValue( u"fq", phrase )
fqa     = usfmTokenValue( u"fqa", phrase )
fe      = usfmEndToken(u"f")

# Cross References
xs      = usfmTokenValue(u"x", plus)
xdcs    = usfmToken(u"xdc")
xdce    = usfmEndToken(u"xdc")
xo      = usfmTokenValue( u"xo", phrase )
xt      = usfmTokenValue( u"xt", phrase )
xe      = usfmEndToken(u"x")

# Transliterated
tls      = usfmToken(u"tl")
tle      = usfmEndToken(u"tl")

# Transliterated
scs      = usfmToken(u"sc")
sce      = usfmEndToken(u"sc")

# Italics
ist     = usfmToken(u"it")
ien     = usfmEndToken(u"it")

# Bold
bds    = usfmToken(u"bd")
bde    = usfmEndToken(u"bd")
bdits  = usfmToken(u"bdit")
bdite  = usfmEndToken(u"bdit")


li      = usfmToken(u"li")
li1     = usfmToken(u"li1")
li2     = usfmToken(u"li2")
li3     = usfmToken(u"li3")
li4     = usfmToken(u"li4")
d       = usfmToken(u"d")
sp      = usfmToken(u"sp")
pn      = usfmToken(u"pn")
adds    = usfmToken(u"add")
adde    = usfmEndToken(u"add")
nds     = usfmToken(u"nd")
nde     = usfmEndToken(u"nd")
pbr     = usfmBackslashToken("\\\\")
mi      = usfmToken(u"mi")

# Comments
rem     = usfmTokenValue( u"rem", phrase )

# Tables
tr      = usfmToken(u"tr")
th1     = usfmToken(u"th1")
th2     = usfmToken(u"th2")
th3     = usfmToken(u"th3")
th4     = usfmToken(u"th4")
th5     = usfmToken(u"th5")
th6     = usfmToken(u"th6")
thr1    = usfmToken(u"thr1")
thr2    = usfmToken(u"thr2")
thr3    = usfmToken(u"thr3")
thr4    = usfmToken(u"thr4")
thr5    = usfmToken(u"thr5")
thr6    = usfmToken(u"thr6")
tc1     = usfmToken(u"tc1")
tc2     = usfmToken(u"tc2")
tc3     = usfmToken(u"tc3")
tc4     = usfmToken(u"tc4")
tc5     = usfmToken(u"tc5")
tc6     = usfmToken(u"tc6")
tcr1    = usfmToken(u"tcr1")
tcr2    = usfmToken(u"tcr2")
tcr3    = usfmToken(u"tcr3")
tcr4    = usfmToken(u"tcr4")
tcr5    = usfmToken(u"tcr5")
tcr6    = usfmToken(u"tcr6")

# Table of Contents
toc1    =  usfmTokenValue( u"toc1", phrase )
toc2    =  usfmTokenValue( u"toc2", phrase )
toc3    =  usfmTokenValue( u"toc3", phrase )

# Introductory Materials
is1     =  usfmTokenValue( u"is1", phrase ) | usfmTokenValue( u"is", phrase )
ip      =  usfmToken( u"ip" )
iot     =  usfmToken( u"iot" )
io1     =  usfmToken( u"io1" ) | usfmToken( u"io" )
io2     =  usfmToken( u"io2" )
ior_s   =  usfmToken( u"ior")
ior_e   =  usfmEndToken( u"ior")

# Quoted book title
bk_s    =  usfmToken( u"bk")
bk_e    =  usfmEndToken( u"bk")

element =  MatchFirst([ide, id, h, toc, toc1, toc2, toc3, mt, mt1, mt2, mt3, mte,
 imt,
 imt1,
 ms,
 ms1,
 ms2,
 mr,
 s,
 s1,
 s2,
 s3,
 s4,
 s5,
 sr,
 sts,
 r,
 p,
 pc,
 pi,
 mi,
 b,
 c,
 cas,
 cae,
 cl,
 v,
 wjs,
 wje,
 nds,
 nde,
 q,
 q1,
 q2,
 q3,
 q4,
 qa,
 qac,
 qc,
 qm,
 qm1,
 qm2,
 qm3,
 qr,
 qss,
 qse,
 qts,
 qte,
 nb,
 m,
 fs,
 fr,
 fre,
 fk,
 ft,
 fp,
 fq,
 fqa,
 fe,
 xs,
 xdcs,
 xdce,
 xo,
 xt,
 xe,
 ist,
 ien,
 bds,
 bde,
 bdits,
 bdite,
 li,
 li1,
 li2,
 li3,
 li4,
 d,
 sp,
 pn,
 adds,
 adde,
 tls,
 tle,
 is1,
 ip,
 iot,
 io1,
 io2,
 ior_s,
 ior_e,
 bk_s,
 bk_e,
 scs,
 sce,
 pbr,
 rem,
 tr,
 th1,
 th2,
 th3,
 th4,
 th5,
 th6,
 thr1,
 thr2,
 thr3,
 thr4,
 thr5,
 thr6,
 tc1,
 tc2,
 tc3,
 tc4,
 tc5,
 tc6,
 tcr1,
 tcr2,
 tcr3,
 tcr4,
 tcr5,
 tcr6,
 textBlock,
 unknown])

usfm    = OneOrMore( element )

# input string
def parseString( unicodeString ):
    try:
        s = clean(unicodeString)
        tokens = usfm.parseString(s, parseAll=True )
    except Exception as e:
        print e
        print repr(unicodeString[:50])
        sys.exit()
    return [createToken(t) for t in tokens]

def clean( unicodeString ):
    # We need to clean the input a bit. For a start, until
    # we work out what to do, non breaking spaces will be ignored
    # ie 0xa0
    return unicodeString.replace(u'\xa0', u' ')

def createToken(t):
    options = {
        u'id':   IDToken,
        u'ide':  IDEToken,
        u'h':    HToken,
        u'toc1': TOC1Token,
        u'toc2': TOC2Token,
        u'toc3': TOC3Token,
        u'mt':   MTToken,
        u'mt1':  MTToken,
        u'mt2':  MT2Token,
        u'mt3':  MT3Token,
        u'mte':  MTEToken,
        u'imt':  IMTToken,
        u'imt1': IMTToken,
        u'ms':   MSToken,
        u'ms1':  MSToken,
        u'ms2':  MS2Token,
        u'mr':   MRToken,
        u'p':    PToken,
        u'pc':   PCToken,
        u'pi':   PIToken,
        u'b':    BToken,
        u's':    SToken,
        u's1':   SToken,
        u's2':   S2Token,
        u's3':   S3Token,
        u's4':   S4Token,
        u's5':   S5Token,
        u'sr':   SRToken,
        u'sts':  STSToken,
        u'mi':   MIToken,
        u'r':    RToken,
        u'c':    CToken,
        u'ca':   CASToken,
        u'ca*':  CAEToken,
        u'cl':   CLToken,
        u'v':    VToken,
        u'wj':   WJSToken,
        u'wj*':  WJEToken,
        u'q':    QToken,
        u'q1':   Q1Token,
        u'q2':   Q2Token,
        u'q3':   Q3Token,
        u'q4':   Q4Token,
        u'qa':   QAToken,
        u'qac':  QACToken,
        u'qc':   QCToken,
        u'qm':   QMToken,
        u'qm1':  QM1Token,
        u'qm2':  QM2Token,
        u'qm3':  QM3Token,
        u'qr':   QRToken,
        u'qs':   QSSToken,
        u'qs*':  QSEToken,
        u'qt':   QTSToken,
        u'qt*':  QTEToken,
        u'nb':   NBToken,
        u'f':    FSToken,
        u'fr':   FRToken,
        u'fr*':  FREToken,
        u'fk':   FKToken,
        u'ft':   FTToken,
        u'fp':   FPToken,
        u'fq':   FQToken,
        u'fqa':  FQAToken,
        u'f*':   FEToken,
        u'x':    XSToken,
        u'xdc':  XDCSToken,
        u'xdc*': XDCEToken,
        u'xo':   XOToken,
        u'xt':   XTToken,
        u'x*':   XEToken,
        u'it':   ISToken,
        u'it*':  IEToken,
        u'bd':   BDSToken,
        u'bd*':  BDEToken,
        u'bdit': BDITSToken,
        u'bdit*':BDITEToken,
        u'li':   LIToken,
        u'li1':  LI1Token,
        u'li2':  LI2Token,
        u'li3':  LI3Token,
        u'li4':  LI4Token,
        u'd':    DToken,
        u'sp':   SPToken,
        u'pn':   PNToken,
        u'i*':   IEToken,
        u'add':  ADDSToken,
        u'add*': ADDEToken,
        u'nd':   NDSToken,
        u'nd*':  NDEToken,
        u'sc':   SCSToken,
        u'sc*':  SCEToken,
        u'm':    MToken,
        u'tl':   TLSToken,
        u'tl*':  TLEToken,
        u'\\\\': PBRToken,
        u'rem':  REMToken,
        u'tr':   TRToken,
        u'th1':  TH1Token,
        u'th2':  TH2Token,
        u'th3':  TH3Token,
        u'th4':  TH4Token,
        u'th5':  TH5Token,
        u'th6':  TH6Token,
        u'thr1': THR1Token,
        u'thr2': THR2Token,
        u'thr3': THR3Token,
        u'thr4': THR4Token,
        u'thr5': THR5Token,
        u'thr6': THR6Token,
        u'tc1':  TC1Token,
        u'tc2':  TC2Token,
        u'tc3':  TC3Token,
        u'tc4':  TC4Token,
        u'tc5':  TC5Token,
        u'tc6':  TC6Token,
        u'tcr1': TCR1Token,
        u'tcr2': TCR2Token,
        u'tcr3': TCR3Token,
        u'tcr4': TCR4Token,
        u'tcr5': TCR5Token,
        u'tcr6': TCR6Token,
        u'toc1': TOC1Token,
        u'toc2': TOC2Token,
        u'toc3': TOC3Token,
        u'is':   IS1_Token,
        u'is1':  IS1_Token,
        u'ip':   IP_Token,
        u'iot':  IOT_Token,
        u'io':   IO1_Token,
        u'io1':  IO1_Token,
        u'io2':  IO2_Token,
        u'ior':  IOR_S_Token,
        u'ior*': IOR_E_Token,
        u'bk':   BK_S_Token,
        u'bk*':  BK_E_Token,
        u'text': TEXTToken,
        u'unknown': UnknownToken
    }
    for k, v in options.iteritems():
        if t[0] == k:
            if len(t) == 1:
                token = v()
            else:
                token = v(t[1])
            token.type = k
            return token
    raise Exception(t[0])

class UsfmToken(object):
    def __init__(self, value=u""):
        self.value = value
    def getType(self):  return self.type
    def getValue(self): return self.value
    def isUnknown(self): return False
    def isID(self):     return False
    def isIDE(self):    return False
    def isH(self):      return False
    def isTOC1(self):   return False
    def isTOC2(self):   return False
    def isTOC3(self):   return False
    def isMT(self):     return False
    def isMT2(self):    return False
    def isMT3(self):    return False
    def isMTE(self):    return False
    def isIMT(self):    return False
    def isMS(self):     return False
    def isMS2(self):    return False
    def isMR(self):     return False
    def isR(self):      return False
    def isP(self):      return False
    def isPC(self):     return False
    def isPI(self):     return False
    def isS(self):      return False
    def isS2(self):     return False
    def isS3(self):     return False
    def isS4(self):     return False
    def isS5(self):     return False
    def isSR(self):     return False
    def isSTS(self):    return False
    def isMI(self):     return False
    def isC(self):      return False
    def isCAS(self):    return False
    def isCAE(self):    return False
    def isCL(self):     return False
    def isV(self):      return False
    def isWJS(self):    return False
    def isWJE(self):    return False
    def isTEXT(self):   return False
    def isQ(self):      return False
    def isQ1(self):     return False
    def isQ2(self):     return False
    def isQ3(self):     return False
    def isQ4(self):     return False
    def isQA(self):     return False
    def isQAC(self):    return False
    def isQC(self):     return False
    def isQM(self):     return False
    def isQM1(self):    return False
    def isQM2(self):    return False
    def isQM3(self):    return False
    def isQR(self):     return False
    def isQSS(self):    return False
    def isQSE(self):    return False
    def isQTS(self):    return False
    def isQTE(self):    return False
    def isNB(self):     return False
    def isFS(self):     return False
    def isFR(self):     return False
    def isFRE(self):    return False
    def isFK(self):     return False
    def isFT(self):     return False
    def isFP(self):     return False
    def isFQ(self):     return False
    def isFQA(self):    return False
    def isFE(self):     return False
    def isXS(self):     return False
    def isXDCS(self):   return False
    def isXDCE(self):   return False
    def isXO(self):     return False
    def isXT(self):     return False
    def isXE(self):     return False
    def isIS(self):     return False
    def isIE(self):     return False
    def isSCS(self):    return False
    def isSCE(self):    return False
    def isLI(self):     return False
    def isLI1(self):    return False
    def isLI2(self):    return False
    def isLI3(self):    return False
    def isLI4(self):    return False
    def isD(self):      return False
    def isSP(self):     return False
    def isPN(self):     return False
    def isADDS(self):   return False
    def isADDE(self):   return False
    def isNDS(self):    return False
    def isNDE(self):    return False
    def isTLS(self):    return False
    def isTLE(self):    return False
    def isB(self):      return False
    def isBDS(self):    return False
    def isBDE(self):    return False
    def isBDITS(self):  return False
    def isBDITE(self):  return False
    def isPBR(self):    return False
    def isM(self):      return False
    def isREM(self):    return False
    def isTR(self):     return False
    def isTH1(self):    return False
    def isTH2(self):    return False
    def isTH3(self):    return False
    def isTH4(self):    return False
    def isTH5(self):    return False
    def isTH6(self):    return False
    def isTHR1(self):   return False
    def isTHR2(self):   return False
    def isTHR3(self):   return False
    def isTHR4(self):   return False
    def isTHR5(self):   return False
    def isTHR6(self):   return False
    def isTC1(self):    return False
    def isTC2(self):    return False
    def isTC3(self):    return False
    def isTC4(self):    return False
    def isTC5(self):    return False
    def isTC6(self):    return False
    def isTCR1(self):   return False
    def isTCR2(self):   return False
    def isTCR3(self):   return False
    def isTCR4(self):   return False
    def isTCR5(self):   return False
    def isTCR6(self):   return False
    def is_toc1(self):  return False
    def is_toc2(self):  return False
    def is_toc3(self):  return False
    def is_is1(self):   return False
    def is_ip(self):    return False
    def is_iot(self):   return False
    def is_io1(self):   return False
    def is_io2(self):   return False
    def is_ior_s(self): return False
    def is_ior_e(self): return False
    def is_bk_s(self):  return False
    def is_bk_e(self):  return False

class UnknownToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderUnknown(self)
    def isUnknown(self):     return True

class IDToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderID(self)
    def isID(self):     return True

class IDEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIDE(self)
    def isIDE(self):    return True

class HToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderH(self)
    def isH(self):      return True

class TOC1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTOC1(self)
    def isTOC1(self):     return True

class TOC2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTOC2(self)
    def isTOC2(self):     return True

class TOC3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTOC3(self)
    def isTOC3(self):     return True

class MTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMT(self)
    def isMT(self):     return True

class MT2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMT2(self)
    def isMT2(self):     return True

class MT3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMT3(self)
    def isMT3(self):    return True

class MTEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMTE(self)
    def isMTE(self):    return True

class IMTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIMT(self)
    def isIMT(self):     return True

class MSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMS(self)
    def isMS(self):     return True

class MS2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMS2(self)
    def isMS2(self):    return True

class MRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMR(self)
    def isMR(self):    return True

class MIToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderMI(self)
    def isMI(self):     return True

class RToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderR(self)
    def isR(self):    return True

class PToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderP(self)
    def isP(self):      return True

class BToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderB(self)
    def isB(self):      return True

class CToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderC(self)
    def isC(self):      return True

class CASToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCAS(self)
    def isCAS(self):    return True

class CAEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCAE(self)
    def isCAE(self):    return True

class CLToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCL(self)
    def isCL(self):     return True

class VToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderV(self)
    def isV(self):      return True

class TEXTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTEXT(self)
    def isTEXT(self):   return True

class WJSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderWJS(self)
    def isWJS(self):    return True

class WJEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderWJE(self)
    def isWJE(self):    return True

class SToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderS(self)
    def isS(self):      return True

class S2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderS2(self)
    def isS2(self):      return True

class S3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderS3(self)
    def isS3(self):      return True

class S4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderS4(self)
    def isS4(self):      return True

class S5Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderS5(self)
    def isS5(self):      return True

class SRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderSR(self)
    def isSR(self):    return True

class STSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderSTS(self)
    def isSTS(self):    return True

class QToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQ(self)
    def isQ(self):      return True

class Q1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQ1(self)
    def isQ1(self):      return True

class Q2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQ2(self)
    def isQ2(self):      return True

class Q3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQ3(self)
    def isQ3(self):      return True

class Q4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQ4(self)
    def isQ4(self):      return True

class QAToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQA(self)
    def isQA(self):      return True

class QACToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQAC(self)
    def isQAC(self):     return True

class QCToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQC(self)
    def isQC(self):      return True

class QMToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQM(self)
    def isQM(self):      return True

class QM1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQM1(self)
    def isQM1(self):     return True

class QM2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQM2(self)
    def isQM2(self):     return True

class QM3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQM3(self)
    def isQM3(self):     return True

class QRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQR(self)
    def isQR(self):      return True

class QSSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQSS(self)
    def isQSS(self):     return True

class QSEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQSE(self)
    def isQSE(self):     return True

class QTSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQTS(self)
    def isQTS(self):     return True

class QTEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderQTE(self)
    def isQTE(self):     return True

class NBToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderNB(self)
    def isNB(self):      return True

class FSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFS(self)
    def isFS(self):      return True

class FRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFR(self)
    def isFR(self):      return True

class FREToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFRE(self)
    def isFRE(self):      return True

class FKToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFK(self)
    def isFK(self):      return True

class FTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFT(self)
    def isFT(self):      return True

class FPToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFP(self)
    def isFP(self):      return True

class FQToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFQ(self)
    def isFQ(self):      return True

class FQAToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFQA(self)
    def isFQA(self):     return True

class FEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFE(self)
    def isFE(self):      return True

class ISToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIS(self)
    def isIS(self):      return True

class IEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIE(self)
    def isIE(self):      return True

class BDSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderBDS(self)
    def isBDS(self):      return True

class BDEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderBDE(self)
    def isBDE(self):      return True

class BDITSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderBDITS(self)
    def isBDITS(self):      return True

class BDITEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderBDITE(self)
    def isBDITE(self):      return True

class LIToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderLI(self)
    def isLI(self):      return True

class LI1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderLI1(self)
    def isLI1(self):     return True

class LI2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderLI2(self)
    def isLI1(self):     return True

class LI3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderLI3(self)
    def isLI1(self):     return True

class LI4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderLI4(self)
    def isLI1(self):     return True

class DToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderD(self)
    def isD(self):      return True

class SPToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderSP(self)
    def isSP(self):      return True

class PNToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPN(self)
    def isPN(self):      return True

class ADDSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderADDS(self)
    def isADDS(self):    return True

class ADDEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderADDE(self)
    def isADDE(self):    return True

class NDSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderNDS(self)
    def isNDS(self):    return True

class NDEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderNDE(self)
    def isNDE(self):    return True

class PBRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPBR(self)
    def isPBR(self):    return True


# Cross References
class XSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXS(self)
    def isXS(self):      return True

class XDCSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXDCS(self)
    def isXDCS(self):      return True

class XDCEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXDCE(self)
    def isXDCE(self):      return True

class XOToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXO(self)
    def isXO(self):      return True

class XTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXT(self)
    def isXT(self):      return True

class XEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXE(self)
    def isXE(self):      return True

class MToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderM(self)
    def isM(self):      return True

# Transliterated Words
class TLSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTLS(self)
    def isTLS(self):      return True

class TLEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTLE(self)
    def isTLE(self):      return True

# Formatted paragraphs, like pc, pi, etc.
class PCToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPC(self)
    def isPC(self):      return True

class PIToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPI(self)
    def isPI(self):      return True

# Small caps
class SCSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderSCS(self)
    def isSCS(self):      return True

class SCEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderSCE(self)
    def isSCE(self):      return True

# REMarks
class REMToken(UsfmToken):
    def renderOn(self, printer):  return printer.renderREM(self)
    def isREM(self):              return True

# Tables
class TRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTR(self)
    def isTR(self):     return True

class TH1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH1(self)
    def isTH1(self):    return True

class TH2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH2(self)
    def isTH2(self):    return True

class TH3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH3(self)
    def isTH3(self):    return True

class TH4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH4(self)
    def isTH4(self):    return True

class TH5Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH5(self)
    def isTH5(self):    return True

class TH6Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTH6(self)
    def isTH6(self):    return True

class THR1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR1(self)
    def isTHR1(self):   return True

class THR2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR2(self)
    def isTHR2(self):   return True

class THR3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR3(self)
    def isTHR3(self):   return True

class THR4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR4(self)
    def isTHR4(self):   return True

class THR5Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR5(self)
    def isTHR5(self):   return True

class THR6Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTHR6(self)
    def isTHR6(self):   return True

class TC1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC1(self)
    def isTC1(self):    return True

class TC2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC2(self)
    def isTC2(self):    return True

class TC3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC3(self)
    def isTC3(self):    return True

class TC4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC4(self)
    def isTC4(self):    return True

class TC5Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC5(self)
    def isTC5(self):    return True

class TC6Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTC6(self)
    def isTC6(self):    return True

class TCR1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR1(self)
    def isTCR1(self):   return True

class TCR2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR2(self)
    def isTCR2(self):   return True

class TCR3Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR3(self)
    def isTCR3(self):   return True

class TCR4Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR4(self)
    def isTCR4(self):   return True

class TCR5Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR5(self)
    def isTCR5(self):   return True

class TCR6Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderTCR6(self)
    def isTCR6(self):   return True

# Introductions
class IS1_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_is1(self)
    def is_is1(self):             return True

class IP_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_ip(self)
    def is_ip(self):              return True

class IOT_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_iot(self)
    def is_iot(self):             return True

class IO1_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_io1(self)
    def is_io1(self):             return True

class IO2_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_io2(self)
    def is_io2(self):             return True

class IOR_S_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_ior_s(self)
    def is_ior_s(self):           return True

class IOR_E_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_ior_e(self)
    def is_ior_e(self):           return True

# Quoted book title
class BK_S_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_bk_s(self)
    def is_bk_s(self):            return True

class BK_E_Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_bk_e(self)
    def is_bk_e(self):            return True


