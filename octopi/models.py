from pyramid.security import ALL_PERMISSIONS, Allow, Authenticated, Everyone
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
import os
import time


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

OWNERS_FILENAME = 'owners.txt'


class User(object):
    @property
    def __acl__(self):
        return [(Allow, self.username, 'view')]

    def __init__(self, username, password, groups=None):
        self.username = username
        self.password = password
        self.groups = groups or []


class Project(object):
    STORAGE_PATH = '/tmp/octopi_files/'

    @classmethod
    def exists(cls, name):
        return os.path.isdir(os.path.join(cls.STORAGE_PATH, name))

    @classmethod
    def get_project_list(cls):
        projects = []
        for filename in os.listdir(cls.STORAGE_PATH):
            dir_path = os.path.join(cls.STORAGE_PATH, filename)
            owner_path = os.path.join(dir_path, OWNERS_FILENAME)
            if not (os.path.isdir(dir_path) and os.path.isfile(owner_path)):
                continue
            projects.append(cls(filename, open(owner_path).read().split()))
        return projects

    @classmethod
    def get_project(cls, name):
        dir_path = os.path.join(cls.STORAGE_PATH, name)
        owner_path = os.path.join(dir_path, OWNERS_FILENAME)
        if not os.path.isdir(dir_path) or not os.path.isfile(owner_path):
            return False
        return cls(name, open(owner_path).read().split())

    @property
    def __acl__(self):
        return [(Allow, x, 'view') for x in self.owners] + \
            [(Allow, Everyone, 'submit')]

    def __init__(self, name, owners):
        self.name = name
        self.owners = owners
        self.path = os.path.join(self.STORAGE_PATH, name)

    def __getitem__(self, key):
        submission = Submission.get_submission(self, key)
        if not submission:
            raise KeyError
        submission.__parent__ = self
        submission.__name__ = key
        return submission

    def get_user_submissions(self, username):
        submissions = Submission.get_submission_list(self)
        if 'admin' in USERS[username].groups or username in self.owners:
            return submissions
        return [s for s in submissions if username in s.owners]


class Submission(object):
    SCRATCH_FILENAME = 'file{}'
    THUMB_FILENAME = 'image.png'

    @property
    def __acl__(self):
        return [(Allow, x, 'view') for x in self.owners]

    @classmethod
    def exists(cls, project, sha1sum, username=None):
        dir_path = os.path.join(project.path, sha1sum)
        if not os.path.isdir(dir_path):
            return False
        # If username is set add it to the owners file if it is not there
        if username:
            owners_file = os.path.join(dir_path, OWNERS_FILENAME)
            owners = open(owners_file).read().split()
            if not username in owners:
                open(owners_file, 'w').write('\n'.join(owners + [username]))
        return True

    @classmethod
    def get_submission_list(cls, project):
        submissions = []
        for sha1sum in os.listdir(project.path):
            submission_path = os.path.join(project.path, sha1sum)
            if sha1sum.endswith('~') or not os.path.isdir(submission_path):
                continue
            owner_path = os.path.join(submission_path, OWNERS_FILENAME)
            submissions.append(cls(project, sha1sum,
                                   open(owner_path).read().split()))
        return submissions

    @classmethod
    def get_submission(cls, project, sha1sum):
        dir_path = os.path.join(project.path, sha1sum)
        owner_path = os.path.join(dir_path, OWNERS_FILENAME)
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
    def save(cls, project, sha1sum, file_, ext, scratch, username):
        dir_path = os.path.join(project.path, sha1sum)
        tmp_dir_path = dir_path + '~'
        if os.path.isdir(tmp_dir_path):
            while os.path.isdir(tmp_dir_path):
                tmp_dir_path += '~'
        # Create the directory by sha1sum
        os.mkdir(tmp_dir_path)
        # Add the owner
        with open(os.path.join(tmp_dir_path, OWNERS_FILENAME), 'w') as fp:
            fp.write(username)
        # Save a copy of the file
        with open(os.path.join(tmp_dir_path, cls.SCRATCH_FILENAME.format(ext)),
                  'wb') as fp:
            fp.write(file_.read())
        # Save the thumbnail
        scratch.thumbnail.save(os.path.join(tmp_dir_path, cls.THUMB_FILENAME))
        # Rename the directory (everything worked!)
        os.rename(tmp_dir_path, dir_path)

    def __init__(self, project, sha1sum, owners):
        self.project = project
        self.sha1sum = sha1sum
        self.owners = owners
        self.created_at = os.path.getctime(os.path.join(project.path,
                                                        sha1sum))

    @property
    def pretty_created_at(self):
        return time.ctime(self.created_at)

    def get_thumbnail_url(self, request):
        return request.static_url(os.path.join(self.project.path, self.sha1sum,
                                               self.THUMB_FILENAME))

    def get_url(self, request):
        return request.route_url('submission.item',
                                 project_id=self.project.name,
                                 submission_id=self.sha1sum)


USERS = {'admin': User('admin', 'admin', ['admin']),
         'user1': User('user1', 'user1'),
         'user2': User('user2', 'user2'),
         'user3': User('user3', 'user3')}


class ProjectFactory(object):
    __acl__ = [(Allow, 'g:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        pass

    def __getitem__(self, key):
        project = Project.get_project(key)
        print project
        if not project:
            raise KeyError
        project.__parent__ = self
        project.__name__ = key
        return project


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


class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    value = Column(Integer)

    def __init__(self, name, value):
        self.name = name
        self.value = value
