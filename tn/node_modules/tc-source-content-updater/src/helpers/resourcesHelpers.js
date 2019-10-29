/* eslint-disable no-console,max-len,camelcase */
import fs from 'fs-extra';
import path from 'path-extra';
import yaml from 'yamljs';
import {isObject} from 'util';
// helpers
import * as zipFileHelpers from './zipFileHelpers';
import * as twArticleHelpers from './translationHelps/twArticleHelpers';
import * as taArticleHelpers from './translationHelps/taArticleHelpers';
import * as twGroupDataHelpers from './translationHelps/twGroupDataHelpers';
import * as packageParseHelpers from './packageParseHelpers';
// constants
import * as errors from '../resources/errors';

const translationHelps = {
  ta: 'translationAcademy',
  tn: 'translationNotes',
  tw: 'translationWords',
  tq: 'translationQuestions'
};

/**
 * @description - Gets the version from the manifest
 * @param {String} resourcePath - folder for manifest.json or yaml
 * @return {String} version
 */
export function getVersionFromManifest(resourcePath) {
  const manifest = getResourceManifest(resourcePath);
  if (!manifest || !manifest.dublin_core || !manifest.dublin_core.version) {
    return null;
  }
  return manifest.dublin_core.version;
}

/**
 * @description Helper function to get manifest file from the resources folder. First
 * it will try manifest.json, then manifest.yaml.
 * @param {String} resourcePath - path to a resource folder which contains the manifest file in its root.
 * @return {Object} manifest
 */
export function getResourceManifest(resourcePath) {
  const manifest = getResourceManifestFromJson(resourcePath);
  if (!manifest) {
    return getResourceManifestFromYaml(resourcePath);
  }
  return manifest;
}

/**
 * @description - Turns a manifest.json file into an object and returns it, null if doesn't exist
 * @param {String} resourcePath - folder for manifest.json
 * @return {Object} manifest
 */
export function getResourceManifestFromJson(resourcePath) {
  const fileName = 'manifest.json';
  const manifestPath = path.join(resourcePath, fileName);
  let manifest = null;
  if (fs.existsSync(manifestPath)) {
    manifest = fs.readJsonSync(manifestPath);
  }
  return manifest;
}

/**
 * @description - Turns a manifest.yaml file into an object and returns it, null if doesn't exist
 * @param {String} resourcePath - folder for manifest.yaml
 * @return {Object} manifest
 */
export function getResourceManifestFromYaml(resourcePath) {
  const fileName = 'manifest.yaml';
  const manifestPath = path.join(resourcePath, fileName);
  let manifest = null;
  if (fs.existsSync(manifestPath)) {
    const yamlManifest = fs.readFileSync(manifestPath, 'utf8').replace(/^\uFEFF/, '');
    manifest = yaml.parse(yamlManifest);
  }
  return manifest;
}

/**
 * Returns an array of versions found in the path that start with [vV]\d
 * @param {String} resourcePath - base path to search for versions
 * @return {Array} - array of versions, e.g. ['v1', 'v10', 'v1.1']
 */
export function getVersionsInPath(resourcePath) {
  if (!resourcePath || !fs.pathExistsSync(resourcePath)) {
    return null;
  }
  const isVersionDirectory = name => {
    const fullPath = path.join(resourcePath, name);
    return fs.lstatSync(fullPath).isDirectory() && name.match(/^v\d/i);
  };
  return sortVersions(fs.readdirSync(resourcePath).filter(isVersionDirectory));
}

/**
 * Returns a sorted an array of versions so that numeric parts are properly ordered (e.g. v10a < v100)
 * @param {Array} versions - array of versions unsorted: ['v05.5.2', 'v5.5.1', 'V6.21.0', 'v4.22.0', 'v6.1.0', 'v6.1a.0', 'v5.1.0', 'V4.5.0']
 * @return {Array} - array of versions sorted:  ["V4.5.0", "v4.22.0", "v5.1.0", "v5.5.1", "v05.5.2", "v6.1.0", "v6.1a.0", "V6.21.0"]
 */
export function sortVersions(versions) {
  // Don't sort if null, empty or not an array
  if (!versions || !Array.isArray(versions)) {
    return versions;
  }
  // Only sort of all items are strings
  for (let i = 0; i < versions.length; ++i) {
    if (typeof versions[i] !== 'string') {
      return versions;
    }
  }
  versions.sort((a, b) => String(a).localeCompare(b, undefined, {numeric: true}));
  return versions;
}

/**
 * Return the full path to the highest version folder in resource path
 * @param {String} resourcePath - base path to search for versions
 * @return {String} - path to highest version
 */
export function getLatestVersionInPath(resourcePath) {
  const versions = sortVersions(getVersionsInPath(resourcePath));
  if (versions && versions.length) {
    return path.join(resourcePath, versions[versions.length - 1]);
  }
  return null; // return illegal path
}

/**
 * @description Unzips a resource's zip file to an imports directory for processing
 * @param {Object} resource Resource object containing resourceId and languageId
 * @param {String} zipFilePath Path to the zip file
 * @param {string} resourcesPath Path to the resources directory
 * @return {String} Path to the resource's import directory
 */
export const unzipResource = async (resource, zipFilePath, resourcesPath) => {
  const importsPath = path.join(resourcesPath, 'imports');
  fs.ensureDirSync(importsPath);
  const importPath = zipFilePath.split('.').slice(0, -1).join('.');
  await zipFileHelpers.extractZipFile(zipFilePath, importPath);
  return importPath;
};

/**
 * Gets the single subdirector of an extracted zip file path
 * @param {String} extractedFilesPath Extracted files path
 * @return {String} The subdir in the extracted path
 */
