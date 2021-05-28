# -*- coding: utf-8 -*-

import sys
from pyparsing import Word, OneOrMore, nums, Literal, White, Group, \
        Suppress, NoMatch, Optional, CharsNotIn, MatchFirst


# A usfm token not necessarily followed by anything
def usfmToken(key):
    return Group(Suppress(backslash) + Literal(key) + Suppress(White()))

# Literal backslash
def usfmBackslashToken(key):
    return Group(Literal(key))

# A terminating token, always ending with '*'
def usfmEndToken(key):
    return Group(Suppress(backslash) + Literal(key + '*'))

# A token that is followed by a value on the same line
def usfmTokenValue(key, value):
    return Group(Suppress(backslash) + Literal(key) + Suppress(White()) + Optional(value))

# Chapter or verse token
def usfmTokenNumber(key):
    return Group(Suppress(backslash) + Literal(key) + Suppress(White()) + Word(nums + '-()') + Suppress(White()))


# Define grammar
# NOTE: We separate fields like \mt and \mt1, \s and \s1
#           so that we could conceivably rewrite the file without changing the convention used
#           even though it does increase the complexity a little.

# phrase = Word(alphas + "-.,!? —–‘“”’;:()'\"[]/&%=*…{}" + nums)
phrase    = CharsNotIn('\n\\')
backslash = Literal('\\')
plus      = Literal('+')

textBlock = Group(Optional(NoMatch(), "text") + phrase)
unknown   = Group(Optional(NoMatch(), "unknown") + Suppress(backslash) + CharsNotIn(' \n\t\\'))
escape    = usfmTokenValue('\\', phrase)

id      = usfmTokenValue("id", phrase)
ide     = usfmTokenValue("ide", phrase)
usfmV   = usfmTokenValue('usfm', phrase) # USFM version marker (new with USFM 3.0)
h       = usfmTokenValue("h", phrase)

mt      = usfmTokenValue("mt", phrase)
mt1     = usfmTokenValue("mt1", phrase)
mt2     = usfmTokenValue("mt2", phrase)
mt3     = usfmTokenValue("mt3", phrase)
mte     = usfmTokenValue("mte", phrase)

ms      = usfmTokenValue('ms', phrase)
ms1     = usfmTokenValue('ms1', phrase)
ms2     = usfmTokenValue('ms2', phrase)
mr      = usfmTokenValue('mr', phrase)

s       = usfmTokenValue("s", phrase)
s1      = usfmTokenValue("s1", phrase)
s2      = usfmTokenValue("s2", phrase)
s3      = usfmTokenValue("s3", phrase)
s4      = usfmTokenValue("s4", phrase)
s5      = usfmTokenValue("s5", phrase)

sr      = usfmTokenValue("sr", phrase)
sts     = usfmTokenValue("sts", phrase)
r       = usfmTokenValue("r", phrase)
p       = usfmToken("p")
pc      = usfmToken("pc")
pi      = usfmToken('pi')
pi1     = usfmToken('pi1')
pi2     = usfmToken('pi2')
cls     = usfmToken('cls')

b       = usfmToken("b")
c       = usfmTokenNumber("c")
ca_s     = usfmToken("ca")
ca_e     = usfmEndToken("ca")
cl      = usfmTokenValue("cl", phrase)
v       = usfmTokenNumber('v')
va_s     = usfmToken('va')
va_e     = usfmEndToken('va')

k_s     = usfmToken("k")
k_e     = usfmEndToken("k")

q       = usfmToken('q')
q1      = usfmToken('q1')
q2      = usfmToken('q2')
q3      = usfmToken('q3')
q4      = usfmToken('q4')

qa      = usfmToken("qa")
qac     = usfmToken("qac")
qc      = usfmToken("qc")
qm      = usfmToken("qm")
qm1     = usfmToken("qm1")
qm2     = usfmToken("qm2")
qm3     = usfmToken("qm3")
qr      = usfmToken("qr")
qs_s    = usfmToken("qs")
qs_e    = usfmEndToken("qs")
qt_s    = usfmToken("qt")
qt_e    = usfmEndToken("qt")
nb      = usfmToken("nb")
m       = usfmToken("m")

