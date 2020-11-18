# -*- coding: utf-8 -*-

# Script for verifying the format of a manifest.yaml file that is part of a Door43 Resource Container.
# Should check the following:
# Manifest file does not have a BOM.
# Valid YAML syntax.
# Manifest contains all the required fields.
#   conformsto 'rc0.2'
#   contributor is a list of at least one name, all names at least 3 characters long
#   creator is a non-empty string
#   identifier is a recognized value: tn, tq, ulb, etc.
#      The RC spec requires identifier to be all lowercase alphanumeric and hyphens.
#      The first characters must be a letter, and the last character must not be a hyphen.
#   identifier equals the last part of the name of the directory in which the manifest file resides
#   format corresponds to identifier
#   language.direction is 'ltr' or rtl'
#   language.identifier equals to first part of the name of the directory in which the manifest file resides
#   language.title is a non-empty string. Prints reminder to localize language title.
#   issued date is less or equal to modified date
#   modified date is greater than or equal to issued date
#   modified date equals today
#   publisher does not contain "Unfolding" or "unfolding" unless language is English
#   relation is a list of at lesat one string, all of which:
#     start with the language identifer and a slash
#     identifier following the slash is valid and must not equal the current project identifer
#     other valid relation strings may also be predefined in this script
#   rights value is 'CC BY-SA 4.0' 
#   source has no extraneous fields
#   source.identifier matches project type identifier above
#   source.language is 'en' (Warning if not)
#   source.version is a string
#   subject is one of the predefined strings and corresponds to project type identifier
#   title is a non-empty string
#   type corresponds to subject
#   version is a string that starts with source.version followed by a period followed by a number
#   checking has no extraneous fields
#   checking.checking_entity is a list of at least one string
#   checking.checking_level is '3'
#   projects is a non-empty list. The number of projects in the list is reasonable for the project type.
#   each subfield of each project exists
#   project identifiers correspond to type of project 
#   project categories correspond to type of project 
#   project paths exist
#
# Also checks for extraneous files in the folder with the manifest file.
# Verifies presence of media.yaml file for OBS projects.
# Verifies presence of valid toc.yaml files in tA projects.
#
# To add:
#   Check for missing config.yaml files
#   Check for ASCII titles in toc.yaml files.
#   Check for 01.md, title.md, and sub-title.md files in each bottom level tA folder.

# Globals
manifestDir = r'C:\DCS\Telugu\te_tq'
nIssues = 0
projtype = ''
issuesFile = None

from datetime import datetime
from datetime import date
import sys
import os
import yaml
import io
import codecs
import re
import usfm_verses

# Returns language identifier based on the directory name
def getLanguageId():
    global manifestDir
    parts = os.path.basename(manifestDir).split('_', 1)
    return parts[0]

# If manifest-issues.txt file is not already open, opens it for writing.
# Returns file pointer, which is also a global.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global manifestDir
        path = os.path.join(manifestDir, "manifest-issues.txt")
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
    return issuesFile

# Writes error message to stderr and to manifest-issues.txt.
def reportError(msg):
    global nIssues
    try:
        sys.stderr.write(msg + '\n')
    except UnicodeEncodeError as e:
        sys.stderr.write("See error message in manifest-issues.txt. It contains Unicode.\n")

#    issues = openIssuesFile().write(msg + u'\n')
    nIssues += 1

# Returns the number of .usfm files in the manifest directory.
def countBookDirs():
    n = 0
    for fname in os.listdir(manifestDir):
        path = os.path.join(manifestDir, fname)
        if os.path.isdir(path) and fname.upper() in usfm_verses.verseCounts:
            n += 1
    return n

# Returns the number of .usfm files in the manifest directory.
def countUsfmFiles():
    n = 0
    for fname in os.listdir(manifestDir):
        if fname.endswith(".usfm"):
            n += 1
    return n

# Returns True if the specified string is a recognized Bible type of project type
def isBibleType(id):
    return (id in {'ulb', 'udb', 'ust', 'ult', 'iev','irv','isv','reg','glt','gst', \
                   'rlb','rob','rlob','rsb','rsob','stv','trs'})

