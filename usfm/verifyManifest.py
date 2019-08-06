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

# Globals
issuesFile = None
manifestDir = None
nIssues = 0
projtype = u''

from datetime import datetime
from datetime import date
import sys
import os
import yaml
import io
import codecs
import re
import usfm_verses

# Returns language identifier based on the director name
def getLanguageId():
    global manifestDir
    parts = os.path.basename(manifestDir).rsplit('_', 1)
    return parts[-2]

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
        sys.stderr.write(msg + u'\n')
    except UnicodeEncodeError as e:
        sys.stderr.write("See error message in manifest-issues.txt. It contains Unicode.\n")

    issues = openIssuesFile().write(msg + u'\n')
    nIssues += 1

# This function validates the project entries for a tA project.
# tA projects should have four projects entries, each with specific content
def verifyAcademyProject(project):
    if len(project['categories']) != 1 or project['categories'][0] != u'ta':
        reportError(u"Invalid project:categories: " + project['categories'][0])

    section = project['identifier']
    if section == u'intro':
        if project['title'] != u"Introduction to translationAcademy":
            reportError(u"Invalid project:title: " + project['title'])
        if project['sort'] != 0:
            reportError(u"Invalid project:sort: " + str(project['sort']))
    elif section == u'process':
        if project['title'] != u"Process Manual":
            reportError(u"Invalid project:title: " + project['title'])
        if project['sort'] != 1:
            reportError(u"Invalid project:sort: " + str(project['sort']))
    elif section == u'translate':
        if project['title'] != u"Translation Manual":
            reportError(u"Invalid project:title: " + project['title'])
        if project['sort'] != 2:
            reportError(u"Invalid project:sort: " + str(project['sort']))
    elif section == u'checking':
        if project['title'] != u"Checking Manual":
            reportError(u"Invalid project:title: " + project['title'])
        if project['sort'] != 3:
            reportError(u"Invalid project:sort: " + str(project['sort']))
    else:
        reportError("Invalid project:identifier: " + section)

# Verifies the checking section of the manifest.
def verifyChecking(checking):
    verifyKeys(u'checking', checking, [u'checking_entity', u'checking_level'])
    if 'checking_entity' in checking.keys():
        if len(checking['checking_entity']) < 1:
            reportError("Missing checking_entity.")
        for c in checking['checking_entity']:
            if (type(c) != str and type(c) != unicode) or len(c) < 3:
                reportError(u"Invalid checking_entity: " + unicode(c))
    if u'checking_level' in checking.keys() and checking['checking_level'] != u'3':
        reportError(u"Invalid value for checking_level: " + checking['checking_level'])

# Verifies the contributors list
def verifyContributors(core):
    if u'contributor' in core.keys():
        if len(core[u'contributor']) < 1:
            reportError(u"Missing contributors!")
        for c in core[u'contributor']:
            if (type(c) != str and type(c) != unicode) or len(c) < 3:
                reportError(u"Invalid contributor name: " + unicode(c))

# Checks the dublin_core of the manifest
def verifyCore(core):
    verifyKeys(u"dublin_core", core, [u'conformsto', u'contributor', u'creator', u'description', u'format', \
        u'identifier', u'issued', u'modified', u'language', u'publisher', u'relation', u'rights', \
        u'source', u'subject', u'title', u'type', u'version'])

    # Check project identifier first because it is used to validate some other fields
    verifyIdentifier(core)  # Sets the projtype global
    if u'conformsto' in core.keys() and core['conformsto'] != u'rc0.2':
        reportError(u"Invalid value for conformsto: " + core['conformsto'])
    verifyContributors(core)
    verifyStringField(core, u'creator', 3)
    verifyDates(core['issued'], core['modified'])
    verifyFormat(core)
    verifyLanguage(core[u'language'])
    
    pub = core['publisher']
    if pub.lower().find(u'unfolding') >= 0 and core['language']['identifier'] != u'en':
        reportError(u"Invalid publisher: " + pub)
    verifyRelations(core[u'relation'])
    if u'rights' in core.keys() and core['rights'] != u'CC BY-SA 4.0':
        reportError(u"Invalid value for rights: " + core['rights'])
    verifySource(core['source'])
    verifySubject(core['subject'])
    verifyStringField(core, u'title', 3)
    verifyType(core['type'])
    verifyVersion(core['version'], core['source'][0]['version'])

