#!/bin/bash

LANGS="$1"

DIR=/var/www/vhosts/door43.org/httpdocs/data/gitrepo/pages
TPL=/var/www/vhosts/door43.org/tpl
TITLES="01-the-creation.txt \
02-sin-enters-the-world.txt \
03-the-flood.txt \
04-gods-covenant-with-abraham.txt \
05-the-son-of-promise.txt \
06-god-provides-for-isaac.txt \
07-god-blesses-jacob.txt \
08-god-saves-joseph-and-his-family.txt \
09-god-calls-moses.txt \
10-the-ten-plagues.txt \
11-the-passover.txt \
12-the-exodus.txt \
13-gods-covenant-with-israel.txt \
14-wandering-in-the-wilderness.txt \
15-the-promised-land.txt \
16-the-deliverers.txt \
17-gods-covenant-with-david.txt \
18-the-divided-kingdom.txt \
19-the-prophets.txt \
20-the-exile-and-return.txt \
21-god-promises-the-messiah.txt \
22-the-birth-of-john.txt \
23-the-birth-of-jesus.txt \
24-john-baptizes-jesus.txt \
25-satan-tempts-jesus.txt \
26-jesus-starts-his-ministry.txt \
27-the-story-of-the-good-samaritan.txt \
28-the-rich-young-ruler.txt \
29-the-story-of-the-unmerciful-servant.txt \
30-jesus-feeds-five-thousand-people.txt \
31-jesus-walks-on-water.txt \
32-jesus-heals-a-demon-possessed-man.txt \
33-the-story-of-the-farmer.txt \
34-jesus-teaches-other-stories.txt \
35-the-story-of-the-compassionate-father.txt \
36-the-transfiguration.txt \
37-jesus-raises-lazarus-from-the-dead.txt \
38-jesus-is-betrayed.txt \
39-jesus-is-put-on-trial.txt \
40-jesus-is-crucified.txt \
41-god-raises-jesus-from-the-dead.txt \
42-jesus-returns-to-heaven.txt \
43-the-church-begins.txt \
44-peter-and-john-heal-a-beggar.txt \
45-philip-and-the-ethiopian-official.txt \
46-paul-becomes-a-christian.txt \
47-paul-and-silas-in-philippi.txt \
48-jesus-is-the-promised-messiah.txt \
49-gods-new-covenant.txt \
50-jesus-returns.txt"

echo "--> we will be creating a default Open Bible Stories template for the following: [$LANGS]"

for i in $LANGS
do
	echo "[ processing $i ]"

	#
	# create LANGUAGE DIRECTORY $DIR/$i if not exist
	#

	if [ ! -d $DIR/$i ]
	then
		echo "+ --> creating [DIRECTORY] $i"
		mkdir $DIR/$i
	fi	


	#
	# create LANGUAGE HOMEPAGE $DIR/$i/home.txt if not exist
	#

	if [ ! -f $DIR/$i/home.txt ]
	then
		echo "+ --> creating [FILE] $i/home.txt"
		sed -e "s/LANGCODE/${i}/g" $TPL/home.txt > $DIR/$i/home.txt
	fi	


	#
	# create LANGUAGE SIDEBAR $DIR/$i/sidebar.txt if not exist
	#

	if [ ! -f $DIR/$i/sidebar.txt ]
	then
		echo "+ --> creating [FILE] $i/sidebar.txt"
		sed -e "s/LANGCODE/${i}/g" $TPL/sidebar.txt > $DIR/$i/sidebar.txt
	fi	


	#
	# create OBS DIRECTORY $DIR/$i/obs if not exist
	#

	if [ ! -d $DIR/$i/obs ]
	then
		echo "+ --> creating [DIRECTORY] $i/obs"
		mkdir $DIR/$i/obs
	fi	


	#
	# create STORIES LINKS 	$DIR/$i/obs/stories.txt if not exist
	#

	if [ ! -f $DIR/$i/obs/stories.txt ]
	then
		echo "+ --> creating [FILE] $i/obs/stories.txt"
		sed -e "s/en:obs/${i}:obs/g" $TPL/obs-stories.txt > $DIR/$i/obs/stories.txt
	fi	

	#
	# create HOMEPAGE 	$DIR/$i/obs.txt if not exist
	#

	if [ ! -f $DIR/$i/obs.txt ]
	then
		echo "+ --> creating [FILE] $i/obs.txt"
		sed -e "s/LANGCODE/${i}/g" $TPL/obs-home.txt > $DIR/$i/obs.txt
	fi	

		
	#
	# create SIDEBAR 	$DIR/$i/obs/sidebar.txt if not exist
	#

	if [ ! -f $DIR/$i/obs/sidebar.txt ]
	then
		echo "+ --> creating [FILE] $i/obs/sidebar.txt"
		sed -e "s/LANGCODE/${i}/g" $TPL/obs-sidebar.txt > $DIR/$i/obs/sidebar.txt
	fi	


	#
	# create ALL STORIES 	for each story in the en/obs/*.txt directory, cp the story *if it does not exist*
	#

	for t in $TITLES
	do
		if [ ! -f $DIR/$i/obs/$t ]
		then
			echo "  + --> creating [STORY FILE] $i/$t"
			cp $DIR/en/obs/$t $DIR/$i/obs/$t
		fi
	done

	#
	# recursively change the ownership of all files under $DIR/$i to apache.door43
	#

	echo "+ --> setting all perms on $DIR/$i"
	sudo chown -R apache.door43 $DIR/$i
	sudo chmod -R g+w $DIR/$i

done

exit 0
