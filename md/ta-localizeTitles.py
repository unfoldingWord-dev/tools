# -*- coding: utf-8 -*-
# This program localizes the titles of tA articles in toc.yaml files.
#   Copies translated titles from the title.md files.
#   Removes links to articles that do not exist.
#   Removes empty sections.
#   Leaves the structure of the table of contents unchanged (except for removing completely empty parts).
#
# Optionally, report errors in config.yaml files.

import re
import io
import os
import codecs
import string
import sys
import yaml

# Globals
source_dir = r'C:\DCS\Spanish-es-419\es-419_ta.STR\translate'
nRewritten = 0
suppress1 = True    # Suppress config.yaml checking

def shortname(path):
    if path.startswith(source_dir):
        path = path[len(source_dir)+1:]
    return path

def reportError(msg):
    try:
        sys.stderr.write(msg + '\n')
    except UnicodeEncodeError as e:
        sys.stderr.write("Error message cannot display, contains Unicode.\n")

# Attempts to load the specified file as a yaml file.
# Reports yaml errors.
# Returns the contents of the file if no errors.
def parseYaml(path):
    contents = None
    if os.path.isfile(path):
        with io.open(path, "tr", encoding='utf-8-sig') as file:
            try:
                contents = yaml.safe_load(file)
            except yaml.scanner.ScannerError as e:
                reportError(f"Yaml syntax error at or before line {e.problem_mark.line} in: {shortname(path)}")
            except yaml.parser.ParserError as e:
                reportError(f"Yaml parsing error at or before line {e.problem_mark.line} in: {shortname(path)}")
    else:
        reportError(f"File missing: {shortname(path)}")
    return contents

# Verify that the specified fields exist and no others.
def verifyKeys(article, dict, keys, configpath):
    for key in keys:
        if key not in dict:
            reportError(f"Missing {key} field under {article} in {configpath}")
    for field in dict:
        if field not in keys:
            reportError(f"Extra field: ({field}) under {article} in {configpath}")


# Reads the translated title from the specified title.md file.
def fetchTitle(folder, linkstr):
    title = None
    titlepath = os.path.join(os.path.join(folder, linkstr), "title.md")
    if os.path.isfile(titlepath):
        input = io.open(titlepath, "tr", 1, encoding="utf-8")
        title = input.read()
        input.close()
        title = title.strip()
    return title

title_re = re.compile(r'([ \-]*title: +)[\'"](.*)[\'"]', flags=re.UNICODE)
link_re =  re.compile(r'link: +([\w\-]+)')
section_re = re.compile(r' *sections', re.UNICODE)

# Puts double quotes or single quotes around the string, as appropriate.
def addQuotes(str):
    quote = '"'
    if quote in str:
        quote = "'"
        if quote in str:
            quote = ""
    return quote + str + quote

# Recursive function to convert toc.yaml content
# Localizes titles where possible.
# Removes (title,link) pairs where the linked article is missing.
# Removes empty (title,section) lists.
def convertContent(folder, content):
    if 'sections' in content:
        i = 0
        while i < len(content['sections']):
            newcontent = convertContent(folder, content['sections'][i])
            if newcontent:
                content['sections'][i] = newcontent
                i += 1
            else:
                del content['sections'][i]
        if len(content['sections']) == 0:
            del content['sections']
    if 'link' in content:
        if newtitle := fetchTitle(folder, content['link']):
            content['title'] = newtitle
        else:
            sys.stdout.write("Article does not exist, removing reference to: " + content['link'] + "\n")
            del content['link']
    if not 'link' in content and not 'sections' in content:
        content = None
    return content

# Recursive function to dump the data in our preferred yaml format.
def dumpContent(content, output, indent):
    if 'title' in content:
        if indent == 0:
            line = f"title: {addQuotes(content['title'])}\n"
        else:
            line = " "*(indent-2) + f"- title: {addQuotes(content['title'])}\n"
        output.write(line)
    if 'link' in content:
        line = " "*indent + f"link: {content['link']}\n"
        output.write(line)
    if 'sections' in content:
        if indent == 0:
            line = "sections:\n"
        else:
            line = " "*indent + f"sections:\n"
        output.write(line)
        for section in content['sections']:
            dumpContent(section, output, indent+4)

