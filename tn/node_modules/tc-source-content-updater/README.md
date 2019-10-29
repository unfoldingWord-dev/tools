[![Build Status](https://api.travis-ci.org/translationCoreApps/tc-source-content-updater.svg?branch=master)](https://travis-ci.org/translationCoreApps/tc-source-content-updater) ![npm](https://img.shields.io/npm/dt/tc-source-content-updater.svg)

# tc-source-content-updater
Module that updates source content for the desktop application translationCore.

# Development

Use the separate helper files (as best you can) for each story.

Some functionality will most likely have to change in the main index as well, but try to keep as much logic as possible in individual helpers.

Parsers can expect the catalog to be fetched before their method is called. It will be under 
the **catalog** property of the Updater object

**Please try and cleary define your input and output parameter structures so to make collaboration easier**

`Check __tests__/fixtures/catalog.json
for example metadata return from DCS`

# Usage
To use this module you must first create a new instance of the object.
i.e.
```
//es6
import updater from 'tc-source-content-updater';
const Updater = new updater();

//commonjs
const updater = require('tc-source-content-updater').default;
const Updater = new updater();
```

Note: In order to limit the amount of API calls the door43 repo, the Updater object uses the same catalog resource throughout its lifetime, without having to continuosly do requests to door43 API on each function call.

## Workflow
1. Create instance
2. Fetch latest resources
3. Download the resources that are not updated

## Updater Object
**`getLatestResources(localResourceList)`**: 
- **description** -
Used to initiate a load of the latest resource so that the user can then select which ones
they would like to update.
Note: This function only returns the resources that are not up to date on the user machine
before the request
- @param {boolean} **localResourceList** - list of resources that are on the users local machine already
- @return {Promise} - Array of languages that have updates in catalog (returns null on error)

**`updateCatalog()`**:
- **description** - Method to manually fetch the latest catalog for the current
Updater instance. This function has no return value

**`downloadResources(resourceList)`**:
- **description** - Downloads the resources from the specified list using the DCS API
- @param {Array} **resourceList** - list of resources that you would like to download
- @return {Promise} Promise that resolves to success or rejects if a resource failed to download


**`parseBiblePackage(resourceEntry, extractedFilesPath, resultsPath)`**:
- **description** - Parses the bible package to generate json bible contents, manifest, and index
- @param {String} **extractedFilesPath** - path to unzipped files from bible package
- @param {String} **resultsPath** - path to store processed bible
- @return {Boolean} true if success
 
 
**`processTranslationAcademy(extractedFilesPath, outputPath)`**:
- **description** - Processes the extracted files for translationAcademy to create a single file for each article
- @param {String} **extractedFilesPath** - Path to the extracted files that came from the zip file in the catalog
- @param {String} **outputPath** - Path to place the processed files WITHOUT version in the path
- @return {String} The path to the processed translationAcademy files with version
 
 
 **`processTranslationWords(extractedFilesPath, outputPath)`**:
- **description** - Processes the extracted files for translationWord to cerate the folder structure and produce the index.js file for the language with the title of each article.
- @param {String} **extractedFilesPath** - Path to the extracted files that came from the zip file from the catalog
- @param {String} **outputPath** - Path to place the processed resource files WIHTOUT the version in the path
- @return {String} Path to the processed translationWords files with version

 **`generateTwGroupDataFromAlignedBible(biblePath, outputPath)`**:
- **description** - Generates the tW Group Data files from the given aligned Bible
- @param {string} **biblePath** Path to the Bible with aligned data
- @param {string} **outputPath** Path where the translationWords group data is to be placed WITHOUT version
- @return {string} Path where tW was generated with version