# Footnotes
f_s      = usfmTokenValue("f", plus)
f_e      = usfmEndToken("f")
fe_s     = usfmTokenValue("fe", plus)
fe_e     = usfmEndToken("fe")
fr      = usfmTokenValue("fr", phrase)
fr_e     = usfmEndToken("fr")
fk      = usfmTokenValue("fk", phrase)
ft      = usfmTokenValue("ft", phrase)
ft_e     = usfmEndToken('ft')
fp      = usfmToken("fp")
fq      = usfmTokenValue("fq", phrase)
fq_e     = usfmEndToken("fq")
fqa     = usfmTokenValue("fqa", phrase)
fqa_e    = usfmEndToken("fqa")
fqb     = usfmTokenValue("fqb", phrase)
fv      = usfmTokenValue('fv', phrase)
fv_e     = usfmEndToken('fv')
fdc     = usfmTokenValue('fdc', phrase)
fdc_e    = usfmEndToken('fdc')

# Cross References
xs      = usfmTokenValue("x", plus)
xe      = usfmEndToken("x")
xdc_s    = usfmToken('xdc')
xdc_e    = usfmEndToken('xdc')
xo      = usfmTokenValue("xo", phrase)
xq      = usfmTokenValue("xq", phrase)

# NOTE: xt can occur outside of cross-references
# Not sure if this is the best way to handle it? (RJH May 2019)
xt      = usfmTokenValue('xt', phrase)
xt_e    = usfmEndToken('xt')
xtnested      = usfmTokenValue('+xt', phrase)
xtnested_e    = usfmEndToken('+xt')

wj_s     = usfmToken('wj')
wj_e     = usfmEndToken('wj')

# Transliterated
tl_s      = usfmToken('tl')
tl_e      = usfmEndToken('tl')

# Small caps
sc_s      = usfmToken('sc')
sc_e      = usfmEndToken('sc')

# Italics
ist     = usfmToken("it")
ien     = usfmEndToken("it")

# Bold
bd_s    = usfmToken('bd')
bd_e    = usfmEndToken('bd')
bdit_s  = usfmToken('bdit')
bdit_e  = usfmEndToken('bdit')

li      = usfmToken("li")
li1     = usfmToken("li1")
li2     = usfmToken("li2")
li3     = usfmToken("li3")
li4     = usfmToken("li4")

d       = usfmTokenValue("d", phrase)
sp      = usfmTokenValue("sp", phrase)
add_s    = usfmToken('add')
add_e    = usfmEndToken('add')
nd_s     = usfmToken('nd')
nd_e     = usfmEndToken('nd')
pn_s    = usfmToken("pn")
pn_e    = usfmEndToken("pn")
rq_s     = usfmToken('rq')
rq_e     = usfmEndToken('rq')
w_s     = usfmToken('w')
w_e     = usfmEndToken('w')
pbr     = usfmBackslashToken('\\\\')
mi      = usfmToken('mi')

# Comments
rem     = usfmTokenValue("rem", phrase)

# Tables
tr      = usfmToken("tr")
th1     = usfmToken("th1")
th2     = usfmToken("th2")
th3     = usfmToken("th3")
th4     = usfmToken("th4")
th5     = usfmToken("th5")
th6     = usfmToken("th6")
thr1    = usfmToken("thr1")
thr2    = usfmToken("thr2")
thr3    = usfmToken("thr3")
thr4    = usfmToken("thr4")
thr5    = usfmToken("thr5")
thr6    = usfmToken("thr6")
tc1     = usfmToken("tc1")
tc2     = usfmToken("tc2")
tc3     = usfmToken("tc3")
tc4     = usfmToken("tc4")
tc5     = usfmToken("tc5")
tc6     = usfmToken("tc6")
tcr1    = usfmToken("tcr1")
tcr2    = usfmToken("tcr2")
tcr3    = usfmToken("tcr3")
tcr4    = usfmToken("tcr4")
tcr5    = usfmToken("tcr5")
tcr6    = usfmToken("tcr6")

# Table of Contents
toc     = usfmTokenValue("toc", phrase)
toc1    = usfmTokenValue("toc1", phrase)
toc2    = usfmTokenValue("toc2", phrase)
toc3    = usfmTokenValue("toc3", phrase)

# Introductory Materials
is0     = usfmTokenValue('is', phrase) # 'is' is a Python keyword so can't be used here
is1     = usfmTokenValue('is1', phrase)
is2     = usfmTokenValue('is2', phrase)
is3     = usfmTokenValue('is3', phrase)

