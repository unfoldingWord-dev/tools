#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#

import os
import glob
import json
import gzip
import re
import httplib


class GoogleConnection(httplib.HTTPConnection):
    """
    This class is here to enable with...as functionality for the HHTPConnection
    """

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exception_type, exception_val, trace):
        self.close()


class ProcessApiLog:
    def __init__(self):
        pass

    # This is the name of the current log file, and the prefix for log file backups
    logFileRoot = '/var/log/nginx/api.unfoldingword.org.log'

    settingsFile = os.path.join(os.path.dirname(__file__), 'lastSentToGA.json')
    hostName = 'api.unfoldingword.org'
    # propertyID = 'UA-60106521-2'  # api.unfoldingword.org
    propertyID = 'UA-37389677-2'  # prayer.hoppenings.net

    # initialize last sent date
    lastSent = '20150322'
    currentSent = ''

    def do_it(self):

        # Example: api.unfoldingword.org.log-20150314.gz
        logfiles = glob.glob(self.logFileRoot + '-*.gz')
        processedcount = 0

        self.get_last_sent()

        for logFile in logfiles:

            filedate = self.get_file_date(logFile)

            if filedate > self.lastSent:
                processedcount += self.process_this_file(logFile)

            if filedate > self.currentSent:
                self.currentSent = filedate

        if processedcount == 0:
            print 'Finished. No log files processed'
        elif processedcount == 1:
            print 'Finished. Processed 1 log file.'
        else:
            print 'Finished. Processed ' + str(processedcount) + ' log files.'

    def get_last_sent(self):

        if os.path.exists(self.settingsFile):

            data = {}

            try:
                with open(self.settingsFile) as settings:
                    data = json.load(settings)

            except ValueError:
                print self.settingsFile + ' is not a valid json file'

            if data:
                if 'lastSent' in data:
                    self.lastSent = data['lastSent']

    @staticmethod
    def get_file_date(logfile):
        return logfile[-11:-3]

    @staticmethod
    def process_this_file(logfile):

        if not os.path.exists(logfile):
            return 0

        # regex for parsing the log entries
        # values: [0]ip_address [1]unk [2]remote_user
        # [3]timestamp [4]request [5]status [6]bytes_sent
        # [7]referer [8]user_agent [9]forwarded_for
        regex = '([\d\.]+) (.*?) (.*?) \[(.*?)\] "(.*?)" (.*?) (.*?) "(.*?)" "(.*?)" "(.*?)"'

        # open the archive and read each line
        with gzip.GzipFile(logfile) as archive:
            for line in archive:

                # skip lines produced by check_http
                if '"check_http' in line:
                    continue

                # skip favicon
                if 'favicon.ico' in line:
                    continue

                # split the line into fields
                fields = re.match(regex, line.rstrip()).groups()

                # skip bots
                if 'bot' in fields[8]:
                    continue

                if 'https' not in line:
                    continue

                # print line.rstrip()
                requestparts = fields[4].split(' ')
                ProcessApiLog.send_hit_to_ga(requestparts[1])

        # increment the count when finished
        return 1

    @staticmethod
    def send_hit_to_ga(page):

        with GoogleConnection('www.google-analytics.com') as connection:

            payload = ['v=1', 'tid=' + ProcessApiLog.propertyID, 'cid=555', 't=pageview',
                       'dh=' + ProcessApiLog.hostName, 'dp=' + page, 'dt=test']
            connection.request('POST', '/collect', '&'.join(payload))
            response = connection.getresponse()

            # check the status
            if response.status != 200:
                print 'Error ' + str(response.status) + ': ' + response.reason


if __name__ == '__main__':
    lp = ProcessApiLog()
    lp.do_it()