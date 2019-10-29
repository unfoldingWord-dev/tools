import fs from 'fs-extra';
import path from 'path-extra';
import {isObject} from 'util';
// heleprs
import * as resourcesHelpers from '../resourcesHelpers';
// constants
import * as errors from '../../resources/errors';

/**
 * @description Processes the extracted files for translationAcademy to create a single file for each
 * article
 * @param {Object} resource - Resource object
 * @param {String} sourcePath - Path to the extracted files that came from the zip file in the catalog
 * @param {String} outputPath - Path to place the processed files WITHOUT version in the path
 * @return {Boolean} true if success
 */
export function processTranslationAcademy(resource, sourcePath, outputPath) {
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
  const manifest = resourcesHelpers.getResourceManifest(sourcePath);
  manifest.projects.forEach(project => {
    const folderPath = path.join(sourcePath, project.path);
    const isDirectory = item => fs.lstatSync(path.join(folderPath, item)).isDirectory();
    const articleDirs = fs.readdirSync(folderPath).filter(isDirectory);
    articleDirs.forEach(articleDir => {
      let content = '# ' + fs.readFileSync(path.join(folderPath, articleDir, 'title.md'), 'utf8') + ' #\n';
      content += fs.readFileSync(path.join(folderPath, articleDir, '01.md'), 'utf8');
      const destinationPath = path.join(
        outputPath,
        project.path,
        articleDir + '.md'
      );
      fs.outputFileSync(destinationPath, content);
    });
  });
  return true;
}
