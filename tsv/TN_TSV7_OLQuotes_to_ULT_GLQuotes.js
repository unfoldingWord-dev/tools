const Axios = require("axios");
const YAML = require('js-yaml-parser');
const xre = require('xregexp');
const deepcopy = require('deepcopy');

const { readTsv } = require('uw-proskomma/src/utils/tsv');
const { rejigAlignment } = require('uw-proskomma/src/utils/rejig_alignment');
// const { doAlignmentQuery } = require('uw-proskomma/src/utils/query');
const { pruneTokens, slimSourceTokens } = require('uw-proskomma/src/utils/tokens');
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
        if (verbose) console.log(`      Downloaded`)

        const startTime = Date.now();
        if (abbr === 'ult') { // Preprocess x-occurrence,x-occurrences,x-content into x-align="content:occurrence:occurrences" for easier handling later
            // console.log(`content1: ${typeof content} (${content.length}) ${Object.keys(content)}`);
            content = [rejigAlignment(content)]; // Tidy-up ULT USFM alignment info
            // console.log(`content2: ${typeof content} (${content.length}) ${content}`);
        }
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


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/query.js May 2021
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
/**
 *
 * @param {string} origString -- the string of original language words being searched for (may include ellipsis)
 * @returns a list of 2-tuples with (origWord, flag if origWord follows an ellipsis)
 */
const searchWordRecords = origString => {
    // console.log(`searchWordRecords = ('${origString}')…`);

    const ret = [];
    for (let searchExpr of xre.split(origString, /[\s־]/)) {
        // The UHB/UGNT "sourceTokens" have all punctuation (incl. word punctuation) as separate tokens!
        // So remove sentence punctuation (incl. all apostrophes!) from our individual search words
        // Added 'all' scope flag below to handle words with multiple punctuation marks to be removed, e.g. "(word),"
        searchExpr = xre.replace(searchExpr, /[(),’?:;.!׃]/, '', 'all'); // Added colon and parentheses -- last char is Hebrew sof pasuq
        if (searchExpr.includes("…")) {
            const searchExprParts = searchExpr.split("…");
            ret.push([searchExprParts[0], false]);
            searchExprParts.slice(1).forEach(p => ret.push([p, true]));
        } else {
            ret.push([searchExpr, false]);
        }
    }
    return ret.filter(t => t[0] !== "׀"); // why is this needed -- ah for \w fields maybe -- still not really sure ???
}


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/tokens.js#L24 May 2021
/**
 *
 * @param {Array} glTokens -- GL token objects with many fields
 * @returns the same number of tokens but with refactored fields in each object (scopes is replaced by blContent and occurrence)
 */
// e.g., {"subType":"wordLike","payload":"But","position":50,"scopes":["attribute/milestone/zaln/x-align/δὲ:1:1"]}
//   becomes {"subType":"wordLike","payload":"But","position":50,"blContent":["δὲ"],"occurrence":[1]}
// and {"subType":"eol","payload":"\n","position":null,"scopes":[]}
//   becomes {"subType":"eol","payload":" ","position":null,"blContent":[],"occurrence":[]}
// and {"subType":"wordLike","payload":"essential","position":925,"scopes":["attribute/milestone/zaln/x-align/τὰς:1:1","attribute/milestone/zaln/x-align/ἀναγκαίας:1:1"]}
//   becomes {"subType":"wordLike","payload":"essential","position":925,"blContent":["τὰς","ἀναγκαίας"],"occurrence":[1,1]}
const slimGLTokens = (glTokens) => {
    // console.log(`slimGLTokens = ((${glTokens.length}) ${JSON.stringify(glTokens)})…`);

    const ret = [];
    if (!glTokens) {
        return null;
    }
    for (const glToken of glTokens) {
        const t2 = deepcopy(glToken);
        const alignScopes = t2.scopes.filter(s => s.startsWith("attribute/milestone/zaln/x-align"));
        // We have to ensure that these GL tokens have the same punctuation as the search text that they'll be compared with later
        // TODO: What about other punctuation -- why do we just remove apostrophe -- where's the other punctuation removed ???
        t2.blContent = alignScopes.map(s => s.split('/')[5].split(':')[0] // Get the word(s)
            .replace('’', '')); // delete one apostrophe -- anything else should be deleted here???
        t2.payload = t2.payload.replace(/[ \t\r\n]+/g, " ");
        t2.occurrence = alignScopes.map(o => parseInt(o.split('/')[5].split(':')[1]));
        console.assert(t2.blContent.length === t2.occurrence.length, `Expected blContent ${t2.blContent} and occurrence ${t2.occurrence} to be the same length!`);
        // console.assert(t2.blContent.length <= 6, `Trying to discover the maximum length of blContent: now have ${t2.blContent.length}`);
        delete t2.scopes;
        ret.push(t2);
    }
    // console.log(`  slimGLTokens returning (${ret.length}) ${JSON.stringify(ret)}`);
    return ret;
}


