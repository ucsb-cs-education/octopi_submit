#!/usr/bin/env python
import os
import sys

PROJECTS = ['AnimalRace', 'CAGeographyBroadcast', 'DanceParty', 'MammalsGame',
            'PinataInitialization', 'Planets', 'PlantGrowing', 'RaceGame',
            'Rocket', '_OTHER_']
EXTS = ('.oct', '.octx', '.sb')

DELETE_FILES = set(['file.oct', 'project.oct'])

OKAY = set()
for project in PROJECTS:
    for ext in EXTS:
        OKAY.add(project + ext)

MAPPING = {'Lesson 1*: Sequence - Predator\Prey': 'MammalsGame',
           'Lesson 2: Events - Planets': 'Planets',
           'Lesson 2B: Initialization - Race': 'AnimalRace',
           'Lesson 3*: Broadcast - Geography': 'CAGeographyBroadcast',
           'Lesson 4*: Costumes - Dance Party': 'DanceParty',
           'Lesson 4: Costumes - Racing': 'RaceGame'}
for from_name, to_name in MAPPING.items():
    for ext in EXTS:
        MAPPING[from_name + ext] = to_name + ext
    del MAPPING[from_name]

READ_ONLY = False


def fix_submission(project_path, sha1sum):
    submission_path = os.path.join(project_path, sha1sum)
    if not os.path.isdir(submission_path):
        print submission_path
        sys.exit(1)
    unhandled = os.listdir(submission_path)
    unhandled.remove('image.png')
    unhandled.remove('owners.json')
    if 'results.html' not in unhandled:
        with open(os.path.join(submission_path, 'results.html'), 'w'):
            pass
    else:
        unhandled.remove('results.html')
    has_octx_symlink = None
    history_file = None
    project = None
    unexpected = []

    while unhandled:
        filename = unhandled.pop(0)
        path = os.path.join(submission_path, filename)
        if filename.startswith('history_') and filename.endswith('.zip'):
            history_file = filename
        elif os.path.islink(path):
            if not project and unhandled:  # handle symlinks last
                unhandled.append(filename)
                continue

            link_dst = os.readlink(path)
            assert os.path.isfile(os.path.join(submission_path, link_dst))
            if not link_dst.startswith('history_') and \
                    (project != '_OTHER_' or link_dst != project + '.oct'):
                print('Invalid symlink {}'.format(path))
                sys.exit(1)

            if os.path.basename(project_path) == '_OTHER_':
                print('ignore _OTHER_ symlink {}'.format(filename))
            elif project:
                assert filename == project + '.octx'
                has_octx_symlink = True
            else:
                unexpected.append(filename)
        elif filename in OKAY:
            if project:
                print 'duplicate project name', project, filename
                sys.exit(1)
            else:
                project = os.path.splitext(filename)[0]
        elif filename in MAPPING:
            print('renaming {} {}'.format(filename, MAPPING[filename]))
            if not READ_ONLY:
                os.rename(path,
                          os.path.join(submission_path, MAPPING[filename]))
            unhandled.append(MAPPING[filename])
        elif filename.startswith('.project(') or filename in DELETE_FILES:
            print('deleting {}'.format(filename))
            if not READ_ONLY:
                os.unlink(path)
        else:
            unexpected.append(filename)

    if unexpected or not project:
        print('Did not expect {} in {}'.format(', '.join(unexpected),
                                               submission_path))
        sys.exit(1)

    if project == '_OTHER_':
        assert not has_octx_symlink
    elif history_file and not has_octx_symlink:
        path = os.path.join(submission_path, project + '.octx')
        print('Creating symlink {}'.format(path))
        if not READ_ONLY:
            os.symlink(history_file, path)

    return project


def fix_project(class_path, project_name):
    project_path = os.path.join(class_path, project_name)
    if not os.path.isdir(project_path):
        return []

    to_rename = []

    for sha1sum in os.listdir(project_path):
        new_project = fix_submission(project_path, sha1sum)
        if project_name != new_project:
            to_rename.append((os.path.join(project_path, sha1sum),
                              os.path.join(class_path, new_project)))
    return to_rename


def fix_class(class_path):
    if not os.path.isdir(class_path):
        return []

    to_rename = []

    for project_name in os.listdir(class_path):
        to_rename.extend(fix_project(class_path, project_name))

    for src, dst in to_rename:
        if not os.path.isdir(dst):
            os.mkdir(dst)
        dst = os.path.join(dst, os.path.basename(src))
        print('Renaming {} to {}'.format(src, dst))
        if not READ_ONLY:
            os.rename(src, dst)


def main():
    BASE_PATH = '/tmp/octopi_files'
    for class_name in os.listdir(BASE_PATH):
        fix_class(os.path.join(BASE_PATH, class_name))

if __name__ == '__main__':
    sys.exit(main())
