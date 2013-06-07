from setuptools import setup, find_packages
import sys

umessages = __import__('umessages')

readme_file = 'README.mkd'
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

setup(name='django-umessages',
      version=umessages.get_version(),
      description='User messaging application for Django',
      long_description=long_description,
      zip_safe=False,
      author='Petar Radosevic, Euan Lau',
      author_email='petar@wunki.org, euanlau@gmail.com',
      url='https://github.com/euanlau/django-umessages/',
      download_url='https://github.com/euanlau/django-umessages/downloads',
      packages = find_packages(exclude=['demo', 'demo.*']),
      include_package_data=True,
      install_requires = [
	django-crispy-forms,
        ### Required to build documentation
        # 'sphinx',
        # 'south',
      ],
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
