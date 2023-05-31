# -*- coding: utf-8 -*-
# This Python 3 module handles asterisks in a string according to markdown syntax rules.
# Use these methods:
#    confidence(str) to evaluate the correctness of the markdown string
#    dump(str, file) to output the analysis
#    fix_boldmarks(str)  to improve the correctness of a line of markdown by adding and removing asterisks

import re       # regular expression module

current_str = ""
current_stars = []

class Cluster:
    def __init__(self, c, pos, spaceleft, leading):
        self.c = c
        self.nstars = c.count('*')
        self.leading = (pos == 0 or leading)
        self.lefty = ((c[0] == ' ' or pos == 0 or spaceleft) and c[-1] == '*')
        self.righty = (c[0] == '*' and c[-1] == ' ') and pos > 0
        self.floating = (c[0] == ' ' and c[-1] == ' ') and pos > 0
        self.tight = (c[0] == '*' and c[-1] == '*') and pos > 0
        self.length = len(c)
        self.startpos = pos
        self.endpos = pos + len(c)
        self.ldist = 0
        self.rdist = 0
        self.if_removed = 9999

    def write(self, file):
        file.write(f"{self.c}: nstars={self.nstars}, ")
        if self.leading:
            file.write("leading, ")
        if self.lefty:
            file.write("lefty, ")
        if self.righty:
            file.write("righty, ")
        if self.floating:
            file.write("floating, ")
        if self.tight:
            file.write("tight, ")
        file.write(f"pos {self.startpos}:{self.endpos}, ")
        file.write(f"ldist={self.ldist}, rdist={self.rdist}\n")

cluster_re = re.compile(r' *\*{1,2} ?', re.UNICODE) # one or two stars possibly surrounded by space
rclinl_re = re.compile(r'rc://*/', re.UNICODE)
blockquote_re = re.compile(r'[> ]*\*', re.UNICODE)

# Parses the string and returns corresponding list of star clusters
def analyze(str):
    starlist = []
    pos = 0
    preceding = ''
    if blockquote_re.match(str):
        preceding = '>'
    rcpos = str.find("rc://*/")
    c = cluster_re.search(str)
    while c:
        if rcpos < 0 or c.start() != rcpos + 5:
            cluster = Cluster(c.group(0), pos + c.start(), (c.start() == 0 and preceding == ' '), (preceding == '>'))
            starlist.append(cluster)
        preceding = str[c.end()-1]    # equals a space when we have two clusters separated by a space
        str = str[c.end():]
        rcpos = str.find("rc://*")
        pos += c.end()
        c = cluster_re.search(str)
    starlist = set_distances(starlist)
    return starlist

# Sets ldist and rdist for each node and returns the list as modified
def set_distances(starlist):
    nclusters = len(starlist)
    i = 0
    while i < nclusters:
        cluster = starlist[i]
        cluster.ldist = cluster.startpos if i==0 else cluster.startpos - starlist[i-1].endpos
        if i + 1 < nclusters:
            cluster.rdist = starlist[i+1].startpos - cluster.endpos
        else:
            cluster.rdist = len(current_str) - cluster.endpos
        i += 1
    return starlist

# Attempts to correct bold markup if it is suspect.
# Returns corrected string.
# Sets current_str and current_stars.
def fix_boldmarks(str):
    global current_str
    global current_stars

    if str != current_str:
        current_str = str
        current_stars = analyze(str)
    conf = calculate_confidence(current_stars)
    if conf < 90:
        newstr = reinterpret(current_str, current_stars)
        if newstr != current_str:
            new_list = analyze(newstr)
            newconf = calculate_confidence(new_list)
            if newconf > conf:
                current_str = newstr
                current_stars = new_list
    return current_str

