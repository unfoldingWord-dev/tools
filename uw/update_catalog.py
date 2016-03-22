#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>


"""
Updates the catalog for the translationStudio and unfoldingWord v2 APIs.
"""
import argparse
import os
import json
import time
import codecs
import urllib2
# noinspection PyUnresolvedReferences
import datetime as dt
from copy import deepcopy
import sys

rtl_langs = ['ar']
project_dirs = ['obs']
bible_dirs = [
    '1ch', '1co', '1jn', '1ki', '1pe', '1sa', '1th', '1ti', '2ch',
    '2co', '2jn', '2ki', '2pe', '2sa', '2th', '2ti', '3jn', 'act',
    'amo', 'col', 'dan', 'deu', 'ecc', 'eph', 'est', 'exo', 'ezk',
    'ezr', 'gal', 'gen', 'hab', 'hag', 'heb', 'hos', 'jas', 'jdg',
    'jer', 'jhn', 'job', 'jol', 'jon', 'jos', 'jud', 'lam', 'lev',
    'luk', 'mal', 'mat', 'mic', 'mrk', 'nam', 'neh', 'num', 'oba',
    'phm', 'php', 'pro', 'rev', 'rom', 'rut', 'sng', 'tit', 'zec',
    'zep', 'isa', 'psa'
]
bible_slugs = [('udb', 'en'), ('ulb', 'en'), ('avd', 'ar')]

usfm_api = u'https://api.unfoldingword.org/{0}/txt/1/{0}-{1}/{2}?{3}'
bible_stat = u'https://api.unfoldingword.org/{0}/txt/1/{0}-{1}/status.json'
obs_v1_api = u'https://api.unfoldingword.org/obs/txt/1'
obs_v1_url = u'{0}/obs-catalog.json'.format(obs_v1_api)
obs_v2_local = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/ts/txt/2'
obs_v2_api = u'https://api.unfoldingword.org/ts/txt/2'
uw_v2_api = u'https://api.unfoldingword.org/uw/txt/2/catalog.json'
uw_v2_local = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/uw/txt/2/catalog.json'
lang_url = u'http://td.unfoldingword.org/exports/langnames.json'
ts_obs_langs_url = u'https://api.unfoldingword.org/ts/txt/2/obs/languages.json'
obs_audio_url = u'https://api.unfoldingword.org/obs/mp3/1/en/en-obs-v4/status.json'


def get_additional_bibles():
    global bible_slugs

    dir_base = '/var/www/vhosts/api.unfoldingword.org/httpdocs/{0}/txt/1/'

    for ver in ['ulb', 'udb']:
        dir_name = dir_base.format(ver)
        if not os.path.isdir(dir_name):
            continue

        for sub_dir in os.listdir(dir_name):
            lang_code = sub_dir[4:]

            # skip english
            if lang_code != 'en':
                bible_slugs.append((ver, lang_code))


def get_url(url):
    # noinspection PyBroadException
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        return False


def write_file(outfile, p):
    make_dir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()


def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)


def get_dump(j):
    return json.dumps(j, sort_keys=True)


