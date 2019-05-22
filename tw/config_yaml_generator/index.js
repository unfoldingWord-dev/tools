/**
 * This script updates the resources in a given directory for the given languages
 * Syntax: node scripts/resources/updateResources.js <path to resources> <language> [language...]
 */
require("babel-polyfill"); // required for async/await
const fs = require('fs-extra');
const generateConfigHelpers = require('./helpers/generateConfigHelpers');

// run as main
if(require.main === module) {
  if (process.argv.length < 3) {
    console.error('Syntax: node index.js <dir to place config.yaml>');
    return 1;
  }
  const outputPath = process.argv[2];
  if (! fs.existsSync(outputPath)) {
    console.error('Directory does not exist: ' + outputPath);
    return 1;
  }
  generateConfigHelpers.generateConfig(outputPath);
}