# This function validates the project entries for a tA project.
# tA projects should have four projects entries, each with specific content
def verifyAcademyProject(project):
    if len(project['categories']) != 1 or project['categories'][0] != 'ta':
        reportError("Invalid project:categories: " + project['categories'][0])

    section = project['identifier']
    if section == 'intro':
        if project['title'] != "Introduction to Translation Academy":
            reportError("Invalid project:title: " + project['title'])
        if project['sort'] != 0:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'process':
        if project['title'] != "Process Manual":
            reportError("Invalid project:title: " + project['title'])
        if project['sort'] != 1:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'translate':
        if project['title'] != "Translation Manual":
            reportError("Invalid project:title: " + project['title'])
        if project['sort'] != 2:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'checking':
        if project['title'] != "Checking Manual":
            reportError("Invalid project:title: " + project['title'])
        if project['sort'] != 3:
            reportError("Invalid project:sort: " + str(project['sort']))
    else:
        reportError("Invalid project:identifier: " + section)

# Verifies that all chapters exist for the given folder.
# Applies to tN and tQ projects only.
def verifyChapters(path):
    for book in os.listdir(path):
        bookpath = os.path.join(path, book)
        if len(book) == 3 and os.path.isdir(bookpath):
            nchapters = usfm_verses.verseCounts[book.upper()]['chapters']
            subdirs = os.listdir(bookpath)
            if len(subdirs) < nchapters or ("front" in subdirs and len(subdirs) <= nchapters):
                reportError("Missing chapters in: " + shortname(bookpath))

# Verifies the checking section of the manifest.
def verifyChecking(checking):
    verifyKeys('checking', checking, ['checking_entity', 'checking_level'])
    if 'checking_entity' in list(checking.keys()):      # would this work: 'checking_entity' in checking
        if len(checking['checking_entity']) < 1:
            reportError("Missing checking_entity.")
        for c in checking['checking_entity']:
            if not isinstance(c, str) or len(c) < 3:
                reportError("Invalid checking_entity: " + str(c))
    if 'checking_level' in list(checking.keys()):      # would this work: 'checking_level' in checking
        if not isinstance(checking['checking_level'], str):
            reportError('checking_level must be a string')
        elif checking['checking_level'] != '3' and projtype != 'reg':
            reportError("Invalid value for checking_level: " + checking['checking_level'])

badname_re = re.compile(r'.*\d\d\d\d+.*\.md$')

# Checks for extraneous files in the directory... recursive
def verifyCleanDir(dirpath):
    for fname in os.listdir(dirpath):
        path = os.path.join(dirpath, fname)
        if projtype in {'ta'} and fname == 'media.yaml':
            reportError("Unwanted media.yaml file: " + shortname(path))
        if (fname.find("temp") >= 0 or fname.find("tmp") >= 0 or fname.find("orig") >= 0 \
            or fname.find("Copy") >= 0 or fname.find(".txt") >= 0 or fname.find("projects") >= 0):
            if fname not in {"translate-original", "temple.md", "tempt.md", "contempt.md"}:
                reportError("Possible extraneous file: " + shortname(path))
        elif badname_re.match(fname):
            reportError("Likely misnamed file: " + shortname(path))
        if os.path.isdir(path) and fname != ".git":
            verifyCleanDir(path)

# Verifies the contributors list
def verifyContributors(core):
    if 'contributor' in list(core.keys()):      # would this work: 'contributor' in core
        if len(core['contributor']) < 1:
            reportError("Missing contributors!")
        for c in core['contributor']:
            if not isinstance(c, str) or len(c) < 3:
                reportError("Invalid contributor name: " + str(c))

