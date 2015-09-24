#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

'''
Exports OBS for given language to specified format.
'''

import os
import re
import sys
import json
import codecs
import shutil
import urllib2
import argparse
from string import Template

body_json = ''

api_url_txt = u'https://api.unfoldingword.org/obs/txt/1'
api_url_jpg = u'https://api.unfoldingword.org/obs/jpg/1'
api_abs = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1'
api_test_door43 = u'http://test.door43.org'  # this one is http and not https
snippets_dir = os.path.dirname(__file__) + u'/tex/'

MATCH_ALL = 0
MATCH_ONE = 0

# Create clickable URL links with \1 \1 or \1 \2, respectively
clickable_item1 = ur'\\startitemize[intro,joinedup,nowhite]{{\\goto{ht===!!!===tp\1}[url(ht===!!!===tp\1)]}}\\stopitemize'
clickable_inline1 = ur'({{\\goto{ht===!!!===tp\1}[url(ht===!!!===tp\1)]}})'
clickable_ownline1 = ur'{{\\goto{ht===!!!===tp\1}[url(ht===!!!===tp\1)]}}'
clickable_item2 = ur'\\startitemize[intro,joinedup,nowhite]{{\\goto{\2}[url(\1)]}}\\stopitemize'
clickable_inline2 = ur'({{\\goto{\2}[url(ht===!!!===tp\1)]}})'
clickable_ownline2 = ur'{{\\goto{\2}[url(ht===!!!===tp\1)]}}'
clickable_inlineB = ur'({{\\goto{ht===!!!===tp\2}[url(ht===!!!===tp\1)]}})'
clickable_ownlineB = ur'{{\\goto{ht===!!!===tp\2}[url(ht===!!!===tp\1)]}}'
# DocuWiki markup patterns
matchRemoveDummyTokenPat = re.compile(ur"===!!!===",re.UNICODE)
matchSingleTokenPat = re.compile(ur"^\s*(\S+)\s*$",re.UNICODE)
matchSectionPat = re.compile(ur"==+\s*(.*?)\s*==+",re.UNICODE)
matchBoldPat = re.compile(ur"[*][*]\s*(.*?)\s*[*][*]",re.UNICODE)
matchItalicPat = re.compile(ur"(?:\A|[^:])//\s*(.*?)\s*//",re.UNICODE)
matchUnderLinePat = re.compile(ur"__\s*(.*?)\s*__",re.UNICODE)
matchMonoPat = re.compile(ur"[\'][\']\s*(.*?)\s*[\'][\']",re.UNICODE)
matchRedPat = re.compile(ur"<red>\s*(.*?)\s*</red>",re.UNICODE)
matchMagentaPat = re.compile(ur"<mag[enta]*>\s*(.*?)\s*</mag[enta]*>",re.UNICODE)
matchBluePat = re.compile(ur"<blue>\s*(.*?)\s*</blue>",re.UNICODE)
matchGreenPat = re.compile(ur"<green>\s*(.*?)\s*</green>",re.UNICODE)
matchHeadingFourLevelPat = re.compile(ur"(\A|[^=])====+\s*(.*?)\s*===+?([^=]|\Z)",re.UNICODE)
matchHeadingThreeLevelPat = re.compile(ur"(\A|[^=])===+\s*(.*?)\s*==+?([^=]|\Z)",re.UNICODE)
matchHeadingTwoLevelPat = re.compile(ur"(\A|[^=])==+\s*(.*?)\s*==+?([^=]|\Z)",re.UNICODE)
matchHeadingOneLevelPat = re.compile(ur"(\A|[^=])=+\s*(.*?)\s*=+?([^=]|\Z)",re.UNICODE)
matchSubScriptPat = re.compile(ur"<sub>\s*(.*?)\s*</sub>",re.UNICODE)
matchSuperScriptPat = re.compile(ur"<sup>\s*(.*?)\s*</sup>",re.UNICODE)
matchStrikeOutPat = re.compile(ur"<del>\s*(.*?)\s*</del>",re.UNICODE)
matchURLandURLPat = re.compile(ur"[(]*\s*[\[][\[]\s*http(s*://[^\|\[\]]*?)\s*[\|]\s*http(s*[^\[\]]*?)\s*[\]][\]][\)\.,]*",re.UNICODE)
matchURLandTextPat = re.compile(ur"[(]*\s*[\[][\[]\s*http(s*://[^\|\[\]]*?)\s*[\|]\s*([^\[\]]*?)\s*[\]][\]][\)\.,]*",re.UNICODE)
matchPipePat = re.compile(ur"(\|)",re.UNICODE)
# DocuWiki markup patterns applied only to front and back matter
matchBulletPat = re.compile(ur"^\s*[\*]\s+(.*)$",re.UNICODE)
# Miscellaneous markup patterns
matchChaptersPat = re.compile(ur"===CHAPTERS===",re.UNICODE)
matchFrontMatterAboutPat = re.compile(ur"===FRONT\.MATTER\.ABOUT===",re.UNICODE)
matchFrontMatterlicensePat = re.compile(ur"===FRONT\.MATTER\.LICENSE===",re.UNICODE)
matchBackMatterPat = re.compile(ur"===BACK\.MATTER===",re.UNICODE)
matchMiscPat = re.compile(ur"<<<[\[]([^<>=]+)[\]]>>>",re.UNICODE)
# Other patterns
NBSP = u'~'         # non-breaking 1-en space
NBKN = u'\\,\\,\\,' # Three kerns in a row, non-breaking space
NBHY = u'\u2012'    # non-breaking hyphen
matchColonSemicolonNotAfterDigits = re.compile(ur"([^\d\s])\s*([:;])\s*([^\s])",re.UNICODE)
matchCommaBetweenDigits = re.compile(ur"(\d)\s*([,])\s*(\d)",re.UNICODE)
matchHyphen = re.compile(ur"[-\u2010\u2012\u2013\uFE63]",re.UNICODE)
matchHyphenEM = re.compile(ur"[\u2014\uFE58]",re.UNICODE)
matchAlphaNumSpaceThenNumber = re.compile(ur"(\w)\s+(\d)",re.UNICODE)
matchAlphaNum = re.compile(ur"[A-Za-z0-9]",re.UNICODE)
matchSignificantTex = re.compile(ur"[A-Za-z0-9\\{}\[\]]",re.UNICODE)
matchBlankLinePat = re.compile(ur"^\s*$",re.UNICODE)
matchPatLongURL = re.compile(ur"[(]*http(s*://[/\w\d,\.\?\&_=+-]{41,9999})[)\.,]*",re.UNICODE)
matchPatURL = re.compile(ur"[(]*http(s*://[/\w\d,\.\?\&_=+-]+)[)\.,]*",re.UNICODE)
matchOrdinalBookSpaces = re.compile(ur"([123](|\.|\p{L]{1,3}))\s",re.UNICODE)
matchChapterVersePat = re.compile(ur"\s+(\d+:\d+)",re.UNICODE)