def verifyDates(issued, modified):
    issuedate = datetime.strptime(issued, "%Y-%m-%d").date()
    moddate = datetime.strptime(modified, "%Y-%m-%d").date()
    if moddate != date.today():
        reportError(u"Wrong date - modified: " + modified)
    if issuedate > moddate:
        reportError(u"Dates wrong - issued: " + issued + u", modified: " + modified)

def verifyDir(dirpath):
    path = os.path.join(dirpath, "manifest.yaml")
    if os.path.isfile(path):
        verifyFile(path)
    else:
        reportError("No manifest.yaml file in: " + dirpath)

# Manifest file verification
def verifyFile(path):
    if has_bom(path):
        reportError(u"manifest.yaml file has a Byte Order Mark. Remove it.")
    manifestFile = io.open(path, "tr", encoding='utf-8')
    manifest = yaml.safe_load(manifestFile)
    manifestFile.close()
    verifyKeys(u"", manifest, [u'dublin_core', u'checking', u'projects'])
    verifyCore(manifest[u'dublin_core'])
    verifyChecking(manifest[u'checking'])
    verifyProjects(manifest['projects'])

# Verifies format field is a valid string, depending on project type.
# Done with iev, obs, ta, tq, tn, tw, ulb, udb, ust
def verifyFormat(core):
    global projtype
    if verifyStringField(core, u'format', 9):
        if projtype in [u'ta', u'tq', u'tn', u'tw', u'obs']:
            if core[u'format'] != u'text/markdown':
                reportError(u"Invalid format: " + core[u'format'])
        elif projtype in [u'ulb', u'udb', u'iev']:
            if core[u'format'] != u'text/usfm':
                reportError(u"Invalid format: " + core[u'format'])
        elif projtype in [u'ust']:
            if core[u'format'] != u'text/usfm3':
                reportError(u"Invalid format: " + core[u'format'])
        else:
            reportError(u"Unable to validate format because script does not yet support project type: " + projtype)
            
# Validates the dublin_core:identifier field in several ways.
# Sets the global projtype variable which is used by subsequent checks.
def verifyIdentifier(core):
    global projtype
    global manifestDir
    if verifyStringField(core, u'identifier', 2):
        id = core[u'identifier']
        if id not in [u'tn', u'tq', u'tw', u'ulb', u'udb', u'ust', u'ta', u'obs', u'iev']:
            reportError(u"Invalid id: " + id)
        else:
            projtype = id
        parts = manifestDir.rsplit('_', 1)
        if id.lower() != parts[-1].lower():     # last part of directory name should match the projtype string
            reportError(u"Wrong project identifier: " + id)

# Verify that the specified fields exist and no others.
def verifyKeys(group, dict, keys):
    for key in keys:
        if key not in dict.keys():
            reportError(u'Missing field: ' + group + u':' + key)
    for field in dict:
        if field not in keys:
            reportError(u"Extra field: " + group + u":" + field)

# Validate the language field and its subfields.
def verifyLanguage(language):
    verifyKeys(u"language", language, [u'direction', u'identifier', u'title'])
    if u'direction' in language.keys():
        if language[u'direction'] != u'ltr' and language[u'direction'] != u'rtl':
            reportError(u"Incorrect language direction: " + language[u'direction'])
    if u'identifier' in language.keys():
        if language[u'identifier'] != getLanguageId():
            reportError(u"Wrong language identifier: " + language[u'identifier'])
    if verifyStringField(language, u'title', 3):
        try:
            sys.stdout.write("Remember to localize language title: " + language[u'title'] + u'\n')
        except UnicodeEncodeError as e:
            x = 1  # No error; the UnicodeEncodeError exception is evidence of a localized language title.