# Checks the dublin_core of the manifest
def verifyCore(core):
    verifyKeys("dublin_core", core, ['conformsto', 'contributor', 'creator', 'description', 'format', \
        'identifier', 'issued', 'modified', 'language', 'publisher', 'relation', 'rights', \
        'source', 'subject', 'title', 'type', 'version'])

    # Check project identifier first because it is used to validate some other fields
    verifyIdentifier(core)  # Sets the projtype global
    if 'conformsto' in list(core.keys()) and core['conformsto'] != 'rc0.2':     # would this work: 'conforms_to' in core
        reportError("Invalid value for conformsto: " + core['conformsto'])
    verifyContributors(core)
    verifyStringField(core, 'creator', 3)
    verifyDates(core['issued'], core['modified'])
    verifyFormat(core)
    verifyLanguage(core['language'])
    
    pub = core['publisher']
    if pub.lower().find('unfolding') >= 0 and core['language']['identifier'] != 'en':
        reportError("Invalid publisher: " + pub)
    verifyRelations(core['relation'])
    if 'rights' in list(core.keys()) and core['rights'] != 'CC BY-SA 4.0':  # would this work: 'rights' in core
        reportError("Invalid value for rights: " + core['rights'])
    verifySource(core['source'])
    verifySubject(core['subject'])
    verifyTitle(core['title'])
    verifyType(core['type'])
    verifyVersion(core['version'], core['source'][0]['version'])

def verifyDates(issued, modified):
    issuedate = datetime.strptime(issued, "%Y-%m-%d").date()
    moddate = datetime.strptime(modified, "%Y-%m-%d").date()
    if moddate != date.today():
        reportError("Wrong date - modified: " + modified)
    if issuedate > moddate:
        reportError("Dates wrong - issued: " + issued + ", modified: " + modified)

def verifyDir(dirpath):
    path = os.path.join(dirpath, "manifest.yaml")
    if os.path.isfile(path):
        verifyFile(path)
    else:
        reportError("No manifest.yaml file in: " + dirpath)
    verifyCleanDir(dirpath)
    if projtype == 'obs':
        mediapath = os.path.join(dirpath, "media.yaml")
        if not os.path.isfile(mediapath):
            reportError("Missing media.yaml file in: " + dirpath)
    if projtype == 'ta':
        verifyTocYamls(dirpath)
    if projtype in {'tn','tq'}:
        verifyChapters(dirpath)

# Manifest file verification
def verifyFile(path):
    if has_bom(path):
        reportError("manifest.yaml file has a Byte Order Mark. Remove it.")
    manifestFile = io.open(path, "tr", encoding='utf-8-sig')
    manifest = yaml.safe_load(manifestFile)
    manifestFile.close()
    verifyKeys("", manifest, ['dublin_core', 'checking', 'projects'])
    verifyCore(manifest['dublin_core'])
    verifyChecking(manifest['checking'])
    verifyProjects(manifest['projects'])

# Verifies format field is a valid string, depending on project type.
# Done with iev, irv, isv, obs, obs-tn, obs-tq, reg, ta, tq, tn, tw, tsv, ulb, udb, ust
def verifyFormat(core):
    global projtype
    if verifyStringField(core, 'format', 8):
        format = core['format']
        if projtype in {'tn'}:
            if format == 'text/tsv':
                projtype = 'tn-tsv'
                print("projtype = " + projtype)
            elif format != 'text/markdown':
                reportError("Invalid format: " + format)
        elif projtype in {'ta', 'tq', 'tw', 'obs', 'obs-tn', 'obs-tq'}:
            if format != 'text/markdown':
                reportError("Invalid format: " + format)
        elif isBibleType(projtype):
            if format not in {'text/usfm', 'text/usfm3'}:
                reportError("Invalid format: " + format)
        elif projtype in {'ust','irv','glt','glt','gst'}:
            if format != 'text/usfm3':
                reportError("Invalid format: " + format)
        else:
            reportError("Unable to validate format because script does not yet support project type: " + projtype)
            
# Validates the dublin_core:identifier field in several ways.
# Sets the global projtype variable which is used by subsequent checks.
def verifyIdentifier(core):
    global projtype
    global manifestDir
    if verifyStringField(core, 'identifier', 2):
        id = core['identifier']
        if id not in {'tn', 'tq', 'tw', 'ta', 'obs', 'obs-tn', 'obs-tq'} and not isBibleType(id):
            reportError("Invalid id: " + id)
        else:
            projtype = id
            print("projtype = " + projtype)
        parts = manifestDir.rsplit('_', 1)
        if id.lower() != parts[-1].lower():     # last part of directory name should match the projtype string
            reportError("Project identifier (" + id + ") does not match last part of directory name: " + parts[-1].lower())

# Verify that the specified fields exist and no others.
def verifyKeys(group, dict, keys):
    for key in keys:
        if key not in list(dict.keys()):      # would this work: key not in dict
            reportError('Missing field: ' + group + ':' + key)
    for field in dict:
        if field not in keys:
            reportError("Extra field: " + group + ":" + field)

