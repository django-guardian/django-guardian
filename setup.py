import sys
from setuptools import setup, find_packages

guardian = __import__('guardian')
readme_file = 'README.rst'
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

setup(
    name = 'django-guardian',
    version = guardian.get_version(),
    url = 'http://github.com/lukaszb/django-guardian',
    author = 'Lukasz Balcerzak',
    author_email = 'lukaszbalcerzak@gmail.com',
    download_url='http://github.com/lukaszb/django-guardian/downloads',
    description = guardian.__doc__,
    long_description = long_description,
    zip_safe = False,
    packages = find_packages(),
    include_package_data = True,
    scripts = [],
    requires = [],
    license = 'BSD',
    install_requires = [
        'Django>=1.2',
    ],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Security',
    ],
    test_suite='tests.main',
)

