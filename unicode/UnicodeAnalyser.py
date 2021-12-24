#!/usr/bin/env python3
#
# UnicodeAnalyser.py
#
# Copyright (c) 2021 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
# Contributors:
#   Robert Hunt <Robert.Hunt@unfoldingword.org>
#
# Written Dec 2021 by RJH
#   Last modified: 2021-12-17 by RJH
#
"""
Quick script to analyse the Unicode status of a local repo clone
"""
from typing import List, Tuple, Optional
import os
import shutil
from pathlib import Path
import unicodedata
import bisect


REPO_NAME = 'hbo_uhb'
# REPO_NAME = 'el-x-koine_ugnt'
# REPO_NAME = 'en_ult'
# REPO_NAME = 'en_ust'
LOCAL_SOURCE_BASE_FOLDERPATH = Path('/mnt/Data/uW_dataRepos/')
LOCAL_SOURCE_FOLDERPATH = LOCAL_SOURCE_BASE_FOLDERPATH.joinpath(REPO_NAME)

BBB_LIST = ('GEN','EXO','LEV','NUM','DEU',
                'JOS','JDG','RUT','1SA','2SA','1KI',
                '2KI','1CH','2CH','EZR', 'NEH', 'EST',
                'JOB','PSA','PRO','ECC','SNG','ISA',
                'JER','LAM','EZK','DAN','HOS','JOL',
                'AMO','OBA','JON','MIC','NAM','HAB',
                'ZEP','HAG','ZEC','MAL',
                'MAT','MRK','LUK','JHN','ACT',
                'ROM','1CO','2CO','GAL','EPH','PHP',
                'COL','1TH','2TH','1TI','2TI','TIT',
                'PHM','HEB', 'JAS','1PE','2PE',
                '1JN','2JN','3JN', 'JUD', 'REV')
assert len(BBB_LIST) == 66