# Validate the language field and its subfields.
def verifyLanguage(language):
    verifyKeys("language", language, ['direction', 'identifier', 'title'])
    if 'direction' in list(language.keys()):      # would this work: 'direction' in language
        if language['direction'] != 'ltr' and language['direction'] != 'rtl':
            reportError("Incorrect language direction: " + language['direction'])
#    if 'identifier' in list(language.keys()):      # would this work: 'identifier' in language
    if 'identifier' in language:
        if language['identifier'] != getLanguageId():
            reportError("Language identifier (" + language['identifier'] + ") does not match first part of directory name: " + os.path.basename(manifestDir))
    if verifyStringField(language, 'title', 3):
        if language['title'].isascii():
            sys.stdout.write("Remember to localize language title: " + language['title'] + '\n')

# Verifies that the project contains the six required fields and no others.
# Verifies that the path exists.
# Verifies that the title corresponds to the project type.
# Validate some other field values, depending on the type of project
def verifyProject(project):
    verifyKeys("projects", project, ['title', 'versification', 'identifier', 'sort', 'path', 'categories'])

    global manifestDir
    fullpath = os.path.join(manifestDir, project['path'])
    if len(project['path']) < 5 or not os.path.exists(fullpath):
        reportError("Invalid path: " + project['path'])
    if projtype == 'ta':
        verifyAcademyProject(project)
    elif projtype in {'tn', 'tq'}:
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if project['sort'] != bookinfo['sort']:
            reportError("Incorrect project:sort: " + str(project['sort']))
        if projtype == 'tn' and len(project['categories']) != 0:
            reportError("Categories list should be empty: project:categories")
    elif projtype == 'tn-tsv':
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if project['sort'] != bookinfo['sort']:
            reportError("Incorrect project:sort: " + str(project['sort']))
        cat = project['categories'][0]
        if len(project['categories']) != 1 or cat not in {'bible-ot', 'bible-nt'}:
            reportError("Invalid project:categories: " + cat)
    elif projtype == 'tw':
        if project['title'] != 'translationWords':
            reportError("Invalid project:title: " + project['title'])
    elif isBibleType(projtype):
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if int(project['sort']) != bookinfo['sort']:
            reportError("Incorrect project:sort: " + str(project['sort']))
        if project['versification'] != 'ufw':
            reportError("Invalid project:versification: " + project['versification'])
        if len(project['identifier']) != 3:
            reportError("Invalid project:identifier: " + project['identifier'])
        cat = project['categories'][0]
        if len(project['categories']) != 1 or not (cat == 'bible-ot' or cat == 'bible-nt'):
            reportError("Invalid project:categories: " + cat)
    elif projtype == 'obs':
        if project['categories']:
            reportError("Should be blank: project:categories")
        if project['versification']:
            reportError("Should be blank: project:versification")
        if project['identifier'] != 'obs':
            reportError("Invalid project:identifier: " + project['identifier'])
        if project['title'] != 'Open Bible Stories':
            reportError("Invalid project:title: " + project['title'])
    elif projtype == 'obs-tn':
        if project['categories'] and len(project['categories']) != 0:
            reportError("Categories list should be empty: project:categories")
        if project['identifier'] != 'obs':
            reportError("Invalid project:identifier: " + project['identifier'])
        if project['title'] != 'Open Bible Stories Translation Notes' and project['title'] != 'OBS translationNotes':
            reportError("Invalid project:title: " + project['title'])
    elif projtype == 'obs-tq':
        if project['categories']:
            reportError("Categories list should be empty: projects:categories")
        if project['identifier'] != 'obs':
            reportError("Invalid project:identifier: " + project['identifier'])
        if project['title'] != 'Open Bible Stories Translation Questions':
            reportError("Invalid project:title: " + project['title'])
    else:
        sys.stdout.write("Verify each project entry manually.\n")   # temp until all projtypes are supported

    # For most project types, the projects:identifier is really a part identifier, like book id (ULB, tQ, etc.), or section id (tA)

