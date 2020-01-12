#!/usr/bin/env python3
#
#  Copyright (c) 2020 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <rich.mahn@unfoldingword.org>

"""
This script generates the HTML and PDF TN documents
"""
import os
import re
from datetime import datetime
from ..general_tools.file_utils import write_file, read_file, load_json_object, unzip, load_yaml_object
from ..general_tools.usfm_utils import usfm3_to_usfm2
from .pdf_converter import PdfConverter, run_converter


class TnPdfConverter(PdfConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chapters_and_verses = {}
        self.verse_usfm = {}
        self.chunks_text = {}
        self.resource_data = {}
        self.rc_lookup = {}
        self.tn_book_data = {}
        self.tw_words_data = {}
        self.bad_links = {}
        self.bad_notes = {}
        self.usfm_chunks = {}
        self._version = None
        self.my_path = os.path.dirname(os.path.realpath(__file__))
        self.tn_resources_dir = os.path.join(self.my_path, 'resources')

        self.lastEndedWithQuoteTag = False
        self.lastEndedWithParagraphTag = False
        self.openQuote = False
        self.nextFollowsQuote = False
        self.generation_info = {}
        self.soup = None
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.verse_to_chunk = {}

    def get_body_html(self):
        self.logger.info('Generating TA html...')
        # self.toc_html = self.get_toc_from_yaml()
        tn_html = self.get_tn_html()
        return tn_html

    def pad(self, num):
        if self.project_id == 'psa':
            return str(num).zfill(3)
        else:
            return str(num).zfill(2)

    def get_usfm_from_verse_objects(self, verse_objects, depth=0):
        usfm = ''
        for idx, obj in enumerate(verse_objects):
            if obj['type'] == 'milestone':
                usfm += self.get_usfm_from_verse_objects(obj['children'])
            elif obj['type'] == 'word':
                if not self.nextFollowsQuote and obj['text'] != 's':
                    usfm += ' '
                usfm += obj['text']
                self.nextFollowsQuote = False
            elif obj['type'] == 'text':
                obj['text'] = obj['text'].replace('\n', '').strip()
                if not self.openQuote and len(obj['text']) > 2 and obj['text'][-1] == '"':
                    obj['text' ] = '{0} {1}'.format(obj['text'][:-1], obj['text'][-1])
                if not self.openQuote and obj['text'] == '."':
                    obj['text' ] = '. "'
                if len(obj['text']) and obj['text'][0] == '"' and not self.openQuote and obj['text'] not in ['-', '—']:
                    usfm += ' '
                usfm += obj['text']
                if obj['text'].count('"') == 1:
                    self.openQuote = not self.openQuote
                if self.openQuote and '"' in obj['text'] or obj['text'] in ['-', '—', '(', '[']:
                    self.nextFollowsQuote = True
            elif obj['type'] == 'quote':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if idx == len(verse_objects) -1 and obj['tag'] == 'q' and len(obj['text']) == 0:
                    self.lastEndedWithQuoteTag = True
                else:
                    usfm += '\n\\{0} {1}'.format(obj['tag'], obj['text'] if len(obj['text']) > 0 else '')
                if obj['text'].count('"') == 1:
                    self.openQuote = not self.openQuote
                if self.openQuote and '"' in obj['text']:
                    self.nextFollowsQuote = True
            elif obj['type'] == 'section':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
            elif obj['type'] == 'paragraph':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                if idx == len(verse_objects) - 1 and not obj['text']:
                    self.lastEndedWithParagraphTag = True
                else:
                    usfm += '\n\\{0}{1}\n'.format(obj['tag'], obj['text'])
            elif obj['type'] == 'footnote':
                obj['text'] = obj['text'].replace('\n', '').strip() if 'text' in obj else ''
                usfm += r' \{0} {1} \{0}*'.format(obj['tag'], obj['content'])
            else:
                self.logger.error("ERROR! Not sure what to do with this:")
                self.logger.error(obj)
                exit(1)
        return usfm

    def populate_verse_usfm(self):
        self.populate_verse_usfm_ult()
        self.populate_verse_usfm_ust()

    def populate_verse_usfm_ust(self):
        book_data = {}
        book_file = os.path.join(self.resources['ust'].repo_dir, f'{self.book_number}-{self.book_id.upper}.usfm')
        usfm3 = read_file(book_file)
        usfm2 = usfm3_to_usfm2(usfm3)
        chapters = usfm2.split(r'\c ')
        for chapter_usfm in chapters[1:]:
            chapter = int(re.findall('(\d+)', chapter_usfm)[0])
            book_data[chapter] = {}
            chapter_usfm = r'\c '+chapter_usfm
            verses = chapter_usfm.split(r'\v ')
            for verseUsfm in verses[1:]:
                verse = int(re.findall('(\d+)', verseUsfm)[0])
                verseUsfm = r'\v '+verseUsfm
                if re.match(r'^\\v \d+\s*$', verseUsfm, flags=re.MULTILINE):
                    verseUsfm = ''
                book_data[chapter][verse] = verseUsfm
        self.verse_usfm[self.ust_id] = book_data

    def populate_verse_usfm_ult(self):
        bookData = {}
        book_file = os.path.join(self.ult_dir, '{0}-{1}.usfm'.format(self.book_number, self.book_id.upper()))
        usfm3 = read_file(book_file)
        usfm2 = usfm3_to_usfm2(usfm3)
        chapters = usfm2.split(r'\c ')
        for chapterUsfm in chapters[1:]:
            chapter = int(re.findall('(\d+)', chapterUsfm)[0])
            bookData[chapter] = {}
            chapterUsfm = r'\c '+chapterUsfm
            verses = chapterUsfm.split(r'\v ')
            for verseUsfm in verses[1:]:
                verse = int(re.findall('(\d+)', verseUsfm)[0])
                verseUsfm = r'\v '+verseUsfm
                if re.match(r'^\\v \d+\s*$', verseUsfm, flags=re.MULTILINE):
                    verseUsfm = ''
                bookData[chapter][verse] = verseUsfm
        self.verse_usfm[self.ult_id] = bookData

    def populate_chapters_and_verses(self):
        versification_file = os.path.join(self.versification_dir, '{0}.json'.format(self.book_id))
        self.chapters_and_verses = {}
        if os.path.isfile(versification_file):
            self.chapters_and_verses = load_json_object(versification_file)

    @staticmethod
    def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
        csv_reader = csv.reader(utf8_data, dialect=dialect, delimiter=str("\t"), quotechar=str('"'), **kwargs)
        for row in csv_reader:
            yield [cell for cell in row]

    def populate_tn_book_data(self):
        book_file = os.path.join(self.tn_dir, '{0}_tn_{1}-{2}.tsv'.format(self.lang_code, self.book_number, self.book_id.upper()))
        self.tn_book_data = {}
        if not os.path.isfile(book_file):
            return
        book_data = {}
        reader = self.unicode_csv_reader(open(book_file))
        header = next(reader)
        for row in reader:
            data = {}
            found = False
            for idx, field in enumerate(header):
                field = field.strip()
                if idx >= len(row):
                    self.logger.error('ERROR: {0} is malformed'.format(book_file))
                    found = False
                    break
                else:
                    found = True
                    data[field] = row[idx]
            if not found:
                break
            # self.logger.info('{0} {1}:{2}:{3}'.format(data['Book'], data['Chapter'], data['Verse'], data['ID']))
            chapter = data['Chapter'].lstrip('0')
            verse = data['Verse'].lstrip('0')
            if not chapter in book_data:
                book_data[chapter] = {}
            if not verse in book_data[chapter]:
                book_data[chapter][verse] = []
            book_data[str(chapter)][str(verse)].append(data)
        self.tn_book_data = book_data

    def get_tn_html(self):
        tn_html = '''
<section id="tn-{0}">
<div class="resource-title-page">
    <img src="html/logo-utn-256.png" class="logo" alt="UTN">
    <h1 class="section-header">{1} - {2}</h1>
</div>
'''.format(self.book_id, self.tn_manifest['dublin_core']['title'], self.book_title)
        if 'front' in self.tn_book_data and 'intro' in self.tn_book_data['front']:
            intro = markdown2.markdown(self.tn_book_data['front']['intro'][0]['OccurrenceNote'].replace('<br>', '\n'))
            title = self.get_first_header(intro)
            intro = self.fix_tn_links(intro, 'intro')
            intro = self.increase_headers(intro)
            intro = self.decrease_headers(intro, 4)  # bring headers of 3 or more down 1
            intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
            intro_id = 'tn-{0}-front-intro'.format(self.book_id)
            tn_html += '<article id="{0}">\n{1}\n</article>\n\n'.format(intro_id, intro)
            # HANDLE RC LINKS AND BACK REFERENCE
            rc = 'rc://{0}/tn/help/{1}/front/intro'.format(self.lang_code, self.book_id)
            self.resource_data[rc] = {
                'rc': rc,
                'id': intro_id,
                'link': '#'+intro_id,
                'title': title
            }
            self.rc_lookup[intro_id] = rc
            self.get_resource_data_from_rc_links(intro, rc)
            self.verse_to_chunk['front'] = {'intro': title}

        for chapter_verses in self.chapters_and_verses:
            chapter = str(chapter_verses['chapter'])
            self.verse_to_chunk[self.pad(chapter)] = {}
            self.logger.info('Chapter {0}...'.format(chapter))
            if 'intro' in self.tn_book_data[chapter]:
                intro = markdown2.markdown(self.tn_book_data[chapter]['intro'][0]['OccurrenceNote'].replace('<br>',"\n"))
                intro = re.sub(r'<h(\d)>([^>]+) 0+([1-9])', r'<h\1>\2 \3', intro, 1, flags=re.MULTILINE | re.IGNORECASE)
                title = self.get_first_header(intro)
                intro = self.fix_tn_links(intro, chapter)
                intro = self.increase_headers(intro)
                intro = self.decrease_headers(intro, 5, 2)  # bring headers of 5 or more down 2
                intro_id = 'tn-{0}-{1}-intro'.format(self.book_id, self.pad(chapter))
                intro = re.sub(r'<h(\d+)>', r'<h\1 class="section-header">', intro, 1, flags=re.IGNORECASE | re.MULTILINE)
                tn_html += '<article id="{0}">\n{1}\n</article>\n\n'.format(intro_id, intro)
                # HANDLE RC LINKS
                rc = 'rc://{0}/tn/help/{1}/{2}/intro'.format(self.lang_code, self.book_id, self.pad(chapter))
                self.resource_data[rc] = {
                    'rc': rc,
                    'id': intro_id,
                    'link': '#'+intro_id,
                    'title': title
                }
                self.rc_lookup[intro_id] = rc
                self.get_resource_data_from_rc_links(intro, rc)
                self.verse_to_chunk[self.pad(chapter)]['intro'] = title

            chapter_chunk_data = {}
            previous_first_verse = None
            for idx, first_verse in enumerate(chapter_verses['first_verses']):
                if idx < len(chapter_verses['first_verses'])-1:
                    last_verse = chapter_verses['first_verses'][idx+1] - 1
                else:
                    last_verse = int(BOOK_CHAPTER_VERSES[self.book_id][chapter])

                chunk_notes = ''
                for verse in range(first_verse, last_verse + 1):
                    if str(verse) in self.tn_book_data[chapter]:
                        verse_notes = ''
                        for data in self.tn_book_data[chapter][str(verse)]:
                            note_quote = data['GLQuote']
                            note = markdown2.markdown(data['OccurrenceNote'].replace('<br>', "\n"))
                            note = re.sub(r'</*p[^>]*>', '', note, flags=re.IGNORECASE | re.MULTILINE)
                            verse_notes += '''
                <div class="verse-note">
                    <h3 class="verse-note-title">{0} <span class="verse-note-reference">{1}</span></h3>
                    <div class="verse-note-text">
                        {2}
                    </div>
                </div>
            '''.format(note_quote, '({0}:{1})'.format(chapter, verse) if first_verse != last_verse else '', note)
                        rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                                   str(verse).zfill(3))
                        self.get_resource_data_from_rc_links(verse_notes, rc)
                        chunk_notes += verse_notes

                chunk_notes = self.decrease_headers(chunk_notes, 5)  # bring headers of 5 or more #'s down 1
                chunk_notes = self.fix_tn_links(chunk_notes, chapter)

                if previous_first_verse and \
                        (not chunk_notes or not chapter_chunk_data[previous_first_verse]['chunk_notes']):
                    if chunk_notes:
                        chapter_chunk_data[previous_first_verse]['chunk_notes'] = chunk_notes
                    chapter_chunk_data[previous_first_verse]['last_verse'] = last_verse
                else:
                    chapter_chunk_data[first_verse] = {
                        'chunk_notes': chunk_notes,
                        'first_verse': first_verse,
                        'last_verse': last_verse
                    }
                    previous_first_verse = first_verse

            for first_verse in sorted(chapter_chunk_data.keys()):
                last_verse = chapter_chunk_data[first_verse]['last_verse']
                chunk_notes = chapter_chunk_data[first_verse]['chunk_notes']
                if first_verse != last_verse:
                    title = '{0} {1}:{2}-{3}'.format(self.book_title, chapter, first_verse, last_verse)
                else:
                    title = '{0} {1}:{2}'.format(self.book_title, chapter, first_verse)

                verse_ids = []
                for verse in range(first_verse, last_verse+1):
                    verse_id = 'tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), str(verse).zfill(3))
                    verse_ids.append(verse_id)
                    rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                               str(verse).zfill(3))
                    self.resource_data[rc] = {
                        'rc': rc,
                        'id': verse_id,
                        'link': '#'+verse_id,
                        'title': title
                    }
                    self.rc_lookup[verse_id] = rc
                    self.rc_lookup[verse_id + '-top'] = rc
                    self.verse_to_chunk[self.pad(chapter)][str(verse).zfill(3)] = title

                ult_highlighted_scripture = self.get_highlighted_html(self.ult_id, int(chapter), first_verse,
                                                                      last_verse)
                ust_scripture = self.get_plain_html(self.ust_id, int(chapter), first_verse, last_verse)
                scripture = '''
    <h3 class="bible-resource-title">{0}</h3>
    <div class="bible-text">{1}</div>
    <h3 class="bible-resource-title">{2}</h3>
    <div class="bible-text">{3}</div>
'''.format(self.ult_id.upper(), ult_highlighted_scripture, self.ust_id.upper(),
           ust_scripture if ust_scripture else '&nbsp;')

                chunk_article = '''
<article id="{0}-top">
    {1}
    <h2 class="section-header">{2}</h2>
    <div class="tn-notes">
            <div class="col1">
                {3}
            </div>
            <div class="col2">
                {4}
            </div>
    </div>
</article>
'''.format(verse_ids[0], "\n".join(map(lambda x: '<a id="{0}"></a>'.format(x), verse_ids)), title, scripture,
           chunk_notes)
                tn_html += chunk_article
        tn_html += "\n</section>\n\n"
        return tn_html

    def populate_tw_words_data(self):
        groups = ['kt', 'names', 'other']
        if int(self.book_number) < 41:
            ol_path = get_latest_version(os.path.join(self.tn_resources_dir, 'hbo/translationHelps/translationWords'))
        else:
            ol_path = get_latest_version(os.path.join(self.tn_resources_dir, 'el-x-koine/translationHelps/translationWords'))
        if not os.path.isdir(ol_path):
            self.logger.error('{0} not found! Please make sure you ran `setup.sh` in the `tn` dir'.format(ol_path))
            exit(1)
        words = {}
        for group in groups:
            files_path = '{0}/{1}/groups/{2}/*.json'.format(ol_path, group, self.book_id)
            files = glob(files_path)
            for file in files:
                base = os.path.splitext(os.path.basename(file))[0]
                rc = 'rc://{0}/tw/dict/bible/{1}/{2}'.format(self.lang_code, group, base)
                occurrences = load_json_object(file)
                for occurrence in occurrences:
                    context_id = occurrence['contextId']
                    chapter = context_id['reference']['chapter']
                    verse = context_id['reference']['verse']
                    context_id['rc'] = rc
                    if chapter not in words:
                        words[chapter] = {}
                    if verse not in words[chapter]:
                        words[chapter][verse] = []
                    words[chapter][verse].append(context_id)
        self.tw_words_data = words

    def get_plain_html(self, resource, chapter, first_verse, last_verse):
        verses = ''
        footnotes = ''
        while first_verse <= last_verse:
            data = self.chunks_text[str(chapter)][str(first_verse)]
            footnotes_split = re.compile('<div class="footnotes">', flags=re.IGNORECASE | re.MULTILINE)
            verses_and_footnotes = re.split(footnotes_split, data[resource]['html'], maxsplit=1)
            verses += verses_and_footnotes[0]
            if len(verses_and_footnotes) == 2:
                footnote = '<div class="footnotes">{0}'.format(verses_and_footnotes[1])
                if footnotes:
                    footnote = footnote.replace('<hr class="footnotes-hr"/>', '')
                footnotes += footnote
            first_verse = data['last_verse'] + 1
        html = ''
        if verses:
            verses = re.sub(r'\s*<span class="v-num"', '</div><div class="verse"><span class="v-num"', verses, flags=re.IGNORECASE | re.MULTILINE)
            verses = re.sub(r'^</div>', '', verses)
            if verses and '<div class="verse">' in verses:
                verses += '</div>'
            html = verses + footnotes
            html = re.sub(r'\s*\n\s*', ' ', html, flags=re.IGNORECASE | re.MULTILINE)
            html = re.sub(r'\s*</*p[^>]*>\s*', ' ', html, flags=re.IGNORECASE | re.MULTILINE)
            html = html.strip()
            html = re.sub(r'id="(ref-)*fn-', r'id="{0}-\1fn-'.format(resource), html,
                          flags=re.IGNORECASE | re.MULTILINE)
            html = re.sub(r'href="#(ref-)*fn-', r'href="#{0}-\1fn-'.format(resource), html,
                          flags=re.IGNORECASE | re.MULTILINE)
        return html

    def get_highlighted_html(self, resource, chapter, first_verse, last_verse):
        html = self.get_plain_html(resource, chapter, first_verse, last_verse)
        footnotes_split = re.compile('<div class="footnotes">', flags=re.MULTILINE | re.IGNORECASE)
        verses_and_footnotes = footnotes_split.split(html, maxsplit=1)
        verses_html = verses_and_footnotes[0]
        footer_html = ''
        if len(verses_and_footnotes) == 2:
            footer_html = '<div class="footnotes">{0}'.format(verses_and_footnotes[1])
        regex = re.compile(r'<div class="verse"><span class="v-num" id="{0}-\d+-ch-\d+-v-\d+"><sup><strong>(\d+)</strong></sup></span>'.
                           format(resource))
        verses_split = regex.split(verses_html)
        verses = {}
        for i in range(1, len(verses_split), 2):
            verses[int(verses_split[i])] = verses_split[i+1]
        new_html = verses_split[0]
        for verse_num in range(first_verse, last_verse+1):
            words = self.get_all_words_to_match(resource, chapter, verse_num)
            for word in words:
                parts = word['text'].split(' ... ')
                pattern = ''
                replace = ''
                new_parts = []
                for idx, part in enumerate(parts):
                    words_to_ignore = ['a', 'am', 'an', 'and', 'as', 'are', 'at', 'be', 'by', 'did', 'do', 'does', 'done', 'for', 'from', 'had', 'has', 'have', 'he', 'her', 'his', 'i', 'in', 'into', 'less', 'let', 'may', 'might', 'more', 'my', 'not', 'is', 'of', 'on', 'one', 'onto', 'our', 'she', 'than', 'the', 'their', 'then', 'they', 'this', 'that', 'those', 'these', 'to', 'was', 'we', 'who', 'whom', 'with', 'will', 'were', 'your', 'you', 'would', 'could', 'should', 'shall', 'can']
                    part = re.sub(r'^(({0})\s+)+'.format('|'.join(words_to_ignore)), '', part, flags=re.MULTILINE | re.IGNORECASE)
                    if not part or (idx < len(parts)-1 and part.lower().split(' ')[-1] in words_to_ignore):
                        continue
                    new_parts.append(part)
                for idx, part in enumerate(new_parts):
                    pattern += r'(?<![></\\_-])\b{0}\b(?![></\\_-])'.format(part)
                    replace += r'<a href="{0}">{1}</a>'.format(word['contextId']['rc'], part)
                    if idx + 1 < len(new_parts):
                        pattern += r'(.*?)'
                        replace += r'\{0}'.format(idx + 1)
                verses[verse_num] = re.sub(pattern, replace, verses[verse_num], 1, flags=re.MULTILINE | re.IGNORECASE)
            rc = 'rc://{0}/tn/help/{1}/{2}/{3}'.format(self.lang_code, self.book_id, self.pad(chapter),
                                                       str(verse_num).zfill(3))
            verse_text = ''
            if verse_num in verses:
                verse_text = verses[verse_num]
                self.get_resource_data_from_rc_links(verses[verse_num], rc)
                new_html += '<div class="verse"><span class="v-num" id="{0}-{1}-ch-{2}-v-{3}"><sup><strong>{4}</strong></sup></span>{5}'.\
                    format(resource, str(self.book_number).zfill(3), str(chapter).zfill(3), str(verse_num).zfill(3),
                           verse_num, verse_text)
        new_html += footer_html
        return new_html

    def get_all_words_to_match(self, resource, chapter, verse):
        path = '{0}/{1}/{2}.json'.format(
            get_latest_version(os.path.join(self.tn_resources_dir, '{0}/bibles/{1}'.format(self.lang_code, resource))),
            self.book_id, chapter)
        words = []
        data = load_json_object(path)
        chapter = int(chapter)
        if chapter in self.tw_words_data and verse in self.tw_words_data[chapter]:
            context_ids = self.tw_words_data[int(chapter)][int(verse)]
            verse_objects = data[str(verse)]['verseObjects']
            for context_id in context_ids:
                aligned_text = self.get_aligned_text(verse_objects, context_id, False)
                if aligned_text:
                    words.append({'text': aligned_text, 'contextId': context_id})
        return words

    def find_target_from_combination(self, verse_objects, quote, occurrence):
        ol_words = []
        word_list = []
        for verse_object in verse_objects:
            if 'content' in verse_object and 'type' in verse_object and verse_object['type'] == 'milestone':
                ol_words.append(verse_object['content'])
                target_words = []
                for child in verse_object['children']:
                    if child['type'] == 'word':
                        target_words.append(child['text'])
                target = ' '.join(target_words)
                found = False
                for idx, word in enumerate(word_list):
                    if word['ol'] == verse_object['content'] and 'occurrence' in verse_object and \
                            word['occurrence'] == verse_object['occurrence']:
                        word_list[idx]['target'] += ' ... ' + target
                        found = True
                if not found:
                    word_list.append({'ol': verse_object['content'], 'target': target, 'occurrence': verse_object['occurrence']})
        combinations = []
        occurrences = {}
        for i in range(0, len(word_list)):
            ol = word_list[i]['ol']
            target = word_list[i]['target']
            for j in range(i, len(word_list)):
                if i != j:
                    ol += ' '+word_list[j]['ol']
                    target += ' '+word_list[j]['target']
                if ol not in occurrences:
                    occurrences[ol] = 0
                occurrences[ol] += 1
                combinations.append({'ol': ol, 'target': target, 'occurrence': occurrences[ol]})
        for combination in combinations:
            if combination['ol'] == quote and combination['occurrence'] == occurrence:
                return combination['target']
        return None

    def find_target_from_split(self, verse_objects, quote, occurrence, is_match=False):
        words_to_match = []
        if isinstance(quote, list):
            for q in quote:
                words_to_match.append(q['word'])
        else:
            words_to_match = quote.split(' ')
        separator = ' '
        needs_ellipsis = False
        text = ''
        for index, verse_object in enumerate(verse_objects):
            last_match = False
            if 'type' in verse_object and (verse_object['type'] == 'milestone' or verse_object['type'] == 'word'):
                if ((('content' in verse_object and verse_object['content'] in words_to_match) or ('lemma' in verse_object and verse_object['lemma'] in words_to_match)) and verse_object['occurrence'] == occurrence) or is_match:
                    last_match = True
                    if needs_ellipsis:
                        separator += '... '
                        needs_ellipsis = False
                    if text:
                        text += separator
                    separator = ' '
                    if 'text' in verse_object and verse_object['text']:
                        text += verse_object['text']
                    if 'children' in verse_object and verse_object['children']:
                        text += self.find_target_from_split(verse_object['children'], quote, occurrence, True)
                elif 'children' in verse_object and verse_object['children']:
                    child_text = self.find_target_from_split(verse_object['children'], quote, occurrence, is_match)
                    if child_text:
                        last_match = True
                        if needs_ellipsis:
                            separator += '... '
                            needs_ellipsis = False
                        text += (separator if text else '') + child_text
                        separator = ' '
                    elif text:
                        needs_ellipsis = True
            if last_match and (index+1) in verse_objects and verse_objects[index + 1]['type'] == "text" and text:
                if separator == ' ':
                    separator = ''
                separator += verse_objects[index + 1]['text']
        return text

    def get_aligned_text(self, verse_objects, context_id, is_match=False):
        if not verse_objects or not context_id or 'quote' not in context_id or not context_id['quote']:
            return ''
        text = self.find_target_from_combination(verse_objects, context_id['quote'], context_id['occurrence'])
        if text:
            return text
        text = self.find_target_from_split(verse_objects, context_id['quote'], context_id['occurrence'])
        if text:
            return text
        rc = 'rc://{0}/{1}/bible/{2}/{3}/{4}'.format(self.lang_code, self.ult_id, self.book_id,
                                                     context_id['reference']['chapter'],
                                                     context_id['reference']['verse'])
        if int(self.book_number) < 41:
            bad_rc = 'rc://hbo/tw/word/{0}/{1}'.format(context_id['quote'], context_id['occurrence'])
        else:
            bad_rc = 'rc://el-x-koine/tw/word/{0}/{1}'.format(context_id['quote'], context_id['occurrence'])
        if rc not in self.bad_links:
            self.bad_links[rc] = {}
        if int(self.book_number) > 40 or self.book_id.lower() == 'rut' or self.book_id.lower() == 'jon':
            self.bad_links[rc][bad_rc] = context_id['rc']
            self.logger.error('{0} word not found for OL word `{1}` (occurrence: {2}) in `ULT {3} {4}:{5}`'.
                              format(self.lang_code.upper(), context_id['quote'], context_id['occurrence'],
                                     self.book_id.upper(), context_id['reference']['chapter'],
                                     context_id['reference']['verse']))

     def fix_tn_links(self, text, chapter):
        def replace_link(match):
            before_href = match.group(1)
            link = match.group(2)
            after_href = match.group(3)
            linked_text = match.group(4)
            new_link = link
            if link.startswith('../../'):
                # link to another book, which we don't link to so link removed
                return linked_text
            elif link.startswith('../'):
                # links to another chunk in another chapter
                link = os.path.splitext(link)[0]
                parts = link.split('/')
                if len(parts) == 3:
                    # should have two numbers, the chapter and the verse
                    c = parts[1]
                    v = parts[2]
                    new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, c, v.zfill(3))
                if len(parts) == 2:
                    # shouldn't be here, but just in case, assume link to the first chunk of the given chapter
                    c = parts[1]
                    new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, c, '001')
            elif link.startswith('./'):
                # link to another verse in the same chapter
                link = os.path.splitext(link)[0]
                parts = link.split('/')
                v = parts[1]
                new_link = '#tn-{0}-{1}-{2}'.format(self.book_id, self.pad(chapter), v.zfill(3))
            return '<a{0}href="{1}"{2}>{3}</a>'.format(before_href, new_link, after_href, linked_text)
        regex = re.compile(r'<a([^>]+)href="(\.[^"]+)"([^>]*)>(.*?)</a>')
        text = regex.sub(replace_link, text)
        return text


if __name__ == '__main__':
    run_converter(['tn', 'ult', 'ust', 'ta', 'tw'], TnPdfConverter)
