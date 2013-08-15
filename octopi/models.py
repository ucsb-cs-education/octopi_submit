from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
import os
import time


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Submission(object):
    STORAGE_PATH = '/tmp/octopi_files/'
    OWNERS_FILENAME = 'owners.txt'
    SCRATCH_FILENAME = 'file{}'
    THUMB_FILENAME = 'image.png'

    @classmethod
    def exists(cls, sha1sum, username=None):
        dir_path = os.path.join(cls.STORAGE_PATH, sha1sum)
        if not os.path.isdir(dir_path):
            return False
        # If username is set add it to the owners file if it is not there
        if username:
            owners_file = os.path.join(dir_path, cls.OWNERS_FILENAME)
            owners = open(owners_file).read().split()
            if not username in owners:
                open(owners_file, 'w').write('\n'.join(owners + [username]))
        return True

    @classmethod
    def get_submission_list(cls):
        submissions = []
        for sha1sum in os.listdir(cls.STORAGE_PATH):
            if sha1sum.endswith('~'):
                continue
            owner_path = os.path.join(cls.STORAGE_PATH, sha1sum,
                                      cls.OWNERS_FILENAME)
            submissions.append(cls(sha1sum, open(owner_path).read().split()))
        return submissions

    @classmethod
    def get_submission(cls, sha1sum):
        dir_path = os.path.join(cls.STORAGE_PATH, sha1sum)
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
        return cls(sha1sum, open(owner_path).read().split())

    @classmethod
    def save(cls, sha1sum, file_, ext, scratch, username):
        dir_path = os.path.join(cls.STORAGE_PATH, sha1sum)
        tmp_dir_path = dir_path + '~'
        if os.path.isdir(tmp_dir_path):
            while os.path.isdir(tmp_dir_path):
                tmp_dir_path += '~'
        # Create the directory by sha1sum
        os.mkdir(tmp_dir_path)
        # Add the owner
        with open(os.path.join(tmp_dir_path, cls.OWNERS_FILENAME), 'w') as fp:
            fp.write(username)
        # Save a copy of the file
        with open(os.path.join(tmp_dir_path, cls.SCRATCH_FILENAME.format(ext)),
                  'wb') as fp:
            fp.write(file_.read())
        # Save the thumbnail
        scratch.thumbnail.save(os.path.join(tmp_dir_path, cls.THUMB_FILENAME))
        # Rename the directory (everything worked!)
        os.rename(tmp_dir_path, dir_path)

    def __init__(self, sha1sum, owners):
        self.sha1sum = sha1sum
        self.owners = owners
        self.created_at = os.path.getctime(os.path.join(self.STORAGE_PATH,
                                                        sha1sum))

    @property
    def pretty_created_at(self):
        return time.ctime(self.created_at)

    def get_thumbnail_url(self, request):
        return request.static_url(os.path.join(self.STORAGE_PATH, self.sha1sum,
                                               self.THUMB_FILENAME))

    def get_url(self, request):
        return request.route_url('submission.item',
                                 submission_id=self.sha1sum)


class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    value = Column(Integer)

    def __init__(self, name, value):
        self.name = name
        self.value = value
