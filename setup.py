import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'SQLAlchemy',
    'hairball>=0.1rc3',
    'kelp',
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_layout',
    'pyramid_tm',
    'transaction',
    'waitress',
    'zope.sqlalchemy']

setup(name='octopi',
      version='0.0',
      description='octopi',
      long_description=README + '\n\n' + CHANGES,
      classifiers=["Programming Language :: Python",
                   "Framework :: Pyramid",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='octopi',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = octopi:main
      [console_scripts]
      initialize_octopi_db = octopi.scripts.initializedb:main
      """,
      )
