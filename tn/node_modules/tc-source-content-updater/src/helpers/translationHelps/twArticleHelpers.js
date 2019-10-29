import fs from 'fs-extra';
import path from 'path-extra';
import {isObject} from 'util';
// helpers
import * as resourcesHelpers from '../resourcesHelpers';
// constants
import * as errors from '../../resources/errors';

/**
 * @description Processes the extracted files for translationWord to cerate the folder
 * structure and produce the index.js file for the language with the title of each article.
 * @param {Object} resource - Resource object
 * @param {String} sourcePath - Path to the extracted files that came from the zip file from the catalog
 * @param {String} outputPath - Path to place the processed resource files WIHTOUT the version in the path
 * @return {Boolean} true if success
 */
export function processTranslationWords(resource, sourcePath, outputPath) {
  if (!resource || !isObject(resource) || !resource.languageId || !resource.resourceId)
    throw Error(resourcesHelpers.formatError(resource, errors.RESOURCE_NOT_GIVEN));
  if (!sourcePath)
    throw Error(resourcesHelpers.formatError(resource, errors.SOURCE_PATH_NOT_GIVEN));
  if (!fs.pathExistsSync(sourcePath))
    throw Error(resourcesHelpers.formatError(resource, errors.SOURCE_PATH_NOT_EXIST));
  if (!outputPath)
    throw Error(resourcesHelpers.formatError(resource, errors.OUTPUT_PATH_NOT_GIVEN));
  if (fs.pathExistsSync(outputPath))
    fs.removeSync(outputPath);
  const typesPath = path.join(sourcePath, 'bible');
  const isDirectory = item => fs.lstatSync(path.join(typesPath, item)).isDirectory();
  const typeDirs = fs.readdirSync(typesPath).filter(isDirectory);
  typeDirs.forEach(typeDir => {
    const typePath = path.join(typesPath, typeDir);
    const files = fs.readdirSync(typePath).filter(filename => path.extname(filename) === '.md');
    generateGroupsIndex(typePath, outputPath, typeDir);
    files.forEach(fileName => {
      const sourcePath = path.join(typePath, fileName);
      const destinationPath = path.join(
        outputPath,
        typeDir,
        'articles',
        fileName,
      );
      fs.copySync(sourcePath, destinationPath);
    });
  });
  return true;
}

/**
 * @description - Generates the groups index for the tw articles (both kt, other and names).
 * @param {String} filesPath - Path to all tw markdown artciles.
 * @param {String} twOutputPath Path to the resource location in the static folder.
 * @param {String} folderName article type. ex. kt or other.
 */
function generateGroupsIndex(filesPath, twOutputPath, folderName) {
  let groupsIndex = [];
  let groupIds = fs.readdirSync(filesPath).filter(filename => {
    return filename.split('.').pop() === 'md';
  });
  groupIds.forEach(fileName => {
    let groupObject = {};
    const filePath = path.join(filesPath, fileName);
    const articleFile = fs.readFileSync(filePath, 'utf8');
    const groupId = fileName.replace('.md', '');
    // get the article's first line and remove #'s and spaces from beginning/end
    const groupName = articleFile.split('\n')[0].replace(/(^\s*#\s*|\s*#\s*$)/gi, '');
    groupObject.id = groupId;
    groupObject.name = groupName;
    groupsIndex.push(groupObject);
  });
  groupsIndex.sort(compareByFirstUniqueWord);
  const groupsIndexOutputPath = path.join(
    twOutputPath,
    folderName,
    'index.json',
  );

  fs.outputJsonSync(groupsIndexOutputPath, groupsIndex, {spaces: 2});
}

/**
 * Splits the string into words delimited by commas and compares the first unique word
 * @param {String} a first string to be compared
 * @param {String} b second string to be compared
 * @return {int} comparison result
 */
function compareByFirstUniqueWord(a, b) {
  let aWords = a.name.toUpperCase().split(',');
  let bWords = b.name.toUpperCase().split(',');
  while (aWords.length || bWords.length) {
    if (!aWords.length)
      return -1;
    if (!bWords.length)
      return 1;
    let aWord = aWords.shift().trim();
    let bWord = bWords.shift().trim();
    if (aWord !== bWord)
      return (aWord < bWord ? -1 : 1);
  }
  return 0; // both lists are the same
}