ip      = usfmToken('ip')
ipi     = usfmToken('ipi')
im      = usfmToken('im')
imi     = usfmToken('imi')
iot     = usfmToken("iot")
io1     = usfmToken("io1") | usfmToken("io")
io2     = usfmToken("io2")
ior_s   = usfmToken("ior")
ior_e   = usfmEndToken("ior")

imt     = usfmTokenValue('imt', phrase)
imt1    = usfmTokenValue('imt1', phrase)
imt2    = usfmTokenValue('imt2', phrase)
imt3    = usfmTokenValue('imt3', phrase)
ie      = usfmToken('ie')

# Quoted book title
bk_s    = usfmToken("bk")
bk_e    = usfmEndToken("bk")
# Key term
k_s     = usfmToken("k")
k_e     = usfmEndToken("k")
# Peripherals
periph = usfmTokenValue("periph", phrase)


element =  MatchFirst([ide, id,
                       usfmV, h,
                       toc, toc1, toc2, toc3,
                       mt, mt1, mt2, mt3,
                       mte,
                       ms, ms1, ms2,
                       imt, imt1, imt2, imt3,
                       ie,
                       mr,
                       s, s1, s2, s3, s4, s5,
                       sr,
                       sts,
                       r,
                       p,
                       pc,
                       pi, pi1, pi2,
                       cls,
                       mi,
                       b,
                       ca_s, ca_e,
                       c,
                       cl,
                       va_s, va_e,
                       v,
                       wj_s, wj_e,
                       nd_s, nd_e,
                       q, q1, q2, q3, q4,
                       qa,
                       qac,
                       qc,
                       qm, qm1, qm2, qm3,
                       qr,
                       qs_s, qs_e,
                       qt_s, qt_e,
                       nb,
                       m,
                       f_s, f_e,
                       fe_s, fe_e,
                       fr, fr_e,
                       fk,
                       ft, ft_e,
                       fq, fq_e,
                       fqa, fqa_e,
                       fqb,
                       fp,
                       fv, fv_e,
                       fdc, fdc_e,
                       xs, xe,
                       xdc_s, xdc_e,
                       xo,
                       xq,
                       xt, xt_e, xtnested, xtnested_e,
                       ist,
                       ien,
                       wj_s, wj_e,
                       bd_s, bd_e,
                       bdit_s, bdit_e,
                       li, li1, li2, li3, li4,
                       d,
                       sp,
                       add_s, add_e,
                       pn_s, pn_e,
                       rq_s, rq_e,
                       w_s, w_e,
                       tl_s, tl_e,
                       is0, is1, is2, is3,
                       ip, ipi,
                       im,
                       imi,
                       iot, io1, io2,
                       ior_s, ior_e,
                       k_s, k_e,
                       bk_s, bk_e,
                       sc_s, sc_e,
                       pbr,
                       rem,
                       tr,
                       th1, th2, th3, th4, th5, th6,
                       thr1, thr2, thr3, thr4, thr5, thr6,
                       tc1, tc2, tc3, tc4, tc5, tc6,
                       tcr1, tcr2, tcr3, tcr4, tcr5, tcr6,
                       textBlock,
                       escape,
                       periph,
                       unknown])

usfm    = OneOrMore(element)

# input string
def parseString(unicodeString):
    try:
        s = clean(unicodeString)
        tokens = usfm.parseString(s, parseAll=True)
    except Exception as e:
        print(e)
        print(repr(unicodeString[:50]))
        sys.exit()
    return [createToken(t) for t in tokens]

#def parseString(unicodeString):
#    """
#    version of parseString for use in libraries
#    :param unicodeString:
#    :return:
#    """
#    cleaned = clean(unicodeString)
#    tokens = usfm.parseString(cleaned, parseAll=True)
#    return [createToken(t) for t in tokens]

