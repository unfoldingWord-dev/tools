# -*- coding: utf-8 -*-

# Script for verifying the format of a manifest.yaml file that is part of a Door43 Resource Container.
# Should check the following:
# Manifest file does not have a BOM.
# Valid YAML syntax and content.
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
#   checks for extraneous files in the folder and subfolders.
#   verifies presence of LICENSE and README files.
#   verifies toc.yaml files in tA projects.
#   verifies presence of title.md and sub-title.md files for tA projects
#   verifies today's date on README file.
#   verifies presence of media.yaml file for OBS projects.
#   verifies config.yaml files for tA or tW projects

# Globals
manifestDir = r'C:\DCS\Hindi\hi_tn.STR'
expectAsciiTitles = False      # Suppress errors/warnings about ASCII tit:l

nIssues = 0
projtype = ''
issuesFile = None

from datetime import datetime
from datetime import date
from datetime import timedelta
import pathlib
import sys
import os
import yaml
import io
import codecs
import numbers
import re
import usfm_verses

# Returns language identifier based on the directory name
def getLanguageId():
    global manifestDir
    parts = os.path.basename(manifestDir).split('_', 1)
    return parts[0]

def expectAscii(language_id):
    return (expectAsciiTitles or language_id in {'ceb','dan','en','es','es-419','fr','gl','ha','hr','id','ilo','kvb','lko','ngp','plt','pmy','pt-br','ruc','sw','tl','tpi'})

# If manifest-issues.txt file is not already open, opens it for writing.
# Returns file pointer, which is also a global.
def openIssuesFile():
    global issuesFile
    if not issuesFile:
        global manifestDir
        path = os.path.join(manifestDir, "manifest-issues.txt")
        issuesFile = io.open(path, "tw", encoding='utf-8', newline='\n')
    return issuesFile

# Writes error message to stderr.
def reportError(msg):
    global nIssues
    try:
        sys.stderr.write(msg + '\n')
    except UnicodeEncodeError as e:
        sys.stderr.write("Error message not shown, contains Unicode.\n")
        #    issues = openIssuesFile().write(msg + '\n')
    nIssues += 1

# Writes warnings message to stderr.
def reportWarning(msg):
    reportError("Possible error (please check): " + msg)

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
    return (isAlignedBibleType(id) or id in {'ulb','udb','reg', 'ayt', 'blv','cuv','nav','det','juds'})

# Returns True if the specified string is a recognized Aligned Bible type of project type
# Preliminary implementation - list needs refinement (6/21/21)
def isAlignedBibleType(id):
    return (id in {'ust', 'ult', 'iev','irv','isv','glt','gnt','gst','ocb', \
                   'rhb','rlb','rlv','rob','rlob','rsb','rsob', \
                   'stv','tlob','trs'})

# This function validates the project entries for a tA project.
# tA projects should have four projects entries, each with specific content
# However, the projet titles don't seem to matter. It's probably better if they are translated, but not required.
def verifyAcademyProject(project):
    if len(project['categories']) != 1 or project['categories'][0] != 'ta':
        reportError("Invalid project:categories: " + project['categories'][0])

    section = project['identifier']
    projtitle = project['title']
    if section == 'intro':
        if projtitle.isascii() and projtitle != "Introduction to Translation Academy":
            reportError("Invalid project:title: " + projtitle)
        if project['sort'] != 0:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'process':
        if projtitle.isascii() and projtitle != "Process Manual":
            reportError("Invalid project:title: " + projtitle)
        if project['sort'] != 1:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'translate':
        if projtitle.isascii() and projtitle != "Translation Manual":
            reportError("Invalid project:title: " + projtitle)
        if project['sort'] != 2:
            reportError("Invalid project:sort: " + str(project['sort']))
    elif section == 'checking':
        if projtitle.isascii() and projtitle != "Checking Manual":
            reportError("Invalid project:title: " + projtitle)
        if project['sort'] != 3:
            reportError("Invalid project:sort: " + str(project['sort']))
    else:
        reportError("Invalid project:identifier: " + section)

