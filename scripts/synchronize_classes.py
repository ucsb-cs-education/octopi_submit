#!/usr/bin/env python
import json
import os
import sys

"""

Formatting

A CLASS_FILE should be or the format:

{username} SPACE {password}

The filename will be the name of the class. The first user listed in each class
will be added as the owner (instructor). If you need additional owners, they
must be added manually.

Additionally, the first line can begin with:

DISPLAY: <CLASS_NAME>

Where <CLASS_NAME> can be replaced with the display name for the class. If not
provieded, the filename will be the name of the class.

"""

DATA_PATH = '/tmp/octopi_files'
SETTINGS_FILENAME = 'settings.json'
USERS_FILENAME = 'users.json'

DISPLAY_PREFIX = 'DISPLAY: '

DRY_RUN = False

def main():
    def usage():
        print('{} CLASS_FILE...'.format(os.path.basename(sys.argv[0])))
        sys.exit(1)

    if len(sys.argv) < 2:
        usage()
    classes = sys.argv[1:]

    users = {}
    class_owners = {}
    class_names = {}
    class_users = {}

    # Parse accounts for each class
    for class_filename in classes:
        try:
            class_name = os.path.splitext(os.path.basename(class_filename))[0]
            with open(class_filename) as fp:
                owner_set = False
                for line in fp:
                    if line.startswith(DISPLAY_PREFIX):
                        name = line[len(DISPLAY_PREFIX):].strip()
                        class_names[class_name] = name
                        continue
                    username, password = line.split()
                    if username in users:
                        print('Warning: User {} already listed.'
                              .format(username))
                    users[username] = password
                    if not owner_set:
                        class_owners[class_name] = username
                        owner_set = True
                    else:
                        class_users.setdefault(class_name, set()).add(username)
        except IOError as exc:
            print('Error with class file: {}'.format(exc))
            return 1

    # Create the DATA_PATH directory if it does not exist
    if not DRY_RUN and not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)

    # Synchronize the set of users
    filename = os.path.join(DATA_PATH, USERS_FILENAME)
    if os.path.exists(filename):
        existing = json.load(open(filename))
    else:
        existing = {}
    for username, password in set(users.items()) - set(existing.items()):
        if username in existing:
            print('Updating password for {}'.format(username))
        else:
            print('Adding user {}'.format(username))
        existing[username] = password
    if not DRY_RUN:
        json.dump(existing, open(filename, 'w'), indent=2, sort_keys=True)

    # Synchronize with the existing class settings
    for filename in os.listdir(DATA_PATH):
        if filename in class_users:  # Load the existing settingse
            settings_path = os.path.join(DATA_PATH, filename,
                                         SETTINGS_FILENAME)
            try:
                settings = json.load(open(settings_path))
            except (IOError, ValueError):
                continue
            changed = False
            # Update the display name
            if filename in class_names and \
                    class_names[filename] != settings.get('name'):
                print('Setting display name of {} to {}'.format(
                        filename, class_names[filename]))
                settings['name'] = class_names[filename]
                changed = True
             # Update the owners
            if class_owners[filename] not in settings['owners']:
                user = class_owners[filename]
                print('Adding owner {} to class {}'.format(user, filename))
                settings['owners'].append(user)
                changed = True
            # Update the students
            for user in class_users[filename] - set(settings['students']):
                print('Adding student {} to class {}'.format(user, filename))
                settings['students'].append(user)
                changed = True
            if changed and not DRY_RUN:
                json.dump(settings, open(settings_path, 'w'),
                          indent=2, sort_keys=True)
            del class_users[filename]

    # Create the new classes
    for class_name, users in class_users.items():
        class_path = os.path.join(DATA_PATH, class_name)
        if not DRY_RUN and not os.path.exists(class_path):
            os.mkdir(class_path)
        settings = {'owners': [class_owners[class_name]],
                    'students': list(users)}
        if class_name in class_names:
            settings['name'] = class_names[class_name]
        if not DRY_RUN:
            json.dump(settings,
                      open(os.path.join(class_path, SETTINGS_FILENAME), 'w'),
                      indent=2, sort_keys=True)
        print('Added class "{}" with owner "{}"'.format(
                class_names[class_name], class_owners[class_name]))

    return 0


if __name__ == '__main__':
    sys.exit(main())
