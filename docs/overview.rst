.. _overview:

Overview
========

``django-guardian`` is an implementation of object permissions for Django_
providing extra *authentication backend*.

Features
--------

- Object permissions for Django_
- AnonymousUser support
- High level API
- Heavely tested
- Django's admin integration
- Decorators

Incoming
--------

- Admin templates for grappelli_

Source and issue tracker
------------------------

Sources are available at `issue-tracker`_. You may also file a bug there.

Alternate projects
------------------

Django_ 1.2 still has *only* foundation for object permissions [1]_ and
``django-guardian`` make use of new facilities and it is based on them.  There
are some other pluggable applications which does *NOT* require latest 1.2
version of Django_. For instance, there are great `django-authority`_ or
`django-permissions`_ available out there.

.. _django: http://www.djangoproject.com/
.. _django-authority: http://bitbucket.org/jezdez/django-authority/
.. _django-permissions: http://bitbucket.org/diefenbach/django-permissions/
.. _issue-tracker: http://github.com/lukaszb/django-guardian
.. _grappelli: http://code.google.com/p/django-grappelli/

.. [1] See http://docs.djangoproject.com/en/1.2/topics/auth/#handling-object-permissions
   for more detail.

