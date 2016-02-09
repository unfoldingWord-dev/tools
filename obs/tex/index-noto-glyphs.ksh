#!/usr/bin/ksh
vendor=google
logicalname=noto
export PATH=/usr/lib64/qt-3.3/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:$PATH
font_root=/opt/context/tex/texmf/fonts
font_dir=/opt/context/tex/texmf/fonts/$vendor/$logicalname
all_file=$font_dir/all-glyphs.txt
tmp_index_file=/tmp/index.txt
tmppre=/tmp/$$.tmp
Cleanup () {
    [[ $tmppre = /tmp* ]] && rm -i ${tmppre}*
}
CreateGlyphLists () {
    # otfinfo ttfdump 
    for ttfile in $(find $font_dir -type f -name '*.?tf' | fgrep -i 'notosans' | fgrep -i regular)
    do
        ttfdump $ttfile  | egrep -i 'char 0x' | awk '{print $2}'| sort -u > $ttfile.glyphs
    done
    cat /opt/context/tex/texmf/fonts/google/noto/*glyphs | sort -u > $all_file
}
CreateTempIndex () {
    for glyph in $(cat $all_file)
    do
        echo $glyph $(fgrep $glyph /opt/context/tex/texmf/fonts/google/noto/*.glyphs | sed -e 's/\.glyphs//' | sed -e 's:^.*/::' | cut -d: -f1 | sort -u)
    done > $tmp_index_file
}
CreateTheFallback () {
    cat $tmp_index_file \
        | fgrep -v 0x00 \
        | fgrep -v NotoSans-Regular.ttf \
        | sed -e 's/[-]Regular\.[a-z]*//g' \
        | awk   'BEGIN{lastname = ""; lastglyph = ""; firstglyph = ""}
                 {
                     glyph = $1
                     currname = $2
                     if (lastname != currname) {
                         if (lastname != "") { print "\\setmainfontfallback[" lastname "][range=" firstglyph "-" lastglyph ",force=yes]" }
                         firstglyph = glyph
                     }
                     lastglyph = glyph
                     lastname = currname
                 }
                 END { print "\\setmainfontfallback[" lastname "][range=" firstglyph "-" lastglyph ",force=yes]" }'
}
CreateTheFontList () {
    # \definefontfeature[condensed][extend=0.8]
    # slanted boldened stretched
    ls -1 $font_dir | egrep '\.(ttf|otf)' | cut -d. -f1 | sort -u > $tmppre.basenames
    cat $tmppre.basenames | cut -d- -f1 | sort -u | tee $tmppre.rangenames | sed -e 's/[MS][eao][rnt][isoh][f]*/.*/' | sort -u > $tmppre.rangepatterns
    print "\\definefontfeature[monospace][letterspacing]"
    print "\\definefontsynonym[Math][MathRoman]"
    print "\\definefontsynonym[MathBold][MathRomanBold]"
    print "\\starttypescriptcollection[" logicalname "]"
    for pattern in $(cat $tmppre.rangepatterns|egrep 'Armen|Ethiop|Sans$|Serif$')
    do
        {
            egrep "^$pattern[-]|^$pattern$" $tmppre.basenames \
                | awk -v logicalname=$logicalname -v rangepat="$pattern" '
                    BEGIN {
                        debug = 0
                        Logicalname = toupper(substr(logicalname,1,1)) substr(logicalname,2)
                        tag = "\\s!"
                        j=(-1)
                        n=(-1)
                        # Font Features listed in: /opt/context/tex/texmf-context/tex/context/base/font-pre.mkiv
                        Attrib_all["Regular"] = 1
                        Attrib_all["Bold"] = 1
                        Attrib_all["Italic"] = 1
                        Attrib_all["BoldItalic"] = 1
                        Stylename_all["Serif"] = 1
                        Stylename_all["Sans"] = 1
                        Stylename_all["Mono"] = 1
                        Stylename_all["Math"] = 1
                        rangepat_suffix = rangepat
                        sub("^.*[\\.][\\*]","",rangepat_suffix)
                    }
                    function set_unless(key,value,base)
                    {
                        if (debug) print "set_unless(key="key",value="value",base="base")"
                        if (key in key_found) return
                        features[key] = value
                        base_of_base[key] = base
                        if (debug) print "++ features[key=" key "]=" value ", base_of_base[key=" key "]=" base
                    }
                    function set_range_etc(Stylename, base)
                    {
                        range = base
                        gsub(rangepat,rangepat_suffix,range)
                        gsub("[-].*$","",range)
                        group = Logicalname Stylename range
                        if (debug) print "set_range_etc(Stylename="Stylename",base="base"), rangepat="rangepat" ,rangepat_suffix="rangepat_suffix" ,range="range" ,group="group
                    }
                    {
                        base = $0
                        if (debug) print ">> " $0
                        basename[++n] = $0
                        # For \definetypeface
                        style = "[rm] [serif]"
                        Stylename = "Serif"
                        if ($0 ~ /[Ss]ans/)             { style = "[ss] [sans]"; Stylename = "Sans" }
                        if ($0 ~ /[Mm]ono/)             { style = "[tt] [mono]"; Stylename = "Mono" }
                        if ($0 ~ /[Mm]ath/)             { style = "[mm] [math]"; Stylename = "Math" }
                        set_range_etc(Stylename, base)
                        # For \definefontsynonym
                        Attrib = "Regular"
                        if ($0 ~ /[-][Rr]/)                     { Attrib = "Regular" }
                        else if ($0 ~ /[-][Ii][Bb]/)            { Attrib = "BoldItalic" }
                        else if ($0 ~ /[-][Bb][Ii]/)            { Attrib = "BoldItalic" }
                        else if ($0 ~ /[-][It]al[ic]*[Bb]old/)  { Attrib = "BoldItalic" }
                        else if ($0 ~ /[-][Bb]old[Ii]/)         { Attrib = "BoldItalic" }
                        else if ($0 ~ /[-][Ii]/)                { Attrib = "Italic" }
                        else if ($0 ~ /[-][Bb]/)                { Attrib = "Bold" }
                        key = Stylename Attrib
                        Stylename_found[Stylename] = 1
                        Attrib_found[Attrib] = 1
                        key_found[key] = base
                        basename[key] = base
                        features[key] = "default"
                        if (debug) print "++ found=" Attrib
                        if (debug) print "++ Stylename="Stylename", basename[key=" key "]=" base ", features[key=" key "]=default"
                    }
                    function print_synonym(name,key)
                    {
                        if (!(key in basename)) { basename[key] = base_of_base[key] }
                        print "        \\definefontsynonym [" tag key "] [" tag "file:" basename[key] "] [" tag "features=" features[key] "]"
                    }
                    function print_face(range,style)
                    {
                        print "        \\definetypeface [" range "] " style " [" range "] [" tag "default]"
                    }
                    function target_Stylename(Stylename)
                    {
                        # tacitly assume either sans or serif defined
                        if (stylename_found[Stylename]) return Stylename
                        if (stylename_found["Sans"]) return "Sans"
                        return "Serif"
                    }
                    END {
                        for (Stylename in Stylename_found) {
                            for (Attrib in Attrib_all) {
                                key_possible[Stylename Attrib] = 1
                            }
                        }
                        for (Stylename in Stylename_all) {
                            for (Attrib in Attrib_all) {
                                key = Stylename Attrib
                                if (debug) print "loop, key=" key ", Attrib=" Attrib
                                if (!(key in key_found)) {
                                    basekey = key
                                    if (debug) print "bgn, key=" key ", basekey=" basekey
                                    if (!(basekey in key_possible)) {
                                        for (s in Stylename_all) { sub(s, target_Stylename("?"), basekey) }
                                    }
                                    if (debug) print "fix, key=" key ", basekey=" basekey
                                    value = ""
                                    if (!(basekey in key_found)) {
                                        if (gsub(/Italics*$/, "", basekey) > 0) value = "slanted"
                                        else if (gsub(/Bold$/, "", basekey) > 0) value =  "boldened"
                                        if (debug) print "chk, key=" key ", basekey=" basekey ", value=[" value "]"
                                        count = 0
                                        if (!(basekey in key_possible)) {
                                            copy = basekey
                                            count += gsub(/Bold$/, "", copy)
                                            count += gsub(/Italics*$/, "", copy)
                                        }
                                        if (count > 1) value = "boldened,slanted"
                                    }
                                    if (!(basekey in key_possible)) {
                                        basekey = basekey "Regular"
                                    }
                                    if (key ~ /Math/) value = value ",mathematics"
                                    if (key ~ /Mono/) value = value ",monospace"
                                    sub("^,,*","",value)
                                    sub("^ *$","default",value)
                                    if (debug) print "sun, key=" key ", value=" value ", basekey=" basekey ", bob=" basename[basekey]
                                    set_unless(key,value,basename[basekey])
                                }
                            }
                        }
                        for (Stylename in Stylename_all) {
                            lcstyle = tolower(Stylename)
                            set_range_etc(Stylename, basename[target_Stylename(Stylename) "Regular" ])
                            name = logicalname "-" lcstyle
                            print "    \\starttypescript[" tag lcstyle "] [" group "] [" tag "file]"
                            print "        \\setups[" tag "font:" tag "fallback:" tag lcstyle "]"
                            print_synonym(name,Stylename"Regular")
                            print_synonym(name,Stylename"Bold")
                            print_synonym(name,Stylename"Italic")
                            print_synonym(name,Stylename"BoldItalic")
                            print "    \\stoptypescript"
                            print "    \\starttypescript[" group "]"
                            print_face(group,"["tag"rm] ["tag"serif]")
                            print_face(group,"["tag"ss] ["tag"sans]")
                            print_face(group,"["tag"tt] ["tag"mono]")
                            print_face(group,"["tag"mm] ["tag"math]")
                            print "    \\stoptypescript"
                        }
                    }'
                    #> $tmppre.$range.cmds
        }
    #> $tmppre.$range.typescript
    done
    print "\\stoptypescriptcollection"
}
#CreateGlyphLists
#CreateTempIndex
#CreateTheFallback
CreateTheFontList
#Cleanup
exit
