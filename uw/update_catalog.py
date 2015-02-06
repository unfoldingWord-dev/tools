#!/usr/bin/env python
# -*- coding: utf8 -*-
#
#  Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#

'''
Updates the catalog for the translationStudio v2 API.
'''

import os
import sys
import json
import codecs
import urllib2
import argparse
from copy import deepcopy

project_dirs = ['obs']
bible_dirs = ['rut', 'luk', 'tit']
bible_slugs = ['udb', 'ulb']
bible_stat = u'https://api.unfoldingword.org/{0}/txt/1/{0}-{1}/status.json'
obs_v1_api = u'https://api.unfoldingword.org/obs/txt/1'
obs_v1_url = u'{0}/obs-catalog.json'.format(obs_v1_api)
obs_v2_local = u'/var/www/vhosts/api.unfoldingword.org/httpdocs/ts/txt/2'
obs_v2_api = u'https://api.unfoldingword.org/ts/txt/2'


def getURL(url):
    try:
        request = urllib2.urlopen(url).read()
        return request
    except:
        print '  => ERROR retrieving {0}\nCheck the URL'.format(url)
        return

def writeFile(outfile, p):
    makeDir(outfile.rpartition('/')[0])
    f = codecs.open(outfile, 'w', encoding='utf-8')
    f.write(p)
    f.close()

def makeDir(d):
    if not os.path.exists(d):
        os.makedirs(d, 0755)

def getDump(j):
    return json.dumps(j, sort_keys=True, indent=2)

def loadJSON(f, t):
    if os.path.isfile(f):
        return json.load(open(f, 'r'))
    if t == 'd':
      return json.loads('{}')
    else:
      return json.loads('[]')

def obs():
    obs_v1 = getURL(obs_v1_url)
    obs_v1_cat = json.loads(obs_v1)
    langs_cat = []
    # Write OBS catalog for each language
    for e in obs_v1_cat:
        front = getURL(u'{0}/{1}/obs-{1}-front-matter.json'.format(obs_v1_api,
                                                               e['language']))
        frontjson = json.loads(front)
        lang_entry = { 'language': { 'slug': e['language'],
                                     'name': e['string'],
                                     'direction': e['direction'],
                                     'date_modified': e['date_modified']
                                   },
                       'project': { 'name': frontjson['name'],
                                    'desc': frontjson['tagline'],
                                    'meta': []
                                  },
                       'res_catalog': u'{0}/obs/{1}/resources.json'.format(
                                                    obs_v2_api, e['language'])
                     }
        langs_cat.append(lang_entry)
        del e['string']
        del e['direction']
        e['slug'] = 'obs'
        e['name'] = 'Open Bible Stories'
        e['source'] = u'{0}/{1}/obs-{1}.json'.format(obs_v1_api,
                                                                e['language'])
        e['terms'] = u'{0}/{1}/kt-{1}.json'.format(obs_v1_api, e['language'])
        e['notes'] = u'{0}/{1}/tN-{1}.json'.format(obs_v1_api, e['language'])
        outfile = u'{0}/obs/{1}/resources.json'.format(obs_v2_local,
                                                                e['language'])
        del e['language']
        writeFile(outfile, getDump([e]))
    # Write global OBS catalog
    outfile = u'{0}/obs/languages.json'.format(obs_v2_local)
    writeFile(outfile, getDump(langs_cat))

def bible():
    bible_status = {}
    bible_bks = []
    for slug in bible_slugs:
        stat = getURL(bible_stat.format(slug, 'en'))
        bible_status[slug] = json.loads(stat)
        bible_bks += bible_status[slug]['books_published'].keys()

    bks_set = set(bible_bks)
    for bk in bks_set:
        resources_cat = []
        for slug in bible_slugs:
            if bk not in bible_status[slug]['books_published'].keys():
                continue
            lang = bible_status[slug]['lang']
            slug_cat = deepcopy(bible_status[slug])
            slug_cat['source'] = '{0}/{1}/{2}/{3}/source.json'.format(
                                   obs_v2_api, bk, lang, slug)
            slug_cat['terms'] = '{0}/{1}/{2}/{3}/terms.json'.format(
                                   obs_v2_api, bk, lang, slug)
            slug_cat['notes'] = '{0}/{1}/{2}/{3}/notes.json'.format(
                                   obs_v2_api, bk, lang, slug)
            del slug_cat['books_published']
            del slug_cat['lang']
            resources_cat.append(slug_cat)
        outfile = '{0}/{1}/{2}/resources.json'.format(obs_v2_local, bk, lang)
        writeFile(outfile, getDump(resources_cat))

    for bk in bks_set:
        languages_cat = []
        res_info = { 'project': bible_status[slug]['books_published'][bk],
                     'language': { 'slug': 'en',
                               'name': 'English',
                               'direction': 'ltr',
                               'date_modified': bible_status[slug][
                                                             'date_modified'],
                             },
                     'res_catalog': '{0}/{1}/{2}/resources.json'.format(
                                                         obs_v2_api, bk, lang)
                   }
        languages_cat.append(res_info)
        outfile = '{0}/{1}/languages.json'.format(obs_v2_local, bk)
        writeFile(outfile, getDump(languages_cat))


def global_cat():
    global_cat = []
    for x in bible_dirs:
        project_dirs.append(x)
    for p in project_dirs:
        proj_url = u'{0}/{1}/languages.json'.format(obs_v2_api, p)
        proj_data = getURL(proj_url)
        proj_cat = json.loads(proj_data)
        dates = set([x['language']['date_modified'] for x in proj_cat])
        dates_list = list(dates)
        dates_list.sort(reverse=True)
        meta = []
        if proj_cat[0]['project']['meta']:
            if 'Bible: OT' in proj_cat[0]['project']['meta']:
                meta += [ 'bible-ot', 'bible', 'ot' ]
            if 'Bible: NT' in proj_cat[0]['project']['meta']:
                meta += [ 'bible-nt', 'bible', 'nt' ]
        global_cat.append({ 'slug': p,
                            'date_modified': dates_list[0],
                            'lang_catalog': proj_url,
                            'meta': meta
                          })
    # Write global catalog
    outfile = u'{0}/catalog.json'.format(obs_v2_local)
    writeFile(outfile, getDump(global_cat))

def main():
    obs()
    bible()  # languages.json
    global_cat()


if __name__ == '__main__':
    main()