def TRUTH(b):
    return "true" if b else "false"

def extract_title_from_frontmatter(frontmatter):
    match = re.compile(u"unfoldingWord \| (.*)\*\*", re.UNICODE).search(frontmatter)
    if match:
        return match.group(1)
    else:
        return "Open Bible Stories"

def checkForStandardKeysJSON():
    global body_json # Cannot pass dictionary via regex framework
    #------------------------------  header/footer spacing and body font-face
    if 'textwidth' not in body_json.keys(): body_json['textwidth'] = '308.9pt' # At 72.27 pt/inch this is width of each figure
    if 'topspace' not in body_json.keys(): body_json['topspace'] = '10pt' # nice for en,fr,es
    if 'botspace' not in body_json.keys(): body_json['botspace'] = '12pt' # nice for en,fr,es
    #if 'fontface' not in body_json.keys(): body_json['fontface'] = 'dejavu' # this is for production but does not seem to work for Russian
    if 'fontface' not in body_json.keys(): body_json['fontface'] = 'noto'
    if 'fontstyle' not in body_json.keys(): body_json['fontstyle'] = 'sans' # this is for production but does not seem to work for Russian
    if 'direction' not in body_json.keys(): body_json['fontface'] = 'ltr' # Use 'rtl' for Arabic, Farsi, etc.
    #------------------------------  Body font size and baseline
    if 'bodysize' not in body_json.keys(): body_json['bodysize'] = '10.0pt'
    if 'bodybaseline' not in body_json.keys(): body_json['bodybaseline'] = '12.0pt'
    if 'bodyalign' not in body_json.keys(): body_json['bodyalign'] = 'width'
    #------------------------------  Body font adjusted sizes
    if 'tfasize' not in body_json.keys(): body_json['tfasize'] = '1.10'
    if 'tfbsize' not in body_json.keys(): body_json['tfbsize'] = '1.20'
    if 'tfcsize' not in body_json.keys(): body_json['tfcsize'] = '1.40'
    if 'tfdsize' not in body_json.keys(): body_json['tfdsize'] = '1.60'
    if 'tfesize' not in body_json.keys(): body_json['tfesize'] = '1.80'
    if 'tfxsize' not in body_json.keys(): body_json['tfxsize'] = '0.9'
    if 'tfxxsize' not in body_json.keys(): body_json['tfxxsize'] = '0.8'
    if 'smallsize' not in body_json.keys(): body_json['smallsize'] = '0.80'
    #------------------------------  Table-of-contents size, etc
    if 'tocsize' not in body_json.keys(): body_json['tocsize'] = '12pt'
    if 'licsize' not in body_json.keys(): body_json['licsize'] = '9pt'
    if 'tocbaseline' not in body_json.keys(): body_json['tocbaseline'] = '16pt'
    if 'licbaseline' not in body_json.keys(): body_json['licbaseline'] = '9pt'
    if 'tocperpage' not in body_json.keys(): body_json['tocperpage'] = '26'
    if 'checkinglevel' not in body_json.keys(): body_json['checkinglevel'] = args.checkinglevel