# Verifies that all chapters exist for the given folder.
def verifyBook(book, bookpath):
    if not book.islower():
        reportError("Upper case book folder: " + os.path.relpath(bookpath, manifestDir))
    nchapters = usfm_verses.verseCounts[book.upper()]['chapters']
    subdirs = os.listdir(bookpath)
    if len(subdirs) < nchapters or ("front" in subdirs and len(subdirs) <= nchapters):
        reportError("Missing chapters in: " + os.path.relpath(bookpath, manifestDir))
    for chapter in subdirs:
        path = os.path.join(bookpath, chapter)
        if os.path.isdir(path):
            verifyChapter( os.path.join(bookpath, chapter) )

# Verifies the folder names correspond to books of the Bible.
# Verifies the chapter folders and file names under each book.
# for tN and tQ projects only.
def verifyBooks(path):
    for book in os.listdir(path):
        if book not in {".git", "LICENSE", "LICENSE.md", "README.md", "manifest.yaml", "media.yaml"}:
            bookpath = os.path.join(path, book)
            if len(book) == 3 and os.path.isdir(bookpath) and book.upper() in usfm_verses.verseCounts:
                verifyBook(book, bookpath)
            elif not book.startswith("issues"):
                reportError("Invalid(?) file or folder: " + os.path.relpath(bookpath, manifestDir))

fname2_re = re.compile(r'[0-8][0-9]\.md$')
fname3_re = re.compile(r'[0-1][0-9][0-9]\.md$')

# Verifies that all file names in the chapter folder are legit.
# Applies to tN and tQ projects only.
def verifyChapter(path):
    skip = (projtype == 'tq' and "psa" in path and "119" in path)  # Psalm 119 in tQ has some 2-digit and some 3-digit verse numbers, and some in the 90s
    fname_re = fname2_re
    if projtype != 'tq' and "psa" in path or "PSA" in path:
        fname_re = fname3_re
    for fname in os.listdir(path):
        if not skip and not fname_re.match(fname) and fname != "intro.md":
            reportError("Invalid file name: " + fname + " in " + os.path.relpath(path, manifestDir))

# Verifies the checking section of the manifest.
def verifyChecking(checking):
    verifyKeys('checking', checking, ['checking_entity', 'checking_level'])
    if 'checking_entity' in checking:
        if len(checking['checking_entity']) < 1:
            reportError("Missing checking_entity.")
        for c in checking['checking_entity']:
            if not isinstance(c, str) or len(c) < 3:
                reportError("Invalid checking_entity: " + str(c))
    if 'checking_level' in checking:
        if not isinstance(checking['checking_level'], str):
            reportError('checking_level must be a string')
        elif checking['checking_level'] != '3' and projtype not in {'reg','tq'}:
            reportError("Invalid value for checking_level: " + checking['checking_level'])

badname_re = re.compile(r'.*\d\d\d\d+.*\.md$')
issuesfile_re = re.compile(r'issues.*\.txt')

# Checks for extraneous files in the directory... recursive
def verifyCleanDir(dirpath):
    for fname in os.listdir(dirpath):
        path = os.path.join(dirpath, fname)
        if projtype == 'ta' and fname == 'media.yaml':
            reportError("Unwanted media.yaml file: " + os.path.relpath(path, manifestDir))
        if "manifest" in fname and fname != "manifest.yaml":
            reportError("Extra manifest file: " + os.path.relpath(path, manifestDir))
        if "temp" in fname or "tmp" in fname or "orig" in fname or "bak" in fname or \
          "Copy" in fname or "txt" in fname or "projects" in fname or fname.endswith(".field"):
            if issuesfile_re.match(fname):
                reportWarning(f"{fname} file may be extraneous")
            elif fname not in {"translate-original", "temple.md", "tempt.md", "contempt.md", "habakkuk.md", "issues.txt"}:
                reportError("Extraneous file: " + os.path.relpath(path, manifestDir))

        elif badname_re.match(fname):
            reportError("Likely misnamed file: " + os.path.relpath(path, manifestDir))
        if os.path.isdir(path) and fname != ".git":
            verifyCleanDir(path)