# Verifies the projects list
def verifyProjects(projects):
    if not projects:
        reportError('Empty projects list')
    else:
        global projtype
        nprojects = len(projects)
        if nprojects < 1:
            reportError('Empty projects list')
        if isBibleType(projtype) and nprojects != countUsfmFiles():
            reportError("Number of projects listed " + str(nprojects) + " does not match number of usfm files: " + str(countUsfmFiles()))
        if projtype in {'tn', 'tq'} and nprojects != countBookDirs():
            reportError("Number of projects listed " + str(nprojects) + " does not match number of book folders: " + str(countBookDirs()))
        if projtype in ['obs', 'obs-tn', 'obs-tq', 'tw'] and nprojects != 1:
            reportError("There should be exactly 1 project listed under projects.")
        elif projtype == 'ta' and nprojects != 4:
            reportError("There should be exactly 4 projects listed under projects.")
        elif projtype in {'tn','tn-tsv'} or isBibleType(projtype):
            if nprojects not in (27,39,66):
                reportError("Number of projects listed: " + str(nprojects))
            
        for p in projects:
            verifyProject(p)

# NOT DONE - need to support UHG-type entries
def verifyRelation(rel):
    if not isinstance(rel, str):
        reportError("Relation element is not a string: " + str(rel))
    elif len(rel) < 5:
        reportError("Invalid value for relation element: " + rel)
    else:
        parts = rel.split('/')
        if len(parts) != 2:
            reportError("Invalid format for relation element: " + rel)
        else:
            global projtype
            if parts[0] != getLanguageId() and parts[0] != "el-x-koine" and parts[0] != "hbo":
                reportError("Incorrect language code for relation element: " + rel)
            if parts[1] not in {'obs','obs-tn','obs-tq','tn','tq','tw','ta'} and not isBibleType(parts[1]):
                if parts[1][0:4] != 'ugnt' and parts[1][0:3] != 'uhb':
                    reportError("Invalid project code in relation element: " + rel)
            if parts[1] == projtype:
                reportError("Project code in relation element is same as current project: " + rel)

# The relation element is a list of strings.
def verifyRelations(relation):
    uhg = False
    if len(relation) < 1 and projtype != 'reg':
        reportError("Missing relations in: relation")
    for r in relation:
        verifyRelation(r)
        if projtype == 'tn-tsv':
            parts = r.split('/')
            if len(parts) == 2 and parts[0] == 'el-x-koine' and 'ugnt?v=' in parts[1]:
                uhg = True
    if projtype == 'tn-tsv' and not uhg:
        reportError("Must reference 'el-x-koine/ugnt?v=...' in relation")
        
# Validates the source field, which is an array of dictionaries.
def verifySource(source):
    if not source or len(source) < 1:
        reportError("Invalid source spec: should be an array of dictionary of three fields.")
    for dict in source:
        verifyKeys("source[x]", dict, ['language', 'identifier', 'version'])

        global projtype
        if dict['identifier'] != projtype and projtype in {'obs', 'obs-tn', 'obs-tq', 'tn', 'tq', 'tw'}:
            reportError("Inappropriate source:identifier (" + dict['identifier'] + ") for project type: " + projtype)
        if dict['identifier'] != 'ulb' and projtype == 'reg':
            reportError("Incorrect source:identifier for reg project: " + dict['identifier'])
        if dict['identifier'] != 'tn' and projtype == 'tn-tsv':
            reportError("Incorrect source:identifier for tn-tsv project: " + dict['identifier'])
        if not re.match(r'[a-z][a-z0-9-]', dict['identifier'], re.UNICODE):
            reportError("Invalid source:identifier (need lower case ascii, no spaces): " + dict['identifier'])
        if dict['language'] == 'English':
            reportError("Use a language code in source:language, not \'" + dict['language'] + '\'')
        elif dict['language'] == getLanguageId():
            reportError("Warning: source:language matches target language")
        elif dict['language'] != 'en':
            reportError("Possible bad source:language: " + dict['language'])
        verifyStringField(dict, 'version', 1)
    
# Validates that the specified key is a string of specified minimum length.
# Returns False if there is a problem.
def verifyStringField(dict, key, minlength):
    success = True
    if key in list(dict.keys()):      # would this work: key in dict
        if not isinstance(dict[key], str):
            reportError("Value must be a string: " + key + ": " + str(dict[key]))
            success = False
        elif len(dict[key]) < minlength:
            reportError("Invalid value for " + key + ": " + dict[key])
            success = False
    return success

