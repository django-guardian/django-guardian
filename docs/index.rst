.. _index:

Welcome to django-guardian documentation!
=========================================

``django-guardian`` is an implementation of object permissions for Django_ 1.2
providing extra *authentication backend*.

**Features**

- Object permissions for Django_
- AnonymousUser support
- High level API
- Heavely tested

**Incoming**

- Django's admin integration
- Management commands
- Decorators

Documentation
=============

**Installation and project configuration**

.. toctree::
   :maxdepth: 1

   installation
   configuration

**Object permissions**

.. toctree::
   :maxdepth: 1

   assign
   check
   remove

**Development**

.. toctree::
   :maxdepth: 1

   changes
   testing
   example_project

**API**

.. toctree::
   :maxdepth: 2

   api/index
  
Source and issue tracker
========================

Sources are available at `issue-tracker`_. You may also file a bug there.

Alternate projects
==================

Django_ 1.2 still has *only* foundation for object permissions [1]_ and
``django-guardian`` make use of new facilities and it is based on them.  There
are some other pluggable applications which does *NOT* require latest 1.2
version of Django_. For instance, there are great `django-authority`_ or
`django-permissions`_ available out there.

Other topics
============

* :ref:`genindex`
* :ref:`search`

.. _django: http://www.djangoproject.com/
.. _django-authority: http://bitbucket.org/jezdez/django-authority/
.. _django-permissions: http://bitbucket.org/diefenbach/django-permissions/
.. _issue-tracker: http://github.com/lukaszb/django-guardian

.. [1] See http://docs.djangoproject.com/en/1.2/topics/auth/#handling-object-permissions
   for more detail.

