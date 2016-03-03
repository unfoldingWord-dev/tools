# Author: Ben R. Olson
# Date: March 1, 2016
#
# Note: Some code adapted from a tutorial by
#   Jesse Griffin, found at
#   http://slides.com/jessegriffin/git_presentation
#   "How to Merge tS Uploads?"
#   
# Purpose (based on above referenced tutorial):
#   (1) Clone a list of repositories and
#   (2) merge them into a master repository
#
# Usage:
#   1. Place this script in a new directory of your choice.
#   2. Place a file names repos_list.txt in this
#      directory, containing a list of all the 
#      repositories to be cloned.  Example repos_list.txt:
#        https://git.door43.org/<userA>/<repositoryA>.git
#        https://git.door43.org/<userB>/<repositoryB>.git
#   With this example repos_list.txt, 
#   repositoryA and repositoryB
#   would both be cloned to directory/repos and then
#   their contents merged into a new repository named
#   master_repo (ideally, but there are issues...)
#
#                ***ISSUES***
# In some cases, the master repository is MISSING
# CONTENT from one or more repositories after the
# merges.  I'm wondering if this is due to there being
# no common ancestors commits between any branches.



folders=();
counter=0;
mkdir repos;

for repoUrl in `cat "repos_list.txt"`; do
  #prefix=( "${repoUrl/*\//}" );
	prefix="branch"
	folder=$prefix"_"$counter;
	mkdir repos/$folder;
	git clone $repoUrl repos/$folder;
  ((counter++));
done

mkdir master_repo
cd master_repo
git init;

cd ..
repos=(`ls "repos"`)
cd repos
for x in ${repos[@]}; do
  echo "CREATING NEW BRANCH..."
  cd $x
	git checkout -b $x
	git push ../../master_repo $x
	echo "NEW BRANCH PUSHED TO master_repo"
	cd ../../master_repo
	echo "IN master_repo MERGING NEW BRANCH..."
  git merge -s ours $x
	cd ../repos
done