// Copied from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/search.js May 2021
/**
 *
 * @param {Array} searchTuples -- a list of 2-tuples with (origWord, flag if origWord follows an ellipsis) for the OrigL search string // NOTE: We've lost the occurrence number!
 * @param {Array} tokens -- a list of token objects -- one for each OrigL word in the OrigL verse
 * @returns a list of 2-tuples with (origWord, occurrenceNumber) including elided words (was that intended or not???)
 */
/*const contentForSearchWords = (searchTuples, tokens) => { // used recursively
    console.log(`contentForSearchWords = ((${searchTuples.length}) ${searchTuples}, (${tokens.length}) ${JSON.stringify(tokens)})…`);

    // NOTE: lfsw = lemmaForSearchWords -- see src/scripts/greek_quote_to_gl_via_lemma.js
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
    let adjustedOrigLTokens = origLTokens; // Make a copy for debugging

    // Helpful function
    const countOccurrences = (arr, val) => arr.reduce((a, v) => (v === val ? a + 1 : a), 0); // From https://www.w3resource.com/javascript-exercises/fundamental/javascript-fundamental-exercise-70.php

    // First find the correct occurrence of the first contiguous part of the search string
    //  and then remove the first portion of the origLTokens
    //  so that the simple matching code below can't get a premature match.
    const occurrenceNumber = Number(searchOccurrence);
    if (searchTuples.length > 1 || occurrenceNumber > 1) { // Do a bit of extra work to ensure we get the starting point right for the occurrence
        // console.log(`HERE1 in contentForSearchWords = ((${searchTuples.length}) '${searchTuples}', ${searchOccurrence}, (${origLTokens.length}) ${JSON.stringify(origLTokens)})…`);
        const allOrigLWords = adjustedOrigLTokens.map(token => token.payload); // Find all the words in the verse
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
            adjustedOrigLTokens = adjustedOrigLTokens.slice(firstSearchWordStartIndex);
            // console.log(`  Now have ${origLTokens.length} origLTokens`);
            const nowAllOrigLWords = adjustedOrigLTokens.map(token => token.payload);
            // console.log(`  Now nowAllOrigLWords (${nowAllOrigLWords.length}) ${nowAllOrigLWords} from (${allOrigLWords.length}) ${allOrigLWords}`);
        }
    }

    // At this point, we may have removed the beginning of the string if necessary
    //  so that we can always guarantee that the first match of the first word will be the correct occurrence
    // console.log(`Now searching for (${searchTuples.length}) '${searchTuples}'`);
    const origLWordsSoFar = [];
    const result = [];
    let searchTupleIndex = 0;
    for (const token of adjustedOrigLTokens) {
        // console.log(`  contentForSearchWords() looking at token: ${JSON.stringify(token)} with ${searchTupleIndex} and ${origLWordsSoFar}`);
        console.assert(token.subType === 'wordLike', "These tokens should only be wordLike now!");
        origLWordsSoFar.push(token.payload);
        const [searchWord, notConsecutive] = searchTuples[searchTupleIndex];
        // console.log(`  searchWord='${searchWord}' consecutive=${!notConsecutive}`);
        if (token.payload === searchWord) {
            result.push([token.payload, token.occurrence]);
            if (++searchTupleIndex === searchTuples.length) {
                // console.log(`  contentForSearchWords() returning (${result.length}) ${result}`);
                console.assert(result.length === searchTuples.length, `contentForSearchWords(${searchTuples}) should return the same number of words! ${result}`);
                return result; // all done
            }
        } else { // we didn't find the word that we were looking for
            // console.log(`Nope: ${searchTupleIndex} '${searchWord}' ${notConsecutive} didn't match with '${token.payload}'`);
            if (searchTupleIndex > 0 && !notConsecutive) { // They should have been consecutive words
                if (searchTupleIndex > 0 && searchTuples[searchTupleIndex - 1][1]) { // Then we're searching for the second contiguous part and might have gotten a false start
                    --searchTupleIndex;
                    result.pop();
                    console.log(`  Seems a mismatch when searching for '${searchWord}': resetting searchTupleIndex back to ${searchTupleIndex}`);
                } else { // TODO: We step back 1 above -- may need to step back further in some complex cases ???
                    console.error(`contentForSearchWords = ((${searchTuples.length}) '${searchTuples}', ${searchOccurrence}, (${origLTokens.length}) ${JSON.stringify(origLTokens)})`);
                    console.error(`  Was searching in (${adjustedOrigLTokens.length}) ${JSON.stringify(adjustedOrigLTokens)}`);
                    console.error(`ERROR: contentForSearchWords() didn\'t match consecutive word '${token.payload}' with searchTupleIndex=${searchTupleIndex} ${searchTuples[searchTupleIndex]}`);
                    return null;
                }
            }
        }
    }
    console.error(`ERROR: contentForSearchWords() didn't match all words '${searchTuples}' in ${origLWordsSoFar}`);
    return null;
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
//  {"subType":"wordLike","payload":"But","position":50,"blContent":["δὲ"],"occurrence":[1]},
//  {"subType":"eol","payload":" ","position":null,"blContent":[],"occurrence":[]},
//  {"subType":"wordLike","payload":"at","position":51,"blContent":["καιροῖς"],"occurrence":[1]}
//  {"subType":"eol","payload":" ","position":null,"blContent":["καιροῖς"],"occurrence":[1]} NOTE: space (correctly) mapped to Grk word
// but NOTE
//  {"subType":"wordLike","payload":"agrees","position":27,"blContent":["κατ’"],"occurrence":[1]} NOTE: the word here DOES HAVE the apostrophe
// Typical contentTuplesWithOccurrences (from ULT Titus 1:3):
//  [(ἐφανέρωσεν,1),(τὸν,1),(λόγον,1),(αὐτοῦ,1)]
const highlightedAlignedGlText = (slimmedGlTokens, contentTuplesWithOccurrences) => {
    // console.log(`highlightedAlignedGlText = ((${slimmedGlTokens.length}) ${JSON.stringify(slimmedGlTokens)}, (${content.length}) ${content})…`);

    return slimmedGlTokens.map(glToken => {
        // console.log(`    Processing GL token: ${JSON.stringify(glToken)}`);

        const matchingContent = contentTuplesWithOccurrences.filter(contentWordOccurrenceTuple =>
            (glToken.occurrence.length > 0) // it's a real word with an occurrence
            && ((glToken.blContent[0] === contentWordOccurrenceTuple[0] && glToken.occurrence[0] === contentWordOccurrenceTuple[1])
                || (glToken.blContent.length > 1 && glToken.blContent[1] === contentWordOccurrenceTuple[0] && glToken.occurrence[1] === contentWordOccurrenceTuple[1])
                || (glToken.blContent.length > 2 && glToken.blContent[2] === contentWordOccurrenceTuple[0] && glToken.occurrence[2] === contentWordOccurrenceTuple[1])
                || (glToken.blContent.length > 3 && glToken.blContent[3] === contentWordOccurrenceTuple[0] && glToken.occurrence[3] === contentWordOccurrenceTuple[1])
                || (glToken.blContent.length > 4 && glToken.blContent[4] === contentWordOccurrenceTuple[0] && glToken.occurrence[4] === contentWordOccurrenceTuple[1])
                || (glToken.blContent.length > 5 && glToken.blContent[5] === contentWordOccurrenceTuple[0] && glToken.occurrence[5] === contentWordOccurrenceTuple[1])
            )
        );
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
    const origLTokens = slimSourceTokens(sourceTokens.filter(t => t.subType === "wordLike")); // drop out punctuation, space, eol, etc., tokens
    // console.log(`  origLTokens = (${origLTokens.length}) ${JSON.stringify(origLTokens)}`); // The length of this list is now the number of Greek words in the verse
    const contentTuplesWithOccurrences = contentForSearchWords(searchTuples, searchOccurrence, origLTokens); // We needed to pass the searchOccurrence parameter thru here
    if (!contentTuplesWithOccurrences) {
        return {
            "error":
                // `NO MATCH IN SOURCE\nSearch Tuples: ${JSON.stringify(searchTuples)}\nCodepoints: ${searchTuples.map(s => "|" + Array.from(s[0]).map(c => c.charCodeAt(0).toString(16)))}`
                // `NO MATCH IN BIBLICAL LANGUAGE SOURCE\n    Search String: ${book} ${cv} '${searchString}' occurrence=${searchOccurrence}\n      from origLTokens (${origLTokens.length}) ${JSON.stringify(origLTokens)}`
                `NO MATCH IN BIBLICAL LANGUAGE SOURCE\n    Search String: ${book} ${cv} '${searchString}' occurrence=${searchOccurrence}`
        }
    }
    // console.log(`  After contentForSearchWords(…): contentTuplesWithOccurrences = (${contentTuplesWithOccurrences.length}) ${contentTuplesWithOccurrences}`);
    const slimmedGlTokens = slimGLTokens(glTokens);
    const highlightedGlTokens = highlightedAlignedGlText(slimmedGlTokens, contentTuplesWithOccurrences);
    // console.log(`  After highlightedAlignedGlText(…): highlightedTokens = (${highlightedGlTokens.length}) ${highlightedGlTokens}`);
    if (!highlightedGlTokens.length) {
        return {
            "error":
                // `EMPTY MATCH IN SOURCE\nSearch Tuples: ${JSON.stringify(searchTuples)}\nCodepoints: ${searchTuples.map(s => "|" + Array.from(s[0]).map(c => c.charCodeAt(0).toString(16)))}`
                `EMPTY MATCH IN GL SOURCE\n    Search String: ${book} ${cv} '${searchString}' occurrence=${searchOccurrence}\n      from origLTokens (${origLTokens.length}) ${JSON.stringify(origLTokens)}\n       then contentTuplesWithOccurrences (${contentTuplesWithOccurrences.length}) ${contentTuplesWithOccurrences}\n       then slimmedGlTokens (${slimmedGlTokens.length}) ${JSON.stringify(slimmedGlTokens)}`
        }
    }
    if (prune) {
        const prunedTokens = pruneTokens(highlightedGlTokens);
        if (!prunedTokens.length) {
            return {
                "error":
                    // I think this is saying that the OrigL source quote was found,
                    //  but no GL words were aligned to it!
                    // `PRUNING LEFT NOTHING—NOTHING ALIGNED TO Quote?\n    Search String: ${book} ${cv} '${searchString}' occurrence=${searchOccurrence}\n      from origLTokens (${origLTokens.length}) ${JSON.stringify(origLTokens)}\n       then contentTuplesWithOccurrences (${contentTuplesWithOccurrences.length}) ${contentTuplesWithOccurrences}\n       then slimmedGlTokens (${slimmedGlTokens.length}) ${JSON.stringify(slimmedGlTokens)}\n       then highlightedGlTokens (${highlightedGlTokens.length}) ${highlightedGlTokens}`
                    `NOTHING ALIGNED TO Quote?\n    Search String: ${book} ${cv} '${searchString}' occurrence=${searchOccurrence}`
            }
        }
        return { "data": prunedTokens };
    } else {
        return { "data": highlightedGlTokens };
    }
}


/**
 *
 * @param {Array} dataPairs a list of pairs containing a string (may be empty) and a boolean (true if GL string matched)
 * @description Drops non-matching words and puts an ellipse between non-contiguous matching words
 * @returns a tidyied string with the matching words
 */
