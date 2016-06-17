## AWS Load Balancer detailed logs app
Quick tool to analyse AWS Load Balancer logs

## Installation
Install dependancies

    pip install -r requirements.txt

Download IP location database, it is assumed this is done in the same directory as `processlogs.py`.

    wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
    gzip -d GeoLite2-City.mmdb.gz

## Downloading AWS log data
Install AWS command line client

    sudo pip install awscli

Configure AWS credentials. This will ask for access key, and secret access key. These are not your username and password.

    aws configure

Download AWS og data. **Note:** before running, ensure current dir is empty.

    aws s3 sync s3://name-of-log-bucket-1 .

## Running the app
```
$ ./processlogs.py -h
usage: processlogs.py [-h] -d LOG_DIR [-sd START_DATE] [-ed END_DATE]

Tool for processing Load Balancer logs

optional arguments:
  -h, --help            show this help message and exit
  -d LOG_DIR, --log-dir LOG_DIR
                        Root directory of logs (eg; should contain a folder
                        2016) (default: None)
  -sd START_DATE, --start-date START_DATE
                        In ISO8601 format (eg; 2016-06-01T21:49:0.0Z)
                        (default: None)
  -ed END_DATE, --end-date END_DATE
                        In ISO8601 format (eg; 2016-06-10T21:49:0.0Z), must be
                        greater than start date (default: None)
```

Example command lines:

    ./processlogs.py -d ../loadbalancerlogs

    ./processlogs.py -d ../loadbalancerlogs -sd 2016-06-15T21:49:0.0Z -ed 2016-06-15T21:55:0.0Z
