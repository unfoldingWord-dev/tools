const Axios = require("axios");
const YAML = require('js-yaml-parser');

const {readTsv} = require('uw-proskomma/src/utils/tsv');
// const {getDocuments} = require('uw-proskomma/src/utils/download');
const {doAlignmentQuery} = require('uw-proskomma/src/utils/query');
const {gl4Source} = require('uw-proskomma/src/utils/search');
const {UWProskomma} = require('uw-proskomma/src/index');

// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/download.js May 2021
const getDocuments = async (pk, book, verbose, serialize) => {
    const baseURLs = [
        ["unfoldingWord", "hbo", "uhb", "https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master"],
        ["unfoldingWord", "grc", "ugnt", "https://git.door43.org/unfoldingWord/el-x-koine_ugnt/raw/branch/master"],
        // ["unfoldingWord", "en", "ust", "https://git.door43.org/unfoldingWord/en_ust/raw/branch/master"],
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
            {method: "get", "url": `${baseURL}/manifest.yaml`}
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
                                {method: "get", "url": `${baseURL}/${bookPath}`}
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


// Adapted from https://github.com/unfoldingWord-box3/uw-proskomma/blob/main/src/utils/render.js May 2021
const highlightedAsString = highlighted =>
    highlighted
        // .map(tp => tp[1] ? tp[0].toUpperCase() : tp[0])
        .map(tp => tp[0]) // Don't want UPPERCASE
        .join("")
        .trim();


// Start of main code
const pk = new UWProskomma();
const args = process.argv.slice(2);
const tsvPath = args[0]; // Path to TSV9 TN
const book = tsvPath.split("/").reverse()[0].split(".")[0].split("-")[1];
// const prune = (args[1] === "prune") || false;
const prune = true; // only return the matching quote -- not the entire verse text


getDocuments(pk, book, true)
    .then(async () => {
            // Query Proskomma which now contains the books
            // Returns the tokens for each verse, accessible by
            // [abbr][book][chapter:verse]
            const tokenLookup = await doAlignmentQuery(pk);
            // Iterate over TSV records
            let nRecords = 0;
            let counts = {pass:0, fail:0};
            for (const tsvRecord of readTsv(tsvPath)) {
                nRecords++;
                const cv = `${tsvRecord.chapter}:${tsvRecord.verse}`;
                // console.log(`  ${tsvRecord.book} ${cv}`);
                // console.log(`    Search string: ${tsvRecord.origQuote}`);
                // Iterate over GLs
                // for (const gl of ["ult", "ust"]) {
                const gl = 'ult';
                    // Pick the right source for the book (inelegant but works)
                    const source = tokenLookup.uhb || tokenLookup.ugnt;
                    // Get the tokens for BCV
                    const sourceTokens = source[book][cv];
                    const glTokens = tokenLookup[gl][book][cv];
                    // Do the alignment
                    const highlighted = gl4Source(
                        book,
                        cv,
                        sourceTokens,
                        glTokens,
                        tsvRecord.origQuote,
                        prune
                    );
                    // Returned object has either "data" or "error"
                    if ("data" in highlighted) {
                        counts.pass++;
                        // console.log(`    ${gl}: “${highlightedAsString(highlighted.data)}”`);
                        console.log(`${tsvRecord.book}_${cv} ►${tsvRecord.origQuote}◄ “${highlightedAsString(highlighted.data)}”`);
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
