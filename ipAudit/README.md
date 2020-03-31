## NAME  ipaudit - scrape DCS and uW repos for license and contributor info

## DEPENDENCIES
       jq    for navigating json
       unzip to unpack repos
       door43 and github tokens to avoid rate limited queries of repos
## BUGS
       should have used access token in header but could not make it work so 
       so I put it in querystring

## USAGE 'ipaudit [-l|-o] uw|dcs
   where 
      uw   = UnfoldingWord* at github.com
      dcs  = Door43 Content Service at git.door43.org
      -l   = do not re download repo lists
      -o   = download uW orgs repos then exit'

