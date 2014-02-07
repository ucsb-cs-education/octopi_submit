#!/usr/bin/env python
from collections import defaultdict
from zipfile import ZipFile
import json
import os
import re
import shutil
import sys


DATE_RE = re.compile('\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}')
ZIP_CRCS = {}


def analyze_projects(base_path):
    projects = defaultdict(lambda: defaultdict(list))
    for path, dirs, filenames in os.walk(base_path):
        if 'owners.json' not in filenames:
            continue
        project = path.split('/')[-2]
        result = {'.oct': None, '.zip': []}

        for filename in filenames:
            fullpath = os.path.join(path, filename)
            if os.path.islink(fullpath):
                continue
            ext = os.path.splitext(filename)[1]
            assert ext != '.octx'
            if ext == '.zip':
                result[ext].append(fullpath)
            elif ext == '.oct':
                assert not result[ext]
                result[ext] = fullpath

        if not any(result.values()):  # Does not contain octopi files
            continue

        with open(os.path.join(path, 'owners.json')) as fp:
            owners = json.load(fp)

        for owner in owners:
            projects[project][owner].append(result)

    return projects


def scratch_file_date(fp):
    return DATE_RE.findall(fp.read())[-1]


def copy_scratch_file(path, fp, file_date, crc=None):
    filepath = os.path.join(path, file_date + '.oct')
    if crc:
        if ZIP_CRCS.get(filepath) == crc:
            return  # We've already got this file
        ZIP_CRCS[filepath] = crc

    if os.path.isfile(filepath):
        print 'file already exists'
        return
    with open(filepath, 'w') as dst_fp:
        shutil.copyfileobj(fp, dst_fp)


def process_group(project, user, submissions):
    path = os.path.join('data', project, user)
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != 17:
            raise

    for sub in submissions:
        if not sub['.zip']:
            with open(sub['.oct']) as fp:
                file_date = scratch_file_date(fp)
                fp.seek(0)
                copy_scratch_file(path, fp, file_date)
            continue
        for zsub in sub['.zip']:
            with ZipFile(zsub) as zfp:
                for info in zfp.infolist():
                    with zfp.open(info) as fp:
                        file_date = scratch_file_date(fp)
                    # zip files cannot be seeked so we have to reopen
                    with zfp.open(info) as fp:
                        copy_scratch_file(path, fp, file_date, crc=info.CRC)


def main():
    def usage():
        print('Usage: restructure.py PATH\n\nPATH is the location to the saved'
              ' octopi files. This program will group submissions by project '
              'and user.')
        sys.exit(1)
    if len(sys.argv) != 2:
        usage()

    if not os.path.isdir(sys.argv[1]):
        print('{} is not a directory'.format(sys.argv[1]))
        sys.exit(1)

    for project, users in analyze_projects(sys.argv[1]).items():
        for user, submissions in users.items():
            process_group(project, user, submissions)


if __name__ == '__main__':
    sys.exit(main())
