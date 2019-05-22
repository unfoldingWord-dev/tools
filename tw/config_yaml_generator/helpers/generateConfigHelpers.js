const path = require('path-extra');
const fs = require('fs-extra');
const sourceContentUpdater = require('tc-source-content-updater').default;

const UGNT_VERSION = 'v0.4';

const generateConfig = async (outputPath) => {
  if (! fs.existsSync(outputPath)) {
    console.error('Directory does not exist: ' + outputPath);
    return false;
  }
  const config = {};
  const grcPath = path.join(outputPath, 'grc');
  let twPath = path.join(grcPath, 'translationHelps', 'translationWords', UGNT_VERSION);
  try {
    if (! fs.existsSync(twPath)) {
      const SourceContentUpdater = new sourceContentUpdater();
      await SourceContentUpdater.getLatestResources([]);
      const resources = await SourceContentUpdater.downloadResources(['grc'], outputPath);
      if (! resources.length) {
        console.error('Failed to download the UGNT');
        return false;
      }
      const resource = resources.filter(resource=>resource.languageId=='grc'&&resource.resourceId=='ugnt')[0];
      twPath = path.join(outputPath, resource.languageId, 'translationHelps', 'translationWords', 'v' + resource.version);
      if (! fs.existsSync(twPath)) {
        console.error('tw Group Data not found at ' + twPath);
        return false;
      }
    }
    const types = fs.readdirSync(twPath).filter(name => fs.lstatSync(path.join(twPath, name)).isDirectory());
    types.forEach(type => {
      typePath = path.join(twPath, type, 'groups');
      const books = fs.readdirSync(typePath).filter(name => fs.lstatSync(path.join(typePath, name)).isDirectory());
      books.forEach(book => {
        const bookPath = path.join(typePath, book);
        const articles = fs.readdirSync(bookPath).filter(articleFile => path.extname(articleFile)=='.json');
        articles.forEach(articleFile => {
          const article = articleFile.split('.').slice(0, -1).join('.');
          if (! config[article]) {
            config[article] = {
              false_positives: [],
              occurrences: []
            }
          }
          const articleContent = fs.readJsonSync(path.join(bookPath, articleFile));
          articleContent.forEach(occurrence => {
            const ref = occurrence.contextId.reference;
            const chapter = (ref.chapter < 10 ? '0' + ref.chapter : ref.chapter);
            const verse = (ref.verse < 10 ? '0' + ref.verse : ref.verse);
            config[article].occurrences.push('rc://*/*/book/' + book + '/' + chapter + '/' + verse);
          });
        });
      });
    });
    const configPath = path.join(outputPath, 'config.yaml');
    fs.writeFileSync(configPath, convertToYaml(config));
    fs.removeSync(grcPath); // Comment this out if you're debugging so the UGNT isn't downloaded every time
    console.log('Done. ' + configPath + ' created.');
  } catch(err) {
    console.error(err);
  }
};

function convertToYaml(config) {
  let yaml = "---\n";
  Object.keys(config).sort().forEach(article => {
    yaml += article + ":\n  false_positives: []\n  occurrences:\n";
    config[article].occurrences.sort().forEach(rc => {
      yaml += "  - " + rc + "\n";
    });
  });
  return yaml;
}

module.exports = {
  generateConfig
};