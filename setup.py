from setuptools import setup, find_packages
import sys

readme_file = 'README.mkd'
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

setup(name='django-umessages',
      version='1.0.0',
      install_requires = [
	'django-crispy-forms>=1.1.1',
        ### Required to build documentation
        # 'sphinx',
        # 'south',
      ],
      requires=[
        'Django (>=1.3)',   # Using staticfiles
      ],
      description='User messaging application for Django',
      long_description=long_description,
      zip_safe=False,
      author='Petar Radosevic, Euan Lau',
      author_email='petar@wunki.org, euanlau@gmail.com',
      url='https://github.com/euanlau/django-umessages/',
      download_url='https://github.com/euanlau/django-umessages/downloads',
      packages = find_packages(exclude=['demo', 'demo.*']),
      include_package_data=True,
      test_suite='tests.main',
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Web Environment',
                     'Framework :: Django',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: Utilities'],
      )
