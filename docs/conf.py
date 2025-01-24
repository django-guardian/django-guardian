import os
import sphinx_rtd_theme
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'guardian.testapp.testsettings'
guardian = __import__('guardian')

import django

django.setup()

# -- General configuration -----------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'exts']

autoclass_content = "both"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['templates']

# The suffix of source filenames.
source_suffix = {'.rst': 'restructuredtext'}

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'django-guardian'
copyright = 'Contributors to the django-guardian project'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = guardian.__version__
# The full version, including alpha/beta/rc tags.
release = version


# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['build']


# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output ---------------------------------------------

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'


# Output file base name for HTML help builder.
htmlhelp_basename = 'guardiandoc'