# Verifies the contributors list
def verifyContributors(core):
    if 'contributor' in core:
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
    if 'conformsto' in core and core['conformsto'] != 'rc0.2':
        reportError("Invalid value for conformsto: " + core['conformsto'])
    verifyContributors(core)
    verifyStringField(core, 'creator', 3)
    verifyDates(core['issued'], core['modified'])
    verifyFormat(core)
    verifyLanguage(core['language'])

    pub = core['publisher']
    if core['language']['identifier'] != 'en':
        if "unfolding" in pub.lower():
            reportError("Invalid publisher: " + pub)
        elif "43" in pub:
            reportWarning("publisher: " + pub)
    elif core['language']['identifier'] in {'as','bn','gu','hi','kn','ml','mr','nag','or','pa','ta','te','ur-deva'} and pub != 'BCS':
        reportError("Publisher name should be 'BCS' for BCS resources.")
    verifyRelations(core['relation'])
    if 'rights' in core and core['rights'] != 'CC BY-SA 4.0':
        reportError("Invalid value for rights: " + core['rights'])
    verifySource(core['source'])
    verifySubject(core['subject'])
    verifyTitle(core['title'])
    verifyType(core['type'])
    if core['source']:
        verifyVersion(core['version'], core['source'][0]['version'])

def verifyDates(issued, modified):
    issuedate = datetime.strptime(issued, "%Y-%m-%d").date()
    moddate = datetime.strptime(modified, "%Y-%m-%d").date()
    if moddate != date.today():
        reportError("Modified date is not today: " + modified)
    if issuedate > moddate:
        reportError("Dates wrong - issued: " + issued + ", modified: " + modified)

def verifyDir(dirpath):
    path = os.path.join(dirpath, "manifest.yaml")
    if os.path.isfile(path):
        verifyFile(path)
        verifyOtherFiles()
    else:
        reportError("No manifest.yaml file in: " + dirpath)
    verifyCleanDir(dirpath)
    if projtype == 'ta':
        for folder in ['checking', 'intro', 'process', 'translate']:
            path = os.path.join(dirpath, folder)
            verifyYamls(path)
            verifyTitleFiles(path)
    if projtype.startswith('obs'):
        verifyMediaYaml(dirpath)
    if projtype == 'tw':
        verifyTWfiles(dirpath)
    if projtype in {'tn','tq'}:
        verifyBooks(dirpath)
    verifyReadme(dirpath)

# Manifest file verification
def verifyFile(path):
    manifest = parseYaml(path)
    verifyKeys("", manifest, ['dublin_core', 'checking', 'projects'])
    verifyCore(manifest['dublin_core'])
    verifyChecking(manifest['checking'])
    verifyProjects(manifest['projects'], manifest['dublin_core']['language']['identifier'])

# Verifies format field is a valid string, depending on project type.
# Done with iev, irv, isv, obs, obs-tn, obs-tq, obs-sn, obs-sq, reg, ta, tq, tn, tw, tsv, ulb, udb, ust
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
        elif projtype in {'ta', 'tq', 'tw', 'obs', 'obs-tn', 'obs-tq', 'obs-sn', 'obs-sq'}:
            if format != 'text/markdown':
                reportError("Invalid format: " + format)
        elif isBibleType(projtype):
            if format not in {'text/usfm', 'text/usfm3'}:
                reportError("Invalid format: " + format)
            if projtype in {'ust','irv','glt','gst','rob','rlob','rsob'}:
                if format != 'text/usfm3':
                    reportError("Invalid format: " + format + ". Expected 'text/usfm3'.")
        else:
            reportError("Unable to validate format because script does not yet support project type: " + projtype)

# Validates the dublin_core:identifier field in several ways.
# Sets the global projtype variable which is used by subsequent checks.
def verifyIdentifier(core):
    global projtype
    global manifestDir
    if verifyStringField(core, 'identifier', 2):
        id = core['identifier']
        if id not in {'tn','tq','tw','ta','obs','obs-tn','obs-tq','obs-sn','obs-sq'} and not isBibleType(id):
            reportError("Invalid id: " + id)
        else:
            projtype = id
            print("projtype = " + projtype)
        parts = manifestDir.rsplit('_', 1)
        lastpart = parts[-1].lower()
        if lastpart != id.lower() and not lastpart.startswith(id.lower() + '.'):
            # last part of directory name should match the projtype string
            reportWarning("Project identifier (" + id + ") does not match last part of directory name: " + lastpart)

