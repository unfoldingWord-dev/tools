#!/usr/bin/bash
########################################################################
#
# NAME  ipaudit - scrape DCS and uW repos for license and contrib info
#
# DEPENDENCIES
#       jq    for navigating json
#       unzip to unpack repos
#       door43 and github tokens to avoid rate limited queries of repos
# BUGS
#       should have used access token in header but could not make it 
#       work so I put it in querystring
#
  USAGE='ipaudit [-l|-o] uw|dcs
   where 
      uw   = UnfoldingWord* at github.com
      dcs  = Door43 Content Service at git.door43.org
      -l   = do not re download repo lists
      -o   = download uW orgs repos then exit'
#########################################################################

function echoList() {
  tmpRaw=$1 ; license=$2 ; file=$3
  li=

  while read ln ; do
    li="$li
    ${ln:0:80}"              
  done < $tmpRaw
              
  echo -n "  $license From: $file"   >> list
  echo "    ${li:-none}"             >> list
}


> list 
cmd=""
opt=""
profile='LICENSE|README|manifest|status'
filter='copyright|this work|license|?cc |public domain'

while [ $# -gt 0 ] ; do
  case $1 in
    uw)  cmd=uw ;;
    dcs) cmd=dcs ;;
    -l)  opt=noLoad ;;
    -o)  opt=loadOnly ;;
    *)   echo "Invalid parameter: $1"
         echo "$USAGE"
         exit ;;
  esac

  shift
done

