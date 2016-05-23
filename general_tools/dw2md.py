#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Ricahrd Mahn <richard_mahn@wycliffeassociates.org>
#
#      docuwiki patterns        docuwiki example                 Y github markdown
# ---- ------------------------ -------------------------------- - ----------------------------------
#  1   tgt-url img-url alt-text [[tgt-url|{{img-url|alt-text}}]] Y [![alt-text](img-url)](tgt-url)
#  2   tgt-url img-url          [[tgt-url|{{img-url}}]]          Y [![](img-url)](tgt-url)     
#  3   image centered           {{ img-url }}                    Y ![](img-url)   
#  4   image left               {{img-url }}                     Y ![](img-url)     
#  5   image right              {{ img-url}}                     Y ![](img-url)     
#  6   image inline             {{img-url}}                      Y ![](img-url)      
#  7   image linkonly           {{img-url?linkonly}}               ![](img-url...)      
#  8   image size               {{img-url?size}}                   ![](img-url...)      
#  9   image caption            {{img-url|tooltip}}              ~ [tooltip](img-url)   
# 10   url link-text            [[url|link-text]]                Y [link-text](url)   
# 11   h1                       ====== h1 ======                 Y # h1 #  
# 12   h1                       ====== h1                        Y # h1   
# 13   h2                       ===== h2 =====                   Y ## h2 ##   
# 14   h2                       ===== h2                         Y ## h2   
# 15   h3                       ==== h3 ====                     Y ### h3 ### 
# 16   h3                       ==== h3                          Y ### h3   
# 17   h4                       === h4 ===                       Y #### h4 ####    
# 18   h4                       === h4                           Y #### h4     
# 19   h5                       == h5 ==                         Y ##### h5 #####    
# 20   h5                       == h5                            Y ##### h5    
# 21   hr                       ---                              Y ---         
# 22   hr                       ----------------------           Y ---          
# 23   numbered list            - ordered list                   Y 1 ordered list     
# 24   numbered sublist          - ordered sublist               Y   1 ordered sublist        
# 25   unordered list           * unordered list                   * unordered list     
# 26   unordered sublist          * unordered sublist                * unordered sublist        
# 27   italic                   //italic//                       Y *italic* _italic_
# 28   bold                     **bold**                           **bold** __bold__
# 29   underscore               __underscore__                   Y <span style="text-decoration: underline;">text</span>
# 30   superscript              <sup>superscript</sup>             <sup>superscript</sup>
# 31   subscript                <sub>subscript</sub>               <sub>subscript</sub>
# 32   overstrike               <del>overstrike</del>            Y ~~overstrike~~
# 33   noformat                 %%no formatting%%                Y `no formatting`
# 33.1 noformat                 <code> asdf </code>              Y ` asdf `
# 33.2 noformat                 <nowiki> asdf </nowiki>          Y ` asdf `
# 34   noformat                 <code>                           Y ```
# 34.1 noformat                 <nowiki>                         Y ```
#                                 text                             text
# 35                            </code>                          Y ```
# 35                            </php>                           Y ```
# 35                            </nowiki>                        Y ```
# 36                            <code lang>                      Y ``` lang
# 37                            <php>                            Y ``` php
# 38   table header n col       ^hdr1^hdr2^hdr3^hdr4^            Y hdr1 | hdr2 | hdr3 | hdr4 exchange and remove first and last 
#                                                                --- | --- | --- | ---
# 39   table row                |cell1|cell2|cell3|cell4|        Y cell1|cell2|cell3|cell4
# 40   row headers              ^hdr|cell1...|                   Y hdr|cell1|cell2
# 41   row span
# 42   underline header 1       ===============                  
# 43   underline subheader 2    ---------------
#
# end of test

# convert docuwiki markup to github markdown

import sys
import re
import codecs

def convert(dwText):
    mdText = dwText
    mdText = re.sub(ur'\[\[(http[^\|]*)\|\{\{(http[^\|]*)\|([^\}]*)\}\}\]\]', ur'[![\3](\2)](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\[\[(http[^\|]*)\|\{\{(http[^\|]*)\|([^\}]*)\}\}\]\]', ur'[![\3](\2)](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\[\[(http[^\|]*)\|\{\{(http[^\|]*)\}\}\]\]', ur'[![](\2)](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\{\{ (http[^ ]*) \}\}', ur'![](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\{\{(http[^ ]*) \}\}', ur'![](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\{\{ (http[^\}]*)\}\}', ur'![](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\{\{(http[^\}]*)\}\}', ur'![](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\{\{(http[^\|]*)\|([^\}]*)\}\}', ur'[\2](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\[\[([^\|]*)\|([^]]*)\]\]', ur'[\2](\1)', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'====== ([^=]*)======', ur'# \1#', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'====== (.*)$', ur'# \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'===== ([^=]*)=====', ur'## \1##', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'===== (.*)$', ur'## \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'==== ([^=]*)====', ur'### \1###', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'==== (.*)', ur'### \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'=== ([^=]*)===', ur'#### \1####', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'=== (.*)$', ur'#### \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'== ([^=]*)==', ur'##### \1#####', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'== (.*)', ur'##### \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'^[-]{3,}$', ur'---', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'^\s*- ', ur' 1 ', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\/\/([^\/]*)', ur'*\1*', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'__([^_]*)__', ur'<span style="text-decoration: underline;">\1<\/span>', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<del>([^<]*)<\/del>', ur'~~\1~~', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<nowiki>([^<]*)<\/nowiki>', ur'`\1`', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<code>([^<]*)<\/code>', ur'`\1`', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'%%([^%]*)%%', ur'`\1`', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<code ([^>]*)>', ur'``` \1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<code>(.*)$', ur'```\1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<nowiki>(.*)$', ur'```\1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<\/(nowiki\|code\|php)>', ur'```', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<php>', ur'``` php', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'<del>([^<]*)<\/del>', ur'~~\1~~', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'^\^(.*)\^$', ur'\1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'^\|(.*)\|$', ur'\1', mdText, flags=re.UNICODE|re.MULTILINE)
    mdText = re.sub(ur'\^(.*)\|', ur'\1', mdText, flags=re.UNICODE|re.MULTILINE)
    return mdText

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: dw2md.py <filename>"
        exit(1)

    filename = sys.argv[1]
    print convert(codecs.open(filename, 'r', encoding='utf-8').read())

