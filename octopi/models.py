from pyramid.security import (ALL_PERMISSIONS, Allow, Authenticated, DENY_ALL,
                              authenticated_userid)
import json
import os
import shutil
import time


STORAGE_PATH = '/tmp/octopi_files'


class User(object):
    @property
    def __acl__(self):
        return [(Allow, self.username, 'view')]

    @property
    def classes(self):
        return self.owner_of | self.student_of

    @property
    def classes_dict(self):
        return {x.name: x for x in self.classes}

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.owner_of = set()
        self.student_of = set()
        self.groups = ['admin'] if username.startswith('admin_') else []

    def make_owner(self, class_):
        self.owner_of.add(class_)

    def make_student(self, class_):
        self.student_of.add(class_)

    def get_projects(self):
        if 'admin' in self.groups:
            return [x for class_ in CLASSES.values()
                    for x in class_.projects.values()]
        return [x for class_ in self.classes
                for x in class_.projects.values()]


class Class(object):
    @property
    def viewers(self):
        return self.owners | self.students

    def __init__(self, name, settings):
        self.name = name
        self.owners = set()
        self.students = set()
        self.projects = {}

        # Update users dictionary to list what classes the user is either
        # an owner, or a student of
        for username in settings['owners']:
            USERS[username].make_owner(self)
            self.owners.add(USERS[username])
        for username in settings['students']:
            USERS[username].make_student(self)
            self.students.add(USERS[username])
        for project_name, plugin in settings['projects'].items():
            project = Project(project_name, plugin, self)
            self.projects[project.name] = project
            # Create the project directory if it does not exist
            path = os.path.join(STORAGE_PATH, name, project.name)
            if not os.path.isdir(path):
                os.mkdir(path)

    def __getitem__(self, project_id):
        return self.projects[project_id]


class Project(object):
    @property
    def __acl__(self):
        acl = [(Allow, Authenticated, 'submit')] +\
            [(Allow, x.username, 'view') for x in self.class_.viewers]
        return acl

    @property
    def display_name(self):
        return '({}) {}'.format(self.class_.name, self.name)

    @property
    def form_name(self):
        return json.dumps((self.class_.name, self.name))

    @property
    def path(self):
        return os.path.join(STORAGE_PATH, self.class_.name, self.name)

    def __init__(self, name, plugin, class_):
        self.name = name.replace('/', '\\')
        self.plugin = plugin
        self.class_ = class_

    def __getitem__(self, key):
        submission = Submission.get_submission(self, key)
        if not submission:
            raise KeyError
        submission.__parent__ = self
        submission.__name__ = key
        return submission

    def get_submissions(self, user=None):
        # Verify access
        if user:
            owner = 'admin' in user.groups or self.class_ in user.owner_of
            if not owner and self.class_ not in user.student_of:
                raise Exception('Invalid project for {}'.format(user.name))
        else:
            owner = True  # No user specified, fetch all submissions

        # Build the list of submissions
        submissions = []
        for filename in os.listdir(self.path):
            path = os.path.join(self.path, filename)
            if filename.endswith('~') or not os.path.isdir(path):
                continue
            submissions.append(Submission(self, filename))

        # Return the appropriate list
        if owner:
            return submissions
        return [s for s in submissions if user.username in s.owners]

    def has_submission(self, sha1sum, add_user=None):
        path = os.path.join(self.path, sha1sum)
        if not os.path.isdir(path):
            return False
        # Add user to owners file if add_user is set and it is not there
        if add_user:
            submission = Submission(self, sha1sum)
            submission.make_owner(add_user)


