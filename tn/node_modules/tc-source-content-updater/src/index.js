import path from 'path';
import ospath from 'ospath';
// helpers
import * as apiHelpers from './helpers/apiHelpers';
import * as parseHelpers from './helpers/parseHelpers';
import * as moveResourcesHelpers from './helpers/moveResourcesHelpers';
import * as packageParseHelpers from "./helpers/packageParseHelpers";
import * as taArticleHelpers from "./helpers/translationHelps/taArticleHelpers";
import * as twArticleHelpers from "./helpers/translationHelps/twArticleHelpers";
import * as twGroupDataHelpers from "./helpers/translationHelps/twGroupDataHelpers";
import * as resourcesDownloadHelpers from "./helpers/resourcesDownloadHelpers";

/**
 * Updater constructor
 */
function Updater() {
  this.remoteCatalog = null;
  this.updatedCatalogResources = null;
}

Updater.prototype = {};

/**
 * Method to manually fetch the latest remoteCatalog for the current
 * Updater instance. This function has no return value
 */
Updater.prototype.updateCatalog = async function() {
  this.remoteCatalog = await apiHelpers.getCatalog();
};

/**
 * Used to initiate a load of the latest resource so that the user can then select which ones
 * they would like to update.
 * Note: This function only returns the resources that are not up to date on the user machine
 * before the request
 * @param {Array.<{
 *                  languageId: String,
 *                  resourceId: String,
 *                  modifiedTime: String,
 *                  }>} localResourceList - list of resources that are on the users local machine already {}
 * @return {
 *          Array.<{
 *                   languageId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String
 *                 }>
 *         }} - list of languages that have updates in catalog (throws exception on error)
 */
Updater.prototype.getLatestResources = async function(localResourceList) {
  await this.updateCatalog();
  this.updatedCatalogResources = parseHelpers.getLatestResources(this.remoteCatalog, localResourceList);
  return parseHelpers.getUpdatedLanguageList(this.updatedCatalogResources);
};

/**
 * get all resources to update for language
 * @param {String} languageId - language to search for
 * @return {Array.<{
 *                   languageId: String,
 *                   resourceId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String,
 *                   downloadUrl: String,
 *                   version: String,
 *                   subject: String,
 *                   catalogEntry: {langResource, bookResource, format}
 *                 }>} - all updated resources for language
 */
export function getResourcesForLanguage(languageId) {
  return parseHelpers.getResourcesForLanguage(this.updatedCatalogResources,
    languageId);
}

/**
 * @description Downloads the resources that need to be updated for the given languages using the DCS API
 * @param {Array.<String>} languageList - Array of language codes to download the resources fsor
 * @param {String} resourcesPath - Path to the resources directory where each resource will be placed
 * @param {Array.<Object>} resources - Array of resources that are newer than previously downloaded resources;
 * defaults to this.updatedCatalogResources which was set by previously calling getLatestResources();
 * If getLatestResources() was never called or resources = null, function will get all resources for the given language(s)
 * (the latter is useful for getting all resources for a set of languages, such as including all resources of
 * 'en' and 'hi' in a build)
 * @return {Promise} Promise that resolves to return all the resources updated or rejects if a resource failed to download
 */
Updater.prototype.downloadResources = async function(languageList, resourcesPath, resources = this.updatedCatalogResources) {
  // call this.getResourcesForLanguage(lang) for each language in list to get all resources to update
  if (!resources) {
    await this.getLatestResources([]);
    resources = this.updatedCatalogResources;
  }
  return resourcesDownloadHelpers.downloadResources(languageList, resourcesPath, resources);
};

/**
 * @description move the converted resource to user's resource folder
 * @param {String} resourceSourcePath - Location of selected downloaded resources
 * @param {String} languageCode - language of resource like en or hi
 * @return {Promise} Promise to move directory
 */
Updater.prototype.moveResources = async function(resourceSourcePath, languageCode) {
  const resourceTargetPath = path.join(
    ospath.home(), 'translationCore', 'resources', languageCode);
  return moveResourcesHelpers.move(resourceSourcePath, resourceTargetPath);
};

/**
 * @description Parses the bible package to generate json bible contents, manifest, and index
 * @param {{
 *          languageId: String,
 *          resourceId: String,
 *          localModifiedTime: String,
 *          remoteModifiedTime: String,
 *          downloadUrl: String,
 *          version: String,
 *          subject: String,
 *          catalogEntry: {langResource, bookResource, format}
 *        }} resourceEntry - resource entry for download
 * @param {String} extractedFilesPath - path to unzipped files from bible package
 * @param {String} resultsPath - path to store processed bible
 * @return {Boolean} true if success
 */
Updater.prototype.parseBiblePackage = function(resourceEntry, extractedFilesPath, resultsPath) {
  return packageParseHelpers.parseBiblePackage(resourceEntry, extractedFilesPath, resultsPath);
};

/**
 * @description Processes the extracted files for translationAcademy to create a single file for each
 * article
 * @param {String} extractedFilesPath - Path to the extracted files that came from the zip file in the catalog
 * @param {String} outputPath - Path to place the processed files WITHOUT version in the path
 * @return {String} The path to the processed translationAcademy files with version
 */
Updater.prototype.processTranslationAcademy = function(extractedFilesPath, outputPath) {
  return taArticleHelpers.processTranslationAcademy(extractedFilesPath, outputPath);
};

/**
 * @description Processes the extracted files for translationWord to cerate the folder
 * structure and produce the index.js file for the language with the title of each article.
 * @param {String} extractedFilesPath - Path to the extracted files that came from the zip file from the catalog
 * @param {String} outputPath - Path to place the processed resource files WIHTOUT the version in the path
 * @return {String} Path to the processed translationWords files with version
 */
Updater.prototype.processTranslationWords = function(extractedFilesPath, outputPath) {
  return twArticleHelpers.processTranslationWords(extractedFilesPath, outputPath);
};

/**
 * @description Generates the tW Group Data files from the given aligned Bible
 * @param {string} biblePath Path to the Bible with aligned data
 * @param {string} outputPath Path where the translationWords group data is to be placed WITHOUT version
 * @return {string} Path where tW was generated with version
 */
Updater.prototype.generateTwGroupDataFromAlignedBible = function(biblePath, outputPath) {
  return twGroupDataHelpers.generateTwGroupDataFromAlignedBible(biblePath, outputPath);
};

export default Updater;
