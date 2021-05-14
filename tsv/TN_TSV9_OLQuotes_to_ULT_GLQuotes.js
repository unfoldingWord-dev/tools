const Axios = require("axios");
const YAML = require('js-yaml-parser');
const xre = require('xregexp');
const deepcopy = require('deepcopy');

const { readTsv } = require('uw-proskomma/src/utils/tsv');
const { doAlignmentQuery } = require('uw-proskomma/src/utils/query');
const { pruneTokens, slimSourceTokens } = require('uw-proskomma/src/utils/tokens');
const { searchWordRecords } = require('uw-proskomma/src/utils/search');
const { UWProskomma } = require('uw-proskomma/src/index');


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/download.js May 2021
// Changed to accept testament as a parameter, and to only load the correct repo -- UHB or UGNT
// Removed UST preloading
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
        const content = [];
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
        if (verbose) console.log(`      Downloaded`)
        const startTime = Date.now();
        pk.importDocuments(selectors, "usfm", content, {});
        if (verbose) console.log(`      Imported in ${Date.now() - startTime} msec`);
        if (serialize) {
            const path = require("path");
            const fse = require('fs-extra');
            const outDir = path.resolve(__dirname, '..', '..', 'serialized');
            fse.mkdirs(outDir);
            fse.writeFileSync(
                path.join(
                    outDir,
                    Object.values(selectors).join('_') + "_pkserialized.json",
                ),
                JSON.stringify(pk.serializeSuccinct(`${org}/${lang}_${abbr}`))
            );
        }
    }
    return pk;
}


// Copied from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js and annotated May 2021
/**
 *
 * @param {string} origString -- the string of original language words being searched for (may include ellipsis)
 * @returns a list of 2-tuples with (origWord, flag if origWord follows an ellipsis)
 */
/*
const searchWordRecords = origString => {
    // console.log(`searchWordRecords = ('${origString}')…`);

    const ret = [];
    for (let searchExpr of xre.split(origString, /[\s־]/)) {
        searchExpr = xre.replace(searchExpr, /[,’?;.!׃]/, ""); // remove sentence punctuation (incl. all apostrophes!)
        if (searchExpr.includes("…")) {
            const searchExprParts = searchExpr.split("…");
            ret.push([searchExprParts[0], false]);
            searchExprParts.slice(1).forEach(p => ret.push([p, true]));
        } else {
            ret.push([searchExpr, false]);
        }
    }
    return ret.filter(t => t[0] !== "׀"); // why is this needed -- ah for \w fields I guess
}
*/


// Copied from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js May 2021
/**
 *
 * @param {Array} searchTuples -- a list of 2-tuples with (origWord, flag if origWord follows an ellipsis) for the OrigL search string // NOTE: We've lost the occurrence number!
 * @param {Array} tokens -- a list of token objects -- one for each OrigL word in the OrigL verse
 * @returns a list of 2-tuples with (origWord, occurrenceNumber) including elided words (was that intended or not???)
 */
/*const contentForSearchWords = (searchTuples, tokens) => { // used recursively
    console.log(`contentForSearchWords = ((${searchTuples.length}) ${searchTuples}, (${tokens.length}) ${JSON.stringify(tokens)})…`);

    // What would lfsw1 stand for???
    const lfsw1 = (searchTuples, tokens, content) => {
        if (!content) {
            content = [];
        }
        if (searchTuples.length === 0) { // Everything matched
            return content;
        } else if (tokens.length === 0) { // No more tokens - fail
            return null;
        } else if (tokens[0].payload === searchTuples[0][0]) { // First word matched, try next one
            return lfsw1(searchTuples.slice(1), tokens.slice(1), content.concat([[tokens[0].payload, tokens[0].occurrence]])); // Wouldn't .push be simpler here x2 ???
        } else if (searchTuples[0][1]) { // non-greedy wildcard, try again on next token
            return lfsw1(searchTuples, tokens.slice(1), content.concat([[tokens[0].payload, tokens[0].occurrence]]));
        } else { // No wildcard and no match - fail
            return null;
        }
    }

    if (tokens.length === 0) {
        return null;
    }
    return lfsw1(searchTuples, tokens) || contentForSearchWords(searchTuples, tokens.slice(1)); // why do we need a second recursive call on this line -- what disturbing token could be at [0]?
}
*/

