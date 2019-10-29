import fs from 'fs-extra';
import path from 'path';

/**
 * @description transfer an entire resource from source to target directory
 * @param {string} resourceSourcePath - current position of resource
 * @param {string} resourceTargetPath - folder where resources are moved
 * @return {Promse} Move directory Promise
 */
export function moveResources(resourceSourcePath, resourceTargetPath) {
  return new Promise((resolve, reject) => {
    if (resourceSourcePath && resourceSourcePath.length &&
      resourceTargetPath && resourceTargetPath.length) {
      if (fs.pathExistsSync(resourceTargetPath)) {
        fs.removeSync(resourceTargetPath);
      }
      fs.ensureDirSync(path.dirname(resourceTargetPath));
      fs.copySync(resourceSourcePath, resourceTargetPath);
      fs.removeSync(resourceSourcePath);
      resolve(resourceTargetPath);
    } else {
      reject('Invalid parameters to moveResources()');
    }
  });
}

