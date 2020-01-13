import os
import markdown2
from bs4 import BeautifulSoup


def get_obs_chapter_data(obs_dir, chapter_num):
    obs_chapter_data = {
        'title': None,
        'frames': [],
        'images': [],
        'bible_reference': None
    }
    obs_chapter_file = os.path.join(obs_dir, 'content', f'{chapter_num}.md')
    if os.path.isfile(obs_chapter_file):
        soup = BeautifulSoup(markdown2.markdown_path(os.path.join(obs_dir, 'content', f'{chapter_num}.md')),
                             'html.parser')
        obs_chapter_data['title'] = soup.h1.text
        paragraphs = soup.find_all('p')
        for idx, p in enumerate(paragraphs):  # iterate over loop [above sections]
            if idx % 2 == 1:
                obs_chapter_data['frames'].append(p.text)
            elif p.img:
                src = p.img['src'].split('?')[0]
                obs_chapter_data['images'].append(src)
            else:
                obs_chapter_data['bible_reference'] = p.text
    return obs_chapter_data