def writeFile(outfile, p):
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()

def getURL(url, outfile):
    try:
        request = urllib2.urlopen(url)
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return
    with open(outfile, 'wb') as fp:
        shutil.copyfileobj(request, fp)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
        return json.loads('{}')
    else:
        return json.loads('[]')

def AnotherReplace(matchobj):
    global body_json
    keyword = matchobj.group(1)
    if keyword in body_json.keys():
        return body_json[keyword]
    return 'nothing'

def tex_load_snippet_file(xtr, entryname):
    f = codecs.open(snippets_dir + entryname, 'r', encoding='utf-8')
    each = f.readlines()
    each = each[1:] # Skip the first line which is the utf-8 coding repeated
    str = u''.join(each)
    f.close()
    occurs = 1
    while ( occurs > 0):
        ( str, occurs ) = matchMiscPat.subn(AnotherReplace,str,MATCH_ALL)
    each = str.split(u'\n')
    while (not matchSignificantTex.search(each[-1])):
        each.pop()
    str = xtr + (u'\n'+xtr).join(each) + u'\n'
    return str

def getTitle(text, format='plain'):
    if format == 'html':
        return u'<h1>{0}</h1>'.format(text)
    elif format == 'md':
        return u'{0}\n=========='.format(text)
    elif format == 'tex':
        return u'    \\startmakeup\\section{{{0}}}\\stopmakeup'.format(text)
    return text

def getImage(xtr, lang, fid, res, format='plain'):
    img_link = '/'.join([api_url_jpg, \
                         lang, res, \
                         'obs-{0}-{1}.jpg'.format(lang, fid) \
                     ])
    if format == 'html':
        return u'<img src="{0}" />'.format(img_link)
    elif format == 'tex':
        return xtr + xtr + xtr + '{{\\externalfigure[{0}][yscale={1}]}}'.format(img_link,950) # 950 = 95%
    return u''

def getFrame(xtr, text, format, texreg):
    xtr2 = xtr + xtr
    xtr3 = xtr + xtr + xtr
    if format == 'html':
        return u'<p>{0}</p>'.format(text)
    elif format == 'md':
        return u'\n{0}\n'.format(text)
    elif format == 'tex':
        return u'\n'.join([
                             xtr2 + u'\\placefigure[nonumber]',
                             xtr3 + u'{{\\copy\\{0}}}'.format(texreg)
                          ])
    return text

def do_not_break_before_chapter_verse(format, text):
    if (format == 'tex'):
        copy = text
        copy = matchHyphen.sub(NBHY, copy, MATCH_ALL)
        copy = matchHyphenEM.sub(NBHY, copy, MATCH_ALL)
        copy = matchAlphaNumSpaceThenNumber.sub(ur'\1'+NBKN+ur'\2', copy, MATCH_ALL) # change spaces to non-breaking 1/2 em
        copy = matchColonSemicolonNotAfterDigits.sub(ur'\1\2 \3', copy, MATCH_ALL)
        copy = matchCommaBetweenDigits.sub(ur'\1\2\3', copy, MATCH_ALL)
        copy = matchOrdinalBookSpaces.sub(ur'\1'+NBSP, copy, MATCH_ALL)
        return copy
    return text

