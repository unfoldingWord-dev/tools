# coding: latin-1
# This program converts a folder of OBS text files in the newer tStudio
# format (one .txt file per OBS chunk, multiple chunks per story)
# to a set of corresponding OBS story files in Markdown format.
# Outputs .md files to a content folder under target_dir.
# The input should contain folders named 01-50, front, and back.

import re       # regular expression module
import io
import os
import codecs
import string
import sys
import shutil

# Globals
target_dir = r'E:\DCS\Arli\rmy-x-vwa_obs'
en_contentdir = r'E:\DCS\English\en_obs\content'

# Merges the contents of each file in the folder, into output mdfile.
# Intersperses image links between text from each file if it can.
# Otherwise, dumps image links at end of file.
def merge(image_list, folder, mdfile):
    chunklist = listChunks(folder)
    images_inline = (len(image_list) == len(chunklist))
    if not images_inline:
        sys.stderr.write("There are " + str(len(chunklist)) + " chunks in " + folder + " but " + str(len(image_list)) + " images for this story.\n")
        sys.stderr.write("Available image links will be dumped at end of .md file.\n")
    chunksOut = 0

    for filename in chunklist:
        inputpath = os.path.join(folder, filename)
        enc = detect_by_bom(inputpath, default="utf-8")
        input = io.open(inputpath, "tr", 1, encoding=enc)
        chunk = input.read().strip()
        if chunk:
            if images_inline and chunksOut < len(image_list):
                mdfile.write("\n" + image_list[chunksOut])
            mdfile.write("\n")
            mdfile.write(chunk + "\n")
        chunksOut += 1
        input.close()

    if not images_inline:
        mdfile.write("\n\n")
        for image in image_list:
            mdfile.write(image + "\n")


# Returns the list of chunk file names
def listChunks(folder):
    filenames = os.listdir(folder)
    chunks = []
    chunkname = re.compile(r'[0-1][0-9]\.txt')
    for filename in filenames:
        if chunkname.match(filename):
            chunks.append(filename)
    return chunks

image_re = re.compile(r'\!\[OBS Image\]')

# Returns a list of images parsed out of the specified OBS file.
def listImages(mdpath):
    image_list = []
    enc = detect_by_bom(mdpath, default="utf-8")
    input = io.open(mdpath, "tr", 1, encoding=enc)
    for line in input.readlines():
        if image_re.match(line):
            image_list.append(line)
    input.close()
    return image_list


def detect_by_bom(path, default):
    with open(path, 'rb') as f:
        raw = f.read(4)
        f.close
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms):
            return enc
    return default

# Outputs up to two line of title.txt into .md file.
def outputTitle(titlepath, mdfile):
    enc = detect_by_bom(titlepath, default="utf-8")
    input = io.open(titlepath, "tr", 1, encoding=enc)
    lines = input.readlines()
    input.close()
    titleLinesOut = 0
    for line in lines:
        line = line.strip()
        if line:
            if titleLinesOut == 0:
                mdfile.write("# " + line + "\n")      # title
                titleLinesOut = 1
            elif titleLinesOut == 1:
                mdfile.write("## " + line + "\n")      # subtitle
                break
    
# Outputs the contents of refpath, enclosed with underscores.
def outputReference(refpath, mdfile):
    enc = detect_by_bom(refpath, default="utf-8")
    input = io.open(refpath, "tr", 1, encoding=enc)
    lines = input.readlines()
    input.close()
    for line in lines:
        line = line.strip()
        if line:
            mdfile.write("\n_" + line + "_\n")

import shutil

# Creates copy of path in contentdir.
# Does nothing if destination path already exists.
# Used for copying "back" or "front" folders to 
def copyFolder(path, subdir, contentdir):
    destpath = os.path.join(contentdir, subdir)
    if not os.path.exists(destpath):
        sys.stdout.write("Copying " + path + "\\\n")
        shutil.copytree(path, destpath)

def renameTitle(contentdir, subdir):
    frontpath = os.path.join(contentdir, subdir)
    titlepath = os.path.join(frontpath, "title.txt")
    if os.path.isfile(titlepath):
        mdpath = os.path.join(frontpath, "title.md")
        os.rename(titlepath, mdpath)
    
# Merge title, chunks, and reference the files from folder into one equivalent .md file
def convertStory(folder, storynumber, contentpath):
    sys.stdout.write("Converting " + folder + "\\\n")
    sys.stdout.flush()
    mdpath = os.path.join(contentpath, storynumber + ".md")
    english_md_path = os.path.join(en_contentdir, storynumber + '.md')

    if not os.path.isfile(english_md_path):
        sys.stderr.write("Cannot access English OBS file: " + english_md_path + "\n")
    else:
        mdfile = io.open(mdpath, "tw", encoding='utf-8', newline='\n')
        
        # convert title
        titlepath = os.path.join(folder, "title.txt")
        if os.path.isfile(titlepath):
            outputTitle(titlepath, mdfile)

        # convert chunks
        image_list = listImages(english_md_path)
        merge(image_list, folder, mdfile)

        # convert reference
        refpath = os.path.join(folder, "reference.txt")
        if os.path.isfile(refpath):
            outputReference(refpath, mdfile)

        mdfile.close()

# Creates content folder if needed.
# Calls convertStory to merge and convert one folder (one story) at a time.
def convertStories(masterfolder):
    contentpath = os.path.join(target_dir, "content")
    if not os.path.isdir(contentpath):
        os.mkdir(contentpath)

    for subdir in os.listdir(masterfolder):
        if subdir[0] == '.':
            continue
        folder = os.path.join(masterfolder, subdir)
        if os.path.isdir(folder):
            if subdir == "front" or subdir == "back":
                copyFolder(folder, subdir, contentpath)
                renameTitle(contentpath, subdir)
            elif re.match(r'[0-5][0-9]$', subdir):
                convertStory(folder, subdir, contentpath)
  
# Copies front/intro.md from English content if missing in target
# Copies back/intro.md from English content if missing in target
def copyIntroFile(target, dir):
    folder = os.path.join(target, dir)
    if not os.path.isdir(folder):
        os.mkdir(folder)

    intropath = os.path.join(folder, "intro.md")
    if not os.path.isfile(intropath):
        enfolder = os.path.join(en_contentdir, dir)
        enpath = os.path.join(enfolder, "intro.md")
        shutil.copyfile(enpath, intropath)

# Processes all .txt files in specified directory, one at a time
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == 'hard-coded-path':
        folder = r'E:\DCS\Arli\OBS'
    else:
        folder = sys.argv[1]

    if folder and os.path.isdir(folder):
        convertStories(folder)
        contentdir = os.path.join(target_dir, "content")
        copyIntroFile(contentdir, "front")
        copyIntroFile(contentdir, "back")
#        sys.stdout.write("\nCarefully check file names and files in front and back folders.\n")
    else:
        sys.stderr.write("Usage: python obs_mergetxt2md.py <folder>\n  Use . for current folder.\n")
