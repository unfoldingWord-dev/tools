/* eslint-disable camelcase,no-empty,no-negated-condition */
import * as ERROR from '../resources/errors';

export const TC_RESOURCES = ['Bible', 'Aligned_Bible', 'Greek_New_Testament', 'Translator_Notes', 'Bible_translation_comprehension_questions', 'Translation_Words', 'Translation_Academy'];
export const RESOURCE_ID_MAP = {
  translationWords: 'tw',
  translationNotes: 'tn',
  translationAcademy: 'ta'
};

/**
 * get all resources to update for language
 * @param {Array.<{
 *                   languageId: String,
 *                   resourceId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String,
 *                   downloadUrl: String,
 *                   version: String,
 *                   subject: String,
 *                   catalogEntry: {langResource, bookResource, format}
 *                 }>} resources - resources to filter
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
 *                 }>|null} - filtered resources for language (returns null on error)
 */
export function getResourcesForLanguage(resources, languageId) {
  if (!Array.isArray(resources)) {
    return null;
  }
  return resources.filter(resource =>
    (resource.languageId === languageId));
}

/**
 * extract list of languages that need to be updated from resources
 *  that need to be updated
 *
 * @param {Array.<{
 *                   languageId: String,
 *                   resourceId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String,
 *                   downloadUrl: String,
 *                   version: String,
 *                   subject: String,
 *                   catalogEntry: {langResource, bookResource, format}
 *                 }>} updatedRemoteResources - resources that have been updated in remote catalog
 * @return {
 *          Array.<{
 *                   languageId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String
 *                 }>
 *         }|null} - list of languages that have updates in catalog (returns null on error)
 */
export function getUpdatedLanguageList(updatedRemoteResources) {
  if (!Array.isArray(updatedRemoteResources)) {
    return null;
  }
  const updatedLanguages = [];
  for (let resource of updatedRemoteResources) {
    const languageId = resource.languageId;
    const updatedBible = {
      languageId,
      localModifiedTime: resource.localModifiedTime || '',
      remoteModifiedTime: resource.remoteModifiedTime
    };
    const dup = updatedLanguages.findIndex(item =>
      (item.languageId === languageId)
    );
    if (dup < 0) {
      updatedLanguages.push(updatedBible); // add if language not present
    }
  }
  return updatedLanguages.sort((a, b) =>
    ((a.languageId > b.languageId) ? 1 : -1));
}

/**
 * Gets the list of all new resources in remoteCatalog, except for
 * the ones already up to date in the given list
 *
 * @param {{subjects: Array.<Object>}} catalog - to parse
 * @param {Array.<{
 *                  languageId: String,
 *                  resourceId: String,
 *                  modifiedTime: String,
 *                  }>} localResourceList - list of resources that are on the users local machine already {}
 * @return {Array.<{
 *                   languageId: String,
 *                   resourceId: String,
 *                   localModifiedTime: String,
 *                   remoteModifiedTime: String,
 *                   downloadUrl: String,
 *                   version: String,
 *                   subject: String,
 *                   catalogEntry: {subject, resource, format}
 *                 }>} updated resources  (throws exception on error)
 */
export function getLatestResources(catalog, localResourceList) {
  if (!catalog || !Array.isArray(localResourceList)) {
    throw new Error(ERROR.PARAMETER_ERROR);
  }
  const tCoreResources = parseCatalogResources(catalog, true, TC_RESOURCES);
  // remove resources that are already up to date
  for (let localResource of localResourceList) {
    let resourceId = localResource.resourceId;
    if (localResource.languageId && resourceId) {
      resourceId = RESOURCE_ID_MAP[resourceId] || resourceId; // map resource names to ids
      const index = tCoreResources.findIndex(remoteResource =>
        ((localResource.languageId === remoteResource.languageId) &&
          (remoteResource.resourceId === resourceId)));
      if (index >= 0) {
        const catalogResource = tCoreResources[index];
        const isNewer = !localResource.modifiedTime ||
          (catalogResource.remoteModifiedTime > localResource.modifiedTime);
        if (!isNewer) { // if resource up to date, remove it from resource list
          tCoreResources.splice(index, 1);
        } else {
          catalogResource.localModifiedTime = localResource.modifiedTime;
        }
      }
    }
  }
  return tCoreResources.sort((a, b) =>
    ((a.languageId > b.languageId) ? 1 : -1)); // resources that are already up to date have been removed, sort by language
}

