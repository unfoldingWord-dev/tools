#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
# Copyright (c) 2015 unfoldingWord
# http://creativecommons.org/licenses/MIT/
# See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#
# References:
#    https://developers.google.com/analytics/devguides/collection/protocol/v1/reference
#    https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide
#

import os
import re
import httplib
import logging
import time
import subprocess
import select
import atexit
import traceback

# enable logging for this script
logging.basicConfig(filename='event.log', level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info('Begin tailing api.unfoldingword.org log for Google Analytics.')


# stop the script by deleting this pid file
pidFile = 'log_to_ga.pid'
with open(pidFile, 'w') as f:
    f.write(str(os.getpid()))


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
propertyID = 'UA-60106521-2'  # api.unfoldingword.org


@atexit.register
def exit_logger():
    print 'Exiting.'
    # attempt to log when the script stops, only works if not stopped using kill
    logging.info('Stopped tailing api.unfoldingword.org log for Google Analytics.')
    logging.shutdown()


def process_this_line(logline):

    # skip lines produced by check_http
    if '"check_http' in logline:
        return

    # skip favicon
    if 'favicon.ico' in logline:
        return

    print logline.rstrip()

    # regex for parsing the log entries
    # values: [0]ip_address [1]unknown [2]remote_user
    #         [3]timestamp [4]request [5]status [6]bytes_sent
    #         [7]referer [8]user_agent [9]forwarded_for
    regex = '([\d\.]+) (.*?) (.*?) \[(.*?)\] "(.*?)" (.*?) (.*?) "(.*?)" "(.*?)" "(.*?)"'

    # split the line into fields
    fields = re.match(regex, logline.rstrip()).groups()

    # skip bots
    if 'bot' in fields[8]:
        return

    requestparts = fields[4].split(' ')
    # send_hit_to_ga(requestparts[1], timestamp)

    # HTTP_PORT or HTTPS_PORT
    with GoogleConnection('ssl.google-analytics.com', httplib.HTTPS_PORT) as connection:

        payload = ['v=1', 'tid=' + propertyID, 'cid=555', 't=pageview', 'dh=' + hostName,
                   'dp=' + requestparts[1]]

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

    # Explanation: -n sets the number of lines to read immediately when starting.
    #              -F sets the file name to tail, and being upper case it tells tail to
    #                 retry opening the file if it fails, like when the log file is rotated.
    f = subprocess.Popen(['tail', '-n', '0', '-F', logFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    print 'Tailing ' + logFile + '...'

    running = True

    while running:

        # exit if pid file has been deleted
        if not os.path.isfile(pidFile):
            running = False
            continue

        # noinspection PyBroadException
        try:
            if p.poll(1):
                line = f.stdout.readline()
                process_this_line(line)
                time.sleep(1)

        except:
            logging.error(traceback.format_exc())
