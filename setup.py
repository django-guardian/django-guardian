import os
import sys
from setuptools import setup, find_packages
from extras import RunFlakesCommand

version_file = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
with open(version_file, 'r') as f:
    version = f.readline().strip()

readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(version_file, 'r') as f:
    long_description = f.readline().strip()

tests_require = ['mock', 'django-environ']

extra_kwargs = {}
if sys.version_info >= (3,):
    extra_kwargs = {'use_2to3': True}
elif sys.version_info < (2, 7):
    tests_require.append('unittest2')

setup(
    name = 'django-guardian',
    version = version,
    url = 'http://github.com/django-guardian/django-guardian',
    author = 'Lukasz Balcerzak',
    author_email = 'lukaszbalcerzak@gmail.com',
    download_url='https://github.com/django-guardian/django-guardian/tags',
    description ="Implementation of per object permissions for Django.",
    long_description = long_description,
    zip_safe = False,
    packages = find_packages(),
    include_package_data = True,
    license = 'BSD',
    install_requires = [
        'Django >= 1.7',
        'six',
    ],
    tests_require=tests_require,
    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Security',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests.main',
    cmdclass={'flakes': RunFlakesCommand},
    **extra_kwargs
)

