import fs from 'fs-extra';
import path from 'path-extra';
import * as bible from '../../resources/bible';
import {isObject} from 'util';
// helpers
import * as resourcesHelpers from '../resourcesHelpers';
// constants
import * as errors from '../../resources/errors';

/**
 * @description Generates the tW Group Data files from the given aligned Bible
 * @param {Objecd} resource Resource object
 * @param {String} sourcePath Path to the Bible with aligned data
 * @param {String} outputPath Path where the translationWords group data is to be placed WITHOUT version
 * @return {Boolean} true if success
 */
export const generateTwGroupDataFromAlignedBible = (resource, sourcePath, outputPath) => {
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
  const version = resourcesHelpers.getVersionFromManifest(sourcePath);
  if (!version) {
    return false;
  }
  let books = bible.BIBLE_LIST_NT.slice(0);
  books.forEach(bookName => {
    convertBookVerseObjectsToTwData(sourcePath, outputPath, bookName);
  });
  return true;
};

/**
 * @description Gets verseObjects of a book and converts to a tW data object to save to file
 * @param {String} sourcePath Usually path to the UGNT
 * @param {String} outputPath The output path for tW files
 * @param {String} bookName Book in format, e.g. '41-MAT'
 */
function convertBookVerseObjectsToTwData(sourcePath, outputPath, bookName) {
  const bookId = getbookId(bookName);
  let twData = {};
  const bookDir = path.join(sourcePath, bookId);
  if (fs.existsSync(bookDir)) {
    const chapters = Object.keys(bible.BOOK_CHAPTER_VERSES[bookId]).length;
    for (let chapter = 1; chapter <= chapters; chapter++) {
      const chapterFile = path.join(bookDir, chapter + '.json');
      if (fs.existsSync(chapterFile)) {
        const json = JSON.parse(fs.readFileSync(chapterFile));
        for (let verse in json) {
          let groupData = [];
          json[verse].verseObjects.forEach(verseObject => {
            populateGroupDataFromVerseObject(groupData, verseObject);
          });
          populateTwDataFromGroupData(twData, groupData, bookId, chapter, verse);
        }
      }
    }
    for (let category in twData) {
      for (let groupId in twData[category]) {
        let groupPath = path.join(outputPath, category, 'groups', bookId, groupId + '.json');
        fs.outputFileSync(groupPath, JSON.stringify(twData[category][groupId], null, 2));
      }
    }
  }
}

/**
 * @description Populates the groupData array with this verseObject and returns its own groupData for milestones
 * @param {Object} groupData Group Data object
 * @param {Object} verseObject Verse object
 * @param {Boolean} isMilestone If true, all word objects will be added to the group data
 * @return {Object} Returns group data for this verse object
 */
function populateGroupDataFromVerseObject(groupData, verseObject, isMilestone = false) {
  var myGroupData = {
    quote: [],
    strong: []
  };
  if (verseObject.type === 'milestone' || (verseObject.type === 'word' && (verseObject.tw || isMilestone))) {
    if (verseObject.type === 'milestone') {
      if (verseObject.text) {
        myGroupData.text.push(verseObject.text);
      }
      verseObject.children.forEach(childVerseObject => {
        let childGroupData = populateGroupDataFromVerseObject(groupData, childVerseObject, true);
        if (childGroupData) {
          myGroupData.quote = myGroupData.quote.concat(childGroupData.quote);
          myGroupData.strong = myGroupData.strong.concat(childGroupData.strong);
        }
      });
    } else if (verseObject.type === 'word') {
      myGroupData.quote.push(verseObject.text);
      myGroupData.strong.push(verseObject.strong);
    }
    if (myGroupData.quote.length) {
      if (verseObject.tw) {
        const twLinkItems = verseObject.tw.split('/');
        const groupId = twLinkItems.pop();
        const category = twLinkItems.pop();
        if (!groupData[category]) {
          groupData[category] = {};
        }
        if (!groupData[category][groupId]) {
          groupData[category][groupId] = [];
        }
        groupData[category][groupId].push({
          quote: myGroupData.quote.join(' '),
          strong: myGroupData.strong
        });
      }
    }
  }
  return myGroupData;
}

/**
 * @description Takes what is in the groupData array and populates the tWData
 * @param {Object} twData Data to be collected for tw
 * @param {Object} groupData Group data object
 * @param {String} bookId Three character code for the book
 * @param {int} chapter Number of the chapter
 * @param {int} verse Number of the verse
 */
function populateTwDataFromGroupData(twData, groupData, bookId, chapter, verse) {
  for (let category in groupData) {
    if (!twData[category]) {
      twData[category] = [];
    }
    for (let groupId in groupData[category]) {
      if (!twData[category][groupId]) {
        twData[category][groupId] = [];
      }
      let occurrences = {};
      groupData[category][groupId].forEach(item => {
        if (!occurrences[item.quote]) {
          occurrences[item.quote] = 1;
        }
        twData[category][groupId].push({
          priority: 1,
          comments: false,
          reminders: false,
          selections: false,
          verseEdits: false,
          contextId: {
            reference: {
              bookId: bookId,
              chapter: chapter,
              verse: parseInt(verse)
            },
            tool: 'translationWords',
            groupId: groupId,
            quote: item.quote,
            strong: item.strong,
            occurrence: occurrences[item.quote]++
          }
        });
      });
    }
  }
}

/**
 * @description Splits book code out of book name, for example 'mat' from '41-MAT'
 * @param {String} bookName Book in format '41-MAT'
 * @return {String} The book ID, e.g. 'mat'
 */
function getbookId(bookName) {
  return bookName.split('-')[1].toLowerCase();
}
