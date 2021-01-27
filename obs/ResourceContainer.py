import os
import re
from datetime import datetime, date
from glob import glob
from json.decoder import JSONDecodeError
from yaml.parser import ParserError, ScannerError
from typing import Dict, List, Set, Any, Optional, Union

from .door43_tools.td_language import TdLanguage
from .door43_tools.bible_books import BOOK_NAMES
from general_tools.file_utils import load_json_object, load_yaml_object, read_file

class Language:
    def __init__(self, rc, language:Dict[str,str]) -> None:
        """
        :param RC rc:
        :param dict language:
        """
        self.rc = rc
        self.language = language
        if not isinstance(self.language, dict):
            raise Exception('Missing dict parameter: language')


    @property
    def identifier(self) -> str:
        if 'identifier' in self.language and self.language['identifier']:
            return self.language['identifier'].lower()
        elif 'slug' in self.language and self.language['slug']:
            return self.language['slug'].lower()
        elif 'id' in self.language and self.language['id']:
            return self.language['id'].lower()
        else:
            return 'en'


    @property
    def direction(self) -> str:
        if 'direction'in self.language:
            return self.language['direction']
        if 'dir'in self.language:
            return self.language['dir']
        else:
            return 'ltr'


    @property
    def title(self) -> str:
        if 'title'in self.language:
            return self.language['title']
        elif 'name'in self.language:
            return self.language['name']
        else:
            return 'English'
# end of Language class



class Project:
    def __init__(self, rc, project=None) -> None:
        """
        :param RC rc:
        :param dict project:
        """
        self.rc = rc
        self.project = project
        if not self.project:
            self.project = {}

        if not isinstance(self.rc, RC):
            raise Exception('Missing RC parameter: rc')
        self.config_yaml = None
        self.toc_yaml = None


    @property
    def identifier(self) -> str:
        if 'identifier'in self.project:
            return self.project['identifier'].lower()
        elif 'id'in self.project:
            return self.project['id'].lower()
        elif 'project_id' in self.project and self.project['project_id']:
            return self.project['project_id'].lower()
        else:
            return self.rc.resource.identifier


    @property
    def title(self) -> str:
        if 'title'in self.project and self.project['title']:
            return self.project['title']
        elif 'name'in self.project and self.project['name']:
            return self.project['name']
        elif self.rc.path and os.path.isfile(os.path.join(self.rc.path, self.path, 'title.txt')):
            self.project['title'] = read_file(os.path.join(self.rc.path, self.path, 'title.txt'))
            return self.project['title']
        elif self.rc.path and os.path.isfile(os.path.join(self.rc.path, 'title.txt')):
            self.project['title'] = read_file(os.path.join(self.rc.path, 'title.txt'))
            return self.project['title']
        else:
            return self.rc.resource.title


    @property
    def path(self) -> str:
        if 'path' in self.project and self.project['path']:
            return self.project['path']
        elif self.rc.path and os.path.isdir(os.path.join(self.rc.path, './content')):
                return './content'
        else:
            return './'


    @property
    def sort(self) -> str:
        return self.project.get('sort', '1')


    @property
    def versification(self) -> str:
        return self.project.get('versification', 'kjv')


    @property
    def categories(self) -> list:
        return self.project.get('categories', [])


    def toc(self) -> str:
        return self.rc.toc(self.identifier)


    def config(self) -> str:
        return self.rc.config(self.identifier)


    def chapters(self):
        return self.rc.chapters(self.identifier)


    def chunks(self, chapter_identifier=None):
        return self.rc.chunks(self.identifier, chapter_identifier)


    def usfm_files(self):
        return self.rc.usfm_files(self.identifier)


    def as_dict(self) -> Dict[str,Any]:
        return {
            'categories': self.categories,
            'identifier': self.identifier,
            'path': self.path,
            'sort': self.sort,
            'title': self.title,
            'versification': self.versification
        }
# end of Project class