# Converts and rewrites the toc.yaml file in the specified folder.
def convertToc(folder):
    global nRewritten
    tocpath = os.path.join(folder, "toc.yaml")
    content = parseYaml(tocpath)
    bakpath = tocpath + ".orig"
    if not os.path.isfile(bakpath):
        os.rename(tocpath, bakpath)
    converted_content = convertContent(folder, content)
    with io.open(tocpath, "tw", encoding="utf-8", newline='\n') as output:
        dumpContent(converted_content, output, 0)
        # yaml.safe_dump(content, output, allow_unicode=True, encoding='utf-8')
    nRewritten += 1

# Recursive routine to process files under the specified folder
# Only one toc.yaml file is processed under each folder considered.
def convertFolder(folder):
    tocpath = os.path.join(folder, "toc.yaml")
    if os.path.isfile(tocpath):
        sys.stdout.write("Rewriting: " + shortname(tocpath) + '\n')
        convertToc(folder)
    else:
        for entry in os.listdir(folder):
            if entry[0] != '.':
                path = os.path.join(folder, entry)
                if os.path.isdir(path):
                    convertFolder(path)

def getlinks(tocpath):
    links = set()
    with io.open(tocpath, "tr", encoding="utf-8-sig") as input:
        lines = input.readlines()
    for line in lines:
        if link := link_re.search(line):
            links.add(link.group(1))
    return links

# Compares the "link" values in toc.yaml to the article names in the specified folder.
# Reports missing and extra "link" values.
def checkToc(folder):
    tocpath = os.path.join(folder, "toc.yaml")
    if parseYaml(tocpath):
        toclinks = getlinks(tocpath)
        articles = list()
        direntries = os.scandir(folder)
        for direntry in direntries:
            if direntry.is_dir():
                articles.append(direntry.name)
        articles.sort()
        for article in articles:
            if not article in toclinks:
                reportError("This article is not referenced in " + shortname(tocpath) + ": " + article)
        for link in toclinks:
            if not link in articles:    # should not occur as rewriteTocLine() removed these
                reportError(shortname(tocpath) + " references a missing article: " + link)

# Compares the articles referenced in config.yaml to the article names in the corresponding folder.
# Reports missing and extra articles.
def checkConfig(folder):
    badnames = set()
    configpath = os.path.join(folder, "config.yaml")
    if contents := parseYaml(configpath):
        for article in contents:
            if not os.path.isdir(os.path.join(folder, article)):
                reportError(f"Article ({article}) referenced in {shortname(configpath)} does not exist")
                badnames.add(article)
            verifyKeys(article, contents[article], ["recommended","dependencies"], shortname(configpath))
            for key in ["recommended","dependencies"]:
                for name in contents[article][key]:
                    if not os.path.isdir(os.path.join(folder, name)) and name not in badnames:
                        reportError(f"Article ({name}) referenced in {shortname(configpath)} does not exist")
                        badnames.add(name)
        direntries = os.scandir(folder)
        for direntry in direntries:
            if direntry.is_dir() and not direntry.name in contents:
                reportError(f"This article is not found in {shortname(configpath)}: ({direntry.name})")

# Rewrites toc.yaml files under the specified directory
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != 'hard-coded-path':
        source_dir = sys.argv[1]

    if source_dir and os.path.isdir(source_dir):
        convertFolder(source_dir)
        if os.path.basename(source_dir) in {"checking","intro","process","translate"}:
            checkToc(source_dir)
        for dir in ["checking","intro","process","translate"]:
            folder = os.path.join(source_dir, dir)
            if os.path.isdir(folder):
                checkToc(folder)
                if not suppress1:
                    checkConfig(folder)
        sys.stdout.write("Done. Rewrote " + str(nRewritten) + " files.\n")
    else:
        sys.stderr.write("Usage: python ta-localizeTitles.py <folder>\n  Use . for current folder.\n")