class Submission(object):
    RESULTS_FILENAME = 'results.html'
    OWNERS_FILENAME = 'owners.json'
    SCRATCH_FILENAME = 'file{}'
    THUMB_FILENAME = 'image.png'

    @property
    def __acl__(self):
        return ([(Allow, x, 'view') for x in self.owners]
                + [(Allow, 'g:admin', ALL_PERMISSIONS)])

    @classmethod
    def get_submission(cls, project, sha1sum):
        dir_path = os.path.join(project.path, sha1sum)
        owner_path = os.path.join(dir_path, cls.OWNERS_FILENAME)
        if not os.path.isdir(dir_path) or not os.path.isfile(owner_path):
            return False
        scratch_file = None
        for ext in ('.oct', '.sb', '.sb2'):
            scratch_file = os.path.join(dir_path,
                                        cls.SCRATCH_FILENAME.format(ext))
            if os.path.isfile(scratch_file):
                break
        else:
            return False
        return cls(project, sha1sum, open(owner_path).read().split())

    @classmethod
    def save(cls, project, sha1sum, file_, ext, scratch, user):
        dir_path = os.path.join(project.path, sha1sum)
        tmp_dir_path = dir_path + '~'
        if os.path.isdir(tmp_dir_path):
            while os.path.isdir(tmp_dir_path):
                tmp_dir_path += '~'
        # Create the directory by sha1sum
        os.mkdir(tmp_dir_path)
        # Save a copy of the file
        file_.seek(0)
        with open(os.path.join(tmp_dir_path, cls.SCRATCH_FILENAME.format(ext)),
                  'wb') as fp:
            fp.write(file_.read())
        # Save the thumbnail
        scratch.thumbnail.save(os.path.join(tmp_dir_path, cls.THUMB_FILENAME))
        # Rename the directory (everything worked!)
        if os.path.isdir(dir_path):  # Delete the old directory if it exists
            shutil.rmtree(dir_path)
        os.rename(tmp_dir_path, dir_path)
        # Add the owner after the folder has been renamed
        submission = Submission(project, sha1sum, create=True)
        submission.make_owner(user)

    def __init__(self, project, sha1sum, create=False):
        self.project = project
        self.sha1sum = sha1sum
        if create:
            self.owners = set()
        else:
            path = os.path.join(project.path, sha1sum, self.OWNERS_FILENAME)
            self.owners = set(json.load(open(path)))
        self.created_at = os.path.getctime(os.path.join(project.path,
                                                        sha1sum))

    @property
    def pretty_created_at(self):
        return time.ctime(self.created_at)

    def get_results(self):
        return open(os.path.join(self.project.path, self.sha1sum,
                                 self.RESULTS_FILENAME)).read()

    def get_thumbnail_url(self, request):
        return request.static_url(os.path.join(self.project.path, self.sha1sum,
                                               self.THUMB_FILENAME))

    def get_url(self, request):
        return request.route_url('submission.item',
                                 class_id=self.project.class_.name,
                                 project_id=self.project.name,
                                 submission_id=self.sha1sum)

    def make_owner(self, user):
        if user.username not in self.owners:
            self.owners.add(user.username)
            with open(os.path.join(self.project.path, self.sha1sum,
                                   self.OWNERS_FILENAME), 'w') as fp:
                json.dump(list(self.owners), fp)


class ClassFactory(object):
    __acl__ = [(Allow, 'g:admin', ALL_PERMISSIONS),
               DENY_ALL]

    def __init__(self, request):
        pass

    def __getitem__(self, class_id):
        return CLASSES[class_id]


class RootFactory(object):
    __acl__ = [(Allow, 'g:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        pass


class SubmissionFactory(object):
    __acl__ = [(Allow, Authenticated, ('create', 'list')),
               (Allow, 'g:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        pass


def groupfinder(userid, request):
    user = USERS.get(userid)
    if user:
        return ['g:{}'.format(x) for x in user.groups]


USERS = {}
CLASSES = {}


def _initialize():
    # users.json is a simple mapping between users and password
    # convert to a more usable internal format
    users = json.load(open(os.path.join(STORAGE_PATH, 'users.json')))
    for user in users:
        USERS[user] = User(user, users[user])

    # Update users dictionary to list the classes they belong to
    for filename in os.listdir(STORAGE_PATH):
        class_path = os.path.join(STORAGE_PATH, filename)
        if os.path.isdir(class_path):
            settings = json.load(open(os.path.join(class_path,
                                                   'settings.json')))
            CLASSES[filename] = Class(filename, settings)


_initialize()