def getRef(xtr, place_ref_template, text, format='plain'):
    global body_json
    if format == 'html':
        return u'<em>{0}</em>'.format(text)
    elif format == 'md':
        return u'*{0}*'.format(text)
    elif format == 'tex':
        #copy = do_not_break_before_chapter_verse(format, text)
        #each = place_ref_template.safe_substitute(thetext=copy).split(u'\n')
        each = place_ref_template.safe_substitute(thetext=text).split(u'\n')
        return xtr + (u'\n'+xtr).join(each) + u'\n\\vskip 6.0pt\n'
    return text

def filter_apply_docuwiki_start(single_line):
    # Order is important here
    single_line = matchHeadingFourLevelPat.sub(ur'\1{\\bfd \2}\3',single_line,MATCH_ALL)
    single_line = matchHeadingThreeLevelPat.sub(ur'\1{\\bfc \2}\3',single_line,MATCH_ALL)
    single_line = matchHeadingTwoLevelPat.sub(ur'\1{\\bfb \2}\3',single_line,MATCH_ALL)
    single_line = matchHeadingOneLevelPat.sub(ur'\1{\\bfa \2}\3',single_line,MATCH_ALL)
    single_line = matchSectionPat.sub(ur'{\\bf \1}',single_line,MATCH_ALL) # Just boldface for stories
    single_line = matchBoldPat.sub(ur'{\\bf \1}',single_line,MATCH_ALL)
    single_line = matchItalicPat.sub(ur'{\\em \1\/}',single_line,MATCH_ALL) # The \/ is an end-of-italic correction to add extra whitespace
    single_line = matchUnderLinePat.sub(ur'\\underbar{\1}',single_line,MATCH_ALL)
    single_line = matchMonoPat.sub(ur'{\\tt \1}',single_line,MATCH_ALL)
    single_line = matchRedPat.sub(ur'\\color[middlered]{\1}',single_line,MATCH_ALL)
    single_line = matchMagentaPat.sub(ur'\\color[magenta]{\1}',single_line,MATCH_ALL)
    #shew = (single_line.find(u'<blue>') >= 0)
    #if (shew): print "~~matchBluePat="+matchBluePat.pattern
    #if (shew): print "--single_line="+single_line
    #if (shew): print matchBluePat.search(single_line).groups()
    single_line = matchBluePat.sub(ur'\\color[blue]{\1}',single_line,MATCH_ALL)
    #if (shew): print "++single_line="+single_line
    single_line = matchGreenPat.sub(ur'\\color[middlegreen]{\1}',single_line,MATCH_ALL)
    single_line = matchSubScriptPat.sub(ur'\\low{\1}',single_line,MATCH_ALL)
    single_line = matchSuperScriptPat.sub(ur'\\high{\1}',single_line,MATCH_ALL)
    single_line = matchStrikeOutPat.sub(ur'\\overstrike{\1}',single_line,MATCH_ALL)
    return single_line

def filter_apply_docuwiki_finish(single_line):
    single_line = matchPipePat.sub(ur'\\textbar{}',single_line,MATCH_ALL)
    single_line = matchRemoveDummyTokenPat.sub(ur'',single_line,MATCH_ALL)
    return single_line

def filter_apply_docuwiki(single_line):
    single_line = filter_apply_docuwiki_start(single_line)
    single_line = filter_apply_docuwiki_finish(single_line)
    return single_line

