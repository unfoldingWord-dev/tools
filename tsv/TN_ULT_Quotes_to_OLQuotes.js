const Axios = require("axios");
const YAML = require('js-yaml-parser');
const xre = require('xregexp');
const deepcopy = require('deepcopy');

const { readTsv } = require('uw-proskomma/src/utils/tsv');
const { rejigAlignment } = require('uw-proskomma/src/utils/rejig_alignment');
// const { doAlignmentQuery } = require('uw-proskomma/src/utils/query');
const { slimSourceTokens } = require('uw-proskomma/src/utils/tokens');
const { UWProskomma } = require('uw-proskomma/src/index');

// Adapted from TN_TSV7_OLQuotes_to_ULT_GLQuotes.js by RJH Sept 2021
//  and using some of that code
// const { getDocuments } = require('./TN_TSV7_OLQuotes_to_ULT_GLQuotes');


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/download.js May 2021
// Changed to accept testament as a parameter, and to only load the correct repo -- UHB or UGNT
// Removed UST preloading
// Called from main
const getDocuments = async (pk, testament, book, verbose, serialize) => {
    const baseURLs = [testament === 'OT' ?
        ["unfoldingWord", "hbo", "uhb", "https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master"] :
        ["unfoldingWord", "grc", "ugnt", "https://git.door43.org/unfoldingWord/el-x-koine_ugnt/raw/branch/master"],
    ["unfoldingWord", "en", "ult", "https://git.door43.org/unfoldingWord/en_ult/raw/branch/master"]
    ];
    verbose = verbose || false;
    serialize = serialize || false;
    if (verbose) console.log("Download USFM");
    for (const [org, lang, abbr, baseURL] of baseURLs) {
        const selectors = {
            org,
            lang,
            abbr
        };
        if (verbose) console.log(`  ${org}/${lang}/${abbr}`)
        let content = [];
        await Axios.request(
            { method: "get", "url": `${baseURL}/manifest.yaml` }
        )
            .then(
                async response => {
                    const manifest = YAML.safeLoad(response.data);
                    const bookPaths = manifest.projects.map(e => e.path.split("/")[1]);
                    for (const bookPath of bookPaths) {
                        const pathBook = bookPath.split(".")[0].split('-')[1];
                        if (book && (pathBook !== book)) {
                            continue;
                        }
                        if (verbose) console.log(`    ${pathBook}`)
                        try {
                            await Axios.request(
                                { method: "get", "url": `${baseURL}/${bookPath}` }
                            )
                                .then(response => {
                                    if (response.status !== 200) {
                                        throw new Error("Bad download status");
                                    }
                                    content.push(response.data);
                                })
                        } catch (err) {
                            if (verbose) console.log(`Could not load ${bookPath} for ${lang}/${abbr}`);
                        }
                    }
                }
            );
        if (content.length === 0) {
            if (verbose) console.log(`      Book ${book} not found`);
            continue;
        }
        if (verbose) console.log(`      Downloaded ${book} ${content.length.toLocaleString()} bytes`)

        const startTime = Date.now();
        if (abbr === 'ult') { // Preprocess x-occurrence,x-occurrences,x-content into x-align="content:occurrence:occurrences" for easier handling later
            // console.log(`content1: ${typeof content} (${content.length}) ${Object.keys(content)}`);
            content = [rejigAlignment(content)]; // Tidy-up ULT USFM alignment info
            // console.log(`content2: ${typeof content} (${content.length}) ${content}`);
        }
        pk.importDocuments(selectors, "usfm", content, {});
        if (verbose) console.log(`      Imported in ${Date.now() - startTime} msec`);
        if (serialize) {
            // console.log(`Serializing ${abbr} ${book}…`);
            const path = require("path");
            const fse = require('fs-extra');
            const outDir = path.resolve(__dirname, '..', '..', 'serialized');
            // console.log(`  outDir=${outDir}`);
            fse.mkdirs(outDir);
            const outPath = path.join(
                outDir,
                Object.values(selectors).join('_') + `_pkserialized.${book}.json`, // RJH added the USFM book code
            );
            // console.log(`  outPath=${outPath}`);
            fse.writeFileSync(
                outPath,
                JSON.stringify(pk.serializeSuccinct(`${org}/${lang}_${abbr}`), null, 2) // RJH added indenting just for interest
            );
        }
    }
    return pk;
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/query.js May 2021
// Called from main
const doAlignmentQuery = async pk => {
    const query = ('{' +
        'docSets {' +
        '  abbr: selector(id:"abbr")' +
        '  documents {' +
        '    book: header(id:"bookCode")' +
        '    mainSequence {' +
        '      itemGroups (' +
        '        byScopes:["chapter/", "verses/"]' +
        '        includeContext:true' +
        '      ) {' +
        '        scopeLabels' +
        '        tokens {' +
        '          subType' +
        '          payload' +
        '          position' +
        '          scopes(startsWith:"attribute/milestone/zaln/x-align")' + // This line was changed (and assumes preprocessing of alignment info)
        '        }' +
        '      }' +
        '    }' +
        '  }' +
        '}' +
        '}');
    const result = await pk.gqlQuery(query);
    if (result.errors) {
        throw new Error(result.errors);
    }
    const ret = {};
    for (const docSet of result.data.docSets) {
        ret[docSet.abbr] = {};
        for (const document of docSet.documents) {
            ret[docSet.abbr][document.book] = {};
            for (const itemGroup of document.mainSequence.itemGroups) {
                const chapter = itemGroup.scopeLabels.filter(s => s.startsWith("chapter/"))[0].split("/")[1];
                for (const verse of itemGroup.scopeLabels.filter(s => s.startsWith("verses/"))[0].split("/")[1].split("-")) {
                    const cv = `${chapter}:${verse}`;
                    ret[docSet.abbr][document.book][cv] = itemGroup.tokens;
                }
            }
        }
    }
    return ret;
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js May 2021
// Called from origLFromGLQuote()
/**
 *
 * @param {string} ULTSearchString -- the string of ULT words being searched for (may include ellipsis)
 * @param {Array} ULTTokens -- ULT token objects with two fields: payload = ULT word; scopes = info about aligned OrigL word(s)
 * @returns a list of 3-tuples with (ULTWord, flag if ULTWord follows an ellipsis, scopes array)
 */
const searchULTWordRecords = (ULTSearchString, ULTTokens) => {
    // console.log(`searchULTWordRecords('${ULTSearchString}', (${ULTTokens.length}), ${JSON.stringify(ULTTokens)})…`);

    // Break the search string into a list of words, and determine if they're contiguous (why do we even need that?)
    const ret = [];
    for (let searchExpr of xre.split(ULTSearchString, /[-\s־]/)) { // includes hyphen (beautiful-looking and maqaf)
        // console.log(`    searchULTWordRecords processing searchExpr='${searchExpr}'`);
        // The ULT "sourceTokens" have all punctuation (incl. word punctuation) as separate tokens!
        // So remove sentence punctuation (incl. all apostrophes!) from our individual search words
        // Added 'all' scope flag below to handle words with multiple punctuation marks to be removed, e.g. "(word),"
        searchExpr = xre.replace(searchExpr, /[“‘(),”’?:;.!]/, '', 'all'); // Added colon and parentheses
        if (searchExpr.includes("…")) {
            const searchExprParts = searchExpr.split("…");
            ret.push([searchExprParts[0], false]);
            searchExprParts.slice(1).forEach(p => ret.push([p, true]));
        } else {
            ret.push([searchExpr, false]);
        }
    }
    const intermediateSearchList = ret.filter(t => t[0] !== "׀"); // why is this needed -- ah for \w fields maybe -- still not really sure ???
    // console.log(`  searchULTWordRecords intermediateSearchList=${intermediateSearchList}`);
    // Now intermediateSearchList is a list of two-tuples being search word, and ellipsis flag

    // Now match the search words against the ULT tokens and get the alignment information (scopes field)
    function getFirstWordIndex(searchWord, ULTTokenList, startAt) {
        while (startAt < ULTTokenList.length) {
            if (ULTTokenList[startAt].payload === searchWord)
                return startAt;
            ++startAt;
        }
        return -1;
    }
    let startULTIndex = 0, foundAllWords = false;
    while ((startULTIndex = getFirstWordIndex(intermediateSearchList[0][0], ULTTokens, startULTIndex)) !== -1) {
        // console.log(`    searchULTWordRecords found first word '${intermediateSearchList[0][0]}' at ${startULTIndex} in ${JSON.stringify(ULTTokens)}`);
        foundAllWords = true;
        let searchIndex = 1, ultIndex = startULTIndex + 1;
        while (ultIndex < ULTTokens.length && searchIndex < intermediateSearchList.length)
            if (ULTTokens[ultIndex++].payload !== intermediateSearchList[searchIndex++][0]) {
                foundAllWords = false;
                break;
            }
        if (foundAllWords) break;
        ++startULTIndex;
    }
    if (!foundAllWords) {
        console.log(`ERROR: searchULTWordRecords couldn't find ${intermediateSearchList} in ${JSON.stringify(ULTTokens.map(t => t.payload))}`);
        return [];
    }
    // console.log(`  searchULTWordRecords found ${intermediateSearchList} starting at ${startULTIndex}`);

    // Now we just have to add the scopes field to the list of two-tuples
    let searchIndex = 0;
    while (startULTIndex < ULTTokens.length && searchIndex < intermediateSearchList.length)
        intermediateSearchList[searchIndex++].push(ULTTokens[startULTIndex++].scopes); // Appends the scopes field (after word and ellipsis flag)
    // console.log(`  searchULTWordRecords returning ${intermediateSearchList}`);
    return intermediateSearchList;
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js#L53 May 2021
// Called from main
/**
 *
 * @param {string} book
 * @param {string} cv
 * @param {Array} sourceTokens
 * @param {Array} ULTTokens
 * @param {string} ULTSearchString
 * @param {bool} prune
 * @returns
 */
const origLFromGLQuote = (book, cv, sourceTokens, ULTTokens, ULTSearchString, searchOccurrence, prune) => {
    // console.log(`origLFromGLQuote(${book}, ${cv}, (${sourceTokens.length}), (${ULTTokens.length}), '${ULTSearchString}', searchOccurrence=${searchOccurrence}, prune=${prune})…`);
    const ULTSearchThreeTuples = searchULTWordRecords(ULTSearchString, ULTTokens); // 0: ULT word, 1: followsEllipsisFlag, 2: alignment scopes array
    // console.log(`  ULTSearchThreeTuples = (${ULTSearchThreeTuples.length}) ${JSON.stringify(ULTSearchThreeTuples)}`);
    // NOTE: We lose the Greek apostrophes (e.g., from κατ’) in the next line
    const wordLikeOrigLTokens = slimSourceTokens(sourceTokens.filter(t => t.subType === "wordLike")); // drop out punctuation, space, eol, etc., tokens
    // console.log(`\n  wordLikeOrigLTokens = (${wordLikeOrigLTokens.length}) ${JSON.stringify(wordLikeOrigLTokens)}`); // The length of this list is now the number of Greek words in the verse
    const origLWordList = wordLikeOrigLTokens.map(t => t.payload);
    // console.log(`\n  origLWordList = (${origLWordList.length}) ${origLWordList}`); // The length of this list is now the number of Greek words in the verse

    // Now we go through in the order of the original language words, to get the ones that match
    const origLQuoteWords = [];
    for (const origLWord of origLWordList) {
        // console.log(`  origLFromGLQuote checking origL word '${origLWord}'`);
        const searchOrigLWord = `/${origLWord}:`;
        for (const ULTSearchThreeTuple of ULTSearchThreeTuples) {
            // console.log(`   origLFromGLQuote have ULTSearchThreeTuple=${ULTSearchThreeTuple}`);
            const scopesArray = ULTSearchThreeTuple[2];
            // console.log(`    origLFromGLQuote looking for scopes ${scopesArray} for '${ULTSearchThreeTuple[0]}'`);
            if (scopesArray.length === 1) {
                if (scopesArray[0].indexOf(searchOrigLWord) !== -1) {
                    origLQuoteWords.push(origLWord); // Might get the same word more than once???
                    break;
                }
            } else if (scopesArray.length === 2) {
                if (scopesArray[0].indexOf(searchOrigLWord) !== -1 || scopesArray[1].indexOf(searchOrigLWord) !== -1) {
                    origLQuoteWords.push(origLWord); // Might get the same word more than once???
                    break;
                }

            } else console.log(`WARNING: origLFromGLQuote code not written for ${scopesArray.length} scopes entries: searching for '${origLWord}' in ${ULTSearchThreeTuple}`);
        }
    }
    // console.log(`  origLFromGLQuote got result (${origLQuoteWords.length}) ${origLQuoteWords}`);
    if (origLQuoteWords.length === 0)
        return {
            "error":
                // `EMPTY MATCH IN SOURCE\nSearch Tuples: ${JSON.stringify(searchTuples)}\nCodepoints: ${searchTuples.map(s => "|" + Array.from(s[0]).map(c => c.charCodeAt(0).toString(16)))}`
                `EMPTY MATCH IN OrigL SOURCE\n    Search String: ${book} ${cv} '${ULTSearchString}' occurrence=${searchOccurrence}\n      from ULTTokens (${ULTTokens.length}) ${JSON.stringify(ULTTokens)}\n       then ULTSearchThreeTuples (${ULTSearchThreeTuples.length}) ${ULTSearchThreeTuples}\n       then wordLikeOrigLTokens (${wordLikeOrigLTokens.length}) ${JSON.stringify(wordLikeOrigLTokens)}`
        }
    // else have some origLQuoteWords
    // console.log(`  origLFromGLQuote returning (${origLQuoteWords.length}) ${origLQuoteWords}`);
    return { "data": origLQuoteWords };
}


// Called from main
/**
 *
 * @param {Array} wordList
 * @description Converts list to string and tidies it
 * @returns a tidyied string with the matching OrigL words
 */
const getTidiedData = (wordList) => {
    // console.log(`getTidiedData((${wordList.length}) ${wordList})…`);

    const tidiedDataString = wordList.join(' ').replace(/ … /, '…');
    // console.log(`  Returning '${tidiedDataString}'`);
    return tidiedDataString;
}


// Start of main code
const pk = new UWProskomma();
const args = process.argv.slice(2);
const tsvPath = args[0]; // Path to TSV9 TN
const book = tsvPath.split("/").reverse()[0].split(".")[0].split("-")[1];
const testament = args[1] // 'OT' or 'NT'
// const prune = (args[1] === "prune") || false;
const prune = true; // only return the matching quote -- not the entire verse text


getDocuments(pk, testament, book, true, false) // last parameters are "verbose" and "serialize"
    .then(async () => {
        // Query Proskomma which now contains the books
        // Returns the tokens for each verse, accessible by
        // [abbr][book][chapter:verse]
        const tokenLookup = await doAlignmentQuery(pk);
        // Iterate over TSV records
        let nRecords = 0;
        let counts = { pass: 0, fail: 0 };
        for (const tsvRecord of readTsv(tsvPath)) {
            // console.log(`tsvRecord = ${JSON.stringify(tsvRecord)}`);
            // if (tsvRecord.chapter === '3') break;
            // if (tsvRecord.verse === '2') break;
            nRecords++;
            const cv = `${tsvRecord.chapter}:${tsvRecord.verse}`;
            const source = testament === 'OT' ? tokenLookup.uhb : tokenLookup.ugnt;
            // Get the tokens for this BCV
            const sourceTokens = source[book][cv];
            // console.log(`\n  All OrigL source tokens = (${sourceTokens.length}) ${JSON.stringify(sourceTokens)}`);

            const allULTTokens = tokenLookup['ult'][book][cv];
            // console.log(`\n  All ULT tokens = (${allULTTokens.length}) ${JSON.stringify(allULTTokens)}`);
            const wordLikeULTTokens = allULTTokens.filter(t => t.subType === "wordLike").map(({ subType, position, ...rest }) => rest);
            // console.log(`\n  Wordlike ULT tokens = (${wordLikeULTTokens.length}) ${JSON.stringify(wordLikeULTTokens)}`);

            // Do the alignment
            const resultObject = origLFromGLQuote(
                book,
                cv,
                sourceTokens,
                wordLikeULTTokens,
                tsvRecord.glQuote,
                tsvRecord.occurrence,
                prune
            );
            // Returned object has either "data" or "error"
            if ("data" in resultObject) {
                console.assert(!resultObject.error);
                counts.pass++;
                // console.log(`  After origLFromGLQuote(): data = (${resultObject.data.length}) ${resultObject.data}`);
                // console.log(`    ult: “${highlightedAsString(resultObject.data)}”`);
                console.log(`${tsvRecord.book}_${cv} ►${tsvRecord.glQuote}◄ “${getTidiedData(resultObject.data)}”`);
            } else {
                console.assert(!resultObject.data);
                counts.fail++;
                console.error(`  Error: ${book} ${cv} ${tsvRecord.id} ${resultObject.error}`);
                console.error(`    Verse words: ${JSON.stringify(sourceTokens)} ${JSON.stringify(wordLikeULTTokens.map(t => t.payload))}\n`);
                // console.error(`    Verse codepoints: ${sourceTokens.filter(t => t.subType === "wordLike").map(t => t.payload).map(s => "|" + Array.from(s).map(c => c.charCodeAt(0).toString(16)))}`);
            }
            // }
        }
        console.log(counts);
    }
    )