const getTidiedData = (dataPairs) => {
    // console.log(`getTidiedData((${dataPairs.length}) ${dataPairs})…`);

    let originalDataString = '';
    let lastItem;
    let inEllipse = false;
    let lastPair = [null, false];
    for (const somePair of dataPairs) { // Each pair contains a string (may be empty) and a boolean (true if GL string matched)
        // console.log("somePair", somePair);
        if (somePair[1]) {// it was a match
            if (lastItem
                && lastItem !== ' ' // Don't want a space before (a matching) space
                && ' ,:.!?)'.indexOf(somePair[0]) === -1 // Don't want a space before (matching) punctuation
                // This next line is very English-centric
                && !(/^\d+$/.test(somePair[0]) && lastItem === ',' && /^\d+$/.test(originalDataString.slice(-2, -1))) // Don't want a space inside something like 75,000
            )
                originalDataString += ' '; // Put a space between words
            if (somePair[0] !== ' '
                || lastItem !== ',' || !/^\d+$/.test(originalDataString.slice(-2, -1)) // Don't want a space inside something like 75,000
            ) {
                originalDataString += somePair[0];
                lastItem = somePair[0]
            }
            inEllipse = false;
        } else if (',:.!?)'.indexOf(somePair[0]) !== -1) { // it's punctuation
            if (lastPair[1]) {// even though somePair[1] is false, this is trailing punctuation that probably/possibly should be included ???
                originalDataString += somePair[0];
                lastItem = somePair[0]
            }
        } else if (somePair[0] !== ' ') { // it's not a match nor punctuation nor a space, so presumably a non-matching word
            if (!inEllipse) originalDataString += '…';
            inEllipse = true;
            lastItem = null;
        }
        lastPair = somePair;
    }
    // TODO: Better if we don't end up with fields like '…,          ,             of the truth …   ,'
    if (originalDataString.indexOf('  ') !== -1 || originalDataString.indexOf(' ,') !== -1) console.log(`Do final tidy of '${originalDataString}'`);
    // NOTE: We need three loops if prune was false
    let tidiedDataString = originalDataString;
    /* Don't seem to need this clean-up now -- we tried to get it right above instead
    for (let n = 0; n < 2; ++n) // Run through this clean-up multiple times to ensure we catch everything
        tidiedDataString = tidiedDataString
            .trim() // remove leading and trailing spaces
            .replace(/^…/, '').replace(/…$/, '') // remove leading and trailing ellipses
            .replace(/^,/, '').replace(/,$/, '') // remove leading and trailing commas
            .replace(/,…/g, '…').replace(/…,/g, '…') // removing hanging comma
            .replace(/ …/g, '…').replace(/… /g, '…') // tidy-up surplus spaces around ellipses
            .replace(/     /g, ' ').replace(/    /g, ' ').replace(/   /g, ' ').replace(/  /g, ' ')
            .replace(/ , /, '').replace(/ ,/, '')
            .replace(/ …/g, '…').replace(/… /g, '…') // tidy-up surplus spaces around ellipses
            .replace(/^…/, '').replace(/…$/, '') // remove leading and trailing ellipses (again)
            .trim(); // remove leading and trailing spaces (again)
            */
    console.assert(tidiedDataString.length, `getTidiedData() Should have some tidiedDataString left from ${dataPairs}!`);
    console.assert(' ,.…'.indexOf(tidiedDataString[0] === -1), `getTidiedData() These characters shouldn't occur at beginning from '${originalDataString}'!`);
    console.assert(' ,.…'.indexOf(tidiedDataString.slice(-1) === -1), `getTidiedData() These characters shouldn't occur at end from '${originalDataString}'!`);
    console.assert(tidiedDataString.indexOf('  ') === -1, `getTidiedData() Should be no more double spaces from '${originalDataString}'!`);
    console.assert(tidiedDataString.indexOf(' ,') === -1, `getTidiedData() Comma should not occur after space from '${originalDataString}'!`);
    console.assert(tidiedDataString.indexOf(' .') === -1, `getTidiedData() Period should not occur after space from '${originalDataString}'!`);
    console.assert(tidiedDataString.indexOf(' :') === -1, `getTidiedData() Colon should not occur after space from '${originalDataString}'!`);
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


getDocuments(pk, testament, book, true, false) //last parameters are "verbose" and "serialize"
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
            // if (tsvRecord.chapter === '3') break;
            // if (tsvRecord.verse === '2') break;
            nRecords++;
            const cv = `${tsvRecord.chapter}:${tsvRecord.verse}`;
            const source = testament === 'OT' ? tokenLookup.uhb : tokenLookup.ugnt;
            // Get the tokens for this BCV
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
                console.assert(!highlighted.error);
                counts.pass++;
                // console.log(`  After gl4Source(): data = (${highlighted.data.length}) ${highlighted.data}`);
                // console.log(`    ${gl}: “${highlightedAsString(highlighted.data)}”`);
                console.log(`${tsvRecord.book}_${cv} ►${tsvRecord.origQuote}◄ “${getTidiedData(highlighted.data)}”`);
            } else {
                console.assert(!highlighted.data);
                counts.fail++;
                console.error(`  Error: ${book} ${cv} ${tsvRecord.id} ${highlighted.error}`);
                console.error(`    Verse words: ${JSON.stringify(sourceTokens.filter(t => t.subType === "wordLike").map(t => t.payload))}\n`);
                // console.error(`    Verse codepoints: ${sourceTokens.filter(t => t.subType === "wordLike").map(t => t.payload).map(s => "|" + Array.from(s).map(c => c.charCodeAt(0).toString(16)))}`);
            }
            // }
        }
        console.log(counts);
    }
    )