case $cmd in
  "")
    echo "Missing arg."
    echo "$USAGE"
    ;;

  dcs)
    domain='https://git.door43.org'
    org='unfoldingWord'
    a='your door43 access token'
    acc="access_token=$a"

    if [ "x$opt" != "xnoLoad" ] ; then     
      if [ -f tmpRepos ] ; then 
        rm tmpRepos ; 
      fi
    
      curl -s "${domain}/api/v1/orgs/unfoldingWord/repos" \
          | jq -r '.[].html_url' | tr '/' ' ' > tmpRepos
    fi

    if [ -f tmpRepos ] ; then
      set `wc -l tmpRepos`
      echo "$1 repos in $org" >> list
      count=0

      while read prot dom org repo ; do
        count=$(( $count + 1 ))
        echo "$count $repo" >> list
        rm -f tmpRepo
        curl -s "${domain}/api/v1/repos/$org/$repo/git/trees/master" \
            | jq '.' > tmpRepo
        rm -f tmpSha
        cat tmpRepo | jq -r '.tree[] | {(.path): .sha}' | egrep "$profile" > tmpSha

        while read file sha ; do
          sfile=`echo "${file%:}" | tr -d \" | tr -d \'`
          rm -f tmpFile
          curl -s "${domain}/api/v1/repos/$org/$repo/raw/$sfile" -o tmpFile

          case $sfile in
            LICENS*) 
              lFile=$sfile
              l1=`egrep "^## " < tmpFile`
              l2=${l1##*\(}
              l3=${l2%%\)}
              l4=
              rm -f lFile
              egrep  "$filter" < tmpFile > lFile

              while read ln ; do
                l4="$l4
      ${ln:0:70}"
              done < lFile

              license="$l3 $l4"
              ;;

            README*) 
              rFile=$sfile
              r1=`egrep "$filter" < tmpFile`
              readme=${r1:0:70}
              ;;

            manifest*) 
              mFile=$sfile
              state=out
              man=
              contrib=

              while read arg1 arg2 ; do
                case $state in
                  in)
                    case $arg1 in
                      creator*)
                        state=out ;;
                      *)
                        co1=${arg2%\'}
                        co2=${co1#\'}
                        co3=${co2%\"}
                        co4=${co3#\"}
                        contrib="$contrib
      $co4"
                        ;;
                    esac
                    ;;
                  out)
                    case $arg1 in
                      contributor*) 
                        state=in
                        ;;
                      rights*)
                        man=$arg2
                        ;;
                    esac
                    ;;
                esac

                manifest=$man
              done < tmpFile
              ;;
          esac 
        done < tmpSha

        rm -f tmpColab
        curl -s "${domain}/api/v1/repos/$org/$repo/collaborators?$acc" > tmpColab
        rm -f tmpGit
        cat tmpColab | jq -r  '.[] | {(.full_name): .username}' | egrep -v '{|}' > tmpGit
        git=
        
        while read ln ; do
          IFS=\:
          set x $ln
          shift
          na="$1"
          id="$2"
          IFS=" "
          na2=`echo $na | tr -d \' | tr -d \"`
          id2=`echo $id | tr -d \' | tr -d \"`
          set x $na2
          shift
          na3="$*"

          if [ -z "$na3" ] ; then
            set $id2
            na3="$*"
          fi

          if [ -n "$na3" ] ; then
            git="$git
      $na3"      
          fi
        done < tmpGit

        echo "  License:"              >> list
        echo "      ${license:-none}"  >> list
        echo "    From: $rFile"        >> list
        echo "      ${readme:-none}"   >> list
        echo "    From: $mFile"        >> list
        echo "      ${manifest:-none}" >> list
        echo "  Colaborators:"         >> list
        echo -n "    From $mFile"      >> list
        echo "      ${contrib:-none}"  >> list
        echo -n "    From: git:"       >> list
        echo "      ${git:-none}"      >> list
      done < tmpRepos   
    fi
    ;;

  uw)
    a="your github access token"
    acc="access_token=$a"
    domain="https://api.github.com"
    echo >> list
    echo "IP Audit of unfoldingWord orgs" >> list

    for org in unfoldingWord unfoldingWord-box3 unfoldingWord-dev ; do
      
      # most of this is because we dont know how many pages will be returned
      if [ "x$opt" != "xnoLoad" ] ; then
        rm -f tmpOrg$prg tmpOrg tmpOrgs
    
        for i in 1 2 3 4 5 ; do

          curl -s "${domain}/orgs/$org/repos?page=$i&per_page=100&$acc" | egrep -v '\[|\]' > tmpOrg
          lines=`wc -l tmpOrg`

          if [ ${lines% *} -gt 2 ] ; then
            if [ -f tmpOrgs ] ; then
              echo ',' >> tmpOrgs
            fi
            
            cat tmpOrg >> tmpOrgs
          else
            break  
          fi  
        done 

        echo '['   > tmpOrg$org
        cat tmpOrgs >> tmpOrg$org
        echo ']'  >> tmpOrg$org
      fi

      if [ "x$opt" == "xloadOnly" ] ; then
        continue
      fi

      count=`cat tmpOrg$org | jq '. | length'`

      if [ $count -lt 3 ] ; then
        echo "Cannot read repo list. Perhaps rate limited." >> list
        rate=`curl -i "https://api.github.com/users/octocat/orgs?$acc" | egrep "^X-RateLimit"`
        echo $rate
        set `echo $rate | grep Reset`
        date -d @$2
        exit
      fi

      echo >> list
      echo "$org repo count: $count" >> list
      > tmpRepoList
      cat tmpOrg$org | jq -r '.[].name' | sort > tmpRepoList
      count=0

      while read repo ; do
        echo $org / $repo
        count=$(( $count + 1 ))
        echo "$count $repo" >> list
        > tmpRepo
        curl -s "${domain}/repos/$org/$repo/git/trees/master?$acc" -o tmpRepo

        > tmpFiles
        cat tmpRepo | jq -r '.tree[] | {(.path): .sha}' \
            | egrep -v '{|}' | egrep "$profile" | tr -d '\"' > tmpFiles
        
        while read file sha ; do
          fi1=${file%\:}
          > tmpFile
          curl -s "${domain}/repos/$org/$repo/git/blobs/$sha?$acc" -o tmpFile -H $a
          >  tmpDecoded
          cat tmpFile | jq -r .content | base64 -di > tmpDecoded

          case $file in
            LICENS*|READM*)
              > tmpRaw
              egrep -i "$filter" < tmpDecoded | egrep -v '^LICENSE$|^License$' > tmpRaw            
              echoList tmpRaw License $file
              ;;

            manifes*)
              > tmpMan
              cat tmpDecoded | jq '.rights' | > tmpMan
              echoList tmpMan License $file
              ;;

            statu*)
              > tmpCon
              cat tmpDecoded | jq -r '.contributors' | tr ',' '\n' | tr ';' '\n' > tmpCon
              echoList tmpCon Contributors $file
              ;;
            esac
        done < tmpFiles

        # git license
        license=`cat tmpOrg$org | jq -r '.[] | {(.full_name): .license.name}' | grep $repo | sed -e 's/[^:]*://' | tr -d \"`
        echo "  License from github: ${license:-none} " >> list

        # collaborators git
        rm -f tmpColab
        curl -s "${domain}/repos/$org/$repo/contributors?$acc" -o tmpColab
        rm -f tmpGit
        cat tmpColab | jq -r  '.[].login' | egrep -v '{|}' > tmpGit
        echoList tmpGit Collaborators github
      done < tmpRepoList
    done
    ;;
esac

