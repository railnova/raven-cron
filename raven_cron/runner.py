from getpass import getuser
from os import getenv, path, SEEK_END
from raven import Client
from subprocess import call
from tempfile import TemporaryFile
from argparse import ArgumentParser
import argparse
from sys import argv, stderr
from time import time
from .version import VERSION

MAX_MESSAGE_SIZE = 4096

parser = ArgumentParser(
    description='Wraps commands and reports failing ones to sentry.',
    epilog='SENTRY_DSN can also be passed as an environment variable.',
)
parser.add_argument(
    '--dsn',
    metavar='SENTRY_DSN',
    default=getenv('SENTRY_DSN'),
    help='Sentry server address',
)
parser.add_argument(
    '--always',
    action='store_true',
    help='Report results to sentry even if the command exits successfully.'
)
parser.add_argument(
    '--logger',
    default='cron'
)
parser.add_argument(
    '--description',
    default=None
)
parser.add_argument(
    '--version',
    action='version',
    version=VERSION,
)
parser.add_argument(
    'cmd',
    nargs=argparse.REMAINDER,
    help='The command to run',
)

def update_dsn(opts):
    """Update the Sentry DSN stored in local configs

    It's assumed that the file contains a DSN endpoint like this:
    https://public_key:secret_key@app.getsentry.com/project_id

    It could easily be extended to override all settings if there
    were more use cases.
    """

    homedir = path.expanduser('~%s' % getuser())
    home_conf_file = path.join(homedir, '.raven-cron')
    system_conf_file = '/etc/raven-cron.conf'

    conf_precedence = [home_conf_file, system_conf_file]
    for conf_file in conf_precedence:
        if path.exists(conf_file):
            with open(conf_file, "r") as conf:
                opts.dsn = conf.read().rstrip()
            return

def run(args=argv[1:]):
    opts = parser.parse_args(args)

    # Command line takes precendence, otherwise check for local configs
    if not opts.dsn:
        update_dsn(opts)
    runner = CommandReporter(**vars(opts))
    runner.run()

class CommandReporter(object):
    def __init__(self, cmd, dsn, always, logger, description):

        self.dsn = dsn
        self.command = " ".join(cmd)
        self.always = always
        self.client = None
        self.logger = logger
        self.description = description

    def run(self):
        buf = TemporaryFile()
        start = time()

        exit_status = call(self.command, stdout=buf, stderr=buf, shell=True)
        
        if exit_status > 0 or self.always == True:
            elapsed = int((time() - start) * 1000)
            self.report_fail(exit_status, buf, elapsed)

        buf.close()
        
    def report_fail(self, exit_status, buf, elapsed):
        if self.dsn is None:
            print >>stderr, "No DSN for raven-cron configured, cannot report failure of script:", self.command
            buf.seek(0)
            print >>stderr, buf.read()
            return

        # Hack to get the file size since the tempfile doesn't exist anymore
        buf.seek(0, SEEK_END)
        file_size = buf.tell()
        if file_size < MAX_MESSAGE_SIZE:
            buf.seek(0)
            last_lines = buf.read()
        else:
            buf.seek(-(MAX_MESSAGE_SIZE-3), SEEK_END)
            last_lines = '...' + buf.read()

        if self.description:
            message=self.description
        elif exit_status != 0:
            message="Command \"%s\" failed" % (self.command,)
        else:
            message="Command \"%s\" report" % (self.command,)

        if self.client is None:
            self.client = Client(dsn=self.dsn)

        self.client.captureMessage(
            message,
            data={
                'logger': self.logger,
            },
            extra={
                'command': self.command,
                'exit_status': exit_status,
                'last_lines': last_lines,
            },
            time_spent=elapsed
        )

