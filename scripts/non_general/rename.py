#!/usr/bin/env python
import os
import sys


def main():
    for path, dirs, files in os.walk('.'):
        for filename in files:
            name, ext = os.path.splitext(filename)
            if name.startswith('Lesson2'):
                src = os.path.join(path, filename)
                dst_name = 'Planets'
                if name.endswith('-1'):
                    dst_name += '-1'
                dst = os.path.join(path, dst_name + ext)
                if os.path.isfile(dst):
                    print('Cannot rename {}'.format(src))
                    continue
                os.rename(src, dst)


if __name__ == '__main__':
    sys.exit(main())
