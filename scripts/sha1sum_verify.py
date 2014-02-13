#!/usr/bin/env python
import os
import sys
from hashlib import sha1

EXTS = ['.oct', '.sb']


def test_submission(project_path, sha1sum):
    project = os.path.basename(project_path)
    submission_path = os.path.join(project_path, sha1sum)

    filepath = None
    for ext in EXTS:
        filepath = os.path.join(submission_path, project + ext)
        if os.path.isfile(filepath):
            break
    else:
        print('Could not find project file')
        sys.exit(1)

    with open(filepath) as fp:
        calculated = sha1(fp.read()).hexdigest()
    if sha1sum != calculated:
        print('Mismatch at {}'.format(filepath))


def test_project(class_path, project_name):
    project_path = os.path.join(class_path, project_name)
    if not os.path.isdir(project_path):
        return
    for sha1sum in os.listdir(project_path):
        test_submission(project_path, sha1sum)


def test_class(class_path):
    if not os.path.isdir(class_path):
        return
    for project_name in os.listdir(class_path):
        test_project(class_path, project_name)


def main():
    BASE_PATH = '/tmp/octopi_files'
    for class_name in os.listdir(BASE_PATH):
        test_class(os.path.join(BASE_PATH, class_name))

if __name__ == '__main__':
    sys.exit(main())