# From https://www.unicode.org/Public/14.0.0/ucd/PropertyValueAliases.txt
PropertyValueAliases_STRING = """# PropertyValueAliases-14.0.0.txt
# Date: 2021-05-10, 21:08:53 GMT
# © 2021 Unicode®, Inc.
# Unicode and the Unicode Logo are registered trademarks of Unicode, Inc. in the U.S. and other countries.
# For terms of use, see http://www.unicode.org/terms_of_use.html
#
# Unicode Character Database
#   For documentation, see http://www.unicode.org/reports/tr44/
#
# This file contains aliases for property values used in the UCD.
# These names can be used for XML formats of UCD data, for regular-expression
# property tests, and other programmatic textual descriptions of Unicode data.
#
# The names may be translated in appropriate environments, and additional
# aliases may be useful.
#
# FORMAT
#
# Each line describes a property value name.
# This consists of three or more fields, separated by semicolons.
#
# First Field: The first field describes the property for which that
# property value name is used.
#
# Second Field: The second field is the short name for the property value.
# It is typically an abbreviation, but in a number of cases it is simply
# a duplicate of the "long name" in the third field.
#
# Third Field: The third field is the long name for the property value,
# typically the formal name used in documentation about the property value.
#
# In the case of Canonical_Combining_Class (ccc), there are 4 fields:
# The second field is numeric, the third is the short name, and the fourth is the long name.
#
# The above are the preferred aliases. Other aliases may be listed in additional fields.
#
# Loose matching should be applied to all property names and property values, with
# the exception of String Property values. With loose matching of property names and
# values, the case distinctions, whitespace, hyphens, and '_' are ignored.
# For Numeric Property values, numeric equivalence is applied: thus "01.00"
# is equivalent to "1".
#
# NOTE: Property value names are NOT unique across properties. For example:
#
#   AL means Arabic Letter for the Bidi_Class property, and
#   AL means Above_Left for the Canonical_Combining_Class property, and
#   AL means Alphabetic for the Line_Break property.
#
# In addition, some property names may be the same as some property value names.
# For example:
#
#   sc means the Script property, and
#   Sc means the General_Category property value Currency_Symbol (Sc)
#
# The combination of property value and property name is, however, unique.
#
# For more information, see UAX #44, Unicode Character Database, and
# UTS #18, Unicode Regular Expressions.
# ================================================


# ASCII_Hex_Digit (AHex)

AHex; N                               ; No                               ; F                                ; False
AHex; Y                               ; Yes                              ; T                                ; True

# Age (age)

age; 1.1                              ; V1_1
age; 2.0                              ; V2_0
age; 2.1                              ; V2_1
age; 3.0                              ; V3_0
age; 3.1                              ; V3_1
age; 3.2                              ; V3_2
age; 4.0                              ; V4_0
age; 4.1                              ; V4_1
age; 5.0                              ; V5_0
age; 5.1                              ; V5_1
age; 5.2                              ; V5_2
age; 6.0                              ; V6_0
age; 6.1                              ; V6_1
age; 6.2                              ; V6_2
age; 6.3                              ; V6_3
age; 7.0                              ; V7_0
age; 8.0                              ; V8_0
age; 9.0                              ; V9_0
age; 10.0                             ; V10_0
age; 11.0                             ; V11_0
age; 12.0                             ; V12_0
age; 12.1                             ; V12_1
age; 13.0                             ; V13_0
age; 14.0                             ; V14_0
age; NA                               ; Unassigned

# Alphabetic (Alpha)

Alpha; N                              ; No                               ; F                                ; False
Alpha; Y                              ; Yes                              ; T                                ; True

# Bidi_Class (bc)

bc ; AL                               ; Arabic_Letter
bc ; AN                               ; Arabic_Number
bc ; B                                ; Paragraph_Separator
bc ; BN                               ; Boundary_Neutral
bc ; CS                               ; Common_Separator
bc ; EN                               ; European_Number
bc ; ES                               ; European_Separator
bc ; ET                               ; European_Terminator
bc ; FSI                              ; First_Strong_Isolate
bc ; L                                ; Left_To_Right
bc ; LRE                              ; Left_To_Right_Embedding
bc ; LRI                              ; Left_To_Right_Isolate
bc ; LRO                              ; Left_To_Right_Override
bc ; NSM                              ; Nonspacing_Mark
bc ; ON                               ; Other_Neutral
bc ; PDF                              ; Pop_Directional_Format
bc ; PDI                              ; Pop_Directional_Isolate
bc ; R                                ; Right_To_Left
bc ; RLE                              ; Right_To_Left_Embedding
bc ; RLI                              ; Right_To_Left_Isolate
bc ; RLO                              ; Right_To_Left_Override
bc ; S                                ; Segment_Separator
bc ; WS                               ; White_Space

# Bidi_Control (Bidi_C)

Bidi_C; N                             ; No                               ; F                                ; False
Bidi_C; Y                             ; Yes                              ; T                                ; True

# Bidi_Mirrored (Bidi_M)

Bidi_M; N                             ; No                               ; F                                ; False
Bidi_M; Y                             ; Yes                              ; T                                ; True

# Bidi_Mirroring_Glyph (bmg)

# @missing: 0000..10FFFF; Bidi_Mirroring_Glyph; <none>

# Bidi_Paired_Bracket (bpb)

# @missing: 0000..10FFFF; Bidi_Paired_Bracket; <none>

# Bidi_Paired_Bracket_Type (bpt)

bpt; c                                ; Close
bpt; n                                ; None
bpt; o                                ; Open
# @missing: 0000..10FFFF; Bidi_Paired_Bracket_Type; n

# Block (blk)

blk; Adlam                            ; Adlam
blk; Aegean_Numbers                   ; Aegean_Numbers
blk; Ahom                             ; Ahom
blk; Alchemical                       ; Alchemical_Symbols
blk; Alphabetic_PF                    ; Alphabetic_Presentation_Forms
blk; Anatolian_Hieroglyphs            ; Anatolian_Hieroglyphs
blk; Ancient_Greek_Music              ; Ancient_Greek_Musical_Notation
blk; Ancient_Greek_Numbers            ; Ancient_Greek_Numbers
blk; Ancient_Symbols                  ; Ancient_Symbols
blk; Arabic                           ; Arabic
blk; Arabic_Ext_A                     ; Arabic_Extended_A
blk; Arabic_Ext_B                     ; Arabic_Extended_B
blk; Arabic_Math                      ; Arabic_Mathematical_Alphabetic_Symbols
blk; Arabic_PF_A                      ; Arabic_Presentation_Forms_A      ; Arabic_Presentation_Forms-A
blk; Arabic_PF_B                      ; Arabic_Presentation_Forms_B
blk; Arabic_Sup                       ; Arabic_Supplement
blk; Armenian                         ; Armenian
blk; Arrows                           ; Arrows
blk; ASCII                            ; Basic_Latin
blk; Avestan                          ; Avestan
blk; Balinese                         ; Balinese
blk; Bamum                            ; Bamum
blk; Bamum_Sup                        ; Bamum_Supplement
blk; Bassa_Vah                        ; Bassa_Vah
blk; Batak                            ; Batak
blk; Bengali                          ; Bengali
blk; Bhaiksuki                        ; Bhaiksuki
blk; Block_Elements                   ; Block_Elements
blk; Bopomofo                         ; Bopomofo
blk; Bopomofo_Ext                     ; Bopomofo_Extended
blk; Box_Drawing                      ; Box_Drawing
blk; Brahmi                           ; Brahmi
blk; Braille                          ; Braille_Patterns
blk; Buginese                         ; Buginese
blk; Buhid                            ; Buhid
blk; Byzantine_Music                  ; Byzantine_Musical_Symbols
blk; Carian                           ; Carian
blk; Caucasian_Albanian               ; Caucasian_Albanian
blk; Chakma                           ; Chakma
blk; Cham                             ; Cham
blk; Cherokee                         ; Cherokee
blk; Cherokee_Sup                     ; Cherokee_Supplement
blk; Chess_Symbols                    ; Chess_Symbols
blk; Chorasmian                       ; Chorasmian
blk; CJK                              ; CJK_Unified_Ideographs
blk; CJK_Compat                       ; CJK_Compatibility
blk; CJK_Compat_Forms                 ; CJK_Compatibility_Forms
blk; CJK_Compat_Ideographs            ; CJK_Compatibility_Ideographs
blk; CJK_Compat_Ideographs_Sup        ; CJK_Compatibility_Ideographs_Supplement
blk; CJK_Ext_A                        ; CJK_Unified_Ideographs_Extension_A
blk; CJK_Ext_B                        ; CJK_Unified_Ideographs_Extension_B
blk; CJK_Ext_C                        ; CJK_Unified_Ideographs_Extension_C
blk; CJK_Ext_D                        ; CJK_Unified_Ideographs_Extension_D
blk; CJK_Ext_E                        ; CJK_Unified_Ideographs_Extension_E
blk; CJK_Ext_F                        ; CJK_Unified_Ideographs_Extension_F
blk; CJK_Ext_G                        ; CJK_Unified_Ideographs_Extension_G
blk; CJK_Radicals_Sup                 ; CJK_Radicals_Supplement
blk; CJK_Strokes                      ; CJK_Strokes
blk; CJK_Symbols                      ; CJK_Symbols_And_Punctuation
blk; Compat_Jamo                      ; Hangul_Compatibility_Jamo
blk; Control_Pictures                 ; Control_Pictures
blk; Coptic                           ; Coptic
blk; Coptic_Epact_Numbers             ; Coptic_Epact_Numbers
blk; Counting_Rod                     ; Counting_Rod_Numerals
blk; Cuneiform                        ; Cuneiform
blk; Cuneiform_Numbers                ; Cuneiform_Numbers_And_Punctuation
blk; Currency_Symbols                 ; Currency_Symbols
blk; Cypriot_Syllabary                ; Cypriot_Syllabary
blk; Cypro_Minoan                     ; Cypro_Minoan
blk; Cyrillic                         ; Cyrillic
blk; Cyrillic_Ext_A                   ; Cyrillic_Extended_A
blk; Cyrillic_Ext_B                   ; Cyrillic_Extended_B
blk; Cyrillic_Ext_C                   ; Cyrillic_Extended_C
blk; Cyrillic_Sup                     ; Cyrillic_Supplement              ; Cyrillic_Supplementary
blk; Deseret                          ; Deseret
blk; Devanagari                       ; Devanagari
blk; Devanagari_Ext                   ; Devanagari_Extended
blk; Diacriticals                     ; Combining_Diacritical_Marks
blk; Diacriticals_Ext                 ; Combining_Diacritical_Marks_Extended
blk; Diacriticals_For_Symbols         ; Combining_Diacritical_Marks_For_Symbols; Combining_Marks_For_Symbols
blk; Diacriticals_Sup                 ; Combining_Diacritical_Marks_Supplement
blk; Dingbats                         ; Dingbats
blk; Dives_Akuru                      ; Dives_Akuru
blk; Dogra                            ; Dogra
blk; Domino                           ; Domino_Tiles
blk; Duployan                         ; Duployan
blk; Early_Dynastic_Cuneiform         ; Early_Dynastic_Cuneiform
blk; Egyptian_Hieroglyph_Format_Controls; Egyptian_Hieroglyph_Format_Controls
blk; Egyptian_Hieroglyphs             ; Egyptian_Hieroglyphs
blk; Elbasan                          ; Elbasan
blk; Elymaic                          ; Elymaic
blk; Emoticons                        ; Emoticons
blk; Enclosed_Alphanum                ; Enclosed_Alphanumerics
blk; Enclosed_Alphanum_Sup            ; Enclosed_Alphanumeric_Supplement
blk; Enclosed_CJK                     ; Enclosed_CJK_Letters_And_Months
blk; Enclosed_Ideographic_Sup         ; Enclosed_Ideographic_Supplement
blk; Ethiopic                         ; Ethiopic
blk; Ethiopic_Ext                     ; Ethiopic_Extended
blk; Ethiopic_Ext_A                   ; Ethiopic_Extended_A
blk; Ethiopic_Ext_B                   ; Ethiopic_Extended_B
blk; Ethiopic_Sup                     ; Ethiopic_Supplement
blk; Geometric_Shapes                 ; Geometric_Shapes
blk; Geometric_Shapes_Ext             ; Geometric_Shapes_Extended
blk; Georgian                         ; Georgian
blk; Georgian_Ext                     ; Georgian_Extended
blk; Georgian_Sup                     ; Georgian_Supplement
blk; Glagolitic                       ; Glagolitic
blk; Glagolitic_Sup                   ; Glagolitic_Supplement
blk; Gothic                           ; Gothic
blk; Grantha                          ; Grantha
blk; Greek                            ; Greek_And_Coptic
blk; Greek_Ext                        ; Greek_Extended
blk; Gujarati                         ; Gujarati
blk; Gunjala_Gondi                    ; Gunjala_Gondi
blk; Gurmukhi                         ; Gurmukhi
blk; Half_And_Full_Forms              ; Halfwidth_And_Fullwidth_Forms
blk; Half_Marks                       ; Combining_Half_Marks
blk; Hangul                           ; Hangul_Syllables
blk; Hanifi_Rohingya                  ; Hanifi_Rohingya
blk; Hanunoo                          ; Hanunoo
blk; Hatran                           ; Hatran
blk; Hebrew                           ; Hebrew
blk; High_PU_Surrogates               ; High_Private_Use_Surrogates
blk; High_Surrogates                  ; High_Surrogates
blk; Hiragana                         ; Hiragana
blk; IDC                              ; Ideographic_Description_Characters
blk; Ideographic_Symbols              ; Ideographic_Symbols_And_Punctuation
blk; Imperial_Aramaic                 ; Imperial_Aramaic
blk; Indic_Number_Forms               ; Common_Indic_Number_Forms
blk; Indic_Siyaq_Numbers              ; Indic_Siyaq_Numbers
blk; Inscriptional_Pahlavi            ; Inscriptional_Pahlavi
blk; Inscriptional_Parthian           ; Inscriptional_Parthian
blk; IPA_Ext                          ; IPA_Extensions
blk; Jamo                             ; Hangul_Jamo
blk; Jamo_Ext_A                       ; Hangul_Jamo_Extended_A
blk; Jamo_Ext_B                       ; Hangul_Jamo_Extended_B
blk; Javanese                         ; Javanese
blk; Kaithi                           ; Kaithi
blk; Kana_Ext_A                       ; Kana_Extended_A
blk; Kana_Ext_B                       ; Kana_Extended_B
blk; Kana_Sup                         ; Kana_Supplement
blk; Kanbun                           ; Kanbun
blk; Kangxi                           ; Kangxi_Radicals
blk; Kannada                          ; Kannada
blk; Katakana                         ; Katakana
blk; Katakana_Ext                     ; Katakana_Phonetic_Extensions
blk; Kayah_Li                         ; Kayah_Li
blk; Kharoshthi                       ; Kharoshthi
blk; Khitan_Small_Script              ; Khitan_Small_Script
blk; Khmer                            ; Khmer
blk; Khmer_Symbols                    ; Khmer_Symbols
blk; Khojki                           ; Khojki
blk; Khudawadi                        ; Khudawadi
blk; Lao                              ; Lao
blk; Latin_1_Sup                      ; Latin_1_Supplement               ; Latin_1
blk; Latin_Ext_A                      ; Latin_Extended_A
blk; Latin_Ext_Additional             ; Latin_Extended_Additional
blk; Latin_Ext_B                      ; Latin_Extended_B
blk; Latin_Ext_C                      ; Latin_Extended_C
blk; Latin_Ext_D                      ; Latin_Extended_D
blk; Latin_Ext_E                      ; Latin_Extended_E
blk; Latin_Ext_F                      ; Latin_Extended_F
blk; Latin_Ext_G                      ; Latin_Extended_G
blk; Lepcha                           ; Lepcha
blk; Letterlike_Symbols               ; Letterlike_Symbols
blk; Limbu                            ; Limbu
blk; Linear_A                         ; Linear_A
blk; Linear_B_Ideograms               ; Linear_B_Ideograms
blk; Linear_B_Syllabary               ; Linear_B_Syllabary
blk; Lisu                             ; Lisu
blk; Lisu_Sup                         ; Lisu_Supplement
blk; Low_Surrogates                   ; Low_Surrogates
blk; Lycian                           ; Lycian
blk; Lydian                           ; Lydian
blk; Mahajani                         ; Mahajani
blk; Mahjong                          ; Mahjong_Tiles
blk; Makasar                          ; Makasar
blk; Malayalam                        ; Malayalam
blk; Mandaic                          ; Mandaic
blk; Manichaean                       ; Manichaean
blk; Marchen                          ; Marchen
blk; Masaram_Gondi                    ; Masaram_Gondi
blk; Math_Alphanum                    ; Mathematical_Alphanumeric_Symbols
blk; Math_Operators                   ; Mathematical_Operators
blk; Mayan_Numerals                   ; Mayan_Numerals
blk; Medefaidrin                      ; Medefaidrin
blk; Meetei_Mayek                     ; Meetei_Mayek
blk; Meetei_Mayek_Ext                 ; Meetei_Mayek_Extensions
blk; Mende_Kikakui                    ; Mende_Kikakui
blk; Meroitic_Cursive                 ; Meroitic_Cursive
blk; Meroitic_Hieroglyphs             ; Meroitic_Hieroglyphs
blk; Miao                             ; Miao
blk; Misc_Arrows                      ; Miscellaneous_Symbols_And_Arrows
blk; Misc_Math_Symbols_A              ; Miscellaneous_Mathematical_Symbols_A
blk; Misc_Math_Symbols_B              ; Miscellaneous_Mathematical_Symbols_B
blk; Misc_Pictographs                 ; Miscellaneous_Symbols_And_Pictographs
blk; Misc_Symbols                     ; Miscellaneous_Symbols
blk; Misc_Technical                   ; Miscellaneous_Technical
blk; Modi                             ; Modi
blk; Modifier_Letters                 ; Spacing_Modifier_Letters
blk; Modifier_Tone_Letters            ; Modifier_Tone_Letters
blk; Mongolian                        ; Mongolian
blk; Mongolian_Sup                    ; Mongolian_Supplement
blk; Mro                              ; Mro
blk; Multani                          ; Multani
blk; Music                            ; Musical_Symbols
blk; Myanmar                          ; Myanmar
blk; Myanmar_Ext_A                    ; Myanmar_Extended_A
blk; Myanmar_Ext_B                    ; Myanmar_Extended_B
blk; Nabataean                        ; Nabataean
blk; Nandinagari                      ; Nandinagari
blk; NB                               ; No_Block
blk; New_Tai_Lue                      ; New_Tai_Lue
blk; Newa                             ; Newa
blk; NKo                              ; NKo
blk; Number_Forms                     ; Number_Forms
blk; Nushu                            ; Nushu
blk; Nyiakeng_Puachue_Hmong           ; Nyiakeng_Puachue_Hmong
blk; OCR                              ; Optical_Character_Recognition
blk; Ogham                            ; Ogham
blk; Ol_Chiki                         ; Ol_Chiki
blk; Old_Hungarian                    ; Old_Hungarian
blk; Old_Italic                       ; Old_Italic
blk; Old_North_Arabian                ; Old_North_Arabian
blk; Old_Permic                       ; Old_Permic
blk; Old_Persian                      ; Old_Persian
blk; Old_Sogdian                      ; Old_Sogdian
blk; Old_South_Arabian                ; Old_South_Arabian
blk; Old_Turkic                       ; Old_Turkic
blk; Old_Uyghur                       ; Old_Uyghur
blk; Oriya                            ; Oriya
blk; Ornamental_Dingbats              ; Ornamental_Dingbats
blk; Osage                            ; Osage
blk; Osmanya                          ; Osmanya
blk; Ottoman_Siyaq_Numbers            ; Ottoman_Siyaq_Numbers
blk; Pahawh_Hmong                     ; Pahawh_Hmong
blk; Palmyrene                        ; Palmyrene
blk; Pau_Cin_Hau                      ; Pau_Cin_Hau
blk; Phags_Pa                         ; Phags_Pa
blk; Phaistos                         ; Phaistos_Disc
blk; Phoenician                       ; Phoenician
blk; Phonetic_Ext                     ; Phonetic_Extensions
blk; Phonetic_Ext_Sup                 ; Phonetic_Extensions_Supplement
blk; Playing_Cards                    ; Playing_Cards
blk; Psalter_Pahlavi                  ; Psalter_Pahlavi
blk; PUA                              ; Private_Use_Area                 ; Private_Use
blk; Punctuation                      ; General_Punctuation
blk; Rejang                           ; Rejang
blk; Rumi                             ; Rumi_Numeral_Symbols
blk; Runic                            ; Runic
blk; Samaritan                        ; Samaritan
blk; Saurashtra                       ; Saurashtra
blk; Sharada                          ; Sharada
blk; Shavian                          ; Shavian
blk; Shorthand_Format_Controls        ; Shorthand_Format_Controls
blk; Siddham                          ; Siddham
blk; Sinhala                          ; Sinhala
blk; Sinhala_Archaic_Numbers          ; Sinhala_Archaic_Numbers
blk; Small_Forms                      ; Small_Form_Variants
blk; Small_Kana_Ext                   ; Small_Kana_Extension
blk; Sogdian                          ; Sogdian
blk; Sora_Sompeng                     ; Sora_Sompeng
blk; Soyombo                          ; Soyombo
blk; Specials                         ; Specials
blk; Sundanese                        ; Sundanese
blk; Sundanese_Sup                    ; Sundanese_Supplement
blk; Sup_Arrows_A                     ; Supplemental_Arrows_A
blk; Sup_Arrows_B                     ; Supplemental_Arrows_B
blk; Sup_Arrows_C                     ; Supplemental_Arrows_C
blk; Sup_Math_Operators               ; Supplemental_Mathematical_Operators
blk; Sup_PUA_A                        ; Supplementary_Private_Use_Area_A
blk; Sup_PUA_B                        ; Supplementary_Private_Use_Area_B
blk; Sup_Punctuation                  ; Supplemental_Punctuation
blk; Sup_Symbols_And_Pictographs      ; Supplemental_Symbols_And_Pictographs
blk; Super_And_Sub                    ; Superscripts_And_Subscripts
blk; Sutton_SignWriting               ; Sutton_SignWriting
blk; Syloti_Nagri                     ; Syloti_Nagri
blk; Symbols_And_Pictographs_Ext_A    ; Symbols_And_Pictographs_Extended_A
blk; Symbols_For_Legacy_Computing     ; Symbols_For_Legacy_Computing
blk; Syriac                           ; Syriac
blk; Syriac_Sup                       ; Syriac_Supplement
blk; Tagalog                          ; Tagalog
blk; Tagbanwa                         ; Tagbanwa
blk; Tags                             ; Tags
blk; Tai_Le                           ; Tai_Le
blk; Tai_Tham                         ; Tai_Tham
blk; Tai_Viet                         ; Tai_Viet
blk; Tai_Xuan_Jing                    ; Tai_Xuan_Jing_Symbols
blk; Takri                            ; Takri
blk; Tamil                            ; Tamil
blk; Tamil_Sup                        ; Tamil_Supplement
blk; Tangsa                           ; Tangsa
blk; Tangut                           ; Tangut
blk; Tangut_Components                ; Tangut_Components
blk; Tangut_Sup                       ; Tangut_Supplement
blk; Telugu                           ; Telugu
blk; Thaana                           ; Thaana
blk; Thai                             ; Thai
blk; Tibetan                          ; Tibetan
blk; Tifinagh                         ; Tifinagh
blk; Tirhuta                          ; Tirhuta
blk; Toto                             ; Toto
blk; Transport_And_Map                ; Transport_And_Map_Symbols
blk; UCAS                             ; Unified_Canadian_Aboriginal_Syllabics; Canadian_Syllabics
blk; UCAS_Ext                         ; Unified_Canadian_Aboriginal_Syllabics_Extended
blk; UCAS_Ext_A                       ; Unified_Canadian_Aboriginal_Syllabics_Extended_A
blk; Ugaritic                         ; Ugaritic
blk; Vai                              ; Vai
blk; Vedic_Ext                        ; Vedic_Extensions
blk; Vertical_Forms                   ; Vertical_Forms
blk; Vithkuqi                         ; Vithkuqi
blk; VS                               ; Variation_Selectors
blk; VS_Sup                           ; Variation_Selectors_Supplement
blk; Wancho                           ; Wancho
blk; Warang_Citi                      ; Warang_Citi
blk; Yezidi                           ; Yezidi
blk; Yi_Radicals                      ; Yi_Radicals
blk; Yi_Syllables                     ; Yi_Syllables
blk; Yijing                           ; Yijing_Hexagram_Symbols
blk; Zanabazar_Square                 ; Zanabazar_Square
blk; Znamenny_Music                   ; Znamenny_Musical_Notation

# Canonical_Combining_Class (ccc)

ccc;   0; NR                         ; Not_Reordered
ccc;   1; OV                         ; Overlay
ccc;   6; HANR                       ; Han_Reading
ccc;   7; NK                         ; Nukta
ccc;   8; KV                         ; Kana_Voicing
ccc;   9; VR                         ; Virama
ccc;  10; CCC10                      ; CCC10
ccc;  11; CCC11                      ; CCC11
ccc;  12; CCC12                      ; CCC12
ccc;  13; CCC13                      ; CCC13
ccc;  14; CCC14                      ; CCC14
ccc;  15; CCC15                      ; CCC15
ccc;  16; CCC16                      ; CCC16
ccc;  17; CCC17                      ; CCC17
ccc;  18; CCC18                      ; CCC18
ccc;  19; CCC19                      ; CCC19
ccc;  20; CCC20                      ; CCC20
ccc;  21; CCC21                      ; CCC21
ccc;  22; CCC22                      ; CCC22
ccc;  23; CCC23                      ; CCC23
ccc;  24; CCC24                      ; CCC24
ccc;  25; CCC25                      ; CCC25
ccc;  26; CCC26                      ; CCC26
ccc;  27; CCC27                      ; CCC27
ccc;  28; CCC28                      ; CCC28
ccc;  29; CCC29                      ; CCC29
ccc;  30; CCC30                      ; CCC30
ccc;  31; CCC31                      ; CCC31
ccc;  32; CCC32                      ; CCC32
ccc;  33; CCC33                      ; CCC33
ccc;  34; CCC34                      ; CCC34
ccc;  35; CCC35                      ; CCC35
ccc;  36; CCC36                      ; CCC36
ccc;  84; CCC84                      ; CCC84
ccc;  91; CCC91                      ; CCC91
ccc; 103; CCC103                     ; CCC103
ccc; 107; CCC107                     ; CCC107
ccc; 118; CCC118                     ; CCC118
ccc; 122; CCC122                     ; CCC122
ccc; 129; CCC129                     ; CCC129
ccc; 130; CCC130                     ; CCC130
ccc; 132; CCC132                     ; CCC132
ccc; 133; CCC133                     ; CCC133 # RESERVED
ccc; 200; ATBL                       ; Attached_Below_Left
ccc; 202; ATB                        ; Attached_Below
ccc; 214; ATA                        ; Attached_Above
ccc; 216; ATAR                       ; Attached_Above_Right
ccc; 218; BL                         ; Below_Left
ccc; 220; B                          ; Below
ccc; 222; BR                         ; Below_Right
ccc; 224; L                          ; Left
ccc; 226; R                          ; Right
ccc; 228; AL                         ; Above_Left
ccc; 230; A                          ; Above
ccc; 232; AR                         ; Above_Right
ccc; 233; DB                         ; Double_Below
ccc; 234; DA                         ; Double_Above
ccc; 240; IS                         ; Iota_Subscript

# Case_Folding (cf)

# @missing: 0000..10FFFF; Case_Folding; <code point>

# Case_Ignorable (CI)

CI ; N                                ; No                               ; F                                ; False
CI ; Y                                ; Yes                              ; T                                ; True

# Cased (Cased)

Cased; N                              ; No                               ; F                                ; False
Cased; Y                              ; Yes                              ; T                                ; True

# Changes_When_Casefolded (CWCF)

CWCF; N                               ; No                               ; F                                ; False
CWCF; Y                               ; Yes                              ; T                                ; True

# Changes_When_Casemapped (CWCM)

CWCM; N                               ; No                               ; F                                ; False
CWCM; Y                               ; Yes                              ; T                                ; True

# Changes_When_Lowercased (CWL)

CWL; N                                ; No                               ; F                                ; False
CWL; Y                                ; Yes                              ; T                                ; True

# Changes_When_NFKC_Casefolded (CWKCF)

CWKCF; N                              ; No                               ; F                                ; False
CWKCF; Y                              ; Yes                              ; T                                ; True

# Changes_When_Titlecased (CWT)

CWT; N                                ; No                               ; F                                ; False
CWT; Y                                ; Yes                              ; T                                ; True

# Changes_When_Uppercased (CWU)

CWU; N                                ; No                               ; F                                ; False
CWU; Y                                ; Yes                              ; T                                ; True

# Composition_Exclusion (CE)

CE ; N                                ; No                               ; F                                ; False
CE ; Y                                ; Yes                              ; T                                ; True

# Dash (Dash)

Dash; N                               ; No                               ; F                                ; False
Dash; Y                               ; Yes                              ; T                                ; True

# Decomposition_Mapping (dm)

# @missing: 0000..10FFFF; Decomposition_Mapping; <code point>

# Decomposition_Type (dt)

dt ; Can                              ; Canonical                        ; can
dt ; Com                              ; Compat                           ; com
dt ; Enc                              ; Circle                           ; enc
dt ; Fin                              ; Final                            ; fin
dt ; Font                             ; Font                             ; font
dt ; Fra                              ; Fraction                         ; fra
dt ; Init                             ; Initial                          ; init
dt ; Iso                              ; Isolated                         ; iso
dt ; Med                              ; Medial                           ; med
dt ; Nar                              ; Narrow                           ; nar
dt ; Nb                               ; Nobreak                          ; nb
dt ; None                             ; None                             ; none
dt ; Sml                              ; Small                            ; sml
dt ; Sqr                              ; Square                           ; sqr
dt ; Sub                              ; Sub                              ; sub
dt ; Sup                              ; Super                            ; sup
dt ; Vert                             ; Vertical                         ; vert
dt ; Wide                             ; Wide                             ; wide

# Default_Ignorable_Code_Point (DI)

DI ; N                                ; No                               ; F                                ; False
DI ; Y                                ; Yes                              ; T                                ; True

# Deprecated (Dep)

Dep; N                                ; No                               ; F                                ; False
Dep; Y                                ; Yes                              ; T                                ; True

# Diacritic (Dia)

Dia; N                                ; No                               ; F                                ; False
Dia; Y                                ; Yes                              ; T                                ; True

# East_Asian_Width (ea)

ea ; A                                ; Ambiguous
ea ; F                                ; Fullwidth
ea ; H                                ; Halfwidth
ea ; N                                ; Neutral
ea ; Na                               ; Narrow
ea ; W                                ; Wide

# Emoji (Emoji)

Emoji; N                              ; No                               ; F                                ; False
Emoji; Y                              ; Yes                              ; T                                ; True

# Emoji_Component (EComp)

EComp; N                              ; No                               ; F                                ; False
EComp; Y                              ; Yes                              ; T                                ; True

# Emoji_Modifier (EMod)

EMod; N                               ; No                               ; F                                ; False
EMod; Y                               ; Yes                              ; T                                ; True

# Emoji_Modifier_Base (EBase)

EBase; N                              ; No                               ; F                                ; False
EBase; Y                              ; Yes                              ; T                                ; True

# Emoji_Presentation (EPres)

EPres; N                              ; No                               ; F                                ; False
EPres; Y                              ; Yes                              ; T                                ; True

# Equivalent_Unified_Ideograph (EqUIdeo)

# @missing: 0000..10FFFF; Equivalent_Unified_Ideograph; <none>

# Expands_On_NFC (XO_NFC)

XO_NFC; N                             ; No                               ; F                                ; False
XO_NFC; Y                             ; Yes                              ; T                                ; True

# Expands_On_NFD (XO_NFD)

XO_NFD; N                             ; No                               ; F                                ; False
XO_NFD; Y                             ; Yes                              ; T                                ; True

# Expands_On_NFKC (XO_NFKC)

XO_NFKC; N                            ; No                               ; F                                ; False
XO_NFKC; Y                            ; Yes                              ; T                                ; True

# Expands_On_NFKD (XO_NFKD)

XO_NFKD; N                            ; No                               ; F                                ; False
XO_NFKD; Y                            ; Yes                              ; T                                ; True

# Extended_Pictographic (ExtPict)

ExtPict; N                            ; No                               ; F                                ; False
ExtPict; Y                            ; Yes                              ; T                                ; True

# Extender (Ext)

Ext; N                                ; No                               ; F                                ; False
Ext; Y                                ; Yes                              ; T                                ; True

# FC_NFKC_Closure (FC_NFKC)

# @missing: 0000..10FFFF; FC_NFKC_Closure; <code point>

# Full_Composition_Exclusion (Comp_Ex)

Comp_Ex; N                            ; No                               ; F                                ; False
Comp_Ex; Y                            ; Yes                              ; T                                ; True

# General_Category (gc)

gc ; C                                ; Other                            # Cc | Cf | Cn | Co | Cs
gc ; Cc                               ; Control                          ; cntrl
gc ; Cf                               ; Format
gc ; Cn                               ; Unassigned
gc ; Co                               ; Private_Use
gc ; Cs                               ; Surrogate
gc ; L                                ; Letter                           # Ll | Lm | Lo | Lt | Lu
gc ; LC                               ; Cased_Letter                     # Ll | Lt | Lu
gc ; Ll                               ; Lowercase_Letter
gc ; Lm                               ; Modifier_Letter
gc ; Lo                               ; Other_Letter
gc ; Lt                               ; Titlecase_Letter
gc ; Lu                               ; Uppercase_Letter
gc ; M                                ; Mark                             ; Combining_Mark                   # Mc | Me | Mn
gc ; Mc                               ; Spacing_Mark
gc ; Me                               ; Enclosing_Mark
gc ; Mn                               ; Nonspacing_Mark
gc ; N                                ; Number                           # Nd | Nl | No
gc ; Nd                               ; Decimal_Number                   ; digit
gc ; Nl                               ; Letter_Number
gc ; No                               ; Other_Number
gc ; P                                ; Punctuation                      ; punct                            # Pc | Pd | Pe | Pf | Pi | Po | Ps
gc ; Pc                               ; Connector_Punctuation
gc ; Pd                               ; Dash_Punctuation
gc ; Pe                               ; Close_Punctuation
gc ; Pf                               ; Final_Punctuation
gc ; Pi                               ; Initial_Punctuation
gc ; Po                               ; Other_Punctuation
gc ; Ps                               ; Open_Punctuation
gc ; S                                ; Symbol                           # Sc | Sk | Sm | So
gc ; Sc                               ; Currency_Symbol
gc ; Sk                               ; Modifier_Symbol
gc ; Sm                               ; Math_Symbol
gc ; So                               ; Other_Symbol
gc ; Z                                ; Separator                        # Zl | Zp | Zs
gc ; Zl                               ; Line_Separator
gc ; Zp                               ; Paragraph_Separator
gc ; Zs                               ; Space_Separator
# @missing: 0000..10FFFF; General_Category; Unassigned

# Grapheme_Base (Gr_Base)

Gr_Base; N                            ; No                               ; F                                ; False
Gr_Base; Y                            ; Yes                              ; T                                ; True

# Grapheme_Cluster_Break (GCB)

GCB; CN                               ; Control
GCB; CR                               ; CR
GCB; EB                               ; E_Base
GCB; EBG                              ; E_Base_GAZ
GCB; EM                               ; E_Modifier
GCB; EX                               ; Extend
GCB; GAZ                              ; Glue_After_Zwj
GCB; L                                ; L
GCB; LF                               ; LF
GCB; LV                               ; LV
GCB; LVT                              ; LVT
GCB; PP                               ; Prepend
GCB; RI                               ; Regional_Indicator
GCB; SM                               ; SpacingMark
GCB; T                                ; T
GCB; V                                ; V
GCB; XX                               ; Other
GCB; ZWJ                              ; ZWJ

# Grapheme_Extend (Gr_Ext)

Gr_Ext; N                             ; No                               ; F                                ; False
Gr_Ext; Y                             ; Yes                              ; T                                ; True

# Grapheme_Link (Gr_Link)

Gr_Link; N                            ; No                               ; F                                ; False
Gr_Link; Y                            ; Yes                              ; T                                ; True

# Hangul_Syllable_Type (hst)

hst; L                                ; Leading_Jamo
hst; LV                               ; LV_Syllable
hst; LVT                              ; LVT_Syllable
hst; NA                               ; Not_Applicable
hst; T                                ; Trailing_Jamo
hst; V                                ; Vowel_Jamo

# Hex_Digit (Hex)

Hex; N                                ; No                               ; F                                ; False
Hex; Y                                ; Yes                              ; T                                ; True

# Hyphen (Hyphen)

Hyphen; N                             ; No                               ; F                                ; False
Hyphen; Y                             ; Yes                              ; T                                ; True

# IDS_Binary_Operator (IDSB)

IDSB; N                               ; No                               ; F                                ; False
IDSB; Y                               ; Yes                              ; T                                ; True

# IDS_Trinary_Operator (IDST)

IDST; N                               ; No                               ; F                                ; False
IDST; Y                               ; Yes                              ; T                                ; True

# ID_Continue (IDC)

IDC; N                                ; No                               ; F                                ; False
IDC; Y                                ; Yes                              ; T                                ; True

# ID_Start (IDS)

IDS; N                                ; No                               ; F                                ; False
IDS; Y                                ; Yes                              ; T                                ; True

# ISO_Comment (isc)

# @missing: 0000..10FFFF; ISO_Comment; <none>

# Ideographic (Ideo)

Ideo; N                               ; No                               ; F                                ; False
Ideo; Y                               ; Yes                              ; T                                ; True

# Indic_Positional_Category (InPC)

InPC; Bottom                          ; Bottom
InPC; Bottom_And_Left                 ; Bottom_And_Left
InPC; Bottom_And_Right                ; Bottom_And_Right
InPC; Left                            ; Left
InPC; Left_And_Right                  ; Left_And_Right
InPC; NA                              ; NA
InPC; Overstruck                      ; Overstruck
InPC; Right                           ; Right
InPC; Top                             ; Top
InPC; Top_And_Bottom                  ; Top_And_Bottom
InPC; Top_And_Bottom_And_Left         ; Top_And_Bottom_And_Left
InPC; Top_And_Bottom_And_Right        ; Top_And_Bottom_And_Right
InPC; Top_And_Left                    ; Top_And_Left
InPC; Top_And_Left_And_Right          ; Top_And_Left_And_Right
InPC; Top_And_Right                   ; Top_And_Right
InPC; Visual_Order_Left               ; Visual_Order_Left

# Indic_Syllabic_Category (InSC)

InSC; Avagraha                        ; Avagraha
InSC; Bindu                           ; Bindu
InSC; Brahmi_Joining_Number           ; Brahmi_Joining_Number
InSC; Cantillation_Mark               ; Cantillation_Mark
InSC; Consonant                       ; Consonant
InSC; Consonant_Dead                  ; Consonant_Dead
InSC; Consonant_Final                 ; Consonant_Final
InSC; Consonant_Head_Letter           ; Consonant_Head_Letter
InSC; Consonant_Initial_Postfixed     ; Consonant_Initial_Postfixed
InSC; Consonant_Killer                ; Consonant_Killer
InSC; Consonant_Medial                ; Consonant_Medial
InSC; Consonant_Placeholder           ; Consonant_Placeholder
InSC; Consonant_Preceding_Repha       ; Consonant_Preceding_Repha
InSC; Consonant_Prefixed              ; Consonant_Prefixed
InSC; Consonant_Subjoined             ; Consonant_Subjoined
InSC; Consonant_Succeeding_Repha      ; Consonant_Succeeding_Repha
InSC; Consonant_With_Stacker          ; Consonant_With_Stacker
InSC; Gemination_Mark                 ; Gemination_Mark
InSC; Invisible_Stacker               ; Invisible_Stacker
InSC; Joiner                          ; Joiner
InSC; Modifying_Letter                ; Modifying_Letter
InSC; Non_Joiner                      ; Non_Joiner
InSC; Nukta                           ; Nukta
InSC; Number                          ; Number
InSC; Number_Joiner                   ; Number_Joiner
InSC; Other                           ; Other
InSC; Pure_Killer                     ; Pure_Killer
InSC; Register_Shifter                ; Register_Shifter
InSC; Syllable_Modifier               ; Syllable_Modifier
InSC; Tone_Letter                     ; Tone_Letter
InSC; Tone_Mark                       ; Tone_Mark
InSC; Virama                          ; Virama
InSC; Visarga                         ; Visarga
InSC; Vowel                           ; Vowel
InSC; Vowel_Dependent                 ; Vowel_Dependent
InSC; Vowel_Independent               ; Vowel_Independent

# Jamo_Short_Name (JSN)

JSN; A                                ; A
JSN; AE                               ; AE
JSN; B                                ; B
JSN; BB                               ; BB
JSN; BS                               ; BS
JSN; C                                ; C
JSN; D                                ; D
JSN; DD                               ; DD
JSN; E                                ; E
JSN; EO                               ; EO
JSN; EU                               ; EU
JSN; G                                ; G
JSN; GG                               ; GG
JSN; GS                               ; GS
JSN; H                                ; H
JSN; I                                ; I
JSN; J                                ; J
JSN; JJ                               ; JJ
JSN; K                                ; K
JSN; L                                ; L
JSN; LB                               ; LB
JSN; LG                               ; LG
JSN; LH                               ; LH
JSN; LM                               ; LM
JSN; LP                               ; LP
JSN; LS                               ; LS
JSN; LT                               ; LT
JSN; M                                ; M
JSN; N                                ; N
JSN; NG                               ; NG
JSN; NH                               ; NH
JSN; NJ                               ; NJ
JSN; O                                ; O
JSN; OE                               ; OE
JSN; P                                ; P
JSN; R                                ; R
JSN; S                                ; S
JSN; SS                               ; SS
JSN; T                                ; T
JSN; U                                ; U
JSN; WA                               ; WA
JSN; WAE                              ; WAE
JSN; WE                               ; WE
JSN; WEO                              ; WEO
JSN; WI                               ; WI
JSN; YA                               ; YA
JSN; YAE                              ; YAE
JSN; YE                               ; YE
JSN; YEO                              ; YEO
JSN; YI                               ; YI
JSN; YO                               ; YO
JSN; YU                               ; YU
# @missing: 0000..10FFFF; Jamo_Short_Name; <none>

# Join_Control (Join_C)

Join_C; N                             ; No                               ; F                                ; False
Join_C; Y                             ; Yes                              ; T                                ; True

# Joining_Group (jg)

jg ; African_Feh                      ; African_Feh
jg ; African_Noon                     ; African_Noon
jg ; African_Qaf                      ; African_Qaf
jg ; Ain                              ; Ain
jg ; Alaph                            ; Alaph
jg ; Alef                             ; Alef
jg ; Beh                              ; Beh
jg ; Beth                             ; Beth
jg ; Burushaski_Yeh_Barree            ; Burushaski_Yeh_Barree
jg ; Dal                              ; Dal
jg ; Dalath_Rish                      ; Dalath_Rish
jg ; E                                ; E
jg ; Farsi_Yeh                        ; Farsi_Yeh
jg ; Fe                               ; Fe
jg ; Feh                              ; Feh
jg ; Final_Semkath                    ; Final_Semkath
jg ; Gaf                              ; Gaf
jg ; Gamal                            ; Gamal
jg ; Hah                              ; Hah
jg ; Hanifi_Rohingya_Kinna_Ya         ; Hanifi_Rohingya_Kinna_Ya
jg ; Hanifi_Rohingya_Pa               ; Hanifi_Rohingya_Pa
jg ; He                               ; He
jg ; Heh                              ; Heh
jg ; Heh_Goal                         ; Heh_Goal
jg ; Heth                             ; Heth
jg ; Kaf                              ; Kaf
jg ; Kaph                             ; Kaph
jg ; Khaph                            ; Khaph
jg ; Knotted_Heh                      ; Knotted_Heh
jg ; Lam                              ; Lam
jg ; Lamadh                           ; Lamadh
jg ; Malayalam_Bha                    ; Malayalam_Bha
jg ; Malayalam_Ja                     ; Malayalam_Ja
jg ; Malayalam_Lla                    ; Malayalam_Lla
jg ; Malayalam_Llla                   ; Malayalam_Llla
jg ; Malayalam_Nga                    ; Malayalam_Nga
jg ; Malayalam_Nna                    ; Malayalam_Nna
jg ; Malayalam_Nnna                   ; Malayalam_Nnna
jg ; Malayalam_Nya                    ; Malayalam_Nya
jg ; Malayalam_Ra                     ; Malayalam_Ra
jg ; Malayalam_Ssa                    ; Malayalam_Ssa
jg ; Malayalam_Tta                    ; Malayalam_Tta
jg ; Manichaean_Aleph                 ; Manichaean_Aleph
jg ; Manichaean_Ayin                  ; Manichaean_Ayin
jg ; Manichaean_Beth                  ; Manichaean_Beth
jg ; Manichaean_Daleth                ; Manichaean_Daleth
jg ; Manichaean_Dhamedh               ; Manichaean_Dhamedh
jg ; Manichaean_Five                  ; Manichaean_Five
jg ; Manichaean_Gimel                 ; Manichaean_Gimel
jg ; Manichaean_Heth                  ; Manichaean_Heth
jg ; Manichaean_Hundred               ; Manichaean_Hundred
jg ; Manichaean_Kaph                  ; Manichaean_Kaph
jg ; Manichaean_Lamedh                ; Manichaean_Lamedh
jg ; Manichaean_Mem                   ; Manichaean_Mem
jg ; Manichaean_Nun                   ; Manichaean_Nun
jg ; Manichaean_One                   ; Manichaean_One
jg ; Manichaean_Pe                    ; Manichaean_Pe
jg ; Manichaean_Qoph                  ; Manichaean_Qoph
jg ; Manichaean_Resh                  ; Manichaean_Resh
jg ; Manichaean_Sadhe                 ; Manichaean_Sadhe
jg ; Manichaean_Samekh                ; Manichaean_Samekh
jg ; Manichaean_Taw                   ; Manichaean_Taw
jg ; Manichaean_Ten                   ; Manichaean_Ten
jg ; Manichaean_Teth                  ; Manichaean_Teth
jg ; Manichaean_Thamedh               ; Manichaean_Thamedh
jg ; Manichaean_Twenty                ; Manichaean_Twenty
jg ; Manichaean_Waw                   ; Manichaean_Waw
jg ; Manichaean_Yodh                  ; Manichaean_Yodh
jg ; Manichaean_Zayin                 ; Manichaean_Zayin
jg ; Meem                             ; Meem
jg ; Mim                              ; Mim
jg ; No_Joining_Group                 ; No_Joining_Group
jg ; Noon                             ; Noon
jg ; Nun                              ; Nun
jg ; Nya                              ; Nya
jg ; Pe                               ; Pe
jg ; Qaf                              ; Qaf
jg ; Qaph                             ; Qaph
jg ; Reh                              ; Reh
jg ; Reversed_Pe                      ; Reversed_Pe
jg ; Rohingya_Yeh                     ; Rohingya_Yeh
jg ; Sad                              ; Sad
jg ; Sadhe                            ; Sadhe
jg ; Seen                             ; Seen
jg ; Semkath                          ; Semkath
jg ; Shin                             ; Shin
jg ; Straight_Waw                     ; Straight_Waw
jg ; Swash_Kaf                        ; Swash_Kaf
jg ; Syriac_Waw                       ; Syriac_Waw
jg ; Tah                              ; Tah
jg ; Taw                              ; Taw
jg ; Teh_Marbuta                      ; Teh_Marbuta
jg ; Teh_Marbuta_Goal                 ; Hamza_On_Heh_Goal
jg ; Teth                             ; Teth
jg ; Thin_Yeh                         ; Thin_Yeh
jg ; Vertical_Tail                    ; Vertical_Tail
jg ; Waw                              ; Waw
jg ; Yeh                              ; Yeh
jg ; Yeh_Barree                       ; Yeh_Barree
jg ; Yeh_With_Tail                    ; Yeh_With_Tail
jg ; Yudh                             ; Yudh
jg ; Yudh_He                          ; Yudh_He
jg ; Zain                             ; Zain
jg ; Zhain                            ; Zhain

# Joining_Type (jt)

jt ; C                                ; Join_Causing
jt ; D                                ; Dual_Joining
jt ; L                                ; Left_Joining
jt ; R                                ; Right_Joining
jt ; T                                ; Transparent
jt ; U                                ; Non_Joining

# Line_Break (lb)

lb ; AI                               ; Ambiguous
lb ; AL                               ; Alphabetic
lb ; B2                               ; Break_Both
lb ; BA                               ; Break_After
lb ; BB                               ; Break_Before
lb ; BK                               ; Mandatory_Break
lb ; CB                               ; Contingent_Break
lb ; CJ                               ; Conditional_Japanese_Starter
lb ; CL                               ; Close_Punctuation
lb ; CM                               ; Combining_Mark
lb ; CP                               ; Close_Parenthesis
lb ; CR                               ; Carriage_Return
lb ; EB                               ; E_Base
lb ; EM                               ; E_Modifier
lb ; EX                               ; Exclamation
lb ; GL                               ; Glue
lb ; H2                               ; H2
lb ; H3                               ; H3
lb ; HL                               ; Hebrew_Letter
lb ; HY                               ; Hyphen
lb ; ID                               ; Ideographic
lb ; IN                               ; Inseparable                      ; Inseperable
lb ; IS                               ; Infix_Numeric
lb ; JL                               ; JL
lb ; JT                               ; JT
lb ; JV                               ; JV
lb ; LF                               ; Line_Feed
lb ; NL                               ; Next_Line
lb ; NS                               ; Nonstarter
lb ; NU                               ; Numeric
lb ; OP                               ; Open_Punctuation
lb ; PO                               ; Postfix_Numeric
lb ; PR                               ; Prefix_Numeric
lb ; QU                               ; Quotation
lb ; RI                               ; Regional_Indicator
lb ; SA                               ; Complex_Context
lb ; SG                               ; Surrogate
lb ; SP                               ; Space
lb ; SY                               ; Break_Symbols
lb ; WJ                               ; Word_Joiner
lb ; XX                               ; Unknown
lb ; ZW                               ; ZWSpace
lb ; ZWJ                              ; ZWJ

# Logical_Order_Exception (LOE)

LOE; N                                ; No                               ; F                                ; False
LOE; Y                                ; Yes                              ; T                                ; True

# Lowercase (Lower)

Lower; N                              ; No                               ; F                                ; False
Lower; Y                              ; Yes                              ; T                                ; True

# Lowercase_Mapping (lc)

# @missing: 0000..10FFFF; Lowercase_Mapping; <code point>

# Math (Math)

Math; N                               ; No                               ; F                                ; False
Math; Y                               ; Yes                              ; T                                ; True

# NFC_Quick_Check (NFC_QC)

NFC_QC; M                             ; Maybe
NFC_QC; N                             ; No
NFC_QC; Y                             ; Yes

# NFD_Quick_Check (NFD_QC)

NFD_QC; N                             ; No
NFD_QC; Y                             ; Yes

# NFKC_Casefold (NFKC_CF)

# @missing: 0000..10FFFF; NFKC_Casefold; <code point>

# NFKC_Quick_Check (NFKC_QC)

NFKC_QC; M                            ; Maybe
NFKC_QC; N                            ; No
NFKC_QC; Y                            ; Yes

# NFKD_Quick_Check (NFKD_QC)

NFKD_QC; N                            ; No
NFKD_QC; Y                            ; Yes

# Name (na)

# @missing: 0000..10FFFF; Name; <none>

# Name_Alias (Name_Alias)

# @missing: 0000..10FFFF; Name_Alias; <none>

# Noncharacter_Code_Point (NChar)

NChar; N                              ; No                               ; F                                ; False
NChar; Y                              ; Yes                              ; T                                ; True

# Numeric_Type (nt)

nt ; De                               ; Decimal
nt ; Di                               ; Digit
nt ; None                             ; None
nt ; Nu                               ; Numeric

# Numeric_Value (nv)

# @missing: 0000..10FFFF; Numeric_Value; NaN

# Other_Alphabetic (OAlpha)

OAlpha; N                             ; No                               ; F                                ; False
OAlpha; Y                             ; Yes                              ; T                                ; True

# Other_Default_Ignorable_Code_Point (ODI)

ODI; N                                ; No                               ; F                                ; False
ODI; Y                                ; Yes                              ; T                                ; True

# Other_Grapheme_Extend (OGr_Ext)

OGr_Ext; N                            ; No                               ; F                                ; False
OGr_Ext; Y                            ; Yes                              ; T                                ; True

# Other_ID_Continue (OIDC)

OIDC; N                               ; No                               ; F                                ; False
OIDC; Y                               ; Yes                              ; T                                ; True

# Other_ID_Start (OIDS)

OIDS; N                               ; No                               ; F                                ; False
OIDS; Y                               ; Yes                              ; T                                ; True

# Other_Lowercase (OLower)

OLower; N                             ; No                               ; F                                ; False
OLower; Y                             ; Yes                              ; T                                ; True

# Other_Math (OMath)

OMath; N                              ; No                               ; F                                ; False
OMath; Y                              ; Yes                              ; T                                ; True

# Other_Uppercase (OUpper)

OUpper; N                             ; No                               ; F                                ; False
OUpper; Y                             ; Yes                              ; T                                ; True

# Pattern_Syntax (Pat_Syn)

Pat_Syn; N                            ; No                               ; F                                ; False
Pat_Syn; Y                            ; Yes                              ; T                                ; True

# Pattern_White_Space (Pat_WS)

Pat_WS; N                             ; No                               ; F                                ; False
Pat_WS; Y                             ; Yes                              ; T                                ; True

# Prepended_Concatenation_Mark (PCM)

PCM; N                                ; No                               ; F                                ; False
PCM; Y                                ; Yes                              ; T                                ; True

# Quotation_Mark (QMark)

QMark; N                              ; No                               ; F                                ; False
QMark; Y                              ; Yes                              ; T                                ; True

# Radical (Radical)

Radical; N                            ; No                               ; F                                ; False
Radical; Y                            ; Yes                              ; T                                ; True

# Regional_Indicator (RI)

RI ; N                                ; No                               ; F                                ; False
RI ; Y                                ; Yes                              ; T                                ; True

# Script (sc)

sc ; Adlm                             ; Adlam
sc ; Aghb                             ; Caucasian_Albanian
sc ; Ahom                             ; Ahom
sc ; Arab                             ; Arabic
sc ; Armi                             ; Imperial_Aramaic
sc ; Armn                             ; Armenian
sc ; Avst                             ; Avestan
sc ; Bali                             ; Balinese
sc ; Bamu                             ; Bamum
sc ; Bass                             ; Bassa_Vah
sc ; Batk                             ; Batak
sc ; Beng                             ; Bengali
sc ; Bhks                             ; Bhaiksuki
sc ; Bopo                             ; Bopomofo
sc ; Brah                             ; Brahmi
sc ; Brai                             ; Braille
sc ; Bugi                             ; Buginese
sc ; Buhd                             ; Buhid
sc ; Cakm                             ; Chakma
sc ; Cans                             ; Canadian_Aboriginal
sc ; Cari                             ; Carian
sc ; Cham                             ; Cham
sc ; Cher                             ; Cherokee
sc ; Chrs                             ; Chorasmian
sc ; Copt                             ; Coptic                           ; Qaac
sc ; Cpmn                             ; Cypro_Minoan
sc ; Cprt                             ; Cypriot
sc ; Cyrl                             ; Cyrillic
sc ; Deva                             ; Devanagari
sc ; Diak                             ; Dives_Akuru
sc ; Dogr                             ; Dogra
sc ; Dsrt                             ; Deseret
sc ; Dupl                             ; Duployan
sc ; Egyp                             ; Egyptian_Hieroglyphs
sc ; Elba                             ; Elbasan
sc ; Elym                             ; Elymaic
sc ; Ethi                             ; Ethiopic
sc ; Geor                             ; Georgian
sc ; Glag                             ; Glagolitic
sc ; Gong                             ; Gunjala_Gondi
sc ; Gonm                             ; Masaram_Gondi
sc ; Goth                             ; Gothic
sc ; Gran                             ; Grantha
sc ; Grek                             ; Greek
sc ; Gujr                             ; Gujarati
sc ; Guru                             ; Gurmukhi
sc ; Hang                             ; Hangul
sc ; Hani                             ; Han
sc ; Hano                             ; Hanunoo
sc ; Hatr                             ; Hatran
sc ; Hebr                             ; Hebrew
sc ; Hira                             ; Hiragana
sc ; Hluw                             ; Anatolian_Hieroglyphs
sc ; Hmng                             ; Pahawh_Hmong
sc ; Hmnp                             ; Nyiakeng_Puachue_Hmong
sc ; Hrkt                             ; Katakana_Or_Hiragana
sc ; Hung                             ; Old_Hungarian
sc ; Ital                             ; Old_Italic
sc ; Java                             ; Javanese
sc ; Kali                             ; Kayah_Li
sc ; Kana                             ; Katakana
sc ; Khar                             ; Kharoshthi
sc ; Khmr                             ; Khmer
sc ; Khoj                             ; Khojki
sc ; Kits                             ; Khitan_Small_Script
sc ; Knda                             ; Kannada
sc ; Kthi                             ; Kaithi
sc ; Lana                             ; Tai_Tham
sc ; Laoo                             ; Lao
sc ; Latn                             ; Latin
sc ; Lepc                             ; Lepcha
sc ; Limb                             ; Limbu
sc ; Lina                             ; Linear_A
sc ; Linb                             ; Linear_B
sc ; Lisu                             ; Lisu
sc ; Lyci                             ; Lycian
sc ; Lydi                             ; Lydian
sc ; Mahj                             ; Mahajani
sc ; Maka                             ; Makasar
sc ; Mand                             ; Mandaic
sc ; Mani                             ; Manichaean
sc ; Marc                             ; Marchen
sc ; Medf                             ; Medefaidrin
sc ; Mend                             ; Mende_Kikakui
sc ; Merc                             ; Meroitic_Cursive
sc ; Mero                             ; Meroitic_Hieroglyphs
sc ; Mlym                             ; Malayalam
sc ; Modi                             ; Modi
sc ; Mong                             ; Mongolian
sc ; Mroo                             ; Mro
sc ; Mtei                             ; Meetei_Mayek
sc ; Mult                             ; Multani
sc ; Mymr                             ; Myanmar
sc ; Nand                             ; Nandinagari
sc ; Narb                             ; Old_North_Arabian
sc ; Nbat                             ; Nabataean
sc ; Newa                             ; Newa
sc ; Nkoo                             ; Nko
sc ; Nshu                             ; Nushu
sc ; Ogam                             ; Ogham
sc ; Olck                             ; Ol_Chiki
sc ; Orkh                             ; Old_Turkic
sc ; Orya                             ; Oriya
sc ; Osge                             ; Osage
sc ; Osma                             ; Osmanya
sc ; Ougr                             ; Old_Uyghur
sc ; Palm                             ; Palmyrene
sc ; Pauc                             ; Pau_Cin_Hau
sc ; Perm                             ; Old_Permic
sc ; Phag                             ; Phags_Pa
sc ; Phli                             ; Inscriptional_Pahlavi
sc ; Phlp                             ; Psalter_Pahlavi
sc ; Phnx                             ; Phoenician
sc ; Plrd                             ; Miao
sc ; Prti                             ; Inscriptional_Parthian
sc ; Rjng                             ; Rejang
sc ; Rohg                             ; Hanifi_Rohingya
sc ; Runr                             ; Runic
sc ; Samr                             ; Samaritan
sc ; Sarb                             ; Old_South_Arabian
sc ; Saur                             ; Saurashtra
sc ; Sgnw                             ; SignWriting
sc ; Shaw                             ; Shavian
sc ; Shrd                             ; Sharada
sc ; Sidd                             ; Siddham
sc ; Sind                             ; Khudawadi
sc ; Sinh                             ; Sinhala
sc ; Sogd                             ; Sogdian
sc ; Sogo                             ; Old_Sogdian
sc ; Sora                             ; Sora_Sompeng
sc ; Soyo                             ; Soyombo
sc ; Sund                             ; Sundanese
sc ; Sylo                             ; Syloti_Nagri
sc ; Syrc                             ; Syriac
sc ; Tagb                             ; Tagbanwa
sc ; Takr                             ; Takri
sc ; Tale                             ; Tai_Le
sc ; Talu                             ; New_Tai_Lue
sc ; Taml                             ; Tamil
sc ; Tang                             ; Tangut
sc ; Tavt                             ; Tai_Viet
sc ; Telu                             ; Telugu
sc ; Tfng                             ; Tifinagh
sc ; Tglg                             ; Tagalog
sc ; Thaa                             ; Thaana
sc ; Thai                             ; Thai
sc ; Tibt                             ; Tibetan
sc ; Tirh                             ; Tirhuta
sc ; Tnsa                             ; Tangsa
sc ; Toto                             ; Toto
sc ; Ugar                             ; Ugaritic
sc ; Vaii                             ; Vai
sc ; Vith                             ; Vithkuqi
sc ; Wara                             ; Warang_Citi
sc ; Wcho                             ; Wancho
sc ; Xpeo                             ; Old_Persian
sc ; Xsux                             ; Cuneiform
sc ; Yezi                             ; Yezidi
sc ; Yiii                             ; Yi
sc ; Zanb                             ; Zanabazar_Square
sc ; Zinh                             ; Inherited                        ; Qaai
sc ; Zyyy                             ; Common
sc ; Zzzz                             ; Unknown

# Script_Extensions (scx)

# @missing: 0000..10FFFF; Script_Extensions; <script>

# Sentence_Break (SB)

SB ; AT                               ; ATerm
SB ; CL                               ; Close
SB ; CR                               ; CR
SB ; EX                               ; Extend
SB ; FO                               ; Format
SB ; LE                               ; OLetter
SB ; LF                               ; LF
SB ; LO                               ; Lower
SB ; NU                               ; Numeric
SB ; SC                               ; SContinue
SB ; SE                               ; Sep
SB ; SP                               ; Sp
SB ; ST                               ; STerm
SB ; UP                               ; Upper
SB ; XX                               ; Other

# Sentence_Terminal (STerm)

STerm; N                              ; No                               ; F                                ; False
STerm; Y                              ; Yes                              ; T                                ; True

# Simple_Case_Folding (scf)

# @missing: 0000..10FFFF; Simple_Case_Folding; <code point>

# Simple_Lowercase_Mapping (slc)

# @missing: 0000..10FFFF; Simple_Lowercase_Mapping; <code point>

# Simple_Titlecase_Mapping (stc)

# @missing: 0000..10FFFF; Simple_Titlecase_Mapping; <code point>

# Simple_Uppercase_Mapping (suc)

# @missing: 0000..10FFFF; Simple_Uppercase_Mapping; <code point>

# Soft_Dotted (SD)

SD ; N                                ; No                               ; F                                ; False
SD ; Y                                ; Yes                              ; T                                ; True

# Terminal_Punctuation (Term)

Term; N                               ; No                               ; F                                ; False
Term; Y                               ; Yes                              ; T                                ; True

# Titlecase_Mapping (tc)

# @missing: 0000..10FFFF; Titlecase_Mapping; <code point>

# Unicode_1_Name (na1)

# @missing: 0000..10FFFF; Unicode_1_Name; <none>

# Unified_Ideograph (UIdeo)

UIdeo; N                              ; No                               ; F                                ; False
UIdeo; Y                              ; Yes                              ; T                                ; True

# Uppercase (Upper)

Upper; N                              ; No                               ; F                                ; False
Upper; Y                              ; Yes                              ; T                                ; True

# Uppercase_Mapping (uc)

# @missing: 0000..10FFFF; Uppercase_Mapping; <code point>

# Variation_Selector (VS)

VS ; N                                ; No                               ; F                                ; False
VS ; Y                                ; Yes                              ; T                                ; True

# Vertical_Orientation (vo)

vo ; R                                ; Rotated
vo ; Tr                               ; Transformed_Rotated
vo ; Tu                               ; Transformed_Upright
vo ; U                                ; Upright

# White_Space (WSpace)

WSpace; N                             ; No                               ; F                                ; False
WSpace; Y                             ; Yes                              ; T                                ; True

# Word_Break (WB)

WB ; CR                               ; CR
WB ; DQ                               ; Double_Quote
WB ; EB                               ; E_Base
WB ; EBG                              ; E_Base_GAZ
WB ; EM                               ; E_Modifier
WB ; EX                               ; ExtendNumLet
WB ; Extend                           ; Extend
WB ; FO                               ; Format
WB ; GAZ                              ; Glue_After_Zwj
WB ; HL                               ; Hebrew_Letter
WB ; KA                               ; Katakana
WB ; LE                               ; ALetter
WB ; LF                               ; LF
WB ; MB                               ; MidNumLet
WB ; ML                               ; MidLetter
WB ; MN                               ; MidNum
WB ; NL                               ; Newline
WB ; NU                               ; Numeric
WB ; RI                               ; Regional_Indicator
WB ; SQ                               ; Single_Quote
WB ; WSegSpace                        ; WSegSpace
WB ; XX                               ; Other
WB ; ZWJ                              ; ZWJ

# XID_Continue (XIDC)

XIDC; N                               ; No                               ; F                                ; False
XIDC; Y                               ; Yes                              ; T                                ; True

# XID_Start (XIDS)

XIDS; N                               ; No                               ; F                                ; False
XIDS; Y                               ; Yes                              ; T                                ; True

# cjkAccountingNumeric (cjkAccountingNumeric)

# @missing: 0000..10FFFF; cjkAccountingNumeric; NaN

# cjkCompatibilityVariant (cjkCompatibilityVariant)

# @missing: 0000..10FFFF; cjkCompatibilityVariant; <code point>

# cjkIICore (cjkIICore)

# @missing: 0000..10FFFF; cjkIICore; <none>

# cjkIRG_GSource (cjkIRG_GSource)

# @missing: 0000..10FFFF; cjkIRG_GSource; <none>

# cjkIRG_HSource (cjkIRG_HSource)

# @missing: 0000..10FFFF; cjkIRG_HSource; <none>

# cjkIRG_JSource (cjkIRG_JSource)

# @missing: 0000..10FFFF; cjkIRG_JSource; <none>

# cjkIRG_KPSource (cjkIRG_KPSource)

# @missing: 0000..10FFFF; cjkIRG_KPSource; <none>

# cjkIRG_KSource (cjkIRG_KSource)

# @missing: 0000..10FFFF; cjkIRG_KSource; <none>

# cjkIRG_MSource (cjkIRG_MSource)

# @missing: 0000..10FFFF; cjkIRG_MSource; <none>

# cjkIRG_SSource (cjkIRG_SSource)

# @missing: 0000..10FFFF; cjkIRG_SSource; <none>

# cjkIRG_TSource (cjkIRG_TSource)

# @missing: 0000..10FFFF; cjkIRG_TSource; <none>

# cjkIRG_UKSource (cjkIRG_UKSource)

# @missing: 0000..10FFFF; cjkIRG_UKSource; <none>

# cjkIRG_USource (cjkIRG_USource)

# @missing: 0000..10FFFF; cjkIRG_USource; <none>

# cjkIRG_VSource (cjkIRG_VSource)

# @missing: 0000..10FFFF; cjkIRG_VSource; <none>

# cjkOtherNumeric (cjkOtherNumeric)

# @missing: 0000..10FFFF; cjkOtherNumeric; NaN

# cjkPrimaryNumeric (cjkPrimaryNumeric)

# @missing: 0000..10FFFF; cjkPrimaryNumeric; NaN

# cjkRSUnicode (cjkRSUnicode)

# @missing: 0000..10FFFF; cjkRSUnicode; <none>

# EOF
"""
categoryNames = {}
bidiNames = {}
eastAsianWidthNames = {}
def preloadData():
    global categoryNames
    for line in PropertyValueAliases_STRING.splitlines():
        if line.startswith('bc ;'):
            bits = line.split(';')
            bidi_abbreviation = bits[1].strip()
            bidi_name = bits[2].strip().split(' ')[0]
            bidiNames[bidi_abbreviation] = bidi_name
        elif line.startswith('ea ;'):
            bits = line.split(';')
            ea_abbreviation = bits[1].strip()
            ea_name = bits[2].strip().split(' ')[0]
            eastAsianWidthNames[ea_abbreviation] = ea_name
        elif line.startswith('gc ;'):
            bits = line.split(';')
            category_abbreviation = bits[1].strip()
            category_name = bits[2].strip().split(' ')[0]
            categoryNames[category_abbreviation] = category_name


