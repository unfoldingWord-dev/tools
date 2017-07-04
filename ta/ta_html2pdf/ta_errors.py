#!/usr/bin/env python
"""
Finds issues with tA pages, links, TOC, config, etc.

"""
import logging
import sys
import os
import yaml
import codecs

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class TaInspector(object):
    def __init__(self, repo_dir):
        """
        :param string repo_dir:
        """
        self.repo_dir = repo_dir  # Local directory
        self.dirs = [name for name in os.listdir(self.repo_dir) if os.path.isfile(os.path.join(self.repo_dir, name, 'toc.yaml'))]
        self.links = []

    def check_exists(self, type, link, d=None, parent=None):
        dirs = []
        if d:
            dirs.append(d)
        else:
            dirs = self.dirs
        found = None
        for d in dirs:
            if os.path.isdir(os.path.join(self.repo_dir, d, link)):
                if not found:
                    found = d
                else:
                    logger.critical('Dependency {0} found in {1} and {2}'.format(link, found, d))
        if found:
            if not os.path.isfile(os.path.join(self.repo_dir, found, link, 'title.md')):
                logger.critical('No title.md for {0}/{1}'.format(found, link))
            if not os.path.isfile(os.path.join(self.repo_dir, found, link, 'sub-title.md')):
                logger.critical('No sub-title.md for {0}/{1}'.format(found, link))
            if not os.path.isfile(os.path.join(self.repo_dir, found, link, '01.md')):
                logger.critical('No 01.md for {0}/{1}'.format(found, link))
        elif type == 'TOC':
            logger.critical('Article {0} in {1}/toc.yaml does not exit ({1}/{0} does not exist)'.format(link, d))
        else:
            logger.critical('{0} {1} for {2} in {3}/config.yaml not found!'.format(type, link, parent, d))

    def inspect_section(self, d, section, config):
        if 'link' in section:
            link = section['link']
            if link in self.links:
                logger.critical('There is already a link called {0}'.format(link))
            else:
                self.links.append(link)
            self.check_exists('TOC', link, d)
            if link in config:
                if 'dependencies' in config[link] and config[link]['dependencies']:
                    for dependency in config[link]['dependencies']:
                        self.check_exists('Dependency', dependency, None, link)
                if 'recommended' in config[link] and config[link]['recommended']:
                    for recommended in config[link]['recommended']:
                        self.check_exists('Recommended', recommended, None, link)
            else:
                logger.warning('{0} does not have an entry in the {1}/config.yaml file'.format(link, d))
        if 'sections' in section:
            for section in section['sections']:
                self.inspect_section(d, section, config)

    def run(self):
        for d in self.dirs:
            toc_path = os.path.join(self.repo_dir, d, 'toc.yaml')
            config_path = os.path.join(self.repo_dir, d, 'config.yaml')
            with codecs.open(toc_path, 'r', encoding='utf-8-sig') as f:
                toc = yaml.load(f)
            with codecs.open(config_path, 'r', encoding='utf-8-sig') as f:
                config = yaml.load(f)
            for section in toc['sections']:
                self.inspect_section(d, section, config)
            for link in config:
                if link not in self.links:
                    logger.warning('{0} in {1}/config.yaml is never used.'.format(link, d))
            for sub in [name for name in os.listdir(os.path.join(self.repo_dir, d)) if os.path.isfile(os.path.join(self.repo_dir, name, 'toc.yaml'))]:
                if sub not in self.links:
                    logger.warning('{0}/{1} is never used in the TOC.'.format(d, sub))


def main():
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        logger.critical('You must provide the path to the tA repo!')
        exit(1)
    repo_dir = sys.argv[1]
    ta = TaInspector(repo_dir)
    ta.run()


if __name__ == '__main__':
    main()