# Verifies that the project contains the six required fields and no others.
# Verifies that the path exists.
# Verifies that the title corresponds to the project type.
# Validate some other field values, depending on the type of project
# Done with tA, tW, ulb, udb, ust
## NOT DONE with tQ, OBS, OBS-tQ, OBS-TN
def verifyProject(project):
    verifyKeys("projects", project, ['title', 'versification', 'identifier', 'sort', 'path', 'categories'])

    global manifestDir
    fullpath = os.path.join(manifestDir, project['path'])
    if len(project['path']) < 5 or not os.path.exists(fullpath):
        reportError("Invalid path: " + project['path'])
    if projtype == u'ta':
        verifyAcademyProject(project)
    elif projtype == u'tn':
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if project['sort'] != bookinfo['sort']:
            reportError(u"Incorrect project:sort: " + str(project['sort']))
        if len(project['categories']) != 0:
            reportError(u"Categories list should be empty: project:categories")
    elif projtype == u'tw':
        if project['title'] != u'translationWords':
            reportError(u"Invalid project:title: " + project['title'])
    elif projtype in [u'ulb', u'udb', u'ust', u'iev']:
        bookinfo = usfm_verses.verseCounts[project['identifier'].upper()]
        if project['sort'] != bookinfo['sort']:
            reportError(u"Incorrect project:sort: " + str(project['sort']))
        if project['versification'] != u'ufw':
            reportError(u"Invalid project:versification: " + project['versification'])
        if len(project['identifier']) != 3:
            reportError(u"Invalid project:identifier: " + project['identifier'])
        cat = project['categories'][0]
        if len(project['categories']) != 1 or not (cat == u'bible-ot' or cat == u'bible-nt'):
            reportError(u"Invalid project:categories: " + cat)
    elif projtype == u'obs':
        if project['categories']:
            reportError(u"Should be blank: project:categories")
        if project['versification']:
            reportError(u"Should be blank: project:versification")
        if project['identifier'] != u'obs':
            reportError(u"Invalid project:identifier: " + project['identifier'])
        if project['title'] != u'Open Bible Stories':
            reportError(u"Invalid project:title: " + project['title'])
    else:
        sys.stdout.write("Verify each project entry manually.\n")   # temp until all projtypes are supported

    # For most project types, the projects:identifier is really a part identifier, like book id (ULB, tQ, etc.), or section id (tA)
    
# Verifies the projects list
def verifyProjects(projects):
    if not projects:
        reportError(u'Empty projects list')
    else:
        global projtype
        nprojects = len(projects)
        if nprojects < 1:
            reportError(u'Empty projects list')
        if projtype in [u'obs', u'tw'] and nprojects != 1:
            reportError(u"There should be exactly 1 project listed under projects.")
        elif projtype == u'ta' and nprojects != 4:
            reportError(u"There should be exactly 4 projects listed under projects.")
        elif projtype in [u'tn', u'ulb', u'udb', u'ust', u'iev'] and nprojects not in (27,39,66):
            reportError(u"Number of projects listed: " + str(nprojects))
            
        for p in projects:
            verifyProject(p)

# NOT DONE - need to support UHG-type entries
def verifyRelation(rel):
    if (type(rel) != str and type(rel) != unicode):
        reportError(u"Relation element is not a string: " + str(rel))
    elif len(rel) < 5:
        reportError(u"Invalid value for relation element: " + rel)
    else:
        parts = rel.split(u'/')
        if len(parts) != 2:
            reportError(u"Invalid format for relation element: " + rel)
        else:
            global projtype
            if parts[0] !=  getLanguageId():
                reportError(u"Incorrect language code for relation element: " + rel)
            if parts[1] not in [u'obs', u'obs-tn', u'tn', u'tq', u'tw', u'udb', u'ulb', u'ust', u'iev']:
                reportError(u"Invalid project code in relation element: " + rel)
            if parts[1] == projtype:
                reportError(u"Project code in relation element is same as current project: " + rel)