def clean(unicodeString):
    # We need to clean the input a bit. For a start, until
    # we work out what to do, non breaking spaces will be ignored
    # ie 0xa0
    ret_value = unicodeString.replace('\xa0', ' ')

    # escape illegal USFM sequences
    ret_value = ret_value.replace('\\\\', '\\ \\ ')  # replace so pyparsing doesn't crash, but still get warnings
    ret_value = ret_value.replace('\\ ',  '\\\\ ')
    ret_value = ret_value.replace('\\\n', '\\\\\n')
    ret_value = ret_value.replace('\\\r', '\\\\\r')
    ret_value = ret_value.replace('\\\t', '\\\\\t')

    # check edge case if backslash is at end of line
    l = len(ret_value)
    if (l > 0) and (ret_value[l-1] == '\\'):
        ret_value += '\\'  # escape it

    return ret_value

def createToken(t):
    options = {
        'id':   IDToken,
        'ide':  IDEToken,
        'usfm': USFMVersionToken,
        'h':    HToken,
        'toc1': TOC1Token,
        'toc2': TOC2Token,
        'toc3': TOC3Token,
        'mt':   MTToken,
        'mt1':  MTToken,
        'mt2':  MT2Token,
        'mt3':  MT3Token,
        'mte':  MTEToken,
        'imt':  IMTToken,
        'imt1': IMTToken,
        'imt2': IMT2Token,
        'imt3': IMT3Token,
        'ie':   IEToken,

        'ms':   MSToken,
        'ms1':  MSToken,
        'ms2':  MS2Token,
        'mr':   MRToken,
        'p':    PToken,
        'pc':   PCToken,
        'pi':   PIToken,
        'pi1':  PI1Token,
        'pi2':  PI2Token,
        'cls':  CLSToken,

        'b':    BToken,

        's':    SToken,
        's1':   SToken,
        's2':   S2Token,
        's3':   S3Token,
        's4':   S4Token,
        's5':   S5Token,

        'sr':   SRToken,
        'sts':  STSToken,
        'mi':   MIToken,
        'r':    RToken,
        'c':    CToken,
        'ca':   CAStartToken, 'ca*':  CAEndToken,
        'cl':   CLToken,
        'v':    VToken,
        'va':   VAStartToken, 'va*':  VAEndToken,
        'q':    QToken,
        'q1':   Q1Token,
        'q2':   Q2Token,
        'q3':   Q3Token,
        'q4':   Q4Token,
        'qa':   QAToken,
        'qac':  QACToken,
        'qc':   QCToken,
        'qm':   QMToken,
        'qm1':  QM1Token,
        'qm2':  QM2Token,
        'qm3':  QM3Token,
        'qr':   QRToken,
        'qs':   QSStartToken, 'qs*':  QSEndToken,
        'qt':   QTStartToken, 'qt*':  QTEndToken,
        'nb':   NBToken,
        'f':    FStartToken, 'f*':   FEndToken,
        'fe':   FEStartToken,  # Footnote intended as an end note
        'fe*':  FEEndToken,
        'fr':   FRToken, 'fr*':  FREndToken,
        'fk':   FKToken,
        'ft':   FTToken, 'ft*':  FTEndToken,
        'fq':   FQToken, 'fq*':  FQEndToken,
        'fqa':  FQAToken, 'fqa*': FQAEndToken,
        'fqb':  FQAEndToken,
        'fv':   FVStartToken, 'fv*':  FVEndToken,
        'fdc':  FDCStartToken, 'fdc*': FDCEndToken,
        'fp':   FPToken,
        'x':    XStartToken, 'x*':   XEndToken,
        'xdc':  XDCStartToken, 'xdc*': XDCEndToken,
        'xo':   XOToken,
        'xq':   XQToken,
        'xt':   XTToken, 'xt*': XTEndToken,
        '+xt':  XTToken, '+xt*': XTEndToken,
        'wj':   WJStartToken, 'wj*':  WJEndToken,
        'tl':   TLStartToken, 'tl*':  TLEndToken,
        'it':   ITStartToken, 'it*':  ITEndToken,
        'bd':   BDStartToken, 'bd*':  BDEndToken,
        'bdit': BDITStartToken, 'bdit*': BDITEndToken,

        'li':   LIToken,
        'li1':  LI1Token,
        'li2':  LI2Token,
        'li3':  LI3Token,
        'li4':  LI4Token,
        'd':    DToken,
        'sp':   SPToken,
#        'i*':   IEndToken,
        'add':  ADDStartToken, 'add*': ADDEndToken,
        'nd':   NDStartToken, 'nd*':  NDEndToken,
        'pn':   PNStartToken, 'pn*': PNEndToken,
        'rq':   RQStartToken, 'rq*': RQEndToken,
        'w':    WStartToken, 'w*': WEndToken,
        'sc':   SCStartToken, 'sc*':  SCEndToken,
        'm':    MToken,
        '\\\\': EscapedToken,
        'rem':  REMToken,
        'tr':   TRToken,
        'th1':  TH1Token,
        'th2':  TH2Token,
        'th3':  TH3Token,
        'th4':  TH4Token,
        'th5':  TH5Token,
        'th6':  TH6Token,
        'thr1': THR1Token,
        'thr2': THR2Token,
        'thr3': THR3Token,
        'thr4': THR4Token,
        'thr5': THR5Token,
        'thr6': THR6Token,
        'tc1':  TC1Token,
        'tc2':  TC2Token,
        'tc3':  TC3Token,
        'tc4':  TC4Token,
        'tc5':  TC5Token,
        'tc6':  TC6Token,
        'tcr1': TCR1Token,
        'tcr2': TCR2Token,
        'tcr3': TCR3Token,
        'tcr4': TCR4Token,
        'tcr5': TCR5Token,
        'tcr6': TCR6Token,
        'toc1': TOC1Token,
        'toc2': TOC2Token,
        'toc3': TOC3Token,

        'is':   ISToken,
        'is1':  ISToken,
        'is2':  IS2Token,
        'is3':  IS3Token,

        'ip':   IPToken,
        'ipi':  IPIToken,
        'im':   IMToken,
        'imi':  IMIToken,
        'iot':  IOTToken,
        'io':   IOToken,
        'io1':  IOToken,
        'io2':  IO2Token,
        'ior':  IORStartToken, 'ior*': IOREndToken,
        'k':    KStartToken, 'k*':  KEndToken,
        'bk':   BKStartToken, 'bk*':  BKEndToken,
        'text': TEXTToken,
        'periph': PeriphToken,
        'unknown': UnknownToken
    }
    for k, v in options.items():
        if t[0] == k:
            if len(t) == 1:
                token = v()
            else:
                token = v(t[1])
            token.type = k
            return token
    raise Exception(t[0])


