import nock from 'nock';

jest.mock('../src/helpers/downloadHelpers');
jest.mock('../src/helpers/zipFileHelpers');

const catalog = require('../__tests__/fixtures/api.door43.org/v3/subjects/pivoted.json');
nock('https://api.door43.org:443')
  .persist()
  .get('/v3/subjects/pivoted.json')
  .reply(200, JSON.stringify(catalog));
