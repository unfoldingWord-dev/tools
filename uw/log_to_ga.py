#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#

import calendar
import re
import httplib
import logging
import time
import subprocess
import select


# enable logging for this script
logging.basicConfig(filename='event.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info('Begin sending api.unfoldingword.org log to Google Analytics.')


class GoogleConnection(httplib.HTTPConnection):
    """
    This class is here to enable with...as functionality for the HHTPConnection
    """

    def __enter__(self):
        return self

    # noinspection PyUnusedLocal
    def __exit__(self, exception_type, exception_val, trace):
        self.close()


# This is the name of the current log file, and the prefix for log file backups
logFile = '/var/log/nginx/api.unfoldingword.org.log'
hostName = 'api.unfoldingword.org'
# propertyID = 'UA-60106521-2'  # api.unfoldingword.org
propertyID = 'UA-37389677-2'  # prayer.hoppenings.net


def process_this_line(logline):

    # regex for parsing the log entries
    # values: [0]ip_address [1]unk [2]remote_user
    # [3]timestamp [4]request [5]status [6]bytes_sent
    # [7]referer [8]user_agent [9]forwarded_for
    regex = '([\d\.]+) (.*?) (.*?) \[(.*?)\] "(.*?)" (.*?) (.*?) "(.*?)" "(.*?)" "(.*?)"'

    # skip lines produced by check_http
    if '"check_http' in logline:
        return

    # skip favicon
    if 'favicon.ico' in logline:
        return

    # split the line into fields
    fields = re.match(regex, logline.rstrip()).groups()

    # skip bots
    if 'bot' in fields[8]:
        return

    # Timestamp example: 21/Mar/2015:04:20:18 +0000
    timestamp = time.strptime(fields[3], '%d/%b/%Y:%H:%M:%S +0000')

    requestparts = fields[4].split(' ')
    # send_hit_to_ga(requestparts[1], timestamp)

    then = calendar.timegm(timestamp)
    queuetime = (time.time() - then) * 1000

    with GoogleConnection('www.google-analytics.com') as connection:
        payload = ['v=1', 'tid=' + propertyID, 'cid=555', 't=pageview', 'dh=' + hostName,
                   'dp=' + requestparts[1], 'qt=' + str(queuetime)]
        connection.request('POST', '/collect', '&'.join(payload))
        response = connection.getresponse()

        # check the status
        if response.status != 200:
            print 'Error ' + str(response.status) + ': ' + response.reason
            logging.error('Bad HTTP request,  ' + str(response.status) + ': ' + response.reason)

    return


if __name__ == '__main__':

    # This is the name of the current log file
    logFile = '/var/log/nginx/api.unfoldingword.org.log'

    f = subprocess.Popen(['tail', '-F', logFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    while True:
        if p.poll(1):
            line = f.stdout.readline()
            process_this_line(line)
            print line
        time.sleep(1)