def filter_apply_docuwiki_and_links(single_line):
    single_line = filter_apply_docuwiki_start(single_line)
    #shew = (single_line.find(u'http') >= 0)
    #if (shew): print u"~~matchURLandTextPat=",matchURLandTextPat.pattern
    #if (shew): print u"__single_line=",single_line
    #if (shew): print matchURLandTextPat.search(single_line).groups()
    if (matchSingleTokenPat.match(single_line)):
        single_line = matchURLandURLPat.sub(clickable_ownlineB,single_line,MATCH_ALL)
        single_line = matchURLandTextPat.sub(clickable_ownline2,single_line,MATCH_ALL)
    else:
        single_line = matchURLandURLPat.sub(clickable_inlineB,single_line,MATCH_ALL)
        single_line = matchURLandTextPat.sub(clickable_inline2,single_line,MATCH_ALL)
    #if (shew): print u"@@single_line=",single_line
    if (matchSingleTokenPat.match(single_line)):
        single_line = matchPatLongURL.sub(clickable_ownline1,single_line,MATCH_ALL)
        single_line = matchPatURL.sub(clickable_ownline1,single_line,MATCH_ALL)
    else:
        single_line = matchPatLongURL.sub(clickable_item1,single_line,MATCH_ALL)
        single_line = matchPatURL.sub(clickable_inline1,single_line,MATCH_ALL)
    #if (shew): print u"==single_line=",single_line
    single_line = filter_apply_docuwiki_finish(single_line)
    #if (shew): print u"!!single_line=",single_line
    return single_line

def export_matter(lang_message, format, img_res, lang, test):
    '''
    Exports JSON front/back matter to specificed format.
    '''
    j = u'\n\n'
    if format == 'tex':
        j = u'\n'
    tmpsplit = lang_message.split(u'\n')
    matter = [ ]
    if (test):
        tmpsplit.append(ur'\\\\ \\\\')
        tmpsplit.append(ur'Testing E=mc<sup>2</sup> and also H<sub>2</sub>O but not <del>discarded</del> \\\\')
        tmpsplit.append(ur'Testing <red>red</red> and <green>green</green> and <blue>blue</blue> and <mag>magenta</mag>')
        tmpsplit.append(ur"and ''mono'' and  __under__  and **bold** and \/ //italics// \\\\")
    global inItems
    inItems = 0
    def AnotherItem(matchobj):
        global inItems
        inItems += 1
        ans = u'    \\item{' + matchobj.group(1) + u'}'
        if (inItems == 1):
            ans = u'    \\startitemize[intro,joinedup,nowhite]\n' + ans
        return ans
    for single_line in tmpsplit:
        copy = single_line
        single_line = matchBlankLinePat.sub(ur'    \\blank',single_line,MATCH_ALL)
        #single_line = matchBlankLinePat.sub(ur'    \\par\\par',single_line,MATCH_ALL)
        (single_line, occurrences) = matchBulletPat.subn(AnotherItem,single_line,MATCH_ONE)
        if ((inItems > 0) and (occurrences == 0)):
            inItems = 0
            single_line = u'    \\stopitemize\n' + single_line
        if (copy == single_line):
            single_line = u'    \\noindentation ' + single_line
        single_line = filter_apply_docuwiki_and_links(single_line)
        single_line = matchChapterVersePat.sub(ur'~\1',single_line,MATCH_ALL)
        matter.append(single_line)
    return j.join(matter)

def start_of_physical_page(xtr):
    return u'\n'.join([xtr+u'%%START-OF-PHYSICAL-PAGE', xtr+u'\\vtop{'])

def end_of_physical_page(xtr):
    return u'\n'.join([xtr+u'}', xtr+u'%%END-OF-PHYSICAL-PAGE'])