class RC:
    current_version = '0.2'

    def __init__(self, directory:Optional[str]=None, repo_name:Optional[str]=None, manifest:Optional[Dict[str,Any]]=None) -> None:
        """
        :param string directory:
        :param string repo_name:
        :param dict manifest:
        """
        self._dir = directory
        self.loadeded_manifest_file = False
        if directory is not None: assert os.path.isdir(directory)
        self._manifest = manifest
        self._repo_name = repo_name
        self._resource = None
        self._projects:List[str] = []
        self.error_messages:Set[str] = set() # Don't want duplicates


    @property
    def manifest(self) -> Dict[str,Any]:
        if not self._manifest:
            self._manifest = self.get_manifest_from_dir()
        return self._manifest


    def get_manifest_from_dir(self) -> Dict[str,Any]:
        manifest = None
        self.loadeded_manifest_file = False
        if not self.path or not os.path.isdir(self.path):
            return get_manifest_from_repo_name(self.repo_name)
        try:
            manifest = load_yaml_object(os.path.join(self.path, 'manifest.yaml'))
        except (ParserError, ScannerError) as e:
            err_msg = f"Badly formed 'manifest.yaml' in {self.repo_name}: {e}"
            self.error_messages.add(err_msg)
        if manifest:
            self.loadeded_manifest_file = True
            return manifest
        try:
            manifest = load_json_object(os.path.join(self.path, 'manifest.json'))
        except JSONDecodeError as e:
                err_msg = f"Badly formed 'manifest.json' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        if manifest:
            self.loadeded_manifest_file = True
            return manifest
        try:
            manifest = load_json_object(os.path.join(self.path, 'package.json'))
        except JSONDecodeError as e:
                err_msg = f"Badly formed 'package.json' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        if manifest:
            self.loadeded_manifest_file = True
            return manifest
        try:
            manifest = load_json_object(os.path.join(self.path, 'project.json'))
        except JSONDecodeError as e:
                err_msg = f"Badly formed 'project.json' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        if manifest:
            self.loadeded_manifest_file = True
            return manifest
        try:
            manifest = load_json_object(os.path.join(self.path, 'meta.json'))
        except JSONDecodeError as e:
                err_msg = f"Badly formed 'meta.json' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        if manifest:
            self.loadeded_manifest_file = True
            return manifest
        return get_manifest_from_repo_name(self.repo_name)


    def as_dict(self) -> Dict[str,Any]:
        """
        Return a proper dict object of the manifest
        :return dict:
        """
        return {
            'dublin_core': {
                'type': self.resource.type,
                'conformsto': self.resource.conformsto,
                'format': self.resource.format,
                'identifier': self.resource.identifier,
                'title': self.resource.title,
                'subject': self.resource.subject,
                'description': self.resource.description,
                'language': {
                    'identifier': self.resource.language.identifier,
                    'title': self.resource.language.title,
                    'direction': self.resource.language.direction
                },
                'source': self.resource.source,
                'rights': self.resource.rights,
                'creator': self.resource.creator,
                'contributor': self.resource.contributor,
                'relation': self.resource.relation,
                'publisher': self.resource.publisher,
                'issued': self.resource.issued,
                'modified': self.resource.modified,
                'version': self.resource.version
            },
            'checking': {
                'checking_entity': self.checking_entity,
                'checking_level': self.checking_level
            },
            'projects': self.projects_as_dict
        }


    @property
    def path(self) -> str:
        if self._dir:
            return self._dir.rstrip('/')
        else:
            return ''


    @property
    def repo_name(self) -> str:
        if self._repo_name:
            return self._repo_name
        elif self.path:
            return os.path.basename(self.path)
        else:
            return ''  # Use empty string instead of None


    @property
    def resource(self):
        if not self._resource:
            if 'dublin_core' in self.manifest and self.manifest['dublin_core']:
                self._resource = Resource(self, self.manifest['dublin_core'])
            elif 'resource' in self.manifest and self.manifest['resource']:
                resource = self.manifest['resource']
                if len(resource) == 2 and 'id' in resource and 'name' in resource:
                    self.manifest['id'] = resource['id']
                    self.manifest['name'] = resource['name']
                    resource = self.manifest
                self._resource = Resource(self, resource)
            else:
                self._resource = Resource(self, self.manifest)
        return self._resource


    @property
    def checking_entity(self) -> str:
        return self.manifest.get('checking', {}).get('checking_entity', ['Wycliffe Associates'])


    @property
    def checking_level(self) -> str:
        return self.manifest.get('checking', {}).get('checking_level', '1')


    @property
    def projects(self):
        if not self._projects:
            if 'projects' in self.manifest and len(self.manifest['projects']):
                for p in self.manifest['projects']:
                    project = Project(self, p)
                    self._projects.append(project)
            elif 'project'in self.manifest:
                project = Project(self, self.manifest['project'])
                self._projects.append(project)
            if not self._projects:
                self._projects.append(Project(self, {}))  # will rely on info in the resource
        return self._projects


    @property
    def projects_as_dict(self) -> List[Dict[str,Any]]:
        projects = []
        for project in self.projects:
            projects.append(project.as_dict())
        return projects


    def project(self, identifier:Optional[str]=None) -> Project:
        """
        Retrieves a project from the RC.

        You can exclude the parameter if the RC only has one project.

        :param identifier:
        :return Project:
        """
        if identifier:
            for p in self.projects:
                if p.identifier == identifier:
                    return p
        else:
            if len(self.projects) == 1:
                return self.projects[0]
            elif len(self.projects) > 1:
                raise Exception('Multiple projects found. Specify the project identifier.')
            else:
                return Project(self)


    @property
    def project_count(self) -> int:
        return len(self.projects)


    @property
    def project_ids(self) -> List[str]:
        identifiers = []
        for p in self.projects:
            identifiers.append(p.identifier)
        return identifiers


    def chapters(self, identifier=None):
        """
        Returns an array of chapters in the project of the given identifier.
        You can exclude the parameter if this RC only has one project.
        :param identifier: The project identifier
        :return array:
        """
        p = self.project(identifier)
        if p is None:
            return []
        else:
            chapters = []

            for d in sorted(glob(os.path.join(self._dir, p.path, '*')),
                            key=lambda path: os.path.basename(path).zfill(3)):
                chapter = os.path.basename(d)
                if os.path.isdir(d) and not chapter.startswith('.'):
                    if self.chunks(identifier, chapter):
                        chapters.append(chapter)
            return chapters


    def chunks(self, project_identifier, chapter_identifier=None):
        if chapter_identifier is None:
            chapter_identifier = project_identifier
            project_identifier = 0
        p = self.project(project_identifier)
        if p is None:
            return []
        chunks = []
        for f in sorted(glob(os.path.join(self.path, p.path, chapter_identifier, '*'))):
            chunk = os.path.basename(f)
            ext = os.path.splitext(chunk)[1]
            if os.path.isfile(f) and not chunk.startswith('.') and ext in ['', '.txt', '.text', '.md', '.usfm']:
                chunks.append(chunk)
        return chunks


    def usfm_files(self, identifier=None):
        """
        Returns an array of .usfm files in the project directory. Mainly used to determine if type is a bundle.
        You can exclude the parameter if this RC only has one project.
        :param identifier: The project identifier
        :return array:
        """
        p = self.project(identifier)
        if p is None:
            return []
        else:
            usfm_files = []
            for f in glob(os.path.join(self.path, p.path, '*.usfm')):
                usfm_files.append(os.path.basename(f))
            return usfm_files


    def config(self, project_identifier=None):
        p = self.project(project_identifier)
        if p is None:
            return None
        if not p.config_yaml:
            file_path = os.path.join(self.path, p.path, 'config.yaml')
            try:
                p.config_yaml = load_yaml_object(file_path)
            except (ParserError, ScannerError) as e:
                err_msg = f"Badly formed 'config.yaml' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        return p.config_yaml


    def toc(self, project_identifier=None):
        p = self.project(project_identifier)
        if p is None:
            return None
        if not p.toc_yaml:
            file_path = os.path.join(self.path, p.path, 'toc.yaml')
            try:
                p.toc_yaml = load_yaml_object(file_path)
            except (ParserError, ScannerError) as e:
                err_msg = f"Badly formed 'toc.yaml' in {self.repo_name}: {e}"
                self.error_messages.add(err_msg)
        return p.toc_yaml