// Rewritten from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js May 2021
/**
 *
 * @param {Array} searchTuples -- a list of 2-tuples with (origWord, flag if origWord follows an ellipsis) for the OrigL search string // NOTE: We've lost the occurrence number!
 * @param {string} searchOccurrence -- an integer string
 * @param {Array} tokens -- a list of token objects -- one for each OrigL word in the OrigL verse
 * @returns a list of 2-tuples with (origWord, occurrenceNumber) -- the occurrenceNumbers are the valuable added info here
 */
const contentForSearchWords = (searchTuples, searchOccurrence, origLTokens) => {
    // console.log(`contentForSearchWords = ((${searchTuples.length}) '${searchTuples}', ${searchOccurrence}, (${origLTokens.length}) ${JSON.stringify(origLTokens)})…`);

    // Helpful function
    const countOccurrences = (arr, val) => arr.reduce((a, v) => (v === val ? a + 1 : a), 0); // From https://www.w3resource.com/javascript-exercises/fundamental/javascript-fundamental-exercise-70.php

    // First find the correct occurrence of the first contiguous part of the search string
    //  and then remove the first portion of the origLTokens
    //  so that the simple matching code below can't get a premature match.
    const occurrenceNumber = Number(searchOccurrence);
    if (searchTuples.length > 1 || occurrenceNumber > 1) { // Do a bit of extra work to ensure we get the starting point right for the occurrence
        // console.log(`HERE1 in contentForSearchWords = ((${searchTuples.length}) '${searchTuples}', ${searchOccurrence}, (${origLTokens.length}) ${JSON.stringify(origLTokens)})…`);
        const allOrigLWords = origLTokens.map(token => token.payload); // Find all the words in the verse
        // console.log(`allOrigLWords (${allOrigLWords.length}) ${allOrigLWords}`);
        const firstContiguousSearchWords = [];
        for (const searchTuple of searchTuples) {
            if (searchTuple[1]) break; // no longer contiguous
            firstContiguousSearchWords.push(searchTuple);
        }
        // console.log(`firstContiguousSearchWords (${firstContiguousSearchWords.length}) ${firstContiguousSearchWords}`);
        console.assert(firstContiguousSearchWords.length >= 1, "Must be at least one search word!");

        const firstSearchWord = searchTuples[0][0];
        console.assert(!searchTuples[0][1], "First search word can't be after ellipsis!");
        if (countOccurrences(allOrigLWords, firstSearchWord) > 1) { // This is when we have to be very careful
            // console.log(`HERE2 in contentForSearchWords = ((${searchTuples.length}) '${searchTuples}', ${searchOccurrence}, (${origLTokens.length}) ${JSON.stringify(origLTokens)})…`);
            // console.log(`firstContiguousSearchWords (${firstContiguousSearchWords.length}) ${firstContiguousSearchWords}`);
            // console.log(`allOrigLWords (${allOrigLWords.length}) ${allOrigLWords}`);
            // console.log(`We have ${countOccurrences(allOrigLWords, firstSearchWord)} occurrences of the first search word '${firstSearchWord}' from (${firstContiguousSearchWords.length}) ${firstContiguousSearchWords}`);
            // console.log(`We have to find the right occurrence of ${firstContiguousSearchWords} ${searchOccurrence}`);
            let firstSearchWordStartIndex = 0, found = false;
            while (!found) { // I'm sure Mark that would do this with recursive calls of some sort :-)
                firstSearchWordStartIndex = allOrigLWords.indexOf(firstSearchWord, firstSearchWordStartIndex)
                // console.log(`In outer loop with firstSearchWordStartIndex=${firstSearchWordStartIndex}`)
                if (firstSearchWordStartIndex === -1) {
                    console.log(`Breaking here coz we couldn't find a good start!`);
                    break // from outer loop
                }
                found = true;
                for (let nextSearchWordIndex = 1; nextSearchWordIndex < firstContiguousSearchWords.length; nextSearchWordIndex++) {
                    const [nextSearchWord, notConsecutive] = firstContiguousSearchWords[nextSearchWordIndex];
                    console.assert(!notConsecutive, "Non-consecutive words should have already been removed!"); // Should already be removed
                    const combinedIndex = firstSearchWordStartIndex + nextSearchWordIndex;
                    if (allOrigLWords[combinedIndex] === nextSearchWord) {
                        // console.log(`Next search word '${nextSearchWord}' matches`);
                    } else {
                        // console.log(`Next search word '${nextSearchWord}' didn't match '${allOrigLWords[combinedIndex]}'`);
                        firstSearchWordStartIndex++;
                        found = false;
                        break;
                    }
                }
            }
            // console.log(`Got here with firstSearchWordStartIndex=${firstSearchWordStartIndex}`);
            console.assert(firstSearchWordStartIndex !== -1, "First word should be found!");
            // Delete the earlier origLTokens so that the code below is guaranteed not to find a premature match
            // console.log(`  Previously had ${origLTokens.length} origLTokens`);
            origLTokens = origLTokens.slice(firstSearchWordStartIndex);
            // console.log(`  Now have ${origLTokens.length} origLTokens`);
            const nowAllOrigLWords = origLTokens.map(token => token.payload);
            // console.log(`  Now nowAllOrigLWords (${nowAllOrigLWords.length}) ${nowAllOrigLWords} from (${allOrigLWords.length}) ${allOrigLWords}`);
        }
    }

    // At this point, we may have removed the beginning of the string
    //  so that we can guarantee that the first match of the first word will be the correct occurrence
    const origLWordsSoFar = [];
    const result = [];
    let searchTupleIndex = 0;
    for (const token of origLTokens) {
        // console.log(`  Looking at token: ${JSON.stringify(token)} with ${searchTupleIndex} and ${origLWordsSoFar}`);
        console.assert(token.subType === 'wordLike', "This tokens should only be wordLike now!");
        origLWordsSoFar.push(token.payload);
        const [searchWord, notConsecutive] = searchTuples[searchTupleIndex];
        // console.log(`  search '${searchWord}' ${notConsecutive}`);
        if (token.payload === searchWord) {
            // && (searchTupleIndex > 0 // we've already started matching
            //     || countOccurrences(origLWordsSoFar, searchWord) === occurrenceNumber)) {
            result.push([token.payload, token.occurrence]);
            if (++searchTupleIndex === searchTuples.length) {
                // console.log(`  contentForSearchWords() returning (${result.length}) ${result}`);
                console.assert(result.length === searchTuples.length, "Should return the same number of words!");
                return result; // all done
            }
        } else if (searchTupleIndex > 0 && !notConsecutive) { // They should have been consecutive words
            console.log(`ERROR: contentForSearchWords() didn\'t match consecutive word '${token.payload}' with ${searchTupleIndex} ${searchTuples}`);
            return null;
        }
    }
    console.log(`ERROR: contentForSearchWords() didn\'t match all words '${searchTuples}'`);
    return null;
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/tokens.js#L24 May 2021
/**
 *
 * @param {Array} tokens -- GL token objects with many fields
 * @returns the same number of tokens but with refactored fields in each object (scopes is replaced by blContent and occurrence)
 */
// e.g., {"subType":"wordLike","payload":"But","position":50,"scopes":["attribute/milestone/zaln/x-occurrence/0/1","attribute/milestone/zaln/x-occurrences/0/1","attribute/milestone/zaln/x-content/0/δὲ"]}
//   becomes {"subType":"wordLike","payload":"But","position":50,"blContent":["δὲ"],"occurrence":[1,1]}
// and {"subType":"eol","payload":"\n","position":null,"scopes":[]}
//   becomes {"subType":"eol","payload":" ","position":null,"blContent":[],"occurrence":[]}
const slimGLTokens = (tokens) => {
    // console.log(`slimGLTokens = ((${tokens.length}) ${JSON.stringify(tokens)})…`);

    const ret = [];
    if (!tokens) {
        return null;
    }
    for (const token of tokens) {
        const t2 = deepcopy(token);
        const occurrenceScopes = t2.scopes.filter(s => s.startsWith("attribute/milestone/zaln/x-occurrence") && !s.endsWith("s"));
        const xContentScopes = t2.scopes.filter(s => s.startsWith("attribute/milestone/zaln/x-content"));
        t2.blContent = xContentScopes.map(s => s.split("/")[5].replace('’', '')); // delete one apostrophe -- anything else should be deleted here???
        t2.payload = t2.payload.replace(/[ \t\r\n]+/g, " ");
        t2.occurrence = occurrenceScopes.map(o => parseInt(o.split("/")[5]));
        delete t2.scopes;
        ret.push(t2);
    }
    // console.log(`  slimGLTokens returning (${ret.length}) ${JSON.stringify(ret)}`);
    return ret;
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js May 2021
// Fixed the matching of the correct occurrence
/**
 *
 * @param {Array} slimmedGlTokens -- these token objects have scopes list already replaced by bl and occurrence lists
 * @param {Array} contentTuplesWithOccurrences -- a list of 2-tuples containing (OrigL word, occurrence number)
 * @returns {Array} -- a list (the same length as the first parameter) of 2-tuples (GLWord, flag if part of match)
 */
// Some slimmedGlTokens are:
//  {"subType":"wordLike","payload":"But","position":50,"blContent":["δὲ"],"occurrence":[1,1]},
//  {"subType":"eol","payload":" ","position":null,"blContent":[],"occurrence":[]},
//  {"subType":"wordLike","payload":"at","position":51,"blContent":["καιροῖς"],"occurrence":[1,1]}
//  {"subType":"eol","payload":" ","position":null,"blContent":["καιροῖς"],"occurrence":[1,1]} NOTE: space (correctly) mapped to Grk word
// but NOTE
//  {"subType":"wordLike","payload":"agrees","position":27,"blContent":["κατ’"],"occurrence":[1,1]} NOTE: the word here DOES HAVE the apostrophe
// Typical contentTuplesWithOccurrences (from ULT Titus 1:3):
//  [(ἐφανέρωσεν,1),(τὸν,1),(λόγον,1),(αὐτοῦ,1)]
const highlightedAlignedGlText = (slimmedGlTokens, contentTuplesWithOccurrences) => {
    // console.log(`highlightedAlignedGlText = ((${slimmedGlTokens.length}) ${JSON.stringify(slimmedGlTokens)}, (${content.length}) ${content})…`);

    return slimmedGlTokens.map(glToken => {
        // console.log(`    Processing GL token: ${JSON.stringify(glToken)}`);
        const matchingContent = contentTuplesWithOccurrences.filter(contentWordOccurrenceTuple =>
            (glToken.occurrence.length > 0) // it's a real word with an occurrence
            && glToken.blContent.includes(contentWordOccurrenceTuple[0])
            && glToken.occurrence[0] === contentWordOccurrenceTuple[1]); // FIXED: it's the correct occurrence
        // if (matchingContent.length > 0) { console.log(`      matchingContent = ${matchingContent} so getting glToken '${token.payload}'`); }
        return [glToken.payload, (matchingContent.length > 0)]; // Returns all slimmedGlTokens payloads, but with added bool for match
    }
    )
};


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js#L53 May 2021
/**
 *
 * @param {string} book
 * @param {string} cv
 * @param {Array} sourceTokens
 * @param {Array} glTokens
 * @param {string} searchString
 * @param {bool} prune
 * @returns
 */
const gl4Source = (book, cv, sourceTokens, glTokens, searchString, searchOccurrence, prune) => {
    // console.log(`gl4Source = (${book}, ${cv}, (${sourceTokens.length}), (${glTokens.length}), '${searchString}', ${searchOccurrence}, ${prune})…`);
    const searchTuples = searchWordRecords(searchString);
    // console.log(`  searchTuples = (${searchTuples.length}) ${searchTuples}`);
    // NOTE: We lose the Greek apostrophes (e.g., from κατ’) in the next line
    const ugntTokens = slimSourceTokens(sourceTokens.filter(t => t.subType === "wordLike")); // drop out punctuation, space, eol, etc., tokens
    // console.log(`  ugntTokens = (${ugntTokens.length}) ${JSON.stringify(ugntTokens)}`); // The length of this list is now the number of Greek words in the verse
    const contentTuplesWithOccurrences = contentForSearchWords(searchTuples, searchOccurrence, ugntTokens); // We needed to pass the searchOccurrence parameter thru here
    if (!contentTuplesWithOccurrences) {
        return {
            "error":
                // `NO MATCH IN SOURCE\nSearch Tuples: ${JSON.stringify(searchTuples)}\nCodepoints: ${searchTuples.map(s => "|" + Array.from(s[0]).map(c => c.charCodeAt(0).toString(16)))}`
                `NO MATCH IN SOURCE\nSearch String: ${book} ${cv} '${searchString}' ${searchOccurrence}`
        }
    }
    // console.log(`  After contentForSearchWords(…): contentTuplesWithOccurrences = (${contentTuplesWithOccurrences.length}) ${contentTuplesWithOccurrences}`);
    const highlightedGlTokens = highlightedAlignedGlText(slimGLTokens(glTokens), contentTuplesWithOccurrences);
    // console.log(`  After highlightedAlignedGlText(…): highlightedTokens = (${highlightedGlTokens.length}) ${highlightedGlTokens}`);
    if (prune) {
        return { "data": pruneTokens(highlightedGlTokens) };
    } else {
        return { "data": highlightedGlTokens };
    }
}

/*
// Copied from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/render.js May 2021
const highlightedAsString = highlighted =>
    highlighted
        .map(tp => tp[1] ? tp[0].toUpperCase() : tp[0])
        // .map(tp => tp[0]) // Don't want UPPERCASE
        .join("")
        .trim();
*/


// Drops non-matching words and puts an ellipse between non-contiguous matching words
const getTidiedData = (dataPairs) => {
    // console.log(`getTidiedData(${dataPairs.length}) ${dataPairs})…`);
    let tidiedData = '';
    inEllipse = false
    for (const somePair of dataPairs) {
        // console.log("somePair", somePair);
        if (somePair[1]) {
            tidiedData += somePair[0];
            inEllipse = false;
        } else if (somePair[0] === ' ' || somePair[0] === ',') { // some spaces are marked as matches and some not -- almost seems random
            tidiedData += somePair[0];
        } else {
            if (!inEllipse) tidiedData += '…';
            inEllipse = true;
        }
    }
    // TODO: Better if we don't end up with fields like '…,          ,             of the truth …   ,' -- where/why is this happening???
    // console.log(`Do final tidy of '${tidiedData}'`);
    // NOTE: We need three loops if prune was false
    for (let n = 0; n < 2; ++n) // Run through this clean-up multiple times to ensure we catch everything
        tidiedData = tidiedData
            .trim() // remove leading and trailing spaces
            .replace(/^…/, '').replace(/…$/, '') // remove leading and trailing ellipses
            .replace(/^,/, '').replace(/,$/, '') // remove leading and trailing commas
            .replace(/,…/g, '…').replace(/…,/g, '…') // removing hanging comma
            .replace(/ …/g, '…').replace(/… /g, '…') // tidy-up surplus spaces around ellipses
            .replace(/ , /, '')
            .replace(/     /g, ' ').replace(/    /g, ' ').replace(/   /g, ' ').replace(/  /g, ' ')
            .replace(/ …/g, '…').replace(/… /g, '…') // tidy-up surplus spaces around ellipses
            .replace(/^…/, '').replace(/…$/, '') // remove leading and trailing ellipses (again)
            .trim(); // remove leading and trailing spaces (again)
    console.assert(tidiedData.length, "Should have some tidiedData left!");
    console.assert(' ,.…'.indexOf(tidiedData[0] === -1),);
    console.assert(' ,.…'.indexOf(tidiedData.slice(-1) === -1), "These characters shouldn't occur at end!");
    console.assert(tidiedData.indexOf('  ') === -1, "Should be no more double spaces!");
    console.assert(tidiedData.indexOf(' ,') === -1, "Comma should not occur after space!");
    console.assert(tidiedData.indexOf(' .') === -1, "Period should not occur after space!");
    console.assert(tidiedData.indexOf(' :') === -1, "Colon should not occur after space!");
    return tidiedData;
}


// Start of main code
const pk = new UWProskomma();
const args = process.argv.slice(2);
const tsvPath = args[0]; // Path to TSV9 TN
const book = tsvPath.split("/").reverse()[0].split(".")[0].split("-")[1];
const testament = args[1] // 'OT' or 'NT'
// const prune = (args[1] === "prune") || false;
const prune = true; // only return the matching quote -- not the entire verse text


getDocuments(pk, testament, book, true) //last parameter is "verbose"
    .then(async () => {
        // Query Proskomma which now contains the books
        // Returns the tokens for each verse, accessible by
        // [abbr][book][chapter:verse]
        const tokenLookup = await doAlignmentQuery(pk);
        // Iterate over TSV records
        let nRecords = 0;
        let counts = { pass: 0, fail: 0 };
        const gl = 'ult';
        for (const tsvRecord of readTsv(tsvPath)) {
            // console.log(`tsvRecord = ${JSON.stringify(tsvRecord)}`);
            // if (tsvRecord.verse === '11') break;
            nRecords++;
            const cv = `${tsvRecord.chapter}:${tsvRecord.verse}`;
            // console.log(`  ${tsvRecord.book} ${cv}`);
            // console.log(`    Search string: ${tsvRecord.origQuote}`);
            // Iterate over GLs
            // for (const gl of ["ult", "ust"]) {
            const source = testament === 'OT' ? tokenLookup.uhb : tokenLookup.ugnt;
            // Get the tokens for BCV
            const sourceTokens = source[book][cv];
            // console.log(`  source tokens = (${sourceTokens.length}) ${JSON.stringify(sourceTokens)}`);
            const glTokens = tokenLookup[gl][book][cv];
            // console.log(`  GL tokens = (${glTokens.length}) ${JSON.stringify(glTokens)}`);
            // Do the alignment
            const highlighted = gl4Source(
                book,
                cv,
                sourceTokens,
                glTokens,
                tsvRecord.origQuote,
                tsvRecord.occurrence, // added by RJH -- it can't work correctly without this info
                prune
            );
            // Returned object has either "data" or "error"
            if ("data" in highlighted) {
                counts.pass++;
                // console.log(`  After gl4Source(): data = (${highlighted.data.length}) ${highlighted.data}`);
                // console.log(`    ${gl}: “${highlightedAsString(highlighted.data)}”`);
                console.log(`${tsvRecord.book}_${cv} ►${tsvRecord.origQuote}◄ “${getTidiedData(highlighted.data)}”`);
            } else {
                counts.fail++;
                console.log(`    Error: ${highlighted.error}`);
                console.log(`Verse tokens: ${JSON.stringify(sourceTokens.filter(t => t.subType === "wordLike").map(t => t.payload))}`);
                console.log(`Verse codepoints: ${sourceTokens.filter(t => t.subType === "wordLike").map(t => t.payload).map(s => "|" + Array.from(s).map(c => c.charCodeAt(0).toString(16)))}`);
            }
            // }
        }
        console.log(counts);
    }
    )
