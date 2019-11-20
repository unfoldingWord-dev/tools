# Setup list of patches and books to use
#

import os
import logging

__logger = logging.getLogger('usfm_tools')

bookKeys = {
    'FRT': '000',
    'GEN': '001',
    'EXO': '002',
    'LEV': '003',
    'NUM': '004',
    'DEU': '005',
    'JOS': '006',
    'JDG': '007',
    'RUT': '008',
    '1SA': '009',
    '2SA': '010',
    '1KI': '011',
    '2KI': '012',
    '1CH': '013',
    '2CH': '014',
    'EZR': '015',
    'NEH': '016',
    'EST': '017',
    'JOB': '018',
    'PSA': '019',
    'PRO': '020',
    'ECC': '021',
    'SNG': '022',
    'ISA': '023',
    'JER': '024',
    'LAM': '025',
    'EZK': '026',
    'DAN': '027',
    'HOS': '028',
    'JOL': '029',
    'AMO': '030',
    'OBA': '031',
    'JON': '032',
    'MIC': '033',
    'NAM': '034',
    'HAB': '035',
    'ZEP': '036',
    'HAG': '037',
    'ZEC': '038',
    'MAL': '039',
    'MAT': '041',
    'MRK': '042',
    'LUK': '043',
    'JHN': '044',
    'ACT': '045',
    'ROM': '046',
    '1CO': '047',
    '2CO': '048',
    'GAL': '049',
    'EPH': '050',
    'PHP': '051',
    'COL': '052',
    '1TH': '053',
    '2TH': '054',
    '1TI': '055',
    '2TI': '056',
    'TIT': '057',
    'PHM': '058',
    'HEB': '059',
    'JAS': '060',
    '1PE': '061',
    '2PE': '062',
    '1JN': '063',
    '2JN': '064',
    '3JN': '065',
    'JUD': '066',
    'REV': '067'
}

silNames = [
    'FRT',
    'GEN',
    'EXO',
    'LEV',
    'NUM',
    'DEU',
    'JOS',
    'JDG',
    'RUT',
    '1SA',
    '2SA',
    '1KI',
    '2KI',
    '1CH',
    '2CH',
    'EZR',
    'NEH',
    'EST',
    'JOB',
    'PSA',
    'PRO',
    'ECC',
    'SNG',
    'ISA',
    'JER',
    'LAM',
    'EZK',
    'DAN',
    'HOS',
    'JOL',
    'AMO',
    'OBA',
    'JON',
    'MIC',
    'NAM',
    'HAB',
    'ZEP',
    'HAG',
    'ZEC',
    'MAL',
    'MAT',
    'MRK',
    'LUK',
    'JHN',
    'ACT',
    'ROM',
    '1CO',
    '2CO',
    'GAL',
    'EPH',
    'PHP',
    'COL',
    '1TH',
    '2TH',
    '1TI',
    '2TI',
    'TIT',
    'PHM',
    'HEB',
    'JAS',
    '1PE',
    '2PE',
    '1JN',
    '2JN',
    '3JN',
    'JUD',
    'REV']

silNamesNTPsalms = [
    'MAT',
    'MRK',
    'LUK',
    'JHN',
    'ACT',
    'ROM',
    '1CO',
    '2CO',
    'GAL',
    'EPH',
    'PHP',
    'COL',
    '1TH',
    '2TH',
    '1TI',
    '2TI',
    'TIT',
    'PHM',
    'HEB',
    'JAS',
    '1PE',
    '2PE',
    '1JN',
    '2JN',
    '3JN',
    'JUD',
    'REV',
    'PSA']

readerNames = [
    'Gen',
    'Exod',
    'Lev',
    'Num',
    'Deut',
    'Josh',
    'Judg',
    'Ruth',
    '1Sam',
    '2Sam',
    '1Kgs',
    '2Kgs',
    '1Chr',
    '2Chr',
    'Ezra',
    'Nehm',
    'Esth',
    'Job',
    'Ps',
    'Prov',
    'Eccl',
    'Song',
    'Isa',
    'Jer',
    'Lam',
    'Ezek',
    'Dan',
    'Hos',
    'Joel',
    'Amos',
    'Obad',
    'Jonah',
    'Mic',
    'Nah',
    'Hab',
    'Zeph',
    'Hag',
    'Zech',
    'Mal',
    'Matt',
    'Mark',
    'Luke',
    'John',
    'Acts',
    'Rom',
    '1Cor',
    '2Cor',
    'Gal',
    'Eph',
    'Phil',
    'Col',
    '1Thess',
    '2Thess',
    '1Tim',
    '2Tim',
    'Titus',
    'Phlm',
    'Heb',
    'Jas',
    '1Pet',
    '2Pet',
    '1John',
    '2John',
    '3John',
    'Jude',
    'Rev']

