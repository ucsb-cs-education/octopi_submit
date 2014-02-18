#!/usr/bin/env python
from datetime import datetime
from zipfile import ZipFile, ZipInfo
import re
import os
import sys


# TODO: The _newest_ file should be project.oct not the oldest.

DATE_RE = re.compile('\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}')
INPUT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def scratch_file_date(filepath):
    with open(filepath) as fp:
        return datetime.strptime(DATE_RE.findall(fp.read())[-1],
                                 INPUT_DATE_FORMAT)


def output_date_format(data):
    return (data.strftime('%d ').lstrip('0') +
            data.strftime('%B %Y,') +
            data.strftime('%H-').lstrip('0') +
            data.strftime('%M-%S %p').lower())


def prompt(msg):
    return raw_input(msg + ' ').lower() in ('1', 'y')


def make_octx(basename, files):
    filepath = os.path.join(os.path.commonprefix([x[1] for x in files]),
                            basename + '.octx')
    files.sort(reverse=True)
    print('Found:')
    for _, path in files:
        print path

    if not prompt('Do you want to create {}?'.format(filepath)):
        return

    if os.path.isfile(filepath) and \
            not prompt('{} already exists. Do you want to continue?'
                       .format(filepath)):
        return

    first = True

    with ZipFile(filepath, 'w') as zfp:
        for file_dt, path in files:
            if first:
                name = 'project.oct'
                first = False
            else:
                name = 'project({}).oct'.format(output_date_format(file_dt))
            info = ZipInfo(name, file_dt.timetuple())
            with open(path) as fp:
                zfp.writestr(info, fp.read())
    for _, path in files:
        os.unlink(path)


def main():
    basename = ' '.join(sys.argv[1:])
    if not basename:
        print('Usage: .make_octx.py BASENAME')
        return 1

    files = []

    for dirpath, _, filenames, in os.walk('.'):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            if filename.startswith(basename) and filename.endswith('.oct'):
                files.append((scratch_file_date(path), path))

    if not files:
        print('No files found matching: {}'.format(basename))
        return 1

    make_octx(basename, files)

    # Cleanup backup directory
    if os.path.isdir('backup') and not os.listdir('backup'):
        os.rmdir('backup')


if __name__ == '__main__':
    sys.exit(main())
