#!/usr/bin/env python
from hashlib import sha1
from zipfile import ZipFile
import os
import sys


def remove_prompt(path1, path2):
    print('Duplicate files detected:\n(A) {}\n(B) {}'
          .format(path1, path2))
    response = raw_input('Do you want to remove (A), (B) or (N)either? ')
    if response.lower() == 'a':
        print 'removing {}'.format(path1)
        os.unlink(path1)
        return path2
    elif response.lower() == 'b':
        print 'removing {}'.format(path2)
        os.unlink(path2)
        return path1
    return None


def remove_longer(path1, path2):
    if len(path1) > len(path2):
        print('Removing {}'.format(path1))
        os.unlink(path1)
        return path2
    elif len(path2) > len(path1):
        print('Removing {}'.format(path2))
        os.unlink(path2)
        return path1
    print path1, path2
    if path1 < path2:
        return path1
    else:
        return path2


def remove_if_zip_duplicate(to_remove, zip_info, zip_path):
    def clean(path):
        if path.endswith('/backup'):
            return os.path.dirname(path)
        return path
    if isinstance(to_remove, basestring):
        to_remove_dir = clean(os.path.dirname(to_remove))
        zip_path_dir = clean(os.path.dirname(zip_path))

        if to_remove_dir == zip_path_dir:
            print('Removing {}'.format(to_remove))
            os.unlink(to_remove)
            return zip_info, zip_path
        else:
            print to_remove, zip_path
    print to_remove[1]
    print zip_path
    print
    return None


def main():
    sha1s = {'.oct': {}, '.octx': {}}
    # First remove top-level duplicate files
    for path, dirs, filenames in os.walk('.'):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext in sha1s:
                filepath = os.path.join(path, filename)
                with open(filepath) as fp:
                    sha1sum = sha1(fp.read()).hexdigest()
                if sha1sum in sha1s[ext]:
                    updated = remove_longer(sha1s[ext][sha1sum], filepath)
                    if updated:
                        sha1s[ext][sha1sum] = updated
                else:
                    sha1s[ext][sha1sum] = filepath

    # Second remove files in the same directory if they're contained in a octx
    for path, dirs, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith('.octx'):  # Compute sha1 for each file in zip
                filepath = os.path.join(path, filename)
                with ZipFile(filepath) as zfp:
                    for info in zfp.infolist():
                        with zfp.open(info) as fp:
                            sha1sum = sha1(fp.read()).hexdigest()
                        if sha1sum in sha1s['.oct']:
                            updated = remove_if_zip_duplicate(
                                sha1s['.oct'][sha1sum], info, filepath)
                            if updated:
                                sha1s['.oct'][sha1sum] = updated
                        else:
                            sha1s['.oct'][sha1sum] = info, filepath


if __name__ == '__main__':
    sys.exit(main())
