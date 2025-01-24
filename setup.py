from setuptools import setup

import os

version = '3.0.0rc1'

readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')
with open(readme_file) as f:
    long_description = f.read()

setup(
    name='django-guardian',
    version=version,
    python_requires='>=3.8',
    url='http://github.com/django-guardian/django-guardian',
    author='Lukasz Balcerzak',
    author_email='lukaszbalcerzak@gmail.com',
    download_url='https://github.com/django-guardian/django-guardian/tags',
    description="Implementation of per object permissions for Django.",
    long_description=long_description,
    zip_safe=False,
    packages=[
        'guardian', 'guardian.conf', 'guardian.management',
        'guardian.migrations', 'guardian.templatetags', 'guardian.testapp',
        'guardian.management.commands', 'guardian.testapp.migrations',
        'guardian.testapp.tests'
    ],
    include_package_data=True,
    license='BSD',
    install_requires=["Django>=3.2"],
    tests_require=['mock', 'django-environ', 'pytest', 'pytest-django'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Framework :: Django :: 3.2',
                 'Framework :: Django :: 4.1',
                 'Framework :: Django :: 4.2',
                 'Framework :: Django :: 5.0',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Security',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3 :: Only',
                 'Programming Language :: Python :: 3.8',
                 'Programming Language :: Python :: 3.9',
                 'Programming Language :: Python :: 3.10',
                 'Programming Language :: Python :: 3.11',
                 'Programming Language :: Python :: 3.12',
                 ],
    test_suite='tests.main'
)