# end of class RC



class Resource:
    def __init__(self, rc:RC, resource:Dict[str,Any]) -> None:
        """
        :param RC rc:
        :param dict resource:
        """
        self.rc = rc
        assert isinstance(rc, RC)
        self.resource = resource
        if not isinstance(self.resource, dict):
            raise Exception('Missing dict parameter: resource')
        # AppSettings.logger.debug(f"Created new RC Resource with: {resource}")
        self._language:Optional[Union[Language, Dict[str,str]]] = None


    @property
    def conformsto(self) -> str:
        return self.resource.get('conformsto', 'rc0.2')


    @property
    def format(self) -> Optional[str]:
        # AppSettings.logger.debug("Resource.format()…")
        if 'format' in self.resource and self.resource['format']:
            old_format = self.resource['format']
            if '/' not in old_format:
                return f'text/{old_format.lower()}'
            return old_format
        elif 'content_mime_type' in self.resource and self.resource['content_mime_type']:
            return self.resource['content_mime_type']
        # RJH added the next few lines Dec 2018
        elif 'content_mime_type' in self.rc.manifest and self.rc.manifest['content_mime_type']:
            return self.rc.manifest['content_mime_type']
        elif 'format' in self.rc.manifest and self.rc.manifest['format']:
            # AppSettings.logger.debug(f"Returning Resource format={self.rc.manifest['format']} from rc.manifest{' for '+self.identifier if self.identifier else ''}.")
            return self.rc.manifest['format']
        elif self.rc.usfm_files(): # e.g., a plain USFM bundle (with no manifest, etc.)
            return 'text/usfm'
        return None
    # end of Resource.format() property


    @property
    def file_ext(self) -> str:
        """
        File extension of this type of resource, such as md or usfm
        :return string:
        """
        # AppSettings.logger.debug("RC.file_ext()…")
        result = {
                'text/usx': 'usx',
                'text/usfm': 'usfm',
                'text/usfm3': 'usfm',
                'text/markdown': 'md',
                'text/tsv': 'tsv',
            }.get(self.format, 'txt')
        if not self.format and self.identifier=='bible':
            result = 'usfm'
        # AppSettings.logger.debug(f"Returning Resource file_ext='{result}' from format={self.format} for identifier={self.identifier}")
        return result
    # end of Resource.file_ext() property


    @property
    def type(self) -> str:
        # AppSettings.logger.debug("Resource.type()…")
        # print(f"Getting resource type for {self.resource}…")
        # print(f"file_ext = {self.file_ext}")
        # AppSettings.logger.debug(f"Type is in RC: {'type' in self.resource}")
        # if 'type' in self.resource: AppSettings.logger.debug(f"RC type is: {self.resource['type']}")
        # NOTE: Seems that type can also be a dict, e.g., {'id': 'text', 'name': 'Text'} for OBS manifest.json
        if 'type' in self.resource and isinstance(self.resource['type'], str):
            return self.resource['type'].lower()
        elif self.file_ext == 'usfm':
            # print(f"rc files = {self.rc.usfm_files()}")
            if self.rc.usfm_files():
                return 'bundle'
            else:
                return 'book'
        # elif self.identifier in resource_map:
        #     AppSettings.logger.critical(f"Found {self.identifier} Resource.type() = '{resource_map[self.identifier]['type']}' in resource_map.")
        #     return resource_map[self.identifier]['type']
        else:
            # AppSettings.logger.critical(f"Searched unsuccessfully for {self.identifier} Resource.type() in resource_map. (Returning 'book'.)")
            return 'book'
    # end of Resource.type() property


    @property
    def identifier(self) -> Optional[str]:
        if 'identifier' in self.resource and self.resource['identifier']:
            # AppSettings.logger.debug(f"Returning Resource identifier='{self.resource['identifier'].lower()}' from self.resource['identifier']")
            return self.resource['identifier'].lower()
        elif 'id' in self.resource and self.resource['id']:
            # AppSettings.logger.debug(f"Returning Resource identifier='{self.resource['id'].lower()}' from self.resource['id']")
            return self.resource['id'].lower()
        elif 'type' in self.resource and 'id' in self.resource['type'] and self.resource['type']['id']:
            # AppSettings.logger.debug(f"Returning Resource identifier='{self.resource['type']['id']}' from self.resource['type']['id']")
            return self.resource['type']['id']
        elif 'slug' in self.resource and self.resource['slug']:
            # AppSettings.logger.debug(f"Returning Resource identifier='{self.resource['slug'].lower()}' from self.resource['slug']")
            return self.resource['slug'].lower()
        return None
    # end of Resource.identifier() property


    @property
    def title(self) -> Optional[str]:
        # AppSettings.logger.debug("Resource.title()…")
        if 'title' in self.resource and self.resource['title']:
            #print(f"RESOURCE.title returning1 resource title {self.resource['title']!r}")
            return self.resource['title']
        elif 'name' in self.resource and self.resource['name']:
            #print(f"RESOURCE.title returning2 resource name {self.resource['name']!r}")
            return self.resource['name']
        # elif self.identifier in resource_map:
        #     #print(f"RESOURCE.title returning3 resource_map title {resource_map[self.identifier]['title']!r}")
        #     AppSettings.logger.critical(f"Found {self.identifier} Resource.title() = '{resource_map[self.identifier]['title']}' in resource_map.")
        #     return resource_map[self.identifier]['title']
        else:
            #print(f"RESOURCE.title (final ELSE) returning4 resource identifier {self.identifier!r}")
            # AppSettings.logger.critical(f"Searched unsuccessfully for {self.identifier} Resource.title() in resource_map. (Returning '{self.identifier}'.)")
            return self.identifier
    # end of Resource.title() property


    @property
    def subject(self) -> str:
        return self.resource.get('subject', self.title)


    @property
    def description(self) -> str:
        return self.resource.get('description', self.title)


    @property
    def relation(self) -> list:
        return self.resource.get('relation', [])


    @property
    def publisher(self) -> str:
        return self.resource.get('publisher', 'Door43')


    @property
    def issued(self) -> str:
        # Make sure a string is returned—not a date object
        if 'issued' in self.resource and self.resource['issued']:
            issued_result = self.resource.get('issued')
            if isinstance(issued_result, str):
                return issued_result
            if isinstance(issued_result, (date, datetime)):
                return issued_result.strftime('%Y-%m-%d')
        elif 'pub_date' in self.resource.get('status', {}):
            issued_pub_date = self.resource['status']['pub_date']
            if isinstance(issued_pub_date, str):
                return issued_pub_date
            if isinstance(issued_result, (date, datetime)):
                return issued_pub_date.strftime('%Y-%m-%d')
        else:
            return datetime.utcnow().strftime('%Y-%m-%d')


    @property
    def modified(self) -> str:
        # Make sure a string is returned—not a date object
        if 'modified' in self.resource and self.resource['modified']:
            modified_result = self.resource.get('modified')
            if isinstance(modified_result, str): return modified_result
            if isinstance(modified_result, (date, datetime)):
                return modified_result.strftime('%Y-%m-%d')
        else:
            return datetime.utcnow().strftime('%Y-%m-%d')


    @property
    def rights(self) -> str:
        return self.resource.get('rights', 'CC BY-SA 4.0')


    @property
    def creator(self) -> str:
        return self.resource.get('creator', 'Unknown Creator')


    @property
    def language(self) -> Union[Language, Dict[str,str]]:
        if not self._language:
            if 'language'in self.resource:
                self._language = Language(self.rc, self.resource['language'])
            elif 'target_language' in self.resource and self.resource['target_language']:
                self._language = Language(self.rc, self.resource['target_language'])
            elif 'target_language' in self.rc.manifest and self.rc.manifest['target_language']:
                self._language = Language(self.rc, self.rc.manifest['target_language'])
            else:
                # Always assume English by default
                self._language = Language(self.rc, {
                    'identifier': 'en',
                    'title': 'English',
                    'direction': 'ltr'
                })
        return self._language


    @property
    def contributor(self) -> list:
        if 'contributor' in self.resource and self.resource['contributor']:
            return self.resource['contributor']
        elif 'translators' in self.resource and self.resource['translators']:
            contributor = []
            for translator in self.resource['translators']:
                if isinstance(translator, dict) and 'name' in translator:
                    contributor.append(translator['name'])
                elif isinstance(translator, (str,bytes)):
                    contributor.append(translator)
            return contributor
        else:
            return []


    @property
    def source(self) -> list:
        if 'source' in self.resource and self.resource['source']:
            return self.resource['source']
        else:
            sts = None
            if 'source_translations' in self.resource and self.resource['source_translations']:
                sts = self.resource['source_translations']
            elif 'source_translations' in self.resource.get('status', {}):
                sts = self.resource['status']['source_translations']
            if sts:
                sources = []
                for st in sts:
                    source = {}
                    if 'resource_id' in st and st['resource_id']:
                        source['identifier'] = st['resource_id']
                    elif 'resource_slug' in st and st['resource_slug']:
                        source['identifier'] = st['resource_slug']
                    if 'language_id' in st and st['language_id']:
                        source['language'] = st['language_id']
                    elif 'language_slug' in st and st['language_slug']:
                        source['language'] = st['language_slug']
                    if 'version' in st and st['version']:
                        source['version'] = st['version']
                    if source:
                        sources.append(source)
                return sources
            else:
                return []


    @property
    def version(self) -> str:
        return self.resource.get('version', '1')