# noinspection PyMethodMayBeStatic
class UsfmToken:
    def __init__(self, value=''):
        self.value = value
        self.type = None

    def getType(self):  return self.type
    def getValue(self): return self.value
    def isUnknown(self): return False
    def isID(self):     return False
    def isIDE(self):    return False
    def isUSFM(self):   return False
    def isH(self):      return False
    def isTOC1(self):   return False
    def isTOC2(self):   return False
    def isTOC3(self):   return False
    def isMT(self):     return False
    def isMT2(self):    return False
    def isMT3(self):    return False
    def isMTE(self):    return False
    def isMS(self):     return False
    def isMS2(self):    return False
    def isMR(self):     return False
    def isR(self):      return False
    def isP(self):      return False
    def isPC(self):     return False
    def isPI(self):     return False
    def isPI1(self):    return False
    def isPI2(self):    return False
    def isCLS(self):    return False
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
    def isKS(self):     return False
    def isKE(self):     return False
    def isV(self):      return False
    def isVAS(self):    return False
    def isVAE(self):    return False
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
    def isF_S(self):     return False
    def isF_E(self):     return False
    def isFE_S(self):    return False
    def isFE_E(self):    return False
    def isFR(self):     return False
    def isFR_E(self):    return False
    def isFK(self):     return False
    def isFT(self):     return False
    def isFT_E(self):   return False
    def isFP(self):     return False
    def isFQ(self):     return False
    def isFQA(self):    return False
    def isFQ_E(self):    return False
    def isFQA_E(self):   return False
    def isFQB(self):    return False
    def isFVS(self):    return False
    def isFVE(self):    return False
    def isFDCS(self):   return False
    def isFDCE(self):   return False
    def isX_S(self):     return False
    def isX_E(self):     return False
    def isXDCS(self):   return False
    def isXDCE(self):   return False
    def isXO(self):     return False
    def isXQ(self):     return False
    def isXT(self):     return False
    def isXTE(self):     return False
    def isITS(self):     return False
    def isITE(self):     return False
    def isSCS(self):    return False
    def isSCE(self):    return False
    def isLI(self):     return False
    def isLI1(self):    return False
    def isLI2(self):    return False
    def isLI3(self):    return False
    def isLI4(self):    return False
    def isD(self):      return False
    def isSP(self):     return False
    def isADDS(self):   return False
    def isADDE(self):   return False
    def isNDS(self):    return False
    def isNDE(self):    return False
    def isPNS(self):    return False
    def isPNE(self):    return False
    def isRQS(self):    return False
    def isRQE(self):    return False
    def isWS(self):    return False
    def isWE(self):    return False
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
    def is_is(self):   return False
    def is_is2(self):   return False
    def is_is3(self):   return False
    def is_imt(self):   return False
    def is_imt2(self):  return False
    def is_imt3(self):  return False
    def is_ie(self):    return False
    def is_ip(self):    return False
    def is_ipi(self):   return False
    def is_im(self):    return False
    def is_imi(self):   return False
    def is_iot(self):   return False
    def is_io(self):    return False
    def is_io2(self):   return False
    def is_ior_s(self): return False
    def is_ior_e(self): return False
    def is_k_s(self):   return False
    def is_k_e(self):   return False
    def is_bk_s(self):  return False
    def is_bk_e(self):  return False
    def is_periph(self):return False

class UnknownToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderUnknown(self)
    def isUnknown(self):     return True

class EscapedToken(UsfmToken):
    def renderOn(self, printer):
        self.value = '\\'
        return printer.renderText(self)
    def isUnknown(self): return True

class IDToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderID(self)
    def isID(self):     return True

class IDEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIDE(self)
    def isIDE(self):    return True

class USFMVersionToken(UsfmToken):
    def renderOn(self, printer): return printer.renderUSFMV(self)
    def isUSFM(self):    return True

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
    def renderOn(self, printer): return printer.render_imt(self)
    def is_imt(self): return True
class IMT2Token(UsfmToken):
    def renderOn(self, printer): return printer.render_imt2(self)
    def is_imt2(self): return True
class IMT3Token(UsfmToken):
    def renderOn(self, printer): return printer.render_imt3(self)
    def is_imt3(self): return True

class IEToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_ie(self)
    def is_ie(self):              return True

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

class CAStartToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCA_S(self)
    def isCAS(self):    return True
class CAEndToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCA_E(self)
    def isCAE(self):    return True

class CLToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCL(self)
    def isCL(self):     return True

class VToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderV(self)
    def isV(self):      return True

class VAStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderVA_S(self)
    def isVAS(self):    return True
class VAEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderVA_E(self)
    def isVAE(self):    return True

class TEXTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderText(self)
    def isTEXT(self):   return True

class WJStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderWJ_S(self)
    def isWJS(self):    return True
class WJEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderWJ_E(self)
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

class QSStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderQS_S(self)
    def isQSS(self):     return True

class QSEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderQS_E(self)
    def isQSE(self):     return True

class QTStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderQT_S(self)
    def isQTS(self):     return True

class QTEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderQT_E(self)
    def isQTE(self):     return True

class NBToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderNB(self)
    def isNB(self):      return True

class FStartToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderF_S(self)
    def isF_S(self):      return True

class FEStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFE_S(self)
    def isFE_S(self):      return True

class FRToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFR(self)
    def isFR(self):      return True
class FREndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFR_E(self)
    def isFR_E(self):      return True

class FKToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFK(self)
    def isFK(self):      return True

class FTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFT(self)
    def isFT(self):      return True
class FTEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFT_E(self)
    def isFT_E(self):      return True

class FPToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderFP(self)
    def isFP(self):      return True

class FQToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFQ(self)
    def isFQ(self):      return True
class FQEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFQ_E(self)
    def isFQ_E(self):      return True

class FQAToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFQA(self)
    def isFQA(self):     return True
class FQAEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFQA_E(self)
    def isFQA_E(self):    return True

class FQBToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFQA_E(self)
    def isFQB(self):     return True

class FEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderF_E(self)
    def isF_E(self):      return True

class FEEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFE_E(self)
    def isFE_E(self):      return True

class FVStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFV_S(self)
    def isFVS(self):      return True
class FVEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFV_E(self)
    def isFVE(self):      return True

class FDCStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFDC_S(self)
    def isFDCS(self):      return True
class FDCEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderFDC_E(self)
    def isFDCE(self):      return True

class IEToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderIE(self)
    def isIE(self):      return True

class ITStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderIT_S(self)
    def isITS(self):      return True
class ITEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderIT_E(self)
    def isITE(self):      return True

class BDStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderBD_S(self)
    def isBDS(self):      return True
class BDEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderBD_E(self)
    def isBDE(self):      return True

class BDITStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderBDIT_S(self)
    def isBDITS(self):     return True
class BDITEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderBDIT_E(self)
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

class ADDStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderADD_S(self)
    def isADDS(self):    return True
class ADDEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderADD_E(self)
    def isADDE(self):    return True

class NDStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderND_S(self)
    def isNDS(self):    return True
class NDEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderND_E(self)
    def isNDE(self):    return True

#class PBRToken(UsfmToken):
#    def renderOn(self, printer):
#        return printer.renderPBR(self)
#    def isPBR(self):    return True

class PNStartToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPN_S(self)
    def isPNS(self):      return True
class PNEndToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPN_E(self)
    def isPNE(self):      return True

class RQStartToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderRQ_S(self)
    def isRQS(self):      return True
class RQEndToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderRQ_E(self)
    def isRQE(self):      return True

class WStartToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderW_S(self)
    def isWS(self):      return True
class WEndToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderW_E(self)
    def isWE(self):      return True

# Cross References
class XStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderX_S(self)
    def isX_S(self):      return True
class XEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderX_E(self)
    def isX_E(self):      return True

class XDCStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderXDC_S(self)
    def isXDCS(self):      return True
class XDCEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderXDC_E(self)
    def isXDCE(self):      return True

class XOToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXO(self)
    def isXO(self):      return True

class XQToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXQ(self)
    def isXQ(self):      return True

class XTToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderXT(self)
    def isXT(self):      return True
class XTEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderXT_E(self)
    def isXTE(self):      return True

class MToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderM(self)
    def isM(self):      return True

# Transliterated Words
class TLStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderTL_S(self)
    def isTLS(self):      return True
class TLEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderTL_E(self)
    def isTLE(self):      return True

# Formatted paragraphs, like pc, pi, etc.
class PCToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPC(self)
    def isPC(self):      return True

# Indenting paragraphs
class PIToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPI(self)
    def isPI(self):      return True
class PI1Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPI1(self)
    def isPI1(self):      return True
class PI2Token(UsfmToken):
    def renderOn(self, printer):
        return printer.renderPI2(self)
    def isPI2(self):      return True

class CLSToken(UsfmToken):
    def renderOn(self, printer):
        return printer.renderCLS(self)
    def isCLS(self):      return True

# Small caps
class SCStartToken(UsfmToken):
    def renderOn(self, printer): return printer.renderSC_S(self)
    def isSCS(self):      return True
class SCEndToken(UsfmToken):
    def renderOn(self, printer): return printer.renderSC_E(self)
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
class ISToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_is(self)
    def is_is(self):             return True
class IS1Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_is1(self)
    def is_is(self):             return True
class IS2Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_is2(self)
    def is_is2(self):             return True
class IS3Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_is3(self)
    def is_is3(self):             return True

class IPToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_ip(self)
    def is_ip(self):              return True
class IPIToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_ipi(self)
    def is_ipi(self):              return True

class IMToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_im(self)
    def is_im(self):              return True

class IMIToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_imi(self)
    def is_imi(self):              return True

class IOTToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_iot(self)
    def is_iot(self):             return True

class IOToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_io(self)
    def is_io(self):             return True
class IO2Token(UsfmToken):
    def renderOn(self, printer):  return printer.render_io2(self)
    def is_io2(self):             return True

class IORStartToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_ior_s(self)
    def is_ior_s(self):           return True
class IOREndToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_ior_e(self)
    def is_ior_e(self):           return True

# Key term
class KStartToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_k_s(self)
    def is_k_s(self):            return True
class KEndToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_k_e(self)
    def is_k_e(self):            return True

# Quoted book title
class BKStartToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_bk_s(self)
    def is_bk_s(self):            return True
class BKEndToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_bk_e(self)
    def is_bk_e(self):            return True

# Peripherals
class PeriphToken(UsfmToken):
    def renderOn(self, printer):  return printer.render_periph(self)
    def is_periph(self):          return True
