import url from 'url';
import {https, http} from 'follow-redirects';
import fs from 'fs-extra';
import rimraf from 'rimraf';
const HttpAgent = require('agentkeepalive');
const HttpsAgent = require('agentkeepalive').HttpsAgent;

let httpAgent = new HttpAgent();
let httpsAgent = new HttpsAgent();

/**
 * @description Reads the contents of a url as a string.
 * @param {String} uri the url to read
 * @return {Promise.<string>} the url contents
 */
export function read(uri) {
  let parsedUrl = url.parse(uri, false, true);
  let makeRequest = parsedUrl.protocol === 'https:' ? https.request.bind(https) : http.request.bind(http);
  let serverPort = parsedUrl.port ? parsedUrl.port : parsedUrl.protocol === 'https:' ? 443 : 80;
  let agent = parsedUrl.protocol === 'https:' ? httpsAgent : httpAgent;

  let options = {
    host: parsedUrl.host,
    path: parsedUrl.path,
    agent: agent,
    port: serverPort,
    method: 'GET',
    headers: {'Content-Type': 'application/json'}
  };

  return new Promise((resolve, reject) => {
    let req = makeRequest(options, response => {
      let data = '';
      response.on('data', chunk => {
        data += chunk;
      });
      response.on('end', () => {
        resolve({
          status: response.statusCode,
          data: data
        });
      });
    });

    req.on('socket', socket => {
      socket.setTimeout(30000);
    });
    req.on('error', reject);
    req.end();
  });
}

/**
 * @description Downloads a url to a file.
 * @param {String} uri the uri to download
 * @param {String} dest the file to download the uri to
 * @param {Function} progressCallback receives progress updates
 * @return {Promise.<{}|Error>} the status code or an error
 */
export function download(uri, dest, progressCallback) {
  progressCallback = progressCallback || function() {};
  let parsedUrl = url.parse(uri, false, true);
  let makeRequest = parsedUrl.protocol === 'https:' ? https.request.bind(https) : http.request.bind(http);
  let serverPort = parsedUrl.port ? parsedUrl.port : parsedUrl.protocol === 'https:' ? 443 : 80;
  let agent = parsedUrl.protocol === 'https:' ? httpsAgent : httpAgent;
  let file = fs.createWriteStream(dest);

  let options = {
    host: parsedUrl.host,
    path: parsedUrl.path,
    agent: agent,
    port: serverPort,
    method: 'GET'
  };

  return new Promise((resolve, reject) => {
    let req = makeRequest(options, response => {
      let size = response.headers['content-length'];
      let progress = 0;

      response.on('data', chunk => {
        progress += chunk.length;
        progressCallback(size, progress);
      });

      response.pipe(file);
      file.on('finish', () => {
        resolve({
          uri,
          dest,
          status: response.statusCode
        });
      });
    });

    req.on('error', error => {
      file.end();
      rimraf.sync(dest);
      reject(error);
    });

    req.end();
  });
}