# Verify that the specified fields exist and no others.
def verifyKeys(group, dict, keys):
    for key in keys:
        if key not in dict:
            reportError('Missing field: ' + group + ':' + key)
    for field in dict:
        if field not in keys and (field != "comment" or group != "dublin_core"):    # dublin_core:comment is optional
            reportError("Extra field: " + group + ":" + field)

# Validate the language field and its subfields.
def verifyLanguage(language):
    verifyKeys("language", language, ['direction', 'identifier', 'title'])
    if 'direction' in language:
        if language['direction'] != 'ltr' and language['direction'] != 'rtl':
            reportError("Incorrect language direction: " + language['direction'])
    if 'identifier' in language:
        if language['identifier'] != getLanguageId():
            reportError("Language identifier (" + language['identifier'] + ") does not match first part of directory name: " + os.path.basename(manifestDir))
    if verifyStringField(language, 'title', 3):
        language_code = language['identifier']
        if language['title'].isascii() and not expectAscii(language_code):
            reportWarning("Remember to localize language title: " + language['title'])

# For OBS projects, verify that media.yaml is valid.
def verifyMediaYaml(dirpath):
    yamlpath = os.path.join(dirpath, "media.yaml")
    if contents := parseYaml(yamlpath):
        verifyKeys("", contents, ['projects'])
        verifyProjectsOBS(contents['projects'])

# Verify media entry from OBS media.yaml file
def verifyMedium(medium):
    verifyKeys("media", medium, ['identifier', 'version', 'contributor', 'url'])
    if 'en' in medium['url']:
        reportError("Replace 'en' with the correct langauge code in media.yaml url's")
    version = "v" + medium['version']
    if medium['identifier'] != 'door43' and medium['url'].count(version) != 2:
        reportError("Correct the version numbers in media.yaml url's")
    if medium['identifier'] == 'pdf':
        sys.stdout.write("Verify all language codes and {latest} version in media.yaml.\n")
    else:
        sys.stdout.write("Review the " + medium['identifier'] + " media entry in media.yaml.\n")

# Confirms the existence of a LICENSE file
def verifyOtherFiles():
    found = False
    for fname in {"LICENSE", "LICENSE.TXT", "LICENSE.MD"}:
        path = os.path.join(manifestDir, fname)
        if os.path.isfile(path):
            found = True
            break
    if not found:
        reportError("LICENSE file is missing")

# Verifies that the project contains the six required fields and no others.
# Verifies that the path exists.
# Verifies that the title corresponds to the project type.
# Verifies that the sort field is not octal.
# Validate some other field values, depending on the type of project
def verifyProject(project, language_code):
    verifyKeys("projects", project, ['title', 'versification', 'identifier', 'sort', 'path', 'categories'])

    global manifestDir
    fullpath = os.path.join(manifestDir, project['path'])
    if len(project['path']) < 5 or not os.path.exists(fullpath):
        reportError("Invalid path: " + project['path'])
    if not isinstance(project['sort'], numbers.Integral):
        reportError("project:sort is the wrong type: " + str(project['sort']))
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
        if project['versification'] != 'ufw':
            reportError("Invalid project:versification: " + project['versification'] + ". Should be 'ufw'")
        cat = project['categories'][0]
        if len(project['categories']) != 1 or cat not in {'bible-ot', 'bible-nt'}:
            reportError("Invalid project:categories: " + cat)
    elif projtype == 'tw':
        if project['title'] not in {'translationWords','Translation Words'}:
            reportError("Invalid project:title: " + project['title'] + ". Should be translationWords or Translation Words")
    elif isBibleType(projtype):
        if project['title'].isascii() and not expectAscii(language_code):
            reportError("ASCII project:title book title: " + str(project['title']))
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if int(project['sort']) != bookinfo['sort']:
            reportError("Incorrect project:sort: " + str(project['sort']))
        if project['versification'] != 'ufw':
            reportError("Invalid project:versification: " + project['versification'] + ". Should be 'ufw'")
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
        if 'Open Bible Stories' not in project['title']:
            reportError("Invalid project:title: " + project['title'])
    elif projtype in {'obs-tn','obs-tq','obs-sn','obs-sq'}:
        if project['categories'] and len(project['categories']) != 0:
            reportError("Categories list should be empty: project:categories")
        if project['identifier'] != "obs":      #  New as of November 2021
            reportError("Invalid project:identifier: " + project['identifier'])
        if projtype == 'obs-tn':
            if not project['title'].endswith('Open Bible Stories Translation Notes') and project['title'] != 'OBS translationNotes':
                reportError("Invalid project:title: " + project['title'])
        elif projtype == 'obs-tq':
            if not project['title'].endswith('Open Bible Stories Translation Questions'):
                reportError("Invalid project:title for obs-tq project: " + project['title'])
        elif projtype == 'obs-sn':
            if project['title'] != 'Open Bible Stories Study Notes':
                reportError("Invalid project:title: " + project['title'])
        elif projtype == 'obs-sq':
            if project['title'] != 'Open Bible Stories Study Questions':
                reportError("Invalid project:title: " + project['title'])
    else:
        sys.stdout.write("Verify each project entry manually.\n")   # temp until all projtypes are supported

