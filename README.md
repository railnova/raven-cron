Raven-cron : error reporting for cron commands
================================================

Raven-cron is a small command-line wrapper that reports errors to
[Sentry](http://getsentry.com). Reports can happen if the script 
exits with an exit status other than zero, or for any output from
the run command.

Install
-------

`python setup.py install`

Usage
-----

```
usage: raven-cron [-h] [--dsn SENTRY_DSN] [--always] [--logger LOGGER]
                  [--description DESCRIPTION] [--version]
                  cmd [cmd ...]

Wraps commands and reports failing ones to sentry.

positional arguments:
  cmd                   The command to run

optional arguments:
  -h, --help            show this help message and exit
  --dsn SENTRY_DSN      Sentry server address
  --always              Report results to sentry even if the command exits
                        successfully.
  --logger LOGGER
  --description DESCRIPTION
  --version             show program's version number and exit

SENTRY_DSN can also be passed as an environment variable.
```

Example
-------

*Usage with crontab:*

`crontab -e`
```
SENTRY_DSN=https://<your_key>:<your_secret>@app.getsentry.com/<your_project_id>
@reboot raven-cron ./my-process
```

*Usage with mdadm:*

/etc/mdadm/mdadm-raven.sh:
```
#!/bin/bash
#
# mdadm RAID health check
#
# Events are being passed to raven-cron via $1 (events) and $2 (device)
#
# Setting variables to readable values
event=$1
device=$2
export SENTRY_DSN="YOURDSN"
# Check event and then popup a window with appropriate message based on event
if [ $event == "Fail" ]; then
    raven-cron --always --logger mdadm --description "MDADM Array Fail" echo "A failure has been detected on device $device"
fi
    
if [ $event == "FailSpare" ]; then
    raven-cron --always  --logger mdadm --description "MDADM Spare Failure" echo "A failure has been detected on spare device $device"
fi

if [ $event == "DegradedArray" ]; then
    raven-cron --always --logger mdadm --description "MDADM Array Degraded" echo "A Degraded Array has been detected on device $device"
fi

if [ $event == "TestMessage" ]; then
    raven-cron --always --logger mdadm --description "MDADM Array Test" echo "A Test Message has been generated on device $device"
fi
```

/etc/mdadm/mdadm.conf:

```
# mdadm.conf
#
# Please refer to mdadm.conf(5) for information about this file.
#

# by default (built-in), scan all partitions (/proc/partitions) and all
# containers for MD superblocks. alternatively, specify devices to scan, using
# wildcards if desired.
#DEVICE partitions containers

# auto-create devices with Debian standard permissions
CREATE owner=root group=disk mode=0660 auto=yes

# automatically tag new arrays as belonging to the local system
HOMEHOST <system>

# definitions of existing MD arrays
#ARRAY /dev/md/cleveland:0 metadata=1.2 name=cleveland:0 UUID=a4de09d4:e6bca445:34231e0b:23131a8a

# This file was auto-generated on Thu, 26 Jul 2012 18:12:32 -0500
# by mkconf $Id$
PROGRAM /etc/mdadm/mdadm-raven.sh
```

Misc
----

Copyright 2013 to MediaCore Technologies and licensed under the MIT license.

