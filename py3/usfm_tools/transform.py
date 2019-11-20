import os
import logging

from . import singlehtmlRenderer



class UsfmTransform:

    savedCWD = ''
    __logger = logging.getLogger('usfm_tools')

    # @staticmethod
    # def runscriptold(c, prefix=''):
    #     UsfmTransform.__logger.info(prefix + ':: ' + c)
    #     pp = Popen(c, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    #     for ln in pp.stdout:
    #         UsfmTransform.__logger.info(prefix + ln[:-1])

    # @staticmethod
    # def runscript(c, prefix='', repeatFilter=''):
    #     UsfmTransform.__logger.info(prefix + ':: ' + c)
    #     pp = Popen([c], shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    #     (result, stderrdata) = pp.communicate()
    #     UsfmTransform.__logger.info(result)
    #     UsfmTransform.__logger.info(stderrdata)
    #     if not repeatFilter == '' and not stderrdata.find(repeatFilter) == -1:
    #         UsfmTransform.runscript(c, prefix, repeatFilter)

    # @staticmethod
    # def setup():
    #     UsfmTransform.__logger.debug("transform.setup() …")
    #     c = """
    #     cd support/thirdparty
    #     rm -rf context
    #     mkdir context
    #     cd context
    #     curl -o first-setup.sh http://minimals.contextgarden.net/setup/first-setup.sh
    #     sh ./first-setup.sh
    #     . ./tex/setuptex
    #     cd ..
    #     curl -o usfm2osis.pl http://crosswire.org/ftpmirror/pub/sword/utils/perl/usfm2osis.pl
    #     """
    #     UsfmTransform.runscript(c)

    # @staticmethod
    # def buildLout(usfmDir, builtDir, buildName):
    #     UsfmTransform.__logger.info('transform: building Lout…')

    #     # Prepare
    #     UsfmTransform.__logger.info('Clean working dir')
    #     UsfmTransform.runscript('rm "' + builtDir + '/working/lout/*"', '       ')

    #     # Convert to Lout
    #     UsfmTransform.__logger.info('Converting to Lout')
    #     UsfmTransform.ensureOutputDir(builtDir + '/working/lout')
    #     c = loutRenderer.LoutRenderer(usfmDir, builtDir + '/working/lout/' + buildName + '.lout')
    #     c.render()

    #     # Run Lout
    #     UsfmTransform.__logger.info('Copying support files')
    #     UsfmTransform.runscript('cp support/lout/oebbook working/lout', '       ')
    #     UsfmTransform.__logger.info('Running Lout')
    #     UsfmTransform.runscript('cd "' + builtDir + '/working/lout"; lout "./' + buildName + '.lout" > "' + buildName +
    #                             '.ps"', '       ',
    #                             repeatFilter='unresolved cross reference')
    #     UsfmTransform.__logger.info('Running ps2pdf')
    #     UsfmTransform.runscript(
    #         'cd "' + builtDir + '/working/lout"; ps2pdf -dDEVICEWIDTHPOINTS=432 -dDEVICEHEIGHTPOINTS=648 "' +
    #         buildName + '.ps" "' + buildName + '.pdf" ',
    #         '       ')
    #     UsfmTransform.__logger.info('Copying into builtDir')
    #     UsfmTransform.runscript('cp "' + builtDir + '/working/lout/' + buildName + '.pdf" "' + builtDir + '/' +
    #                             buildName + '.pdf" ', '       ')

    # @staticmethod
    # def buildConTeXt(usfmDir, builtDir, buildName):
    #     UsfmTransform.__logger.info("transform: building PDF via ConTeXt…")

    #     # Convert to ConTeXt
    #     UsfmTransform.__logger.info("Converting to ConTeXt…")
    #     # c = texise.TransformToContext()
    #     # c.setupAndRun(usfmDir, 'working/tex', buildName)
    #     UsfmTransform.ensureOutputDir(builtDir + '/working/tex')
    #     UsfmTransform.ensureOutputDir(builtDir + '/working/tex-working')
    #     c = contextRenderer.ConTeXtRenderer(usfmDir, builtDir + '/working/tex/bible.tex')
    #     c.render()

    # @staticmethod
    # def buildWeb(usfmDir, builtDir, buildName):
    #     # Convert to HTML
    #     UsfmTransform.__logger.info("transform: building Web HTML…")
    #     UsfmTransform.ensureOutputDir(builtDir + '/' + buildName + '_html')
    #     c = htmlRenderer.HTMLRenderer(usfmDir, builtDir + '/' + buildName + '_html')
    #     c.render()

    @staticmethod
    def buildSingleHtml(usfmDir, builtDir, buildName):
        # UsfmTransform.__logger.debug("transform.buildSingleHtml( … ) …")
        # Convert to HTML
        UsfmTransform.__logger.debug("transform: building Single Page HTML…")
        UsfmTransform.ensureOutputDir(builtDir)
        c = singlehtmlRenderer.SingleHTMLRenderer(usfmDir, builtDir + '/' + buildName + '.html')
        warning_list = c.render()
        return warning_list

    # @staticmethod
    # def buildCSV(usfmDir, builtDir, buildName):
    #     # Convert to CSV
    #     UsfmTransform.__logger.info("transform: building CSV…")
    #     UsfmTransform.ensureOutputDir(builtDir)
    #     c = csvRenderer.CSVRenderer(usfmDir, builtDir + '/' + buildName + '.csv')
    #     c.render()

    # @staticmethod
    # def buildReader(usfmDir, builtDir, buildName):
    #     # Convert to HTML for online reader
    #     UsfmTransform.__logger.info("transform: building for Reader…")
    #     UsfmTransform.ensureOutputDir(builtDir + 'en_oeb')
    #     c = readerise.TransformForReader()
    #     c.setupAndRun(usfmDir, builtDir + 'en_oeb')

    # @staticmethod
    # def buildMarkdown(usfmDir, builtDir, buildName):
    #     # Convert to Markdown for Pandoc
    #     UsfmTransform.__logger.info('transform: building for Markdown…')
    #     UsfmTransform.ensureOutputDir(builtDir)
    #     c = mdRenderer.MarkdownRenderer(usfmDir, builtDir + '/' + buildName + '.md')
    #     c.render()

    # @staticmethod
    # def buildASCII(usfmDir, builtDir, buildName):
    #     # Convert to ASCII
    #     UsfmTransform.__logger.info('transform: building for ASCII…')
    #     UsfmTransform.ensureOutputDir(builtDir)
    #     c = asciiRenderer.ASCIIRenderer(usfmDir, builtDir + '/' + buildName + '.txt')
    #     c.render()

    # @staticmethod
    # def buildUSX(usfmDir, builtDir, buildName, byBookFlag):
    #     # Convert to USX
    #     UsfmTransform.__logger.info('transform: building for USX…')
    #     UsfmTransform.ensureOutputDir(builtDir)
    #     c = usxRenderer.USXRenderer(usfmDir, builtDir + '/', buildName, byBookFlag)
    #     c.render()

    # @staticmethod
    # def buildMediawiki(usfmDir, builtDir, buildName):
    #     # Convert to MediaWiki format for Door43
    #     UsfmTransform.__logger.info('transform: building for Mediawiki…')
    #     # Check output directory
    #     UsfmTransform.ensureOutputDir(builtDir + '/mediawiki')
    #     mediawikiPrinter.Transform().setupAndRun(usfmDir, builtDir + '/mediawiki')

    @staticmethod
    def ensureOutputDir(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    # @staticmethod
    # def saveCWD():
    #     global savedCWD
    #     savedCWD = os.getcwd()
    #     root_dir_of_tools = os.path.dirname(os.path.abspath(__file__))
    #     os.chdir(root_dir_of_tools)

    # @staticmethod
    # def restoreCWD(): os.chdir(savedCWD)