# For most project types, the projects:identifier is really a part identifier, like book id (ULB, tQ, etc.), or section id (tA)

# Verifies the projects list
def verifyProjects(projects, language_code):
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
        if projtype in ['obs','obs-tn','obs-tq','obs-sn','obs-sq', 'tw'] and nprojects != 1:
            reportError("There should be exactly 1 project listed under projects.")
        elif projtype == 'ta' and nprojects != 4:
            reportError("There should be exactly 4 projects listed under projects.")
        elif projtype in {'tn','tn-tsv','tq'} or isBibleType(projtype):
            if nprojects not in (27,39,66):
                reportWarning("Number of projects listed: " + str(nprojects))

        for p in projects:
            verifyProject(p, language_code)

# Verify one project of an OBS media.yaml file
def verifyProjectOBS(project):
    if project['identifier'] in {'obs','obs-tn','obs-tq'}:
        nmedia = len(project['media'])
        if nmedia < 1:
            reportError('No media are defined in media.yaml')
        else:
            for medium in project['media']:
                verifyMedium(medium)
    else:
        reportError("Unknowns identifier in media.yaml: " + project['identifier'])


# Verify the projects section of an OBS media.yaml file, which is the only section
def verifyProjectsOBS(projects):
    if not projects:
        reportError('media.yaml is empty')
    else:
        for p in projects:
            verifyProjectOBS(p)

def verifyReadme(dirpath):
    readmepath = os.path.join(dirpath, "README.md")
    if not os.path.isfile(readmepath):
        readmepath = os.path.join(dirpath, "README")
    if not os.path.isfile(readmepath):
        reportError("No README file is found")
    else:
        pathlibpath = pathlib.Path(readmepath)
        modtime = datetime.fromtimestamp(pathlibpath.stat().st_mtime)
        gitpath = os.path.join(dirpath, ".git/config")
        if os.path.isfile(gitpath):
            pathlibpath = pathlib.Path(gitpath)
            delta = modtime - datetime.fromtimestamp(pathlibpath.stat().st_mtime)
        else:
            delta = timedelta(hours=2)
        if modtime.date() != date.today():
            reportWarning("README file was not updated today")
        else:
            print("Remember to update README file.")

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
                reportWarning("Non-matching language code for relation element: " + rel)
            if parts[1] not in {'obs','obs-tn','obs-tq','obs-sn','obs-sq','tn','tq','tw','ta','tm'} and not isBibleType(parts[1]):
                if parts[1][0:4] != 'ugnt' and parts[1][0:3] != 'uhb':
                    reportError("Invalid project code in relation element: " + rel)
            #if parts[1] == projtype or (projtype == 'tn-tsv' and parts[1] == 'tn'):
                #reportError("Project code in relation element is same as current project: " + rel)