# Change 1-star nodes (other than a leading single asterisk) to 2-star nodes.
# Removed stranded nodes (unbalanced)
# Returns new string.
def reinterpret(str, starlist):
    newstr = str
    pos = 0
    nchars_added = 0
    # Combine adjacent 1-star nodes
    nClusters = len(starlist)
    i = 0
    while i + 1 < nClusters:
        if starlist[i].nstars == 1 and starlist[i+1].nstars == 1 and starlist[i].rdist == 0:
            length = starlist[i].length + starlist[i+1].length
            if length == 3:
                replacement = "** "
            else:
                replacement = " **" + ' ' * (length-3)    # Don't change the length of the string
            newstr = newstr[:starlist[i].startpos] + replacement + newstr[starlist[i+1].endpos:]
            i += 1
        i += 1
    if newstr != str:
        str = newstr
        starlist = analyze(str)

    # Resolve leading, lefty 1-star nodes if possible
    if starlist[0].leading and starlist[0].nstars == 1 and starlist[0].lefty:
        insertc = None
        if len(starlist) == 1:
            insertc =  ' '
        elif starlist[1].nstars >= 2 and starlist[1].startpos - starlist[0].endpos < 35:
            insertc = '*'
        if insertc:
            pos = str.find('*')
            newstr = str[:pos+1] + insertc + str[pos+1:]
            str = newstr
            starlist = analyze(str)

    # Promote unpaired 1-star nodes to 2-star nodes
    pos = 0
    nsingles = nclustersOfSize(1, starlist)
    # if starlist[0].nstars == 1 and starlist[0].leading:
    #     nsingles -= 1
    if nsingles > 0 and nsingles % 2 != 0 and nclustersOfSize(2, starlist) > 0:
        newstr = ""
        for cluster in starlist:
            newc = cluster.c
            if cluster.nstars == 1 and not cluster.leading:
                cpos = newc.find('*')
                newc = newc[:cpos] + '*' + newc[cpos:]
            newstr += str[pos:cluster.startpos] + newc
            pos = cluster.endpos
        newstr += str[pos:]
        if newstr != str:
            starlist = analyze(newstr)

    # Remove stranded cluster
    nClusters = len(starlist)
    if nClusters > 0:
        cluster1 = starlist[0]
        if cluster1.nstars == 1 and cluster1.leading and nsingles % 2 != 0:
            startbold = 1
        else:
            startbold = 0
        if (nClusters-startbold) % 2 != 0:
            (first,last) = find_stranded_by_spacing(starlist[startbold:])
            if first == last:
                stranded = first + startbold
            else:
                stranded = find_stranded_by_length(starlist[first+startbold:]) + first+startbold
            pos1 = starlist[stranded].startpos + (1 if starlist[stranded].lefty and not starlist[stranded].leading else 0)
            pos2 = starlist[stranded].endpos - (1 if (starlist[stranded].righty or starlist[stranded].floating) else 0)
            addspace = ""
            if pos2 < len(newstr) and starlist[stranded].tight and newstr[pos2] not in ".,;?!\"" and newstr[pos1-1] not in "\"'":
                addspace = " "
            newstr = newstr[:pos1] + addspace + newstr[pos2:]  # eliminates stranded cluster
    return newstr

# Determines which cluster is most likely stranded, based on adjacency of asterisks to text
# and to other clusters.
# Returns the indexes of the first and last likely stranded clusters.
def find_stranded_by_spacing(starlist):
    if starlist[0].rdist == 0:
        i = j = 0
    elif starlist[-1].ldist == 0:
        i = j = len(starlist) - 1
    else:
        nclusters = len(starlist)
        # find first suspect cluster
        i = 0
        while i+1 < nclusters:
            if starlist[i].lefty and starlist[i+1].righty and starlist[i].rdist > 0:
                i += 2
            else:
                break
        # Find last suspect cluster
        j = nclusters - 1
        while j-1 >= 0:         # find last suspect cluster
            if starlist[j-1].lefty and starlist[j].righty and starlist[j].ldist > 0:
                j -= 2
            else:
                break
    return (i, j)

# Determines which cluster is most likely stranded, based on distances between clusters.
# Returns the index of the stranded cluster.
# This algorithm should be improved to give some weight to lefty righty properties.
def find_stranded_by_length(starlist):
    i = 0
    stranded = i
    while i < len(starlist):
        shortlist = starlist[:i] + starlist[i+1:]
        lefties = shortlist[::2]
        starlist[i].if_removed = 0
        for cluster in lefties:
            starlist[i].if_removed += cluster.rdist
        if starlist[i].if_removed <= starlist[stranded].if_removed:
            stranded = i
        i += 2
    return stranded

# twopairs_re = re.compile(r'\*\* *\*\*', re.UNICODE)
# first2_re = re.compile(r' *\*\* ?', re.UNICODE)