# The relation element is a list of strings.
def verifyRelations(relation):
    if len(relation) < 1:
        reportError(u"Missing relations in: relation")
    for r in relation:
        verifyRelation(r)
        
# Validates the source field, which is an array of exactly one dictionary.
def verifySource(source):
    if len(source) != 1:
        reportError(u"Invalid source spec: should be an array of one dictionary of three fields.")
    if len(source) > 0:
        verifyKeys(u"source[0]", source[0], [u'language', u'identifier', u'version'])

    global projtype
    if source[0]['identifier'] != projtype:
        reportError("Incorrect source:identifier: " + source[0]['identifier'])
    if source[0]['language'] == u'English':
        reportError("Use language code in source:language, not \'" + source[0]['language'] + u'\'')
    elif source[0]['language'] != u'en':
        reportError("Possible bad source:language: " + source[0]['language'])
    verifyStringField(source[0], u'version', 1)
    
# Validates that the specified key is a string of specified minimum length.
# Returns False if there is a problem.
def verifyStringField(dict, key, minlength):
    success = True
    if key in dict.keys():
        if (type(dict[key]) != str and type(dict[key]) != unicode):
            reportError(u"Value must be a string: " + key + u": " + str(dict[key]))
            success = False
        elif len(dict[key]) < minlength:
            reportError(u"Invalid value for " + key + u": " + dict[key])
            success = False
    return success

# Validates the subject field
def verifySubject(subject):
    failure = False
    if projtype == u'ta':
        failure = (subject != u'Translation Academy')
    elif projtype == u'tw':
        failure = (subject != u'Translation Words')
    elif projtype == u'tn':
        failure = (subject != u'Translation Notes')
    elif projtype == u'tq':
        failure = (subject != u'Translation Questions')
    elif projtype in [u'ulb', u'udb', u'ust', u'iev']:
        failure = (subject != u'Bible')
    elif projtype == u'obs':
        failure = (subject != u'Open Bible Stories')
    elif projtype == u'obs-tq':
        failure = (subject != u'OBS Translation Questions')
    elif projtype == u'obs-tn':
        failure = (subject != u'OBS Translation Notes')
    else:
        sys.stdout.write("Verify subject manually.\n")
    if failure:
        reportError(u"Invalid subject: " + subject)
    
def verifyType(type):
    failure = False
    if projtype == u'ta':
        failure = (type != u'man')
    elif projtype == u'tw':
        failure = (type != u'dict')
    elif projtype in [u'tn', u'tq', u'obs-tn', u'obs-tn']:
        failure = (type != u'help')
    elif projtype in [u'ulb', u'udb', u'ust', u'iev']:
        failure = (type != u'bundle')
    elif projtype == u'obs':
        failure = (type != u'book')
    elif projtype == u'obs-tq':
        failure = (type != u'OBS Translation Questions')
    elif projtype == u'obs-tn':
        failure = (type != u'OBS Translation Notes')
    else:
        sys.stdout.write("Verify type manually.\n")
    if failure:
        reportError(u"Invalid type: " + type)

def verifyVersion(version, sourceversion):
    parts = version.rsplit(u'.', 1)
    if parts[0] != sourceversion or int(parts[-1]) < 1:
        reportError(u"Invalid version: " + version)

# Returns True if the file has a BOM
def has_bom(path):
    with open(path, 'rb') as f:
        raw = f.read(4)
    for bom in [codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE, codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE]:
        if raw.startswith(bom):
            return True
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        manifestDir = r'C:\DCS\Nagamese\nag_obs'
    else:
        manifestDir = sys.argv[1]

    if os.path.isdir(manifestDir):
        verifyDir(manifestDir)
    else:
        reportError("Invalid directory: " + manifestDir + '\n') 

    if issuesFile:
        issuesFile.close()
    if nIssues == 0:
        print "Done, no issues found.\n"
    else:
        print "Finished checking, found " + str(nIssues) + " issues.\n"