import os
import sys
from setuptools import setup, find_packages, Command

guardian = __import__('guardian')
readme_file = os.path.join(os.path.dirname(__file__), 'README.rst')
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

class run_flakes(Command):
    """
    Runs pyflakes against guardian codebase.
    """
    description = "Check sources with pyflakes"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            import pyflakes.scripts.pyflakes as flakes
        except ImportError:
            sys.stderr.write("No pyflakes installed!\n")
            sys.exit(-1)

        warns = 0
        # Define top-level directories
        for topdir, dirnames, filenames in os.walk(guardian.__path__[0]):
            paths = (os.path.join(topdir, f) for f in filenames if f .endswith('.py'))
            for path in paths:
                warns += flakes.checkPath(path)
        if warns > 0:
            sys.stderr.write("ERROR: Finished with total %d warnings.\n" % warns)
            sys.exit(1)
        else:
            print "No problems found in source codes."



setup(
    name = 'django-guardian',
    version = guardian.get_version(),
    url = 'http://github.com/lukaszb/django-guardian',
    author = 'Lukasz Balcerzak',
    author_email = 'lukaszbalcerzak@gmail.com',
    download_url='http://github.com/lukaszb/django-guardian/downloads',
    description = guardian.__doc__.strip(),
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
    tests_require = [
        'mock',
    ],
    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Security',
    ],
    test_suite='tests.main',
    cmdclass={'flakes': run_flakes},
)

