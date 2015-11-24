#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#  Richard Mahn <richard_mahn@wycliffeassociates.org>
#

import codecs
import json
import os
import shlex
import urllib
import re
import datetime
import argparse
import sys
from subprocess import Popen, PIPE

OBSURL = 'https://api.unfoldingword.org/obs/txt/1/{0}/obs-{0}.json'
NOTESURL = 'https://api.unfoldingword.org/obs/txt/1/{0}/tN-{0}.json'
TERMSURL = 'https://api.unfoldingword.org/obs/txt/1/{0}/kt-{0}.json'
CHECKURL = 'https://api.unfoldingword.org/obs/txt/1/{0}/CQ-{0}.json'

OUTFILE = 'obs_tn-{0}-{1}.{2}'

class Stories(list):
    """
    Retrieves data from api.unfoldingword.org and parses it into a collection of Note objects.
    One Note object per frame
    """
    def __init__(self, lang):
        super(Stories, self).__init__()
        self.lang = lang
        response = urllib.urlopen(OBSURL.format(lang))
        data = json.loads(response.read())
        for obj in data['chapters']:
            if 'number' in obj:
                self.append(Story(obj))

    def get_story(self, story_id):
        """
        Gets the story with the desired story id
        :rtype : Story
        """
        for story in self:
            if story.story_id == story_id:
                return story

        # if you are here, the story was not found
        return None

    def get_frame(self, frame_id):
        """
        Gets the frame with the desired frame id
        :rtype : Frame
        """
        story_id = frame_id[:2]
        for story in self:
            if story.story_id == story_id:
                for frame in story.frames:
                    if frame.frame_id == frame_id:
                        return frame

        # if you are here, the frame was not found
        return None


class Story:
    def __init__(self, obj):
        self.story_id = obj['number']
        self.frames = []
        self.questions = []
        self.title = obj['title']
        self.ref = obj['ref']

        for frm in obj['frames']:
            self.frames.append(Frame(frm))


class Frame:
    def __init__(self, obj):
        self.frame_id = obj['id']
        self.text = obj['text']
        self.notes = None
        self.questions = []
        self.key_terms = []


class Notes:
    """
    Retrieves data from api.unfoldingword.org and parses it into a collection of Note objects.
    One Note object per frame
    """
    def __init__(self, all_stories, lang):
        """
        :type all_stories: Stories
        """
        self.lang = lang
        response = urllib.urlopen(NOTESURL.format(lang))
        data = json.loads(response.read())
        for obj in data:
            if 'id' in obj:
                all_stories.get_frame(obj['id']).notes = Note(obj)


class Note:
    def __init__(self, obj):
        self.frame_id = obj['id']
        self.note_items = obj['tn']


class Terms(list):
    """
    Retrieves data from api.unfoldingword.org and parses it into a collection of Term objects
    """
    def __init__(self, all_stories, lang):
        super(Terms, self).__init__()
        self.lang = lang
        response = urllib.urlopen(TERMSURL.format(lang))
        data = json.loads(response.read())
        term_id = 0
        for obj in data:
            if 'term' in obj:
                term_id += 1
                self.append(Term(obj, term_id))

                # look for references in the examples
                for ex in obj['ex']:
                    all_stories.get_frame(ex['ref']).key_terms.append([term_id, obj['term']])


class Term:
    def __init__(self, obj, term_id):
        self.term_id = term_id
        self.term = obj['term']
        self.definition = obj['def']
        self.examples = obj['ex']
        if 'aliases' in obj:
            self.aliases = obj['aliases']
        else:
            self.aliases = []


class Questions:
    """
    Retrieves data from api.unfoldingword.org and parses it into a collection of StoryQuestions objects
    """
    def __init__(self, all_stories, lang):
        self.lang = lang
        response = urllib.urlopen(CHECKURL.format(lang))
        data = json.loads(response.read())
        for obj in data:
            if 'id' in obj:
                all_stories.get_story(obj['id']).questions = obj['cq']


class StoryQuestions:
    def __init__(self, obj):
        self.story_id = obj['id']
        self.question_items = obj['cq']


def fix_b_tags(html):
    """
    We need to do this because the data has a lot of closing 'b' tags missing the slash
    :param html: string
    :return: string
    """

    # make sure there are the same number of opening and closing tags
    num = html.count('<b>') - html.count('</b>')

    # if more oepning than closing, change the last one to a closing tag
    if num > 0:
        return html[::-1].replace('<b>'[::-1], '</b>'[::-1], 1)[::-1]

    return html


