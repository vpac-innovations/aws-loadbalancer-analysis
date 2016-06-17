#!/usr/bin/env python

import os
import sys
import csv
import argparse
import dateutil.parser
import datetime

import matplotlib.pyplot as plt
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange

import geoip2.database

class LogEntry:
    def __init__(
        self,
        timestamp,
        client_ip,
        backend_ip,
        request_processing_time,
        backend_processing_time,
        response_processing_time,
        request,
        elb_status_code,
        backend_status_code,
        received_bytes,
        sent_bytes,
        user_agent):
        self.timestamp = timestamp
        self.client_ip = client_ip
        self.backend_ip = backend_ip
        self.request_processing_time = request_processing_time
        self.backend_processing_time = backend_processing_time
        self.response_processing_time = response_processing_time
        self.request = request
        self.elb_status_code = elb_status_code
        self.backend_status_code = backend_status_code
        self.received_bytes = received_bytes
        self.sent_bytes = sent_bytes
        self.user_agent = user_agent

    def __str__(self):
        return "timestamp: " + str(self.timestamp) + "\n" + \
               "request: " + self.request + "\n" + \
               "client IP: " + self.client_ip + "\n" + \
               "backend IP: " + self.backend_ip + "\n" + \
               "backend_processing_time: " + str(self.backend_processing_time) + "\n" + \
               "total time: " + str(self.total_time) + "\n" + \
               "elb status code: " + self.elb_status_code + "\n" + \
               "backend status code: " + self.backend_status_code + "\n" + \
               "recieved bytes: " + self.received_bytes + "\n" + \
               "sent bytes: " + self.sent_bytes + "\n" + \
               "user agent: " + self.user_agent

    @property
    def total_time(self):
        return self.request_processing_time + self.backend_processing_time + self.response_processing_time

    @classmethod
    def fromCsvRow(cls, row):
        # refer http://docs.aws.amazon.com/ElasticLoadBalancing/latest/DeveloperGuide/access-log-collection.html#access-log-entry-format
        ts = dateutil.parser.parse(row[0])
        clientip, _ = row[2].split(':')
        backendip, _ = row[3].split(':')
        requestpt = float(row[4])
        backendpt = float(row[5])
        responsept = float(row[6])
        elbstatuscode = row[7]
        backendstatuscode = row[8]
        receivedbytes = row[9]
        sentbytes = row[10]
        request = row[11]
        useragent = row[12]

        return LogEntry(
            ts,
            clientip,
            backendip,
            requestpt,
            backendpt,
            responsept,
            request,
            elbstatuscode,
            backendstatuscode,
            receivedbytes,
            sentbytes,
            useragent)


class LogFileProcessor:

    def __init__(self):
        self.maxRequestProcessingTime = None
        self.maxBackendProcessingTime = None
        self.maxResponseProcessingTime = None
        self.logFileCount = 0
        self.logEntryCount = 0
        self.logEntries = []

    def __str__(self):
        return "Log files read: " + str(self.logFileCount) + "\n" + \
               "Log entries read: " + str(self.logEntryCount) + "\n" + \
               "Max request_processing_time: " + str(self.maxRequestProcessingTime.request_processing_time) + "\n" + \
               "Max backend_processing_time: " + str(self.maxBackendProcessingTime.backend_processing_time) + "\n" + \
               "Max response_processing_time: " + str(self.maxResponseProcessingTime.response_processing_time) + "\n"

    def _testLogEntry(self, log_entry):
        if self.maxRequestProcessingTime == None or self.maxRequestProcessingTime.request_processing_time < log_entry.request_processing_time:
            self.maxRequestProcessingTime = log_entry
        if self.maxBackendProcessingTime == None or self.maxBackendProcessingTime.backend_processing_time < log_entry.backend_processing_time:
            self.maxBackendProcessingTime = log_entry
        if self.maxResponseProcessingTime == None or self.maxResponseProcessingTime.response_processing_time < log_entry.response_processing_time:
            self.maxResponseProcessingTime = log_entry

    def process_logfile(self, logfile):
        logfileentries = []
        with open(logfile, 'rb') as f:
            reader = csv.reader(f, delimiter=' ', quotechar='"')
            for row in reader:
                le = LogEntry.fromCsvRow(row)
                logfileentries.append(le)
                self._testLogEntry(le)

        self.logFileCount += 1
        self.logEntryCount += len(logfileentries)
        return logfileentries

    def process_daydir(self, day_dir, start_date, end_date, year, month, day):

        dirdatetime = datetime.date(year,month,day)
        if not (start_date <= dirdatetime and dirdatetime <= end_date):
            return

        print('processing ' + day_dir)
        directorycontents = os.listdir(day_dir)
        filesonly = [os.path.join(day_dir,afile)
            for afile in directorycontents
            if os.path.isfile(os.path.join(day_dir,afile))]

        for f in filesonly:
            logentries = self.process_logfile(f)
            self.logEntries.extend(logentries)

    def process_monthdir(self, month_dir, start_date, end_date, year, month):
        directorycontents = os.listdir(month_dir)
        directoriesonly = [os.path.join(month_dir,adir)
            for adir in directorycontents
            if not os.path.isfile(os.path.join(month_dir,adir))]

        for adir in directoriesonly:
            _, day = os.path.split(adir)
            self.process_daydir(adir, start_date, end_date, year, month, int(day))

    def process_yeardir(self, year_dir, start_date, end_date, year):
        directorycontents = os.listdir(year_dir)
        directoriesonly = [os.path.join(year_dir,adir)
            for adir in directorycontents
            if not os.path.isfile(os.path.join(year_dir,adir))]

        for adir in directoriesonly:
            _, month = os.path.split(adir)
            self.process_monthdir(adir, start_date, end_date, year, int(month))

    def process_rootdir(self, root_dir, start_date, end_date):
        directorycontents = os.listdir(root_dir)
        directoriesonly = [os.path.join(root_dir,adir)
            for adir in directorycontents
            if not os.path.isfile(os.path.join(root_dir,adir))]

        for adir in directoriesonly:
            _, year = os.path.split(adir)
            self.process_yeardir(adir, start_date, end_date, int(year))


class HelpOnErrorArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def countryIsoCode(ip_address, ip_database):
    response = ip_database.city(ip_address)
    return response.country.iso_code

    ##city code is not always included in returned data
    #return response.city.name

def plotAllRequests(log_entries, start_date, end_date):

    reader = geoip2.database.Reader('GeoLite2-City.mmdb')

    contryDataSeries = {}

    log_entries.sort(key=lambda le: le.timestamp)

    for logentry in log_entries:

        if not (start_date < logentry.timestamp and logentry.timestamp <= end_date):
            continue

        countrycode = countryIsoCode(logentry.client_ip, reader)

        if countrycode in contryDataSeries:
            date,time = contryDataSeries[countrycode]
        else:
            date = []
            time = []
            contryDataSeries[countrycode] = (date, time)

        date.append(logentry.timestamp)
        time.append(logentry.total_time)

        #hacked in filtering of what data gets printed to stdout
        if logentry.total_time > 5 and not ('tabular' in logentry.request):
            print(logentry)
            print(countrycode)
            print('')

    #12 hours between date lables on x-axis
    delta = datetime.timedelta(hours=12)

    colours = ['red', 'green', 'blue', 'orange', 'black', 'cyan', 'magenta', 'yellow', 'purple']

    fig, ax = plt.subplots()

    count = 0
    for code, series in contryDataSeries.iteritems():
        xValues, yValues = series
        colour = colours[count % len(colours)]
        ax.plot_date(xValues, yValues, label=code, color=colour, markeredgecolor='none', markersize=5)

        count += 1

    ax.xaxis.set_major_locator(HourLocator(interval=4))
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M:%S'))
    ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    fig.autofmt_xdate()
    plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)

    plt.show()


if __name__ == "__main__":
    global args

    def handle_sigint(signal, frame):
        print("Received interrupt")
        sys.exit(0)

    parser = HelpOnErrorArgumentParser(
        description='Tool for processing Load Balancer logs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-d", "--log-dir", help="Root directory of logs (eg; should contain a folder 2016)",
        required=True)
    parser.add_argument(
        "-sd", "--start-date", help="In ISO8601 format (eg; 2016-06-01T21:49:0.0Z)")
    parser.add_argument(
        "-ed", "--end-date", help="In ISO8601 format (eg; 2016-06-10T21:49:0.0Z), must be greater than start date")

    args = parser.parse_args()

    start_date = datetime.datetime.min
    end_date = datetime.datetime.max
    if args.start_date:
        start_date = dateutil.parser.parse(args.start_date)
    if args.end_date:
        end_date = dateutil.parser.parse(args.end_date)

    assert start_date < end_date, "end date must be greater than start date"

    logprocessor = LogFileProcessor()
    logprocessor.process_rootdir(os.path.relpath(args.log_dir), start_date.date(), end_date.date())

    print(logprocessor)

    plotAllRequests(logprocessor.logEntries, start_date, end_date)