'''
# If there are any 4-star nodes, reinterprets them and returns a new list of clusters
def reinterpret4star(starlist):
    i = 0
    while i < len(starlist):
        oldcluster = starlist[i]
        if oldcluster.nstars == 4:
            # if "****" in oldcluster.c:
                # del starlist[i:i+1]
                # cluster = Cluster("", oldcluster.startpos)
                # starlist[i].changelength = -6
                # starlist[i:i+1] = [cluster]     # replace old cluster with newly calculated one
                # starlist[i].changelength = -len(oldcluster.length)

            if twopairs_re.search(oldcluster.c):
                del starlist[i:i+1]
                first2 = first2_re.match(oldcluster.c)
                newc = first2.group(0)
                cluster = Cluster(newc, oldcluster.startpos)
                starlist[i:i] = [cluster]
                # last2 = last2_re.search(oldcluster.c)
                newc = oldcluster.c[len(newc):]
                cluster = Cluster(newc, oldcluster.endpos - len(newc))
                starlist[i+1:i+1] = [cluster]
        i += 1
    starlist = set_distances(starlist)
    return starlist
'''

'''
def regenerate_str(str, starlist):
    newstr = ""
    needto = False
    for cluster in starlist:
        if cluster.changelength != 0:
            needto = True
            break
    if needto:
        pos = 0
        for cluster in starlist:
            newstr += str[pos:cluster.startpos] + cluster.c
            pos = cluster.endpos - cluster.changelength
        newstr += str[pos:]
    return (newstr if needto else str)
'''

# Output asterisk analysis to specified file.
# Does not reparse or reanalyze string unless it changed from the last analysis
def dump(str, file):
    global current_str
    global current_stars

    if str != current_str:
        current_str = str
        current_stars = analyze(str)
    if len(current_stars) > 0 and file:
        file.write(str + '\n' + f"  has {len(current_stars)} clusters\n")
        for cluster in current_stars:
            cluster.write(file)
        file.write(f"Confidence: {confidence(str)}\n\n")

# Calculates a number between 0 and 100 estimating how likely the asterisk placements
# in the current string are correct.
def confidence(str):
    global current_str
    global current_stars

    if str != current_str:
        current_str = str
        current_stars = analyze(str)
    if len(current_stars) > 0:
        conf = calculate_confidence(current_stars)
    else:
        conf = 100
    return (conf if conf >= 0 else 0)

# Calculates a number between 0 and 100 estimating how likely the bold markup
# in the current string is correct.
def calculate_confidence(starlist):
    conf = 100
    nclusters = len(starlist)
    if nclusters > 0:
        nsingles = nclustersOfSize(1, starlist)
        # ntriples = nclustersOfSize(3, starlist)
        # nquads = nclustersOfSize(4, starlist)
        cluster1 = starlist[0]
        if cluster1.nstars == 1 and cluster1.leading and (nsingles % 2 == 1 or not cluster1.lefty):
            startbold = 1
        else:
            startbold = 0
        if (nclusters+startbold) % 2 == 1:
            conf = 0
        if nsingles > 0 and (cluster1.nstars != 1 or not cluster1.leading or cluster1.lefty):
            conf -= (40 if nsingles % 2 == 1 else 20)
        # if ntriples > 0:
            # conf -= (5 if (ntriples == 1 and cluster1.nstars == 3) else 80)
        # if nquads > 0:
            # conf -= nquads * 10
        # galaxy = starlist[startbold:]
        maxlen = maxBoldLength(starlist[startbold:])
        if maxlen > 15:
            conf -= (20 if maxlen > 35 else maxlen-15)
        elif maxlen < 2:
            conf -= 10
        conf -= 5 * badPairing(starlist[startbold:])
    return conf

# Examines each pair and counts number of instances where the left asterisk isn't adjacent
# to text on the right, and where the right asterisk isn't adjacent to text on the left.
# Floating and tight asterisks count 1. Lefty/righty opposites count 4.
def badPairing(starlist):
    n = 0
    nclusters = len(starlist)
    i = 0
    while i+1 < nclusters:
        cluster = starlist[i]
        next = starlist[i+1]
        if cluster.righty:
            n += 4
        elif cluster.floating or cluster.tight:
            n += 1
        if next.lefty:
            n += 4
        elif next.floating or next.tight:
            n += 1
        i += 2
    return n

# Returns the length of the longest bold substring
def maxBoldLength(stars):
    maxlen = 0
    nclusters = len(stars)
    i = 0
    while i+1 < nclusters:
        cluster = stars[i]
        next = stars[i+1]
        length = next.startpos - cluster.endpos
        if length > maxlen:
            maxlen = length
        i += 2
    return maxlen

# Returns the number of star clusters of the specified size in the list
def nclustersOfSize(size, starlist):
    count = 0
    for cluster in starlist:
        if cluster.nstars == size:
            count += 1
    return count