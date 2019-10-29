/* eslint-disable camelcase */
import fs from 'fs-extra';
import path from 'path-extra';

/**
 * generate manifest.json
 * @param {Object} oldManifest - old manifest data
 * @param {String} RESOURCE_OUTPUT_PATH - folder to store manifest.json
 * @return {Object} new manifest data
 */
export function generateBibleManifest(oldManifest, RESOURCE_OUTPUT_PATH) {
  const newManifest = {};
  newManifest.dublin_core = oldManifest.dublin_core; // preserve original manifest data
  newManifest.checking = oldManifest.checking;
  newManifest.projects = oldManifest.projects;
  newManifest.original_manifest = oldManifest;

  // copy some data for more convenient access
  newManifest.language_id = oldManifest.dublin_core.language.identifier;
  newManifest.language_name = oldManifest.dublin_core.language.title;
  newManifest.direction = oldManifest.dublin_core.language.direction;
  newManifest.subject = oldManifest.dublin_core.subject;
  newManifest.resource_id = oldManifest.dublin_core.identifier;
  newManifest.resource_title = oldManifest.dublin_core.title;
  const oldMainfestIdentifier = oldManifest.dublin_core.identifier
                                      .toLowerCase();
  const identifiers = ['ugnt', 'ubh'];
  newManifest.description = identifiers.includes(oldMainfestIdentifier) ?
    'Original Language' : 'Gateway Language';

  let savePath = path.join(RESOURCE_OUTPUT_PATH, 'manifest.json');
  fs.writeFileSync(savePath, JSON.stringify(newManifest, null, 2));
  return newManifest;
}