def export(chapters_json, format, max_chapters, img_res, lang):
    global body_json
    '''
    Exports JSON to specificed format.
    '''
    spaces4 = u'    '
    j = u'\n\n'
    output = []
    if format == 'tex':
        j = u'\n'
        calc_vertical_need_snip = tex_load_snippet_file(spaces4,'calculate-vertical-need.tex')
        calc_leftover_snip = tex_load_snippet_file(spaces4,'calculate-leftover.tex')
        begin_loop_snip = tex_load_snippet_file(spaces4,'begin-adjust-loop.tex')
        in_leftover_snip = tex_load_snippet_file(spaces4+spaces4,'calculate-leftover.tex')
        in_adjust_snip = tex_load_snippet_file(spaces4+spaces4,'adjust-spacing.tex')
        end_loop_snip = tex_load_snippet_file(spaces4,'end-adjust-loop.tex')
        verify_snip = tex_load_snippet_file(spaces4,'verify-vertical-space.tex')
        place_ref_snip = tex_load_snippet_file(spaces4,'place-reference.tex')
        adjust_one_snip = calc_vertical_need_snip + calc_leftover_snip + verify_snip
        adjust_two_snip = calc_vertical_need_snip + begin_loop_snip + in_leftover_snip + in_adjust_snip + end_loop_snip + calc_leftover_snip + verify_snip
        adjust_one = Template(adjust_one_snip)
        adjust_two = Template(adjust_two_snip)
        place_ref_template = Template(place_ref_snip)
    ixchp = (-1)
    for chp in chapters_json:
        ixchp = 1 +  ixchp
        past_max_chapters = (max_chapters > 0) and (ixchp >= max_chapters)
        if (past_max_chapters):
            break
        output.append(getTitle(chp['title'], format))
        ixframe = (-1)
        ChapterFrames = chp['frames']
        nframe = len(ChapterFrames)
        RefTextOnly = do_not_break_before_chapter_verse(format, chp['ref'])
        for fr in ChapterFrames:
            ixframe = 1 + ixframe
            ixlookahead = 1 + ixframe
            is_even = ((ixframe % 2) == 0)
            is_last_page = \
                (is_even and ((ixframe + 2) >= nframe)) \
                or ((not is_even) and ((ixframe + 1) >= nframe))
            page_is_full = (not is_even) or (ixlookahead < nframe)
            TextOnly = fr['text']
            if format == 'tex':
                TextOnly = filter_apply_docuwiki(TextOnly)
                RefTextOnly = filter_apply_docuwiki(RefTextOnly)
            TextFrame = getFrame(spaces4, TextOnly, format, \
                                 'toptry' if is_even else 'bottry')
            ImageFrame = getImage(spaces4, lang, fr['id'], img_res, format)
            adjust_tex = adjust_two if (page_is_full) else adjust_one
            #print "ixframe=",ixframe,"{",nframe,"}, even=",TRUTH(is_even),", last=",TRUTH(is_last_page),", full=",TRUTH(page_is_full)
            if format != 'tex':
                output.append(ImageFrame)
                output.append(TextFrame)
            else:
                AlsoReg = u'\\refneed' if (is_last_page) else u'\\EmptyString'
                NeedAlso = u'\\refneed + ' if (is_last_page) else u''
                pageword = u'LAST_PAGE' if (is_last_page) else u'CONTINUED'
                TruthIsLastPage = 'true' if (is_last_page) else 'false'
                if (not is_even):
                    output.append(spaces4 + spaces4 + u'\\vskip \\the\\leftover')
                elif (page_is_full):
                    nextfr = ChapterFrames[ixlookahead]
                    NextTextOnly = nextfr['text']
                    if format == 'tex':
                        NextTextOnly = filter_apply_docuwiki(NextTextOnly)
                    NextImageFrame = getImage(spaces4, lang, nextfr['id'], img_res, format)
                    texdict = dict(pageword=pageword,needalso=NeedAlso,alsoreg=AlsoReg,
                                   topimg=ImageFrame,botimg=NextImageFrame,
                                   lang=lang,fid=fr['id'],isLastPage=TruthIsLastPage,
                                   toptxt=TextOnly,bottxt=NextTextOnly,reftxt=RefTextOnly)
                    output.append(adjust_two.safe_substitute(texdict))
                else:
                    texdict = dict(pageword=pageword,needalso=NeedAlso,alsoreg=AlsoReg,
                                   topimg=ImageFrame,botimg='',
                                   lang=lang,fid=fr['id'],isLastPage=TruthIsLastPage,
                                   toptxt=TextOnly,bottxt='',reftxt=RefTextOnly)
                    output.append(adjust_one.safe_substitute(texdict))
                if (is_even):
                    output.append(start_of_physical_page(spaces4))
                output.append(spaces4 + spaces4 + u''.join([u'\message{FIGURE: ',lang,'-',fr['id'],'}']))
                output.append(TextFrame)
                output.append(ImageFrame)
                if ((not is_even) and (not is_last_page)):
                    output.append(end_of_physical_page(spaces4))
                    output.append(spaces4 + u'\\page[yes]')
        output.append(getRef(spaces4, place_ref_template, RefTextOnly, format))
        output.append(end_of_physical_page(spaces4))
        output.append(spaces4 + u'\\page[yes]')
    return j.join(output)

