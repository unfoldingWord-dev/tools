require("babel-polyfill"); // required for async/await
const path = require('path-extra');
const fs = require('fs-extra');
const sourceContentUpdater = require('tc-source-content-updater').default;

const getReources = async (outputPath) => {
  if (! fs.existsSync(outputPath)) {
    console.error('Directory does not exist: ' + outputPath);
    return false;
  }
  const grcPath = path.join(outputPath, 'grc');
  const SourceContentUpdater = new sourceContentUpdater();
  await SourceContentUpdater.getLatestResources([]);
  const resources = await SourceContentUpdater.downloadResources(['el-x-koine', 'en', 'kn', 'hbo'], outputPath);
  if (! resources.length) {
    console.error('Failed to download resources');
    return false;
  }
  return true;
};

// run as main
if(require.main === module) {
  if (process.argv.length < 3) {
    console.error('Syntax: node getResources.js [outputPath]');
    return 1;
  }
  const outputPath = process.argv[2];
  if (! fs.existsSync(outputPath)) {
    console.error('Directory does not exist: ' + outputPath);
    return 1;
  }
  getReources(outputPath);
}