/**
 * if Array is not valid, return empty array
 * @param {Array} array - array to validate
 * @return {Array} array if valid, or empty array
 */
export function getValidArray(array) {
  if (Array.isArray(array)) {
    return array;
  }
  return [];
}

/**
 * gets an array of the formats.  Most are in resources.formats, but tWords are in resources.projects.formats
 * @param {Object} resource object
 * @return {Array} array if valid, or empty array
 */
export function getFormatsForResource(resource) {
  if (Array.isArray(resource.formats)) {
    return resource.formats;
  }

  if (Array.isArray(resource.projects)) {
    const formats = [];
    for (let project of resource.projects) {
      const projectFormats = getFormatsForResource(project);
      formats.push(...projectFormats);
    }
    return formats;
  }

  return [];
}

/**
 * parses the remoteCatalog and returns list of catalog resources
 *
 * @param {{subjects: Array.<Object>}} catalog - to parse
 * @param {boolean} ignoreObsResources - if true then reject obs resources
 * @param {Array.<String>} subjectFilters - optional array of subjects to include.  If null then every subject is returned
 * @return {Array.<{
 *                   languageId: String,
 *                   resourceId: String,
 *                   remoteModifiedTime: String,
 *                   downloadUrl: String,
 *                   version: String,
 *                   subject: String,
 *                   catalogEntry: {subject, resource, format}
 *                 }>|null} list of updated resources (returns null on error)
 */
export function parseCatalogResources(catalog, ignoreObsResources = true, subjectFilters = null) {
  if (!catalog || !Array.isArray(catalog.subjects)) {
    throw new Error(ERROR.CATALOG_CONTENT_ERROR);
  }
  const catalogResources = [];
  if (catalog && catalog.subjects) {
    for (let catSubject of catalog.subjects) {
      const subject = catSubject.identifier;
      const isGreekOL = (catSubject.language === "el-x-koine");
      const languageId = isGreekOL ? 'grc' : catSubject.language; // we use grc internally for Greek Original language
      const resources = getValidArray(catSubject.resources);
      for (let resource of resources) {
        const isCheckingLevel2 = resource.checking.checking_level >= 2;
        const resourceId = resource.identifier;
        if (ignoreObsResources && (resourceId.indexOf('obs') >= 0)) { // see if we should skip obs resources
          continue;
        }
        const version = resource.version;
        const formats = getFormatsForResource(resource);
        for (let format of formats) {
          try {
            const isZipFormat = format.format.indexOf("application/zip;") >= 0;
            const downloadUrl = format.url;
            const remoteModifiedTime = format.modified;
            const isDesiredSubject = !subjectFilters ||
              subjectFilters.includes(subject);
            if (isDesiredSubject && isZipFormat && isCheckingLevel2 &&
              downloadUrl && remoteModifiedTime && languageId && version) {
              const foundResource = {
                languageId,
                resourceId,
                remoteModifiedTime,
                downloadUrl,
                version,
                subject,
                catalogEntry: {
                  subject: catSubject,
                  resource,
                  format
                }
              };
              catalogResources.push(foundResource);
            }
          } catch (e) {
            // recover if required fields are missing
          }
        }
      }
    }
  }
  return catalogResources;
}

/**
 * Formats the given content in an importable form for tC
 * @param {Object} content - The unparsed content from DCS
 */
export function formatResources(content) {
  //
}