bookNames = [
    'Genesis',
    'Exodus',
    'Leviticus',
    'Numbers',
    'Deuteronomy',
    'Joshua',
    'Judges',
    'Ruth',
    '1 Samuel',
    '2 Samuel',
    '1 Kings',
    '2 Kings',
    '1 Chronicles',
    '2 Chronicles',
    'Ezra',
    'Nehemiah',
    'Esther',
    'Job',
    'Psalms',
    'Proverbs',
    'Ecclesiastes',
    'Song of Solomon',
    'Isaiah',
    'Jeremiah',
    'Lamentations',
    'Ezekiel',
    'Daniel',
    'Hosea',
    'Joel',
    'Amos',
    'Obadiah',
    'Jonah',
    'Micah',
    'Nahum',
    'Habakkuk',
    'Zephaniah',
    'Haggai',
    'Zechariah',
    'Malachi',
    'Matthew',
    'Mark',
    'Luke',
    'John',
    'Acts',
    'Romans',
    '1 Corinthians',
    '2 Corinthians',
    'Galatians',
    'Ephesians',
    'Philippians',
    'Colossians',
    '1 Thessalonians',
    '2 Thessalonians',
    '1 Timothy',
    '2 Timothy',
    'Titus',
    'Philemon',
    'Hebrews',
    'James',
    '1 Peter',
    '2 Peter',
    '1 John',
    '2 John',
    '3 John',
    'Jude',
    'Revelation']

# books = bookNames


# # noinspection PyPep8Naming
# def readerName(num):
#     return readerNames[int(num) - 1]


# # noinspection PyPep8Naming
# def fullName(num):
#     return bookNames[int(num) - 1]


# # noinspection PyPep8Naming,PyUnusedLocal
# def nextChapter(bookNumber, chapterNumber):
#     return 1, 1


# # noinspection PyPep8Naming
# def previousChapter(bookNumber, chapterNumber):
#     if chapterNumber > 1:
#         return bookNumber, chapterNumber - 1
#     else:
#         if bookNumber > 1:
#             return bookNumber - 1, 50  # bookSize[bookNumber -1])
#         else:
#             return 1, 1


# noinspection PyPep8Naming
def bookKeyForIdValue(book_id):
    e = book_id.find(' ')
    i = book_id if e == -1 else book_id[:e]
    return bookKeys[i]


# noinspection PyPep8Naming
def bookID(usfm):
    s = usfm.find('\\id ') + 4
    e = usfm.find(' ', s)
    e2 = usfm.find('\n', s)
    e = e if e < e2 else e2
    return usfm[s:e].strip()


# # noinspection PyPep8Naming
# def bookName(usfm):
#     book_id = bookID(usfm)
#     index = silNames.index(book_id)
#     return bookNames[index]


# noinspection PyPep8Naming
def loadBooks(path):
    loaded_books = {}
    dirList = os.listdir(path)
    __logger.debug(f"Loading all USFM book files from {path} …")
    for fname in dirList:

        full_file_name = os.path.join(path, fname)
        if not os.path.isfile(full_file_name):
            continue

        if fname[-4:].lower() in ['.pdf', '.sig']:
            continue

        # noinspection PyBroadException
        try:
            f = open(full_file_name, 'rt')
            usfm = f.read().lstrip()
            if usfm[:4] == r'\id ' and usfm[4:7] in silNames:
                # print('     Loaded ' + fname + ' as ' + usfm[4:7])
                loaded_books[bookID(usfm)] = usfm
                f.close()
            else:
                __logger.info('Ignored ' + fname)
        except:
            __logger.warning(f"loadBooks couldn't open '{fname}'")
    # __logger.debug(f"Finished loading {len(loaded_books)} USFM book(s).")
    return loaded_books


# noinspection PyPep8Naming
def orderFor(booksDict):
    order = silNames
    if 'PSA' in booksDict and 'GEN' not in booksDict and 'MAT' in booksDict:
        # This is a big hack. When doing Psalms + NT, put Psalms last
        order = silNamesNTPsalms
    a = []
    for book_name in order:
        if book_name in booksDict:
            a.append(booksDict[book_name])
    return a