# The relation element is a list of strings.
def verifyRelations(relations):
    uniq = set(relations)
    if len(uniq) < len(relations):
        reportError("There are duplicates in the relations list")
    if len(uniq) < 2 and not isBibleType(projtype) and projtype != 'obs':
        reportWarning("The relations list seems incomplete")
    ugnt = False
    uhb = False
    if len(relations) < 1 and projtype != 'reg':
        reportWarning("No relations are listed")
    for r in relations:
        verifyRelation(r)
        if projtype == 'tn-tsv':
            parts = r.split('/')
            if len(parts) == 2 and parts[0] == 'el-x-koine' and 'ugnt?v=' in parts[1]:
                ugnt = True
            if len(parts) == 2 and parts[0] == 'hbo' and 'uhb?v=' in parts[1]:
                uhb = True
    if projtype == 'tn-tsv' and not ugnt:
        reportError("Must reference 'el-x-koine/ugnt?v=...' in relation if there are any NT notes")
    if projtype == 'tn-tsv' and not uhb:
        reportError("Must reference 'hbo/uhb?v=...' in relation if there are any OT notes")
    if projtype in {'tn-tsv','tw'} and '/glt' not in relations[0] and '/ult' not in relations[0]:
        reportError("'glt' should be first relation listed for tn and tw projects, if there is a glt")

# Validates the source field, which is an array of dictionaries.
def verifySource(source):
    if not source or len(source) < 1:
        reportError("Invalid source spec: should be an array of dictionary of three fields.")
    for dict in source:
        verifyKeys("source[x]", dict, ['language', 'identifier', 'version'])

        global projtype
        if projtype in {'obs','obs-tq','obs-tn','obs-sq','obs-sn'} and dict['identifier'] != 'obs':
            reportError(f"Incorrect source:identifier for project type: {projtype}: should be 'obs'")
        if dict['identifier'] != projtype and projtype in {'obs', 'tn', 'tq', 'tw'}:
            reportError("Inappropriate source:identifier (" + dict['identifier'] + ") for project type: " + projtype)
        if dict['identifier'] != 'ulb' and projtype == 'reg':
            reportWarning("Unusual source:identifier for reg project: " + dict['identifier'])
        if dict['identifier'] != 'tn' and projtype == 'tn-tsv':
            reportError("Incorrect source:identifier for tn-tsv project: " + dict['identifier'])
        if not re.match(r'[a-z][a-z0-9-]', dict['identifier'], re.UNICODE):
            reportError("Invalid source:identifier (need lower case ascii, no spaces): " + dict['identifier'])
        if dict['language'] == 'English':
            reportError("Use a language code in source:language, not \'" + dict['language'] + '\'')
        elif dict['language'] == getLanguageId():
            reportWarning("source:language matches target language")
        elif dict['language'] not in {'en','hbo','el-x-koine'}:
            reportWarning("source:language: " + dict['language'])
        verifyStringField(dict, 'version', 1)

# Validates that the specified key is a string of specified minimum length.
# Returns False if there is a problem.
def verifyStringField(dict, key, minlength):
    success = True
    if key in dict:
        if not isinstance(dict[key], str):
            reportError("Value must be a string: " + key + ": " + str(dict[key]))
            success = False
        elif len(dict[key]) < minlength:
            reportError("Invalid value for " + key + ": " + dict[key])
            success = False
    return success

# Validates the subject field
def verifySubject(subject):
    if isBibleType(projtype):
        if subject not in {'Bible', 'Aligned Bible'}:
            reportError("Invalid subject: " + subject + " (expected 'Bible' or 'Aligned Bible')")
        elif isAlignedBibleType(projtype) and subject != "Aligned Bible":
            reportError("Invalid subject: " + subject + " (expected 'Aligned Bible')")
        expected_subject = subject  # to avoid redundant error msgs
    elif projtype == 'ta':
        expected_subject = 'Translation Academy'
    elif projtype == 'tw':
        expected_subject = 'Translation Words'
    elif projtype == 'tn':
        expected_subject = 'Translation Notes'
    elif projtype == 'tn-tsv':
        expected_subject = 'TSV Translation Notes'
    elif projtype == 'tn':
        expected_subject = 'Translation Notes'
    elif projtype == 'tq':
        expected_subject = 'Translation Questions'
    elif projtype == 'obs':
        expected_subject = 'Open Bible Stories'
    elif projtype == 'obs-tq':
        expected_subject = 'OBS Translation Questions'
    elif projtype == 'obs-tn':
        expected_subject = 'OBS Translation Notes'
    elif projtype == 'obs-sq':
        expected_subject = 'OBS Study Questions'
    elif projtype == 'obs-sn':
        expected_subject = 'OBS Study Notes'
    else:
        sys.stdout.write("Verify subject manually.\n")
        expected_subject = subject
    if subject != expected_subject:
        reportError("Invalid subject: " + subject + " (expected '" + expected_subject + "')")