def make_html(all_stories, all_terms):
    """
    :type all_terms: Terms
    :type all_stories: Stories
    """
    nl = u"\n"
    divs = u''

    global lang, date, outpath

    for story in all_stories:

        # hyperlink to the story: story_01
        div = u'<a name="story_' + story.story_id + u'"></a><div class="page">' + nl + u'<h2>' \
              + story.title + u'</h2>' + nl

        # checking questions
        div += u'<div class="frame">' + nl
        div += u'<h4 style="margin-bottom: 0">Checking Quesitons:</h4>' + nl
        div += u'<p style="margin-top: 10px; margin-bottom: 20px;">' \
               + u'These questions will be used by translators to conduct community checks of this story.</p>' + nl
        div += u'<table class="cq">' + nl

        for question in story.questions:
            div += u'<tr><td><table class="cq-inner">' + nl
            div += u'<tr class="q"><td class="q">Q?</td><td>' + fix_b_tags(question['q']) + u'</td></tr>' + nl
            div += u'<tr class="a"><td class="a">A.</td><td>' + fix_b_tags(question['a'])

            for ref in question['ref']:
                div += u' <a href="#frame_' + ref + u'">[' + ref + u']</a>'

            div += u'</td></tr>' + nl
            div += u'</table></td></tr>' + nl

        div += u'</table>' + nl
        div += u'</div>' + nl

        # each frame starts a new page
        for frame in story.frames:
            div += u'<div class="frame">' + nl

            # hyperlink to the frame: frame_01-01
            div += u'<a name="frame_' + frame.frame_id + u'"></a><h4>[' + frame.frame_id + u']</h4>' + nl
            div += u'<p>' + frame.text + u'</p>' + nl

            # display key terms in a list of links
            div += u'<h4>Important Terms:</h4>' + nl + u'<ul>' + nl
            for term in frame.key_terms:
                div += u'<li><a href="#term_' + unicode(term[0]) + u'">' + term[1] + u'</a></li>' + nl

            div += u'</ul>' + nl

            # display the notes in a list
            div += u'<h4>Translation Notes:</h4>' + nl + u'<ul>' + nl
            for note in frame.notes.note_items:
                div += u'<li><strong>' + note['ref'] + u':</strong> ' \
                       + fix_b_tags(note['text']) + '</li>' + nl

            div += u'</ul>' + nl

            div += u'</div>' + nl

        div += u'</div>' + nl
        divs += div

    # key terms is a new section
    div = u'<div class="page">' + nl + u'<h2>Important Words</h2></a>' + nl
    for term in all_terms:
        div += u'<div class="frame">' + nl
        div += u'<a name="term_' + unicode(term.term_id) + u'"></a><h4>' + term.term

        for alias in term.aliases:
            div += u', ' + alias

        # hyperlink to the term: term_1
        div += u'</h4>' + nl
        div += u'<h5>Definition:</h5>' + nl
        div += u'<p>' + fix_b_tags(term.definition) + u'</p>' + nl

        div += u'<h5>Examples:</h5>' + nl + u'<ul>' + nl
        for ex in term.examples:
            div += u'<li><strong>[' + ex['ref'] + u']</strong> ' + fix_b_tags(ex['text']) + u'</li>' + nl

        div += u'</ul>' + nl
        div += u'</div>' + nl

    div += u'</div>' + nl
    divs += div

    # read the template
    with open(os.path.dirname(os.path.realpath(__file__)) + '/obs_notes_template.html', 'r') as f:
        html = f.read()

    # insert the html into the template
    regex = re.compile(r"^(.*<body>)(.*?)(</body>.*)$", re.DOTALL | re.MULTILINE)
    match = regex.search(html)
    if match:
        html = match.group(1) + "\n" + divs + match.group(3)

    # write the output file
    with codecs.open('/'.join([outpath, OUTFILE.format(lang, date, 'html')]), 'w', 'utf-8') as out_file:
        out_file.write(html)

    return html


def html_to_docx(html):
    global lang, date, outpath

    # html = html.replace('<a href="#', '<a href="')
    command = shlex.split('/usr/bin/pandoc --toc --toc-depth=1 -f html -t docx -o "' + '/'.join([outpath, OUTFILE.format(lang, date, 'docx')]) + '"')
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate(html.encode('utf-8'))

    if len(err) > 0:
        print err


if __name__ == '__main__':
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--language', dest="lang", default='en',
        required=False, help="Language code")
    parser.add_argument('-o', '--output', dest="outpath", default='.',
        required=False, help="Output path")

    args = parser.parse_args(sys.argv[1:])

    lang = args.lang

    outpath = args.outpath

    stories = Stories(lang)
    notes = Notes(stories, lang)
    terms = Terms(stories, lang)
    questions = Questions(stories, lang)

    html_to_docx(make_html(stories, terms))