# end of class Resource



def get_manifest_from_repo_name(repo_name:str) -> Dict[str,Any]:
    """
    If no manifest file was given, try dissecting the repo name.
    """
    manifest:Dict[str,Any] = {
        'dublin_core': {},
    }
    if not repo_name:
        return manifest

    language_set = False
    parts = re.findall(r'[A-Za-z0-9]+', repo_name)
    for part in parts:
        if not language_set:
            if part == 'en':
                # Speeds things up for English repos
                manifest['dublin_core']['language'] = {
                    'identifier': 'en',
                    'title': 'English',
                    'direction': 'ltr'
                }
                language_set = True
                continue # Used the part
            else:
                lang = TdLanguage.get_language(part)
                if lang:
                    if 'language' not in manifest['dublin_core']:
                        manifest['dublin_core']['language'] = {
                            'identifier': lang.lc,
                            'title': lang.ln,
                            'direction': lang.ld
                            }
                        continue # Used the part

        # AppSettings.logger.critical(f"Checking for {part}/{part.lower()} in resource_map…")
        # if part.lower() in resource_map:
        #     AppSettings.logger.critical(f"Found {part.lower()} in resource_map…")
        #     manifest['dublin_core']['identifier'] = part
        #     if 'projects' not in manifest:
        #         manifest['projects'] = [{'identifier': part}]
        #     continue

        if part.lower() in BOOK_NAMES:
            project = {
                'identifier': part.lower(),
                'title': BOOK_NAMES[part.lower()]
            }
            # This wasn't a correct assumption, e.g., in 'ha_num_tq_l2' (also has book abbreviation)
            # if 'identifier' not in manifest['dublin_core']:
            #     manifest['dublin_core']['identifier'] = 'bible'
            if 'projects' not in manifest:
                manifest['projects'] = []
            manifest['projects'].append(project)
            continue

    # Note: Sometimes repo names end with checking level fields, e.g., _l2
    # TODO: What other fields could we detect here?
    if repo_name.endswith('_ta') or '_ta_l' in repo_name:
        manifest['dublin_core']['subject'] = 'Translation Academy'
    elif repo_name.endswith('_tn') or '_tn_l' in repo_name:
        manifest['dublin_core']['subject'] = 'Translation Notes'
    elif repo_name.endswith('_tq') or '_tq_l' in repo_name:
        manifest['dublin_core']['subject'] = 'Translation Questions'
        manifest['dublin_core']['format'] = 'text/markdown'
    elif repo_name.endswith('_tw') or '_tw_l' in repo_name:
        manifest['dublin_core']['subject'] = 'Translation Words'
        manifest['dublin_core']['format'] = 'text/markdown'

    if 'identifier' not in manifest['dublin_core']:
        manifest['dublin_core']['identifier'] = repo_name

    return manifest
# end of get_manifest_from_repo_name(repo_name)
