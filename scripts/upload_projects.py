#!/usr/bin/env python
import json
import os
import requests
import sys


def main():
    SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(SCRIPT_PATH, 'users.json')) as fp:
        users = json.load(fp)

    for path, dirs, files in os.walk('.'):
        user = os.path.basename(path)
        if not files:
            continue
        if user not in users:
            print('Cannot find {}'.format(user))
            continue

        print user, users[user]

        with requests.Session() as s:
            resp = s.post('http://octopi.cs.ucsb.edu/login',
                          allow_redirects=False, data={'login': user,
                                                       'passwd': users[user],
                                                       'submit': 'a'})
            assert resp.status_code == 302

            for filename in files:
                filepath = os.path.join(path, filename)
                with open(filepath) as fp:
                    resp = s.post('http://octopi.cs.ucsb.edu/sub/',
                                  allow_redirects=False,
                                  files={'file_to_upload': fp})
                    print resp.status_code, filepath


if __name__ == '__main__':
    sys.exit(main())
