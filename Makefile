stat:
	git status -s

commit:
	git diff >/tmp/git-diff.out 2>&1
	git commit -a
	git pull --no-edit origin master
	git push origin master