# From https://github.com/neuront/pyunicodeblock/blob/master/unicodeblock/blocks.py
_BLOCK_STARTS, _BLOCK_NAMES = (lambda x: (
    [i[0] for i in x], [i[1] for i in x]))([
    (0x0000, None),
    (0x0020, 'SPACE'),
    (0x0021, 'BASIC_PUNCTUATION'),
    (0x0030, 'DIGIT'),
    (0x003A, 'BASIC_PUNCTUATION'),
    (0x0041, 'BASIC_LATIN'),
    (0x005B, 'BASIC_PUNCTUATION'),
    (0x0061, 'BASIC_LATIN'),
    (0x007B, 'BASIC_PUNCTUATION'),
    (0x007f, None),
    (0x00A0, 'LATIN_1_SUPPLEMENT'),
    (0x00C0, 'LATIN_EXTENDED_LETTER'),
    (0x0100, 'LATIN_EXTENDED_A'),
    (0x0180, 'LATIN_EXTENDED_B'),
    (0x0250, 'IPA_EXTENSIONS'),
    (0x02B0, 'SPACING_MODIFIER_LETTERS'),
    (0x0300, 'COMBINING_DIACRITICAL_MARKS'),
    (0x0370, 'GREEK'),
    (0x0400, 'CYRILLIC'),
    (0x0500, 'CYRILLIC_SUPPLEMENTARY'),
    (0x0530, 'ARMENIAN'),
    (0x0590, 'HEBREW'),
    (0x0600, 'ARABIC'),
    (0x0700, 'SYRIAC'),
    (0x0750, 'ARABIC_SUPPLEMENT'),
    (0x0780, 'THAANA'),
    (0x07C0, 'NKO'),
    (0x0800, 'SAMARITAN'),
    (0x0840, 'MANDAIC'),
    (0x0860, None),
    (0x0900, 'DEVANAGARI'),
    (0x0980, 'BENGALI'),
    (0x0A00, 'GURMUKHI'),
    (0x0A80, 'GUJARATI'),
    (0x0B00, 'ORIYA'),
    (0x0B80, 'TAMIL'),
    (0x0C00, 'TELUGU'),
    (0x0C80, 'KANNADA'),
    (0x0D00, 'MALAYALAM'),
    (0x0D80, 'SINHALA'),
    (0x0E00, 'THAI'),
    (0x0E80, 'LAO'),
    (0x0F00, 'TIBETAN'),
    (0x1000, 'MYANMAR'),
    (0x10A0, 'GEORGIAN'),
    (0x1100, 'HANGUL_JAMO'),
    (0x1200, 'ETHIOPIC'),
    (0x1380, 'ETHIOPIC_SUPPLEMENT'),
    (0x13A0, 'CHEROKEE'),
    (0x1400, 'UNIFIED_CANADIAN_ABORIGINAL_SYLLABICS'),
    (0x1680, 'OGHAM'),
    (0x16A0, 'RUNIC'),
    (0x1700, 'TAGALOG'),
    (0x1720, 'HANUNOO'),
    (0x1740, 'BUHID'),
    (0x1760, 'TAGBANWA'),
    (0x1780, 'KHMER'),
    (0x1800, 'MONGOLIAN'),
    (0x18B0, 'UNIFIED_CANADIAN_ABORIGINAL_SYLLABICS_EXTENDED'),
    (0x1900, 'LIMBU'),
    (0x1950, 'TAI_LE'),
    (0x1980, 'NEW_TAI_LUE'),
    (0x19E0, 'KHMER_SYMBOLS'),
    (0x1A00, 'BUGINESE'),
    (0x1A20, 'TAI_THAM'),
    (0x1AB0, None),
    (0x1B00, 'BALINESE'),
    (0x1B80, 'SUNDANESE'),
    (0x1BC0, 'BATAK'),
    (0x1C00, 'LEPCHA'),
    (0x1C50, 'OL_CHIKI'),
    (0x1C80, None),
    (0x1CD0, 'VEDIC_EXTENSIONS'),
    (0x1D00, 'PHONETIC_EXTENSIONS'),
    (0x1D80, 'PHONETIC_EXTENSIONS_SUPPLEMENT'),
    (0x1DC0, 'COMBINING_DIACRITICAL_MARKS_SUPPLEMENT'),
    (0x1E00, 'LATIN_EXTENDED_ADDITIONAL'),
    (0x1F00, 'GREEK_EXTENDED'),
    (0x2000, 'GENERAL_PUNCTUATION'),
    (0x2070, 'SUPERSCRIPTS_AND_SUBSCRIPTS'),
    (0x20A0, 'CURRENCY_SYMBOLS'),
    (0x20D0, 'COMBINING_MARKS_FOR_SYMBOLS'),
    (0x2100, 'LETTERLIKE_SYMBOLS'),
    (0x2150, 'NUMBER_FORMS'),
    (0x2190, 'ARROWS'),
    (0x2200, 'MATHEMATICAL_OPERATORS'),
    (0x2300, 'MISCELLANEOUS_TECHNICAL'),
    (0x2400, 'CONTROL_PICTURES'),
    (0x2440, 'OPTICAL_CHARACTER_RECOGNITION'),
    (0x2460, 'ENCLOSED_ALPHANUMERICS'),
    (0x2500, 'BOX_DRAWING'),
    (0x2580, 'BLOCK_ELEMENTS'),
    (0x25A0, 'GEOMETRIC_SHAPES'),
    (0x2600, 'MISCELLANEOUS_SYMBOLS'),
    (0x2700, 'DINGBATS'),
    (0x27C0, 'MISCELLANEOUS_MATHEMATICAL_SYMBOLS_A'),
    (0x27F0, 'SUPPLEMENTAL_ARROWS_A'),
    (0x2800, 'BRAILLE_PATTERNS'),
    (0x2900, 'SUPPLEMENTAL_ARROWS_B'),
    (0x2980, 'MISCELLANEOUS_MATHEMATICAL_SYMBOLS_B'),
    (0x2A00, 'SUPPLEMENTAL_MATHEMATICAL_OPERATORS'),
    (0x2B00, 'MISCELLANEOUS_SYMBOLS_AND_ARROWS'),
    (0x2C00, 'GLAGOLITIC'),
    (0x2C60, 'LATIN_EXTENDED_C'),
    (0x2C80, 'COPTIC'),
    (0x2D00, 'GEORGIAN_SUPPLEMENT'),
    (0x2D30, 'TIFINAGH'),
    (0x2D80, 'ETHIOPIC_EXTENDED'),
    (0x2DE0, 'CYRILLIC_EXTENDED_A'),
    (0x2E00, 'SUPPLEMENTAL_PUNCTUATION'),
    (0x2E80, 'CJK_RADICALS_SUPPLEMENT'),
    (0x2F00, 'KANGXI_RADICALS'),
    (0x2FE0, None),
    (0x2FF0, 'IDEOGRAPHIC_DESCRIPTION_CHARACTERS'),
    (0x3000, 'CJK_SYMBOLS_AND_PUNCTUATION'),
    (0x3041, 'HIRAGANA'),
    (0x3097, 'CJK_SYMBOLS_AND_PUNCTUATION'),
    (0x30A1, 'KATAKANA'),
    (0x30FB, 'CJK_SYMBOLS_AND_PUNCTUATION'),
    (0x30FC, 'KATAKANA'),
    (0x3100, 'BOPOMOFO'),
    (0x3130, 'HANGUL_COMPATIBILITY_JAMO'),
    (0x3190, 'KANBUN'),
    (0x31A0, 'BOPOMOFO_EXTENDED'),
    (0x31C0, 'CJK_STROKES'),
    (0x31F0, 'KATAKANA_PHONETIC_EXTENSIONS'),
    (0x3200, 'ENCLOSED_CJK_LETTERS_AND_MONTHS'),
    (0x3300, 'CJK_COMPATIBILITY'),
    (0x3400, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_A'),
    (0x4DC0, 'YIJING_HEXAGRAM_SYMBOLS'),
    (0x4E00, 'CJK_UNIFIED_IDEOGRAPHS'),
    (0xA000, 'YI_SYLLABLES'),
    (0xA490, 'YI_RADICALS'),
    (0xA4D0, 'LISU'),
    (0xA500, 'VAI'),
    (0xA640, 'CYRILLIC_EXTENDED_B'),
    (0xA6A0, 'BAMUM'),
    (0xA700, 'MODIFIER_TONE_LETTERS'),
    (0xA720, 'LATIN_EXTENDED_D'),
    (0xA800, 'SYLOTI_NAGRI'),
    (0xA830, 'COMMON_INDIC_NUMBER_FORMS'),
    (0xA840, 'PHAGS_PA'),
    (0xA880, 'SAURASHTRA'),
    (0xA8E0, 'DEVANAGARI_EXTENDED'),
    (0xA900, 'KAYAH_LI'),
    (0xA930, 'REJANG'),
    (0xA960, 'HANGUL_JAMO_EXTENDED_A'),
    (0xA980, 'JAVANESE'),
    (0xA9E0, None),
    (0xAA00, 'CHAM'),
    (0xAA60, 'MYANMAR_EXTENDED_A'),
    (0xAA80, 'TAI_VIET'),
    (0xAAE0, None),
    (0xAB00, 'ETHIOPIC_EXTENDED_A'),
    (0xAB30, None),
    (0xABC0, 'MEETEI_MAYEK'),
    (0xAC00, 'HANGUL_SYLLABLES'),
    (0xD7B0, 'HANGUL_JAMO_EXTENDED_B'),
    (0xD800, 'HIGH_SURROGATES'),
    (0xDB80, 'HIGH_PRIVATE_USE_SURROGATES'),
    (0xDC00, 'LOW_SURROGATES'),
    (0xE000, 'PRIVATE_USE_AREA'),
    (0xF900, 'CJK_COMPATIBILITY_IDEOGRAPHS'),
    (0xFB00, 'ALPHABETIC_PRESENTATION_FORMS'),
    (0xFB50, 'ARABIC_PRESENTATION_FORMS_A'),
    (0xFE00, 'VARIATION_SELECTORS'),
    (0xFE10, 'VERTICAL_FORMS'),
    (0xFE20, 'COMBINING_HALF_MARKS'),
    (0xFE30, 'CJK_COMPATIBILITY_FORMS'),
    (0xFE50, 'SMALL_FORM_VARIANTS'),
    (0xFE70, 'ARABIC_PRESENTATION_FORMS_B'),
    (0xFF00, 'HALFWIDTH_AND_FULLWIDTH_FORMS'),
    (0xFF10, 'FULLWIDTH_DIGIT'),
    (0xFF1A, 'HALFWIDTH_AND_FULLWIDTH_FORMS'),
    (0xFF21, 'FULLWIDTH_LATIN'),
    (0xFF3B, 'HALFWIDTH_AND_FULLWIDTH_FORMS'),
    (0xFF41, 'FULLWIDTH_LATIN'),
    (0xFF5B, 'HALFWIDTH_AND_FULLWIDTH_FORMS'),
    (0xFFF0, 'SPECIALS'),

    (0x10000, 'LINEAR_B_SYLLABARY'),
    (0x10080, 'LINEAR_B_IDEOGRAMS'),
    (0x10100, 'AEGEAN_NUMBERS'),
    (0x10140, 'ANCIENT_GREEK_NUMBERS'),
    (0x10190, 'ANCIENT_SYMBOLS'),
    (0x101D0, 'PHAISTOS_DISC'),
    (0x10200, None),
    (0x10280, 'LYCIAN'),
    (0x102A0, 'CARIAN'),
    (0x102E0, None),
    (0x10300, 'OLD_ITALIC'),
    (0x10330, 'GOTHIC'),
    (0x10350, None),
    (0x10380, 'UGARITIC'),
    (0x103A0, 'OLD_PERSIAN'),
    (0x103E0, None),
    (0x10400, 'DESERET'),
    (0x10450, 'SHAVIAN'),
    (0x10480, 'OSMANYA'),
    (0x104B0, None),
    (0x10800, 'CYPRIOT_SYLLABARY'),
    (0x10840, 'IMPERIAL_ARAMAIC'),
    (0x10860, None),
    (0x10900, 'PHOENICIAN'),
    (0x10920, 'LYDIAN'),
    (0x10940, None),
    (0x10A00, 'KHAROSHTHI'),
    (0x10A60, 'OLD_SOUTH_ARABIAN'),
    (0x10A80, None),
    (0x10B00, 'AVESTAN'),
    (0x10B40, 'INSCRIPTIONAL_PARTHIAN'),
    (0x10B60, 'INSCRIPTIONAL_PAHLAVI'),
    (0x10B80, None),
    (0x10C00, 'OLD_TURKIC'),
    (0x10C50, None),
    (0x10E60, 'RUMI_NUMERAL_SYMBOLS'),
    (0x10E80, None),
    (0x11000, 'BRAHMI'),
    (0x11080, 'KAITHI'),
    (0x110D0, None),
    (0x12000, 'CUNEIFORM'),
    (0x12400, 'CUNEIFORM_NUMBERS_AND_PUNCTUATION'),
    (0x12480, None),
    (0x13000, 'EGYPTIAN_HIEROGLYPHS'),
    (0x13430, None),
    (0x16800, 'BAMUM_SUPPLEMENT'),
    (0x16A40, None),
    (0x1B000, 'KANA_SUPPLEMENT'),
    (0x1B100, None),
    (0x1D000, 'BYZANTINE_MUSICAL_SYMBOLS'),
    (0x1D100, 'MUSICAL_SYMBOLS'),
    (0x1D200, 'ANCIENT_GREEK_MUSICAL_NOTATION'),
    (0x1D250, None),
    (0x1D300, 'TAI_XUAN_JING_SYMBOLS'),
    (0x1D360, 'COUNTING_ROD_NUMERALS'),
    (0x1D380, None),
    (0x1D400, 'MATHEMATICAL_ALPHANUMERIC_SYMBOLS'),
    (0x1D800, None),
    (0x1F000, 'MAHJONG_TILES'),
    (0x1F030, 'DOMINO_TILES'),
    (0x1F0A0, 'PLAYING_CARDS'),
    (0x1F100, 'ENCLOSED_ALPHANUMERIC_SUPPLEMENT'),
    (0x1F200, 'ENCLOSED_IDEOGRAPHIC_SUPPLEMENT'),
    (0x1F300, 'MISCELLANEOUS_SYMBOLS_AND_PICTOGRAPHS'),
    (0x1F600, 'EMOTICONS'),
    (0x1F650, None),
    (0x1F680, 'TRANSPORT_AND_MAP_SYMBOLS'),
    (0x1F700, 'ALCHEMICAL_SYMBOLS'),
    (0x1F780, None),
    (0x20000, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_B'),
    (0x2A6E0, None),
    (0x2A700, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_C'),
    (0x2B740, 'CJK_UNIFIED_IDEOGRAPHS_EXTENSION_D'),
    (0x2B820, None),
    (0x2F800, 'CJK_COMPATIBILITY_IDEOGRAPHS_SUPPLEMENT'),
    (0x2FA20, None),
    (0xE0000, 'TAGS'),
    (0xE0080, None),
    (0xE0100, 'VARIATION_SELECTORS_SUPPLEMENT'),
    (0xE01F0, None),
    (0xF0000, 'SUPPLEMENTARY_PRIVATE_USE_AREA_A'),
    (0x100000, 'SUPPLEMENTARY_PRIVATE_USE_AREA_B'),
    (0x10FFFF, None),
])
def unicode_blocks_of(uchar: str) -> str:
    return _BLOCK_NAMES[bisect.bisect_right(_BLOCK_STARTS, ord(uchar)) - 1]


def analyse(folderpath, filename):
    filepath = os.path.join(folderpath, filename)
    print(f"      Analysing {filepath}…")
    with open( filepath, 'rt') as source_file:
        file_contents = source_file.read()
        print(f"        Loaded {len(file_contents):,} characters")

    is_NFC_normalised = unicodedata.is_normalized('NFC', file_contents)
    is_NFD_normalised = unicodedata.is_normalized('NFD', file_contents)
    print(f"          NFC_normalised={is_NFC_normalised} NFD_normalised={is_NFD_normalised}")
    if is_NFC_normalised and is_NFD_normalised: # no accented/combined characters
        print(f"            No accented or combined characters")
        return # No need to analyse further
    if is_NFC_normalised: # that's how we want to handle accented/combined characters
        print(f"            All accented or combined characters are composed")
        return # No need to analyse further

    name_set = set()
    category_set = set()
    bidirectional_set = set()
    combining_set = set()
    east_asian_width_set = set()
    mirrored_set = set()
    blocks_set = set()
    name_dict = {}
    for char in file_contents:
        if char == '\n': continue # Seems to be not part of Unicode
        try:
            name = unicodedata.name(char) # Returns the name assigned to the character char as a string. If no name is defined, default is returned, or, if not given, ValueError is raised.
        except ValueError:
            if char != '\n': print(f"Why doesn't {char} ({ord(char)}) have a Unicode name???")
            name = 'UNKNOWN'
        name_set.add(name)
        category_abbreviation = unicodedata.category(char) # Returns the general category assigned to the character char as string.
        category_name = categoryNames[category_abbreviation]
        category_set.add(category_name)
        bidirectional_abbreviation = unicodedata.bidirectional(char) # Returns the bidirectional class assigned to the character char as string. If no such value is defined, an empty string is returned.
        bidirectional_name = bidiNames[bidirectional_abbreviation]
        bidirectional_set.add(bidirectional_name)
        combining = unicodedata.combining(char) # Returns the canonical combining class assigned to the character char as integer. Returns 0 if no combining class is defined.
        combining_set.add(combining)
        east_asian_width_abbreviation = unicodedata.east_asian_width(char) # Returns the east asian width assigned to the character char as string.
        east_asian_width_name = eastAsianWidthNames[east_asian_width_abbreviation]
        east_asian_width_set.add(east_asian_width_name)
        mirrored = unicodedata.mirrored(char) # Returns the mirrored property assigned to the character char as integer. Returns 1 if the character has been identified as a “mirrored” character in bidirectional text, 0 otherwise.
        mirrored_set.add(mirrored)
        decomposition = unicodedata.decomposition(char) # Returns the character decomposition mapping assigned to the character char as string. An empty string is returned in case no such mapping is defined.
        # print(f"{char} {category_abbreviation}={category_name} {bidirectional} {combining} {east_asian_width_abbreviation} {mirrored} {decomposition}")
        blocks = unicode_blocks_of(char)
        blocks_set.add(blocks)
        if name not in name_dict:
            name_dict[name] = {'char':char, 'count':1, 'category':category_name, 'bidi':bidirectional_name, 'combining':combining, 'east_asian_width':east_asian_width_name, 'mirrored':mirrored, 'decomposition':decomposition, 'blocks':blocks}
        else: name_dict[name]['count'] += 1
    print(f"          Blocks ({len(blocks_set)}) {sorted(blocks_set)}")
    print(f"          Names ({len(name_set)}) {sorted(name_set)}")
    print(f"          Categories ({len(category_set)}) {sorted(category_set)}")
    print(f"          bidirectional_set ({len(bidirectional_set)}) {sorted(bidirectional_set)}")
    print(f"          combining_set ({len(combining_set)}) {combining_set}")
    print(f"          east_asian_width_set ({len(east_asian_width_set)}) {east_asian_width_set}")
    print(f"          mirrored_set ({len(mirrored_set)}) {mirrored_set}")

    have_Hebrew = have_Greek = False
    for name in name_dict:
        if name.startswith('HEBREW '): have_Hebrew = True
        if name.startswith('GREEK '): have_Greek = True
    print(f"          {have_Hebrew=} {have_Greek=}")
    if have_Hebrew and have_Greek: wow
    cutoff_count = max(10, len(file_contents) / 1_000)
    for name,name_entry in sorted(name_dict.items(), key=lambda entryTuple: entryTuple[1]['count'], reverse=True):
        count = name_entry['count']
        if count < cutoff_count and not name.startswith('LATIN SMALL LETTER ') and not name.startswith('LATIN CAPITAL LETTER '):
            combining_string = f"   combining={name_entry['combining']}" if name_entry['combining'] else ''
            mirrored_string = f"   mirrored={name_entry['mirrored']}" if name_entry['mirrored'] else ''
            decomposition_string = f"   decomposition={name_entry['decomposition']}" if name_entry['decomposition'] else ''
            print(f"              ({count:,}) {name_entry['char']} {name} {name_entry['category']} blocks={name_entry['blocks']}  {name_entry['bidi']}{combining_string}   EastAsianWidth={name_entry['east_asian_width']}{mirrored_string}{decomposition_string}")

    if not is_NFC_normalised:
        filenameBits = filename.split('.')
        filenameBits.insert(len(filenameBits)-1,'NFC_normalised')
        new_filename = '.'.join(filenameBits)
        new_filepath = os.path.join(folderpath, new_filename)
        new_file_contents = unicodedata.normalize('NFC', file_contents)
        print(f"      Writing {new_filepath}…")
        with open( new_filepath, 'wt') as nfc_file:
            nfc_file.write(new_file_contents)
            print(f"        Wrote {len(new_file_contents):,} characters")


def main():
    """
    """
    print(f"UnicodeAnalyser.py v0.01 with Unicode data v{unicodedata.unidata_version}")
    preloadData()

    print(f"  Source folderpath is {LOCAL_SOURCE_FOLDERPATH}/")
    total_files_read = 0
    for folderpath, subdirList, fileList in os.walk(LOCAL_SOURCE_FOLDERPATH):
        print(f"Found folderpath: {folderpath}/")
        if subdirList: print(f"  Found subdirList: ({len(subdirList)}) {subdirList}")
        for ignore_folder in ('.git','.github'):
            if ignore_folder in subdirList:
                print("    Ignoring '{ignore_folder}/' subfolder")
                subdirList.remove(ignore_folder)  # Ignore this folder
        if fileList: print(f"  Found fileList: ({len(fileList)}) {fileList}")
        for filename in sorted(fileList):
            print(f"    Processing {filename}…")
            if not 'RUT' in filename: continue # Skip all other books
            analyse(folderpath, filename)
            total_files_read += 1
    print(f"{total_files_read:,} total files read from {LOCAL_SOURCE_FOLDERPATH}/")
# end of main function

if __name__ == '__main__':
    main()
# end of UnicodeAnalyser.py