def getJSON(lang,entry,tmpent):
    anyJSONe = entry.format(lang)
    anyJSONf = '/'.join([api_url_txt, lang, anyJSONe])
    anytmpf = '/'.join(['/tmp', tmpent]).format(lang)
    getURL(anyJSONf, anytmpf)
    if not os.path.exists(anytmpf):
        print "Failed to get JSON {0} file into {1}.".format(anyJSONe,anytmpf)
        sys.exit(1)
    return anytmpf

def main(lang, outpath, format, max_chapters, img_res, checkinglevel):
    global body_json
    sys.stdout = codecs.getwriter('utf8')(sys.stdout);
    toptmpf = getJSON(lang, 'obs-{0}-front-matter.json', '{0}-front-matter-json.tmp')
    bottmpf = getJSON(lang, 'obs-{0}-back-matter.json', '{0}-back-matter-json.tmp')
    lang_top_json = loadJSON(toptmpf, 'd')
    lang_bot_json = loadJSON(bottmpf, 'd')
    # Parse the front and back matter
    front_matter = export_matter(lang_top_json['front-matter'], format, img_res, lang_top_json['language'], 0)
    # The front matter really has two parts, an "about" section and a "license" section
    # Sadly the API returns it as one blob, but we want to insert the checking level
    # indicator on between the two. Until such a time as the API returns these strings separately,
    # this is a cludge to split them. Faling a match it should just put the whole thing in the first section
    #fm = re.split(r'\{\\\\bf.+:\s*\}\\n', front_matter)
    fm = re.split(r'\s(?=\{\\bf.+:\s*\})', front_matter)
    output_front_about = fm[0]
    if len(fm) > 1:
        output_front_license = ''.join(fm[1:])
    else:
        output_front_license = ''
    output_back = export_matter(lang_bot_json['back-matter'], format, img_res, lang_bot_json['language'], 0)
    # Parse the body matter
    jsonf = 'obs-{0}.json'.format(lang)
    lang_url = '/'.join([api_url_txt, lang, jsonf])
    tmpf = getJSON(lang, jsonf, '{0}-body-matter-json.tmp')
    body_json = loadJSON(tmpf, 'd')
    checkForStandardKeysJSON()
    # Hacks to make up for missing localized strings
    if 'toctitle' not in body_json.keys():
        body_json['toctitle'] = extract_title_from_frontmatter(lang_top_json['front-matter'])
    output = export(body_json['chapters'], format, max_chapters, img_res, body_json['language'])
    # For ConTeXt files only, Read the "main_template.tex" file replacing
    # all <<<[anyvar]>>> with its definition from the body-matter JSON file
    if format == 'tex':
        outlist = []
        tex_tempate = snippets_dir + 'main_template.tex'
        if not os.path.exists(tex_tempate):
            print "Failed to get TeX template."
            sys.exit(1)
        template = codecs.open(tex_tempate, 'r', encoding='utf-8').readlines()
        for single_line in template:
            single_line = single_line.rstrip('\r\n') # .encode('utf-8')
            if (matchChaptersPat.search(single_line)):
                outlist.append(output)
            elif (matchFrontMatterAboutPat.search(single_line)):
                outlist.append(output_front_about)
            elif (matchFrontMatterlicensePat.search(single_line)):
                outlist.append(output_front_license)
            elif (matchBackMatterPat.search(single_line)):
                outlist.append(output_back)
            else:
                occurs = 1
                while ( occurs > 0):
                    ( single_line, occurs ) \
                        = matchMiscPat.subn(AnotherReplace,single_line,MATCH_ALL)
                outlist.append(single_line)
        full_output = u'\n'.join(outlist)
        writeFile(outpath, full_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-o', '--output', dest="outpath", default=False,
        required=True, help="Output path")
    parser.add_argument('-l', '--language', dest="lang", default=False,
        required=True, help="Language code")
    parser.add_argument('-f', '--format', dest="format", default=False,
        required=True, help="Desired format: html, md, tex, or plain")
    parser.add_argument('-m', '--max-chapters', dest="max_chapters", default="0",
         help="Typeset only the first n chapters")
    parser.add_argument('-r', '--resolution', dest="img_res", default='360px',
        help="Image resolution: 360px, or 2160px")
    parser.add_argument('-c', '--checkinglevel', dest="checkinglevel", default="1",
        help="Quality Assurace level campleted: 1, 2, or 3")
    args = parser.parse_args(sys.argv[1:])
    main(args.lang, args.outpath, args.format, int(args.max_chapters), args.img_res, args.checkinglevel)