export function getSubdirOfUnzippedResource(extractedFilesPath) {
  const subdirs = fs.readdirSync(extractedFilesPath);
  if (subdirs.length === 1 && fs.lstatSync(path.join(extractedFilesPath, subdirs[0])).isDirectory()) {
    return path.join(extractedFilesPath, subdirs[0]);
  }
  return extractedFilesPath;
}

/**
 * @description Processes a resource in the imports directory as needed
 * @param {Object} resource Resource object
 * @param {String} sourcePath Path the the source dictory of the resource
 * @return {String} Path to the directory of the processed files
 */
export function processResource(resource, sourcePath) {
  if (!resource || !isObject(resource) || !resource.languageId || !resource.resourceId)
    throw Error(formatError(resource, errors.RESOURCE_NOT_GIVEN));
  if (!sourcePath)
    throw Error(formatError(resource, errors.SOURCE_PATH_NOT_GIVEN));
  if (!fs.pathExistsSync(sourcePath))
    throw Error(formatError(resource, errors.SOURCE_PATH_NOT_EXIST));
  const processedFilesPath = sourcePath + '_processed';
  fs.ensureDirSync(processedFilesPath);
  switch (resource.subject) {
    case 'Translation_Words':
      twArticleHelpers.processTranslationWords(resource, sourcePath, processedFilesPath);
      break;
    case 'Translation_Academy':
      taArticleHelpers.processTranslationAcademy(resource, sourcePath, processedFilesPath);
      break;
    case 'Bible':
    case 'Aligned_Bible':
    case 'Greek_New_Testament':
      packageParseHelpers.parseBiblePackage(resource, sourcePath, processedFilesPath);
      break;
    default:
      fs.copySync(sourcePath, processedFilesPath);
  }
  let manifest = getResourceManifest(sourcePath);
  if (!getResourceManifest(processedFilesPath) && manifest) {
    manifest.catalog_modified_time = resource.remoteModifiedTime;
    fs.writeFileSync(path.join(processedFilesPath, 'manifest.json'), JSON.stringify(manifest, null, 2));
  }
  return processedFilesPath;
}

/**
 * @description Gets the actual path to a resource based on the resource object
 * @param {Object} resource The resource object
 * @param {String} resourcesPath The path to the resources directory
 * @return {String} The resource path
 */
export function getActualResourcePath(resource, resourcesPath) {
  const languageId = resource.languageId;
  let resourceName = resource.resourceId;
  let type = 'bibles';
  if (translationHelps[resourceName]) {
    resourceName = translationHelps[resourceName];
    type = 'translationHelps';
  }
  const actualResourcePath = path.join(resourcesPath, languageId, type, resourceName, 'v' + resource.version);
  fs.ensureDirSync(actualResourcePath);
  return actualResourcePath;
}

/**
 * @description Downloads the resources that need to be updated for a given language using the DCS API
 * @param {Object.<{
 *             languageId: String,
 *             resourceId: String,
 *             localModifiedTime: String,
 *             remoteModifiedTime: String,
 *             downloadUrl: String,
 *             version: String,
 *             subject: String,
 *             catalogEntry: {langResource, bookResource, format}
 *           }>} resource - resource to download
 * @param {String} sourcePath Path to the Bible directory
 * @return {String} Path to the processed tw Group Data files
 */
export function makeTwGroupDataResource(resource, sourcePath) {
  if (!resource)
    throw Error(formatError(resource, errors.RESOURCE_NOT_GIVEN));
  if (!fs.pathExistsSync(sourcePath))
    throw Error(formatError(resource, errors.SOURCE_PATH_NOT_EXIST));
  if ((resource.languageId === 'grc' && resource.resourceId === 'ugnt') ||
      (resource.languageId === 'hbo' && resource.resourceId === 'uhb')) {
    const twGroupDataPath = path.join(sourcePath + '_tw_group_data_' + resource.languageId + '_v' + resource.version);
    const result = twGroupDataHelpers.generateTwGroupDataFromAlignedBible(resource, sourcePath, twGroupDataPath);
    if (result)
      return twGroupDataPath;
  }
}

/**
 * Removes all version directories except the latest
 * @param {String} resourcePath Path to the reosurce dirctory that has subdirs of versions
 * @return {Boolean} True if versions were deleted, false if nothing was touched
 */
export function removeAllButLatestVersion(resourcePath) {
  // Remove the previoius verison(s)
  const versionDirs = getVersionsInPath(resourcePath);
  if (versionDirs && versionDirs.length > 1) {
    const lastVersion = versionDirs[versionDirs.length - 1];
    versionDirs.forEach(versionDir => {
      if (versionDir !== lastVersion) {
        fs.removeSync(path.join(resourcePath, versionDir));
      }
    });
    return true;
  }
  return false;
}

/**
 * @description Formats an error for all resources to have a standard format
 * @param {Object} resource Resource object
 * @param {String} errMessage Error message
 * @return {String} The formatted error message
 */
export function formatError(resource, errMessage) {
  if (!resource || !isObject(resource) || !resource.languageId || !resource.resourceId) {
    resource = {
      languageId: 'unknown',
      resourceId: 'unknown'
    };
  }
  return resource.languageId + '_' + resource.resourceId + ': ' + errMessage;
}

/**
 *  converts error to string
 * @param {Error|String} error - error to append
 * @return {string} concatenated message
 */
export function getErrorMessage(error) {
  return ((error && error.message) || error || "UNDEFINED");
}

/**
 * appends error message to string
 * @param {string} str - string to use as prefix
 * @param {Error|String} err - error to append
 * @return {string} concatenated message
 */
export function appendError(str, err) {
  return str + ": " + getErrorMessage(err);
}