# Validates the subject field
def verifySubject(subject):
    failure = False
    if projtype == 'ta':
        failure = (subject != 'Translation Academy')
    elif projtype == 'tw':
        failure = (subject != 'Translation Words')
    elif projtype == 'tn':
        failure = (subject != 'Translation Notes')
    elif projtype == 'tn-tsv':
        failure = (subject != 'TSV Translation Notes')
    elif projtype == 'tn':
        failure = (subject not in {'Translation Notes', 'TSV Translation Notes'})
    elif projtype == 'tq':
        failure = (subject != 'Translation Questions')
    elif isBibleType(projtype):
        failure = (subject not in {'Bible', 'Aligned Bible'})
    elif projtype == 'obs':
        failure = (subject != 'Open Bible Stories')
    elif projtype == 'obs-tq':
        failure = (subject != 'OBS Translation Questions')
    elif projtype == 'obs-tn':
        failure = (subject != 'OBS Translation Notes')
    else:
        sys.stdout.write("Verify subject manually.\n")
    if failure:
        reportError("Invalid subject: " + subject)

# Verifies that the title
def verifyTitle(title):
    if not isinstance(title, str):
        reportError("Incorrect type for title field: " + str(title))
    elif len(title) < 3:
        reportError("String value too short for title: " + title)
    if isBibleType(projtype):
        if projtype in {'iev', 'udb', 'ust', 'gst'} and ("Literal" in title or "Revised" in title):
            reportError("Title contradicts project type: " + title)
        elif projtype in {'irv', 'isv', 'ulb', 'ult','glt'} and ("Easy" in title or "Dynamic" in title):
            reportError("Title contradicts project type: " + title)

def verifyTocYaml(yamlpath):
    yamlFile = io.open(yamlpath, "tr", encoding='utf-8-sig')
    contents = yaml.safe_load(yamlFile)
    yamlFile.close()

# For tA projects, verify that each folder has a valid toc.yaml file.
def verifyTocYamls(dirpath):
    for folder in ['checking', 'intro', 'process', 'translate']:
        path = os.path.join(dirpath, folder)
        path = os.path.join(path, "toc.yaml")
        if os.path.isfile(path):
            verifyTocYaml(path)
        else:
            reportError("toc.yaml file missing: " + shortname(path))

def verifyType(type):
    failure = False
    if projtype == 'ta':
        failure = (type != 'man')
    elif projtype == 'tw':
        failure = (type != 'dict')
    elif projtype in {'tn', 'tn-tsv', 'tq', 'obs-tn', 'obs-tq'}:
        failure = (type != 'help')
    elif isBibleType(projtype):
        failure = (type != 'bundle')
    elif projtype == 'obs':
        failure = (type != 'book')
    else:
        sys.stdout.write("Verify type manually.\n")
    if failure:
        reportError("Invalid type: " + type)

def verifyVersion(version, sourceversion):
    # The rules seem to be optional, so may comment out most of this code if necessary.
    parts = version.rsplit('.', 1)
    if int(sourceversion) < 100 and (len(parts) < 2 or parts[0] != sourceversion or int(parts[-1]) < 1):
        reportError("Invalid version: " + version + "; Source version is " + sourceversion)
    if int(sourceversion) >= 100 and (len(parts) > 1 or int(parts[0]) > 99):
        reportError("Invalid version: " + version + ". Source version is " + sourceversion)

# Returns True if the file has a BOM
def has_bom(path):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for bom in [codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]:
        if raw.startswith(bom):
            return True
    return False

def shortname(longpath):
    shortname = longpath
    if manifestDir in longpath:
        shortname = longpath[len(manifestDir)+1:]
    return shortname


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        manifestDir = sys.argv[1]

    if os.path.isdir(manifestDir):
        verifyDir(manifestDir)
    else:
        reportError("Invalid directory: " + manifestDir + '\n') 

    if issuesFile:
        issuesFile.close()
    if nIssues == 0:
        print("Done, no issues found.\n")
    else:
        print("Finished checking, found " + str(nIssues) + " issues.\n")