def load_json(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
        return json.loads('{}')
    else:
        return json.loads('[]')


def obs(obs_v1_cat):
    langs_cat = []
    # Write OBS catalog for each language
    for e in obs_v1_cat:
        front = get_url(u'{0}/{1}/obs-{1}-front-matter.json'.format(obs_v1_api,
                                                                    e['language']))
        front_json = json.loads(front)
        lang_entry = {'language': {'slug': e['language'],
                                   'name': e['string'],
                                   'direction': e['direction'],
                                   'date_modified': e['date_modified']
                                   },
                      'project': {'name': front_json['name'],
                                  'desc': front_json['tagline'],
                                  'meta': []
                                  }
                      }
        del e['string']
        del e['direction']
        e['slug'] = 'obs'
        e['name'] = 'Open Bible Stories'
        e['source'] = add_date(u'{0}/{1}/obs-{1}.json'.format(obs_v1_api,
                                                              e['language']))
        e['terms'] = add_date(u'{0}/{1}/kt-{1}.json'.format(obs_v1_api,
                                                            e['language']))
        e['notes'] = add_date(u'{0}/{1}/tN-{1}.json'.format(obs_v1_api,
                                                            e['language']))
        e['tw_cat'] = add_date(u'{0}/{1}/tw_cat-{1}.json'.format(obs_v1_api,
                                                                 e['language']))
        e['checking_questions'] = add_date(u'{0}/{1}/CQ-{1}.json'.format(
                obs_v1_api, e['language']))
        e['date_modified'] = most_recent(e)
        outfile = u'{0}/obs/{1}/resources.json'.format(obs_v2_local,
                                                       e['language'])
        lang = e['language']
        del e['language']
        write_file(outfile, get_dump([e]))

        lang_entry['res_catalog'] = u'{0}/obs/{1}/resources.json?date_modified={2}'.format(
                obs_v2_api, lang, e['date_modified'])
        langs_cat.append(lang_entry)
    # Write global OBS catalog
    outfile = u'{0}/obs/languages.json'.format(obs_v2_local)
    write_file(outfile, get_dump(langs_cat))


def add_date(url):
    """
    Adds 'date_modified=datestamp' to URL based on value found in the url.'
    :param url:
    """
    src_str = get_url(url)
    if not src_str:
        return url
    src = json.loads(src_str)
    if type(src) == dict:
        date_mod = src['date_modified']
    else:
        date_mod = [x['date_modified'] for x in src if 'date_modified' in x][0]
    return u'{0}?date_modified={1}'.format(url, date_mod)


def most_recent(cat):
    """
    Returns date_modified string that matches the most recent sub catalog.
    :param cat:
    """
    try:
        date_mod = cat['date_modified']
    except KeyError:
        date_mod = cat['language']['date_modified']
    for k in cat.keys():
        if 'date_modified' not in cat[k]:
            continue

        if not type(cat[k]) == unicode:
            continue

        item_date_mod = cat[k].split('date_modified=')[1]
        if int(item_date_mod) > int(date_mod):
            date_mod = item_date_mod

    return date_mod


def bible(lang_names, bible_status, bible_bks, langs):
    bks_set = set(bible_bks)
    for bk in bks_set:
        for lang_iter in langs:
            resources_cat = []
            for slug, lang in bible_slugs:
                if bk not in bible_status[(slug, lang)]['books_published'].keys():
                    continue

                if lang != lang_iter:
                    continue

                lang = bible_status[(slug, lang)]['lang']
                slug_cat = deepcopy(bible_status[(slug, lang)])
                slug_cat['source'] = add_date('{0}/{1}/{2}/{3}/source.json'
                                              .format(obs_v2_api, bk, lang, slug))
                source_date = u''
                if '?' in slug_cat['source']:
                    source_date = slug_cat['source'].split('?')[1]
                usfm_name = u'{0}-{1}.usfm'.format(bible_status[(slug, lang)][
                                                       'books_published'][bk]['sort'], bk.upper())
                slug_cat['usfm'] = usfm_api.format(slug.split('-', 1)[0],
                                                   lang, usfm_name, source_date).rstrip(u'?')
                slug_cat['terms'] = add_date('{0}/bible/{1}/terms.json'.format(
                        obs_v2_api, lang))
                slug_cat['notes'] = add_date('{0}/{1}/{2}/notes.json'.format(
                        obs_v2_api, bk, lang))
                slug_cat['tw_cat'] = add_date(u'{0}/{1}/{2}/tw_cat.json'.format(
                        obs_v2_api, bk, lang))
                slug_cat['checking_questions'] = add_date(
                        '{0}/{1}/{2}/questions.json'.format(obs_v2_api, bk, lang))

                del slug_cat['books_published']
                del slug_cat['lang']
                slug_cat['date_modified'] = most_recent(slug_cat)
                resources_cat.append(slug_cat)
            outfile = '{0}/{1}/{2}/resources.json'.format(obs_v2_local, bk,
                                                          lang_iter)
            write_file(outfile, get_dump(resources_cat))

    for bk in bks_set:
        languages_cat = []
        langs_processed = []
        for lang_iter in langs:
            for slug, lang in bible_slugs:
                if lang in langs_processed:
                    continue
                if lang != lang_iter:
                    continue
                if (slug, lang_iter) not in bible_status:
                    continue
                if bk not in bible_status[(slug, lang_iter)]['books_published'].keys():
                    continue
                lang_info = get_lang_info(lang_iter, lang_names)
                res_info = {'project': bible_status[(slug, lang_iter)]['books_published'][bk],
                            'language': {'slug': lang_info['lc'],
                                         'name': lang_info['ln'],
                                         'direction': lang_info['dir'],
                                         'date_modified':
                                             bible_status[(slug, lang_iter)]['date_modified'],
                                         },
                            'res_catalog': add_date(
                                    '{0}/{1}/{2}/resources.json'.format(
                                            obs_v2_api, bk, lang_info['lc']))
                            }
                res_info['language']['date_modified'] = most_recent(res_info)
                languages_cat.append(res_info)
                langs_processed.append(lang)
        outfile = '{0}/{1}/languages.json'.format(obs_v2_local, bk)
        write_file(outfile, get_dump(languages_cat))


def get_lang_info(lc, lang_names):
    lang_info = [x for x in lang_names if x['lc'] == lc][0]
    lang_info['dir'] = 'ltr'
    if lc in rtl_langs:
        lang_info['dir'] = 'rtl'
    return lang_info


def ts_cat():
    ts_categories = []
    for x in bible_dirs:
        project_dirs.append(x)
    for p in project_dirs:
        proj_url = u'{0}/{1}/languages.json'.format(obs_v2_api, p)
        proj_data = get_url(proj_url)
        proj_cat = json.loads(proj_data)
        dates = set([x['language']['date_modified'] for x in proj_cat])
        dates_list = list(dates)
        dates_list.sort(reverse=True)
        sort = '01'
        if p in bible_dirs:
            sort = [x['project']['sort'] for x in proj_cat if 'project' in x][0]
        meta = []
        if proj_cat[0]['project']['meta']:
            if 'Bible: OT' in proj_cat[0]['project']['meta']:
                meta += ['bible-ot']
            if 'Bible: NT' in proj_cat[0]['project']['meta']:
                meta += ['bible-nt']
        ts_categories.append({'slug': p,
                              'date_modified': dates_list[0],
                              'lang_catalog': u'{0}?date_modified={1}'.format(
                                      proj_url, dates_list[0]),
                              'sort': sort,
                              'meta': meta
                              })
    # Write global catalog
    outfile = u'{0}/catalog.json'.format(obs_v2_local)
    write_file(outfile, get_dump(ts_categories))


def uw_cat(obs_v1_cat, bible_status):
    # Create Bible section
    uw_bible = {'title': 'Bible',
                'slug': 'bible',
                'langs': []
                }
    lang_cat = {}
    for slug, lang in bible_slugs:
        date_mod = get_seconds(bible_status[(slug, lang)]['date_modified'])
        if lang not in lang_cat:
            lang_cat[lang] = {'lc': lang,
                              'mod': date_mod,
                              'vers': []
                              }
        ver = {'name': bible_status[(slug, lang)]['name'],
               'slug': bible_status[(slug, lang)]['slug'],
               'mod': date_mod,
               'status': bible_status[(slug, lang)]['status'],
               'toc': []
               }
        bk_pub = bible_status[(slug, lang)]['books_published']
        short_slug = slug.split('-', 1)[0]
        for x in bk_pub:
            usfm_name = u'{0}-{1}.usfm'.format(bk_pub[x]['sort'], x.upper())
            source = usfm_api.format(short_slug, lang, usfm_name, u'').rstrip(u'?')
            source_sig = source.replace('.usfm', '.sig')
            pdf = source.replace('.usfm', '.pdf')
            ver['toc'].append({'title': bk_pub[x]['name'],
                               'slug': x,
                               'mod': date_mod,
                               'desc': bk_pub[x]['desc'],
                               'sort': bk_pub[x]['sort'],
                               'src': source,
                               'src_sig': source_sig,
                               'pdf': pdf
                               })
        ver['toc'].sort(key=lambda s: s['sort'])
        for x in ver['toc']:
            del x['sort']
        lang_cat[lang]['vers'].append(ver)
    uw_bible['langs'] = [lang_cat[k] for k in lang_cat.iterkeys()]
    uw_bible['langs'].sort(key=lambda c: c['lc'])

    # Create OBS section
    uw_obs = {'title': 'Open Bible Stories',
              'slug': 'obs',
              'langs': []
              }
    ts_obs_langs_str = get_url(ts_obs_langs_url)
    ts_obs_langs = json.loads(ts_obs_langs_str)
    for e in obs_v1_cat:
        date_mod = get_seconds(e['date_modified'])
        desc = u''
        name = u''
        for x in ts_obs_langs:
            if x['language']['slug'] == e['language']:
                desc = x['project']['desc']
                name = x['project']['name']
        slug = u'obs-{0}'.format(e['language'])
        source = u'{0}/{1}/{2}.json'.format(obs_v1_api, e['language'], slug)
        source_sig = source.replace('.json', '.sig')
        media = get_media(e['language'])
        entry = {'lc': e['language'],
                 'mod': date_mod,
                 'vers': [{'name': name,
                           'slug': slug,
                           'mod': date_mod,
                           'status': e['status'],
                           'toc': [{'title': '',
                                    'slug': '',
                                    'media': media,
                                    'mod': date_mod,
                                    'desc': desc,
                                    'src': source,
                                    'src_sig': source_sig
                                    }]
                           }]
                 }
        uw_obs['langs'].append(entry)
    uw_obs['langs'].sort(key=lambda c: c['lc'])

    # Write combined uW catalog
    mods = [int(x['mod']) for x in uw_bible['langs']]
    mods += [int(x['mod']) for x in uw_obs['langs']]
    mods.sort(reverse=True)
    uw_category = {'cat': [uw_bible, uw_obs], 'mod': mods[0]}
    write_file(uw_v2_local, get_dump(uw_category))


def get_media(lang):
    media = {'audio': {},
             'video': {},
             }
    if lang == 'en':
        obs_audio = get_url(obs_audio_url)
        media['audio'] = json.loads(obs_audio)
        del media['audio']['slug']
    return media


def get_seconds(date_str):
    today = ''.join(str(dt.date.today()).rsplit('-')[0:3])
    date_secs = time.mktime(dt.datetime.strptime(date_str,
                                                 "%Y%m%d").timetuple())
    if date_str == today:
        date_secs = time.mktime(dt.datetime.now().timetuple())
    return str(int(date_secs))


def main():
    # OBS
    obs_v1 = get_url(obs_v1_url)
    obs_v1_catalog = json.loads(obs_v1)
    obs(deepcopy(obs_v1_catalog))

    # Bible
    lang_names = json.loads(get_url(lang_url))
    bible_status = {}
    bible_bks = []
    langs = set([x[1] for x in bible_slugs])
    for slug, lang in bible_slugs:
        stat = get_url(bible_stat.format(slug.split('-', 1)[0], lang))
        bible_status[(slug, lang)] = json.loads(stat)
        bible_bks += bible_status[(slug, lang)]['books_published'].keys()
    bible(lang_names, bible_status, bible_bks, langs)

    # Global
    ts_cat()
    uw_cat(obs_v1_catalog, bible_status)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest="lang", default=False,
                        required=False, help="Language code of resource.")
    parser.add_argument('-s', '--slug', dest="slug", default=False,
                        required=False, help="Slug of resource name (e.g. ulb).")

    args = parser.parse_args(sys.argv[1:])

    if args.slug and args.lang:
        bible_slugs = [(args.slug, args.lang), ]
    else:
        get_additional_bibles()

    main()
