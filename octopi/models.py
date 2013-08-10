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

    @classmethod
    def get_submission_list(cls):
        submissions = []
        for filename in os.listdir(cls.STORAGE_PATH):
            submissions.append(cls(filename))
        return submissions

    @classmethod
    def get_submission(cls, filename):
        if not os.path.isfile(os.path.join(cls.STORAGE_PATH, filename)):
            return False
        return cls(filename)

    def __init__(self, filename):
        self.filename = filename
        self.created_at = os.path.getctime(os.path.join(self.STORAGE_PATH,
                                                        filename))

    @property
    def pretty_created_at(self):
        return time.ctime(self.created_at)

    def get_url(self, request):
        return request.route_url('submission_item',
                                 submission_id=self.filename)


class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    value = Column(Integer)

    def __init__(self, name, value):
        self.name = name
        self.value = value