# Verifies that the title in the manifest files is acceptable.
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

# For tA projects, verify that each subfolder in the folder has the three necessary files.
def verifyTitleFiles(folder):
    if os.path.isdir(folder):
        direntries = os.scandir(folder)
        for direntry in direntries:
            if direntry.is_dir():
                articlePath = os.path.join(folder, direntry.name)
                for fname in ["01.md", "title.md", "sub-title.md"]:
                    path = os.path.join(articlePath, fname)
                    if not os.path.isfile(path):
                        reportError("Missing file: " + os.path.relpath(path, manifestDir))

def verifyTWfiles(path):
    parseYaml( os.path.join(os.path.join(path, "bible"), "config.yaml") )

# Returns number of ASCII titles found in toc.yaml files (tA projects only).
# Reports non-ASCII links as errors.
def verifyTocYaml(contents, tocpath):
    nAsciiTitles = 0
    if contents['title'].isascii():
        nAsciiTitles += 1
    if 'sections' in contents:
        if contents['sections']:
            for section in contents['sections']:
                nAsciiTitles += verifyTocYaml(section, tocpath)
        else:
            reportError(f"Empty section ({contents['title']}) in {tocpath}")
    if 'link' in contents and not contents['link'].isascii():
        reportError(f"Non-ASCII link ({contents['link']}) in {tocpath}")
    return nAsciiTitles

# Loads the specified yaml file and reports errors.
# Returns the contents of the file if no errors.
def parseYaml(path):
    contents = None
    if os.path.isfile(path):
        if has_bom(path):
            reportError(f"{path} file has a Byte Order Mark. Remove it.")
        with io.open(path, "tr", encoding='utf-8-sig') as file:
            try:
                contents = yaml.safe_load(file)
            except yaml.scanner.ScannerError as e:
                reportError(f"Yaml syntax error at or before line {e.problem_mark.line} in: {os.path.relpath(path, manifestDir)}")
            except yaml.parser.ParserError as e:
                reportError(f"Yaml parsing error at or before line {e.problem_mark.line} in: {os.path.relpath(path, manifestDir)}")
    else:
        reportError(f"File missing: {os.path.relpath(path, manifestDir)}")
    return contents

# For tA projects, verify that each folder has a valid toc.yaml and config.yaml file.
def verifyYamls(folderpath):
    parseYaml( os.path.join(folderpath, "config.yaml") )
    tocpath = os.path.join(folderpath, "toc.yaml")
    if contents := parseYaml(tocpath):
        nAsciiTitles = verifyTocYaml(contents, os.path.relpath(tocpath, manifestDir))
        if nAsciiTitles > 0 and not expectAscii(getLanguageId()):
            reportWarning(f"{nAsciiTitles} likely untranslated titles in {os.path.relpath(tocpath, manifestDir)}")

def verifyType(type):
    failure = False
    if projtype == 'ta':
        failure = (type != 'man')
    elif projtype == 'tw':
        failure = (type != 'dict')
    elif projtype in {'tn', 'tn-tsv', 'tq', 'obs-tn','obs-tq','obs-sn','obs-sq'}:
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
#    if int(sourceversion) < 100 and (len(parts) < 2 or parts[0] != sourceversion or int(parts[-1]) < 1):
#        reportError("Invalid version: " + version + "; Source version is " + sourceversion)
#    if int(sourceversion) >= 100 and (len(parts) > 1 or int(parts[0]) > 99):
#        reportError("Invalid version: " + version + ". Source version is " + sourceversion)
    if projtype == 'obs':
        sys.stdout.write("Verify that the version number listed in front/intro.md is: " + version + "\n")

# Returns True if the file has a BOM
def has_bom(path):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for bom in [codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]:
        if raw.startswith(bom):
            return True
    return False

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
        print("Done, no errors found.\n")
    else:
        print("Finished checking, found " + str(nIssues) + " issues.